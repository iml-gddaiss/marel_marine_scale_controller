import re

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


class Controller:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.values = {}
        self.is_running = False
        self.is_connecting = False
        self.client: MarelClient = None

        self.units = "kg"

    def start_listening(self):
        self.client = MarelClient()

        self.is_connecting = True
        self.client.connect(self.host, self.port)
        self.is_connecting = False

        if self.client.is_connected:
            logging.info('Controller Connected')
            try:
                self.is_running = True
                self.run()
            except Exception as err:
                logging.error(f'Error on listening {err}')
                self.client.disconnect()

    def stop_listening(self):
        self.is_running = False
        if self.client is not None:
            self.client.disconnect()

    def get_latest_values(self):
        return self.values.copy()

    def run(self):
        logging.info('Start Controller Run()')
        while self.is_running:
            data = self.client.receive()
            if not data:
                continue

            for message in data:
                logging.debug(f'Received Messages: {message}')
                self.process_message(message)

    def process_message(self, message):
        pattern = "%(\S),(-?\d+.\d+)(\S+)#"
        match = re.match(pattern, message)
        if match:
            prefix = match.group(1)
            value = match.group(2)
            unit = match.group(3)

            value = float(value) * convert_units(unit, self.units)

            self.values[prefix] = value

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


if __name__ == "__main__":
    HOST = "localhost"
    PORT = 52210

