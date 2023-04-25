"""
Date: April 2023

This module contains the MarelController class that is used to connect and process data from a Marel Marine Scale.

The controller is used to:
    - Connect ot the Marel Scale via Ethernet.
    - Upload the Compatible Lua Application to the scale.
    - Store the latest weight values.
    - Print received weight values at the current cursor position. (Keyboard Emulation)

Lua App:
    The Lua App developed for the Scale (`./static/marel_app_v2.lua`) sends messages of the form:
        `%<prefix>,<weight><units>#\n`,
    where:
        prefix: `w` or `k`.
        weight: float of variable precision.
        units: Unit of the weight [kg, g, lb ,oz].
    Messages with a `w` are sent at regular intervals. `k` messages are sent when the assign Scale button is pressed.
    When receiving `k` messages, the Controller emulates a keyboard entry of that given values.


Notes
-----
This project was developed with the Marel Marine Scale M2200. There is no guarantee that it will work with other models.


Attributes
----------
COMM_PORT :
    Port use to receive scale messages. (Same as in the Lua Code).
DOWNLOAD_PORT :
    Default Port to send Lua code to the scale.
UPLOAD_PORT :
    Default Port to receive Lua code from the scale.
RECEIVE_SLEEP :
    Delay in seconds between message reception.
UNITS_CONVERSION :
    Dictionnary containing the ratio between 1 kg different units of weight (g, lb, oz). Use to convert units.


Examples
--------
```
controller = MarelController(self.host)

listening_thread = threading.Thread(target=self.controller.start_listening, dameon=True)
start_listening_thread.start()

"""


import logging
import re
import threading
import time
from typing import *

import pyautogui as pag

from marel_marine_scale_controller.client import MarelClient

logging.basicConfig(level=logging.DEBUG)

COMM_PORT = 52212
DOWNLOAD_PORT = 52202
UPLOAD_PORT = 52203


RECEIVE_SLEEP = 0.05

UNITS_CONVERSION = {
    'kg': 1, 'g': 1e-3, 'lb': 0.453592, 'oz': 0.0283495
}


def convert_units(a, b):
    """Return conversion factor from unit `a` to unit `b`.

    Possible units are in the `UNITS_CONVERSIONS` dictionnary.

    Examples
    --------
        value_lb = value_kg * convert_units('kg', 'lb')


    """
    return UNITS_CONVERSION[a] / UNITS_CONVERSION[b]


