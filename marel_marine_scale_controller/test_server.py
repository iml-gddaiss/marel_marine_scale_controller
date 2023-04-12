import socket
import threading
import random
import time
import logging

logging.basicConfig(level=logging.DEBUG)

class TestServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.running = False
        self._socket = None
        self.conns = {}
        self.thread = None

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

    def start(self, number_of_connections = 5):
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

        self._socket.listen(5)

        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

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
        for k, v in self.conns.items():
            v.detach()

        if self._socket:
            self._socket.close()
            self._socket = None

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
    PORT = 5000

    s=TestServer(HOST, PORT)
    s.start()
