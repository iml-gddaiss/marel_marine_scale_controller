"""
Date: April 2023

This module contains the MarelClient() class that is used by the MarelController() object to connect to the Marel Scale.

Attributes
----------
MAREL_MSG_ENCODING :
    Character Encoding used by the Marel Scale to send data.


"""
import logging
import socket
import time

MAREL_MSG_ENCODING = 'utf-8'


class MarelClient:
    """
    Ethernet Client for Marel Controller.

    Notes
    -----
    The client, by default, split received message on b'\n'. See the receive() method.

    Attributes
    ----------
    host : str
        Socket host IP address.
    port : int
        Socket port number
    socket : socket.Socket
    timeout :
        Socket timeout in seconds.
    is_connected :
        Flag that is True when the socket is connected.
    is_connected :
        Flag that is True when the client is attempting to connect.
    auto_reconnect :
        If True, the client attempts to reconnect with a new socket when the connection is lost.
    reconnect_delay :
        Time in second between each reconnection attempts.
    data_buffer :
        Binary buffer of the received data.
    """
    def __init__(self):
        self.host = None
        self.port = None
        self.socket = None
        self.timeout = 2  # seconds
        self.is_connected = False
        self.is_connecting = False
        self.auto_reconnect = True
        self.reconnect_delay = 2  # seconds
        self.data_buffer = None

    def connect(self, host: str, port: int, single_try=True, timeout=1):
        """Connect socket to `host:post`.

        Connection attempts are made while `self.auto_reconnect` is True and until connected unless
        `single_try` is True. While attempting to connect, `self.is_connecting` is set to True.

        When done connecting (or not), self.auto_reconnect` is always set to True.

        Parameters
        ----------
        host :
            IP Address of the host. Sets the self.host value.
        port :
            Port Number to connect to. Sets the self.port value.

        single_try :
            If True, it will only try to connect once.
        timeout :
            Timeout value (seconds) for the connection attempts.

        """
        self.data_buffer = b''
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
                self.is_connected = True

                self.test_new_connection()  # Check if its is really connected

                self.socket.settimeout(self.timeout)
                break
            except OSError as err:
                # INFO:root:Connection failed. OSError [Errno 113] No route to host GOT THIS ON WIFI
                logging.debug(f"Connection failed. OSError {err}")
                if err.errno == 133:
                    logging.info('Host not found, exiting.')

                elif (not single_try) and self.auto_reconnect:
                    logging.info(f"Retrying in {self.reconnect_delay} seconds...")
                    time.sleep(self.reconnect_delay)
                    continue

                time.sleep(1)  # Small delay after a failed single connection attempt. Help with the GUI>
                break

        self.is_connecting = False
        self.auto_reconnect = True

    def send(self, message: str):
        """Send message via `self.socket`.

        Call `self.close()` on OSError.

        Parameters
        ----------
        message :
            Message to send.

        Returns
        -------
            Receive Bytes or None.
        """
        try:
            self.socket.sendall(message.encode(MAREL_MSG_ENCODING))
        except OSError as err:
            logging.debug(f'MAREL: OSError on sendall: {err}')
            self.close()

    def receive(self, allow_timeout=False, split=True, split_char: bytes = b"\n") -> list:
        """Receive message via `self.socket`.

        Will try to reconnect if an OSError is caught on receive.

        Timeout Error is internally raised if no bytes are received.

        If a Timeout error is raised an `self.allow_timeout` is False, the socket will be closed
        setting `self.is_connected` to False. If `self.auto_reconnect` is True, `self.connect` is called.

        Parameters
        ----------
        allow_timeout :
            If True, socket will stay connected on timeout.

        split :
            If True, messages are split on newline and the last value is
            put back in the received buffer.
        split_char :
            Character for splitting. Must be a byte string.

        Returns
        -------
        List of decoded messages or empty list.
        """
        while True:
            try:
                received = self.socket.recv(4096)

                if received == b"":  # The Scale is not supposed to send Empty string. Does so on bad connection.
                    raise TimeoutError

            except OSError as err:
                if err.errno is None and allow_timeout:
                    return []

                logging.debug(f"MAREL: OSError on receive: {err}")
                logging.info('Connection lost.')
                self.close()

                if self.auto_reconnect:
                    logging.info(f"Trying to reconnect in {self.reconnect_delay} seconds...")
                    time.sleep(self.reconnect_delay)
                    self.connect(self.host, self.port)

                return []

            self.data_buffer += received

            if split is True:
                messages = self.data_buffer.split(split_char)
                if len(messages) > 1:
                    self.data_buffer = messages.pop()
                    return [message.decode(MAREL_MSG_ENCODING) for message in messages]
            else:
                message = [self.data_buffer.decode(MAREL_MSG_ENCODING)]
                self.data_buffer = b''
                return message

    def disconnect(self):
        """Force disconnection of the socket.

        `self.auto_reconnect` is set to False to prevent auto-reconnection and `self.close` is called.

        """
        logging.info('Disconnecting Client')
        self.auto_reconnect = False
        self.close()

    def test_new_connection(self):
        """Raise OSError if the scale was not really connected.

        The client can still connect to the scale even if the scale is already connected,
        thus is unavailable.

        This function calls self.receive(allow_timeout=False).
        The self.receive function will call self.close() if an error occurs.

        If the self.receive raises and error, the connection is close with self.close.
        This function will then raise an OSError.
        """
        self.auto_reconnect = False
        self.socket.recv(4096) #Test this
        # self.receive(allow_timeout=False, split=True)
        # if self.is_connected:
        #     logging.info("Client Socket Connected")
        # else:
        #     logging.info('Device Unavailable')
        #     raise OSError("Device Unavailable")

    def close(self):
        """Close the socket and set `self.is_connected` to False."""
        logging.info('Closing Client')
        if self.socket:
            self.socket.close()
        self.is_connected = False

