import socket
import threading
import time
import logging

from marel_marine_scale_controller.gui import LUA_SCRIPT_PATH
from marel_marine_scale_controller.marel_controller import COMM_PORT, MarelController, DOWNLOAD_PORT, UPLOAD_PORT

HOST = "localhost"

ABS_LUA_SCRIPT_PATH = "../marel_marine_scale_controller/" + LUA_SCRIPT_PATH

logging.basicConfig(level=logging.ERROR)


class Server:
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

    def start_comm_port(self, number_of_connections=5):
        logging.info('Starting Test')

        self.running = True
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        while self.running:
            try:
                self._socket.bind((self.host, self.port))
                break
            except OSError:
                logging.debug(f'Error, download port {COMM_PORT} unavailable. (Retrying in 2 seconds)')
                time.sleep(2)
                #self.port += 1

        self._socket.listen(number_of_connections)
        self.thread = threading.Thread(target=self.run_comm_port, daemon=True)
        self.thread.start()

    def start_download(self, number_of_connections=5):
        logging.info('Starting Download')

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
        self.download_thread = threading.Thread(target=self.run_download, daemon=True)
        self.download_thread.start()

    def start_upload(self, number_of_connections=5):
        logging.info('Starting Upload')

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
        self.upload_thread = threading.Thread(target=self.run_upload, daemon=True)
        self.upload_thread.start()

    def run_comm_port(self):
        logging.info(f"Test server listening on port {self.port}")
        while self.running:
            try:
                conn, addr = self._socket.accept()
                logging.info(f"Test server accepted connection from {addr}")
                threading.Thread(target=self.handle_connection, args=(conn, addr[1])).start()
            except Exception as e:
                logging.debug(f"Error accepting connection: {e}")
                time.sleep(1)

    def run_upload(self):
        logging.info(f"Test upload server on port {UPLOAD_PORT}")
        with open(ABS_LUA_SCRIPT_PATH, 'r') as lua_app:
            lua_script = lua_app.read()

        while self.upload_running:
            try:
                conn, addr = self._upload_socket.accept()
                logging.info(f"Test upload Server accepted connection from {addr}")
                # time.sleep(2)
                conn.sendall(lua_script.encode())
                logging.info("send all done")
                # time.sleep(1)
                conn.close()

            except Exception as e:
                logging.debug(f"upload Test Error accepting connection: {e}")
                time.sleep(1)

    def run_download(self):
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

    def handle_connection(self, conn, name):
        self.conns[name] = conn
        try:
            while True:
                message = self.generate_message()
                conn.sendall(message.encode())
                logging.debug(f"sent: {message}")
                time.sleep(.2)
        except Exception as e:
            logging.debug(f"Error handling connection: {e}")
        finally:
            conn.close()
            self.conns.pop(name)

    def close_all(self):
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

        if self._upload_socket:
            self._upload_socket.close()
            self._upload_socket = None

    @staticmethod
    def generate_message():
        #sensor_id = random.choice(['w'])
        #value = random.uniform(0, 10000)/1e3
        #unit = 'kg'
        #message = f"%{sensor_id},{value:.2f}{unit}#\n"
        #return message
        return "%w,1.000kg#\n"


    def send_to(self, name, msg):
        self.conns[name].sendall(msg.encode())


def start_server():
    server = Server(HOST, COMM_PORT)
    server.start_comm_port()
    server.start_download()
    server.start_upload()
    return server


def start_controller():
    controller = MarelController(host=HOST)
    controller.start_listening()
    return controller


SERVER = start_server()
CONTROLLER = start_controller()


def test_controller_weight_value():
    assert CONTROLLER.weight.value == 1.000


def test_controller_weight_units():
    assert CONTROLLER.weight.units == 'kg'


def test_controller_get_weight():
    assert CONTROLLER.weight.get_weight('g') == 1000
    assert CONTROLLER.weight.get_weight('kg') == 1.000
    assert CONTROLLER.weight.get_weight('lb') == 2.2046
    assert CONTROLLER.weight.get_weight('oz') == 35.2740


def test_update_lua():
    assert CONTROLLER.update_lua_code(ABS_LUA_SCRIPT_PATH) == 1
