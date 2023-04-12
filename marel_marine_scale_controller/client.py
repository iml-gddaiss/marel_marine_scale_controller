import logging
import socket
import time


class MarelClient:
    def __init__(self):
        self.host = None
        self.port = None
        self.socket = None
        self.is_connected = False
        self.auto_reconnect = True
        self.reconnect_delay = 2
        self.data = None

    def connect(self, host, port):
        self.data = b''
        self.host = host
        self.port = port
        self.auto_reconnect = True

        while self.auto_reconnect:
            print(f'auto reconnect: {self.auto_reconnect}')
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.host, self.port))
                self.is_connected = True
                self.socket.settimeout(5)
                break
            except OSError as err:
                logging.info(f"Connection failed. OSError {err}")
                if self.auto_reconnect:
                    logging.info(f"Retrying in {self.reconnect_delay} seconds...")
                    time.sleep(self.reconnect_delay)
                continue

        self.auto_reconnect = True


    def receive(self):

        while True:
            try:
                received = self.socket.recv(4096)
            except OSError as err:
                logging.info(f"Connection failed. OSError {err}")
                logging.debug('Connection lost.')
                self.disconnect()

                if self.auto_reconnect:
                    print("Connection lost. Retrying in", self.reconnect_delay, "seconds...")
                    time.sleep(self.reconnect_delay)
                    self.connect(self.host, self.port)

                return []
            self.data += received
            messages = self.data.split(b'\n')
            if len(messages) > 1:
                self.data = messages.pop()
                return [message.decode('utf-8') for message in messages if message]

    def disconnect(self):
        self.auto_reconnect = False
        if self.socket:
            self.socket.close()
            self.socket = None
        self.is_connected = False

