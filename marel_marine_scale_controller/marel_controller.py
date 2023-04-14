import re
import time

import logging

from typing import *

import pyautogui as pag

from marel_marine_scale_controller.client import MarelClient

logging.basicConfig(level=logging.DEBUG)

UNITS_CONVERSION = {
    'kg': 1, 'g': 1e-3, 'lb': 0.453592, 'oz': 0.0283495
}


def convert_units(a, b):
    return UNITS_CONVERSION[a] / UNITS_CONVERSION[b]


COMM_PORT = 52212
DOWNLOAD_PORT = 52202
UPLOAD_PORT = 52203


class Controller:
    def __init__(self, host, port=COMM_PORT):
        self.host = host
        self.comm_port = port
        self.values = {}
        self.units = "kg"
        self.weight: float = None
        self.is_listening = False
        self.is_connecting = False
        self.client: MarelClient = MarelClient()

    def start_listening(self):
        self.connect_client()
        if self.client.is_connected:
            try:
                self.is_listening = True
                self.run()
            except Exception as err:
                logging.error(f'Error on listening {err}')
                self.client.disconnect()

    def connect_client(self):
        self.is_connecting = True
        self.client.connect(self.host, self.comm_port)
        self.is_connecting = False

    def stop_listening(self):
        self.is_listening = False
        self.client.disconnect()

    def get_latest_values(self):
        return self.values.copy()

    def get_weight(self):
        return self.weight

    def run(self):
        logging.info('Start Controller ')
        while self.is_listening:
            data = self.client.receive()
            if not data:
                continue

            for message in data:
                logging.debug(f'Received Messages: {message}')
                self.process_message(message)
            time.sleep(0.01)

    def process_message(self, message):
        pattern = "%(\S),(-?\d+.\d+)(\S+)#"
        match = re.match(pattern, message)
        if match:
            prefix = match.group(1)
            value = match.group(2)
            unit = match.group(3)

            value = float(value) * convert_units(unit, self.units)

            self.values[prefix] = value
            self.weight = value

            if prefix == 'k':
                self.to_keyboard(value)

    @staticmethod
    def to_keyboard(value: Union[float, int, str, bool], auto_enter=True):
        """Print the `value` (as a string) where the cursor is.

        Parameters
        ----------
        value :
            Value to print.66.01

        auto_enter :
            If True, the `enter` key is pressed.
        """
        pag.write(str(value))
        if auto_enter is True:
            pag.press('enter')

    def set_units(self, units: str):
        if units in UNITS_CONVERSION:
            self.units = units
        else:
            logging.error(f'MAREL: Invalid units. Available units: {list(UNITS_CONVERSION.keys())}.')

    def update_lua_code(self, filename: str):
        download_client = MarelClient()
        download_client.connect(self.host, DOWNLOAD_PORT, single_try=True)

        with open(filename, 'r') as lua_app:
            sent_lua_script = lua_app.read()

        if download_client.is_connected:
            download_client.send(sent_lua_script)
            download_client.close()
            logging.info('Lua Script downloaded to scale.')
        else:
            return -1  # Marel not reach

        time.sleep(1)  # Some delay (>0.1) needs to be necessary between download and upload check.

        upload_client = MarelClient()
        upload_client.connect(self.host, UPLOAD_PORT, single_try=True)

        received = []
        count = 0

        if upload_client.is_connected:
            while True:
                received += upload_client.receive(allow_timeout=True)

                if count > 5:
                    break
                count += 1

            upload_client.close()
            received_lua_script = '\n'.join(received)
            logging.info('Lua Script uploaded from scale.')

            if received_lua_script == sent_lua_script:
                logging.info('Lua script successfully uploaded.')
                return 1  # Sucess

        logging.info('Failed to upload Lua Script.')
        return 0  # File downloaded but did not match the uploaded one.


if __name__ == "__main__":
    HOST = "localhost"
    PORT = 52210
