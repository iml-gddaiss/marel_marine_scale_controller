import logging
import socket
import time

MAREL_MSG_ENCODING = 'utf-8'


class MarelClient:
    def __init__(self):
        self.host = None
        self.port = None
        self.socket = None
        self.timeout = 2
        self.is_connected = False
        self.is_connecting = False
        self.auto_reconnect = True
        self.reconnect_delay = 2
        self.data = None

    def connect(self, host: str, port: int, single_try=True, timeout: float=1):
        """

        Parameters
        ----------
        host :
        port :

        single_try :
            If True, it will only try to connect once.
        timeout :
            Timeout value (seconds) for the connection attemps.

        """
        self.data = b''
        self.host = host
        self.port = port
        self.auto_reconnect = True

        self.is_connecting = True
        while self.auto_reconnect:
            logging.info(f'Trying to connect ... {host}:{port}')
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(timeout)
                self.socket.connect((self.host, self.port))
                logging.info("Client Socket Connected")
                self.is_connected = True
                self.socket.settimeout(self.timeout)
                break
            except OSError as err:
                # INFO:root:Connection failed. OSError [Errno 113] No route to host GOT THIS ON WIFI
                logging.info(f"Connection failed. OSError {err}")
                if err.errno == 133:
                    logging.info('Host not found, exiting.')

                elif (not single_try) and self.auto_reconnect:
                    logging.info(f"Retrying in {self.reconnect_delay} seconds...")
                    time.sleep(self.reconnect_delay)
                    continue

                time.sleep(1)  #Small delay after a failed single connection attemp. Help with the GUI>
                break

        self.is_connecting = False
        self.auto_reconnect = True

    def send(self, command: str):
        try:
            return self.socket.sendall(command.encode(MAREL_MSG_ENCODING))
        except OSError as err:
            logging.debug(f'MAREL: OSError on sendall: {err}')
            self.close()
            return None

    def receive(self, allow_timeout=False, split=True, split_char: bytes=b"\n") -> list:
        """Will try to reconnect if an OSError is raise on receive.

        Timeout Error is internally raised and caught if no bytes are received.

        If a Timeout error is raised an allow_timeout is False, the socket will be closed
        setting `self.is_connected` to False. If `self.auto_reconnect` is True, it will attempt
        to reconnect (within the receive method).

        Parameters
        ----------
        allow_timeout :
            If True, socket will stay connected on timeout.

        split :
            If True, messages are split on newline and the last value is
            put back in the received buffer.
        split_char :
            Character for splitting. Mus be a byte string.

        """
        while True:
            try:
                received = self.socket.recv(4096)

                if received == b"":              # The Scale is not supposed to send Empty string. Does so on bad connection.
                    raise TimeoutError

            except OSError as err:
                if err.errno is None and allow_timeout:
                    return []

                logging.info(f"MAREL: OSError on receive: {err}")
                logging.debug('Connection lost.')
                self.close()

                if self.auto_reconnect:
                    logging.info(f"Trying to reconnect in {self.reconnect_delay} seconds...")
                    time.sleep(self.reconnect_delay)
                    self.connect(self.host, self.port)

                return []

            self.data += received

            if split is True:
                messages = self.data.split(split_char)
                if len(messages) > 1:
                    self.data = messages.pop()
                    return [message.decode(MAREL_MSG_ENCODING) for message in messages]
            else:
                message = [self.data.decode(MAREL_MSG_ENCODING)]
                self.data = b''
                return message

    def disconnect(self):
        """Force disconnection of the socket e.i Use Shutdown"""
        self.auto_reconnect = False
        self.close()

    def close(self):
        """Close the socket"""
        if self.socket:
            self.socket.close()
        self.is_connected = False

