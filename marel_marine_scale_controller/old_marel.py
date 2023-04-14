"""
For Marel Marine Scale M2200

Marel Passwords:
 Service: 62735
 W&M conf: 322225

How to communicate with the scale ?
-----------------------------------
    Through an ethernet connection.
     - Setting the IP_ADDRESS in the scale settings. (detail how )

    Available Ports:
        52200: For dot commands according the Marel documentations. (to access model )
        52202: To send a Lua Script (as a string) and overwrite the one on the scale.
        52203: Once connected to the comm_port, the scale will send the Lua script in memory.
        52210: Marel Lua Interpreter Standard Output, for example using Lua print()
        52211: Usable output using the Marel Lua function CommStr(4, <str>). Persistent queue.
        52212: Usable output using the Marel Lua function CommStr(5, <str>).  (?).
        52213: Usable output using the Marel Lua function CommStr(6, <str>).  (?).

What does the scale do ?
------------------------
    + If the Lua App parameter is `On` (detail how), the scale will run the Lua script in memory in a loop.
    + The Lua script seems to be saved on persistent Memory (not RAM).
    + To send weight a Packing method needs to be set in the Scale settings (detail how).

Lua Script
----------
    The Scale has builtin Lua function to interact with the Scale. However, the basic Lua Libraries seem to
    be missing in the scale.

Notes
-----
    Received on scale restart:
    ```
    10043
    20043
    30043
    40043
    50043
    60043
    10043
    20043
    30043
    40043
    50043
    60043
    ```

"""
import re
import logging
import socket
import time
import threading
from typing import *
import pyautogui as pag


UNITS_CONVERSION = {
    'kg': 1, 'g': 1e-3, 'lb': 0.453592, 'oz': 0.0283495
}


PORTS = {
    'dot_port': 52200,
    'download_port': 52202,
    'upload_port': 52203,
    'output_port': 52210,
    'comm4_port': 52211,
    'comm5_port': 52212,
    'comm6_port': 52213
}

MAREL_MSG_ENCODING = 'UTF-8'
BUFFER_SIZE = 4092


def to_keyboard(value: Union[float, int, str, bool], auto_enter=True):
    """Print the `value` (as a string) where the cursor is.

    Parameters
    ----------
    value :
        Value to print.
    auto_enter :
        If True, the `enter` key is pressed.
    """
    pag.write(str(value))
    if auto_enter is True:
        pag.press('enter')


class EthernetClient:
    def __init__(self):
        self.ip_address: str = None
        self.port: int = None
        self.socket: socket.socket = None
        self.default_timeout = .1
        self._is_connected = False

    @property
    def is_connected(self):
        return self._is_connected

    def connect(self, ip_address, port, timeout: int = None):
        self.ip_address = ip_address
        self.port = port
        timeout = timeout or self.default_timeout

        logging.debug(f'MAREL: Attempting to connect to ip: {ip_address} on comm_port {port}. Timeout: {timeout} seconds')

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
            self.socket.settimeout(timeout)
            self.socket.connect((ip_address, port))
            self._is_connected = True
            self.socket.settimeout(self.default_timeout)
            logging.debug(f'MAREL: Connected on comm_port {port}')
        except TimeoutError:
            logging.error(f'Failed to connect: Timeout. Device not found.')
        except OSError as err:
            logging.debug('MAREL: Fail to connect')

    def send(self, command: str):
        try:
            return self.socket.sendall(command.encode(MAREL_MSG_ENCODING))
        except OSError as err:
            logging.debug(f'MAREL: OSError on sendall')
            self.close()
            return None

    def receive(self):
        try:
            return self.socket.recv(BUFFER_SIZE).decode(MAREL_MSG_ENCODING)
        except OSError as err:
            logging.debug(f'MAREL: OSError on receive: {err}, {err.errno}')
            self.close()
            return ""

    def clear(self):
        while self.receive() != "":
            continue

    def close(self):
        self.socket.close()
        self._is_connected = False



def convert_units(a, b):
    return UNITS_CONVERSION[a] / UNITS_CONVERSION[b]


