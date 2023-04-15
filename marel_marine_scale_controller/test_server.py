import socket
import threading
import random
import time
import logging

from marel_marine_scale_controller import LUA_SCRIPT_PATH

DOWNLOAD_PORT = 52202
UPLOAD_PORT = 52203

logging.basicConfig(level=logging.DEBUG)

class TestServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.running = False
        self.upload_running = False
        self.download_running = False

        self._socket = None
        self._upload_socket = None
        self._download_socket = None

        self.conns = {}

        self.thread = None
        self.upload_thread = None
        self.download_thread = None

        logging.info(f'Test server host: {host}')

    def run(self):
        logging.info(f"Test server listening on port {self.port}")
        while self.running:
            try:
                conn, addr = self._socket.accept()
                logging.info(f"Test server accepted connection from {addr}")
                threading.Thread(target=self.handle_connection, args=(conn, addr[1])).start()
            except Exception as e:
                logging.debug(f"Error accepting connection: {e}")
                time.sleep(1)

    def upload_run(self):
        logging.info(f"Test upload server on port {UPLOAD_PORT}")
        with open(LUA_SCRIPT_PATH, 'r') as lua_app:
            lua_script = lua_app.read() + '\n'

        while self.upload_running:
            try:
                conn, addr = self._upload_socket.accept()
                logging.info(f"Test upload Server accepted connection from {addr}")
                #time.sleep(2)
                conn.sendall(lua_script.encode())
                logging.info("send all done")
                #time.sleep(1)
                conn.close()

            except Exception as e:
                logging.debug(f"upload Test Error accepting connection: {e}")
                time.sleep(1)

    def download_run(self):
        logging.info(f"Test download server on port {DOWNLOAD_PORT}")
        with open(LUA_SCRIPT_PATH, 'r') as lua_app:
            lua_script = lua_app.read()

        while self.download_running:
            try:
                conn, addr = self._download_socket.accept()
                conn.close()
                logging.info(f"Test Download Server accepted connection from {addr}")
            except Exception as e:
                logging.debug(f"Download Test Error accepting connection: {e}")
                time.sleep(1)

    def start(self, number_of_connections=5):
        logging.info('Starting Test')

        self.running = True
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        while self.running:
            try:
                self._socket.bind((self.host, self.port))
                break
            except OSError:
                self.port += 1

        self._socket.listen(number_of_connections)

        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def start_test_download(self, number_of_connections=5):
        logging.info('Starting Download test')

        self.download_running = True
        self._download_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._download_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        while self.download_running:
            try:
                self._download_socket.bind((self.host, DOWNLOAD_PORT))
                break
            except OSError:
                logging.debug(f'Error, download port {DOWNLOAD_PORT} unavailable. (Retrying in 2 seconds)')
                time.sleep(2)

        self._download_socket.listen(number_of_connections)
        self.download_thread = threading.Thread(target=self.download_run, daemon=True)
        self.download_thread.start()

        #----------------------------------------------------#

        self.upload_running = True
        self._upload_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._upload_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        while self.upload_running:
            try:
                self._upload_socket.bind((self.host, UPLOAD_PORT))
                break
            except OSError:
                logging.debug(f'Error, upload port {UPLOAD_PORT} unavailable. (Retrying in 2 seconds)')
                time.sleep(2)

        self._upload_socket.listen(number_of_connections)
        self.upload_thread = threading.Thread(target=self.upload_run, daemon=True)
        self.upload_thread.start()

    def handle_connection(self, conn, name):
        self.conns[name] = conn
        try:
            while True:
                message = self.generate_message()
                conn.sendall(message.encode())
                logging.debug(f"sent: {message}")
                time.sleep(1)
        except Exception as e:
            logging.debug(f"Error handling connection: {e}")
        finally:
            conn.close()
            self.conns.pop(name)

    def stop(self):
        self.running = False
        self.download_running = False
        for k, v in self.conns.items():
            v.detach()

        if self._socket:
            self._socket.close()
            self._socket = None

        if self._download_socket:
            self._download_socket.close()
            self._download_socket = None



    @staticmethod
    def generate_message():
        sensor_id = random.choice(['w'])
        value = random.uniform(0, 100)
        unit = 'kg'
        message = f"%{sensor_id},{value:.2f}{unit}#\n"
        return message

    def send_to(self, name, msg):
        self.conns[name].sendall(msg.encode())


if __name__ == "__main__":
    HOST = "localhost"
    PORT = 52212

    s = TestServer(HOST, PORT)
    s.start()
    s.start_test_download()