class MarelController:
    """
    Controller for Marel Marine Scale (M2200) using the `./static/marel_app_v2.lua` app.

    Attributes
    ----------
    host :
        IP address of the host. (Scale)
    comm_port :
        Communication port used. Lua App Default: 52212
    client :
        MarelClient object use to connect to the scale.
    received_values :
        Latest values received from the scale.
    units :
        Desired units for weight.
    weight :
        Latest weight value.
    is_listening :
        Is set to True when the controller is listening for messages from the Scale.
    listening_thread :
        Thread used to call `self.listen()`
    auto_enter :
        When `True`, the `enter` is pressed after printing the weight value.
    is_muted :
        When True, the keyboard emulation is disabled.
    """
    def __init__(self, host, port=COMM_PORT):
        self.host = host
        self.comm_port = port
        self.client: MarelClient = MarelClient()
        self.received_values = {}
        self.units = "kg"
        self.weight: float = None
        self.is_listening = False
        self.auto_enter = True
        self.listening_thread = None
        self.is_muted = False

    def start_listening(self):
        """Connect client to the Scale and start listening.

        Connects to `self.host:self.comm_port` and calls `self.listen` from another thread.

        Disconnect the client (and close the client socket) on any exception.

        """
        self.client.connect(self.host, self.comm_port, timeout=1)

        if self.client.is_connected:
            try:
                self.is_listening = True
                self.listening_thread = threading.Thread(target=self.listen, daemon=True)
                self.listening_thread.start()
            except Exception as err:
                logging.error(f'Error on listening {err}')
                self.client.disconnect()

    def stop_listening(self):
        """Stop listening and disconnect the client.

        Sets `self.is_listening` to False.
        """
        self.is_listening = False
        self.client.disconnect()

    def get_latest_values(self):
        """Return a copy of `self.receivd_values`.
        """
        return self.received_values.copy()

    def mute(self):
        """Sets `self.is_muted` to True"""
        self.is_muted = True

    def unmute(self):
        """Sets `self.is_muted` to False"""
        self.is_muted = False

    def get_weight(self):
        """Return `self.weight`"""
        return self.weight

    def listen(self):
        """Listen and process received message from the scale.

        Listen while `self.is_listening` is True, thus it should be called
        from another thread.

        While listening, calls `self.client.receive(allow_timeout=False, split=True).
        If any messages are received, `self.process_message` is called for each message.
        """
        logging.info('Start MarelController ')
        while self.is_listening:
            data = self.client.receive(allow_timeout=False, split=True)
            if not data:
                continue

            for message in data:
                logging.debug(f'Received Messages: {message}')
                self.process_message(message)
            time.sleep(RECEIVE_SLEEP)

    def process_message(self, message):
        """Parse message with regex.

        Message expected: `%<prefix>,<weight><units>#`

        Convert the received weight value to the  required units (`self.units`).

        Updates values in `self.received_values` and `self.weight`.
            `self.received_values[prefix] = weight`
            `self.weight = weight`

        If the prefix is `k`, `self.to_keyboard(weight) is called.

        Parameters
        ----------
        message :
            Message to process.

        Returns
        -------

        """
        pattern = "%(\S),(-?\d+.\d+)(\S+)#"
        match = re.match(pattern, message)
        if match:
            prefix = match.group(1)
            value = match.group(2)
            unit = match.group(3)

            value = float(value) * convert_units(unit, self.units)

            self.received_values[prefix] = value
            self.weight = value

            if prefix == 'p' and not self.is_muted:
                self.to_keyboard(value)
        else:
            self.weight = None

    def to_keyboard(self, value: Union[float, int, str, bool]):
        """Print the `value` (as a string) where the cursor is (emulates a keyboard entry).

        Parameters
        ----------
        value :
            Value to print.
        """
        pag.write(str(value))
        if self.auto_enter is True:
            pag.press('enter')

    def set_units(self, units: str):
        """Change the weight units.

        Parameters
        ----------
        units : ['kg', 'g', 'lb', 'oz']
            new weight units.

        Raises
        ------
        ValueError if units no in `UNITS_CONVERSION`.

        """
        if units in UNITS_CONVERSION:
            self.units = units
        else:
            raise ValueError(f'Invalid units. Available units: {list(UNITS_CONVERSION.keys())}.')

    def update_lua_code(self, filename: str):
        """Update the scale Lua code.

        New clients are made to download and upload the Lua Code.

        First the Lua file is downloaded (to the scale). Then the Scale Lua code is
        uploaded (from the scale) and compared to the file sent for confirmation.

        The download and upload ports are hardcoded in the scale software.
            Download port: 52202
            Upload port: 52203


        Parameters
        ----------
        filename :
            Lua code file.

        Returns
        -------
        -1 : (Failed) Scale not reach or file failed to download (to the scale).
        0 : (Failed) File downloaded (to the scale) but could not upload (from the scale) the Lua code
            or the uploaded and downloaded Lua code were no identical.
        1 : (Succeeded) The file download (to the scale) was the same as the one uploaded (from the scale).

        """
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
                received += upload_client.receive(allow_timeout=True, split=False)

                if count > 10:
                    break
                count += 1

            upload_client.close()

            received_lua_script = ''.join(received)

            logging.info('Lua Script uploaded from scale.')

            if received_lua_script == sent_lua_script:
                logging.info('Lua script successfully uploaded.')
                return 1  # Sucess

        logging.info('Failed to upload Lua Script.')
        return 0  # File downloaded but did not match the uploaded one.