class MarelController:
    port = PORTS['comm5_port']
    msg_pattern = "%(\S),(-?\d+.\d+)(\S+)#"

    def __init__(self, ip_address: str):
        self.ip_address: str = ip_address
        self.client: EthernetClient = None
        self.listen_thread: threading.Thread = None
        self.is_listening = False
        self.weight = ''
        self._weight_units = 'kg'
        self.wait_delay = .1
        self.fading_delay = 5
        self.client = None

    @property
    def is_connected(self):
        if self.client is not None:
            return self.client.is_connected
        else:
            return False

    def start_client(self):
        if self.is_connected:
            self.close_client()

        self.client = EthernetClient()
        self.client.connect(self.ip_address, self.port)

    def close_client(self):
        if self.is_connected:
            self.client.close()

    def set_units(self, units: str):
        if units in UNITS_CONVERSION:
            self._weight_units = units
        else:
            logging.error(f'MAREL: Invalid units. Available units: {list(UNITS_CONVERSION.keys())}.')

    def start_listening(self):
        self.is_listening = True
        self.listen_thread = threading.Thread(
            target=self.listen,
            name="marel listening", daemon=True
        )
        self.listen_thread.start()

    def stop_listening(self):
        self.close_client()
        self.is_listening = False

    def listen(self):
        timer = self.fading_delay - 1
        buff = ""
        while self.is_listening:
            self.start_client()

            while self.is_connected:
                time.sleep(self.wait_delay)
                buff += self.client.receive()
                if buff:
                    messages = buff.split('\n')
                    buff = messages.pop(-1)
                    for msg in messages:
                        match = re.findall(self.msg_pattern, msg)
                        if len(match) > 0:
                            self.weight = float(match[0][1]) * convert_units(match[0][2], self._weight_units)
                            if match[0][0] == "k":
                                self.to_keyboard(self.weight)
                            timer = time.time_ns()
                        elif (time.time_ns() - timer)/1e9 > self.fading_delay:
                            self.weight = ""
                elif (time.time_ns() - timer)/1e9 > self.fading_delay:
                    self.weight = ""
            time.sleep(5)

    def to_keyboard(self, value):
        to_keyboard(value, auto_enter=True)


class TestMarel:
    def __init__(self, ip_address):
        self.weight = None
        self.run_prog_1 = False
        self.controller: MarelController = None
        thread: threading.Thread

        self.controller = MarelController(ip_address=ip_address)
        self.controller.start_listening()

    def get_controller(self):
        return self.controller

    def start_prog_1(self):
        self.run_prog_1 = True
        thread = threading.Thread(target=self._prog_1, name='Test Pro 1', daemon=True)
        thread.start()

    def stop_prog_1(self):
        self.run_prog_1 = False

    def _prog_1(self):
        while self.run_prog_1 is True:
            time.sleep(0.05) # Smaller then controller.wait_delay
            self.get_weight()

    def get_weight(self):
        if self.controller.weight != "":
            weight = self.controller.weight
            self.controller.weight = ""
            print(f'Weight: {weight}')


def update_lua_code(filename: str, ip_address: str):
    download_port = PORTS['download_port']
    upload_port = PORTS['upload_port']

    # download
    download_client = EthernetClient()
    download_client.connect(ip_address, download_port)

    with open(filename, 'r') as lua_app:
        lua_script = lua_app.read()

    # TODO check return value ? To see if everything has been sent.
    if download_client.is_connected:
        download_client.send(lua_script)
        download_client.close()

    logging.info('Lua Script downloaded to scale.')

    time.sleep(1) # Some delay (>0.1) needs to be necessary between download and upload check.

    # integrity check
    upload_client = EthernetClient()
    upload_client.connect(ip_address, upload_port)

    marel_lua_script = ""

    count = 0

    if upload_client.is_connected:
        while True:
            msg = upload_client.receive()
            if count > 10:
                break
            count += 1
            marel_lua_script += msg
        upload_client.close()

    logging.info('Lua Script uploaded from scale.')

    if marel_lua_script == lua_script:
        logging.info('Lua script successfully uploaded.')
    else:
        logging.info('Failed ot upload Lua Script.')


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    test_ip_addr = "192.168.0.202"
    lua_script = 'marel_app.lua'

    update_lua_code(lua_script, ip_address=test_ip_addr)

    #mc = MarelController(ip_address=test_ip_addr)
    #
    #mc.start_listening()
    #

    #
    #t = TestMarel(ip_address=test_ip_addr)
    #t.start_prog_1()

    # c = t.get_controller()