"""
Date: April 2023

GUI Application used to interact with the MarelController.

Usages
------
    Running the script will launch the Gui App::
        $ python gui.py


Notes
-----
The last host ip address used is store in `./config/gui_config.json`

Attributes
----------
PROGRAM_DIRECTORY :
    Directory when the SCript was run.
LUA_SCRIPT_PATH :
    Relative path to the Lua Script.
CONFIG_PATH :
    Relative path to the gui configuration file.
LOGO_PATH:
    Relative path to the gui app logo.
ABS_LUA_SCRIPT_PATH :
    Absolute path to the Lua Script.
ABS_CONFIG_PATH :
    Absolute path to the gui configuration file.
ABS_LOGO_PATH:
    Absolute path to the gui app logo.

"""
import platform
import json
import threading
import time
import tkinter as tk
from pathlib import Path

from marel_marine_scale_controller import VERSION, LUA_SCRIPT_PATH, CONFIG_PATH, LOGO_PATH
from marel_marine_scale_controller.marel_controller import MarelController

PROGRAM_DIRECTORY = Path(__file__).parent

ABS_LUA_SCRIPT_PATH = str(PROGRAM_DIRECTORY.joinpath(LUA_SCRIPT_PATH))
ABS_CONFIG_PATH = str(PROGRAM_DIRECTORY.joinpath(CONFIG_PATH))
ABS_LOGO_PATH = str(PROGRAM_DIRECTORY.joinpath(LOGO_PATH))

COLOR_LIGHT_RED = '#E2C8C8'
COLOR_LIGHT_GREEN = '#AAC893'
COLOR_WHITE = "#FFFFFF"
COLOR_ROSE = "#F7B7C2"
COLOR_GREY = '#C0C0C0'
COLOR_BLUE_GREY = '#AAC8C1'


class GUI:
    """
    Gui Application for the MarelController.

    Examples
    --------
    >>>  gui = GUI()
    >>>  gui.run()
    """

    def __init__(
            self,
            host: str = None,
            lua_script_path=ABS_LUA_SCRIPT_PATH,
            config_path=ABS_CONFIG_PATH,
            logo_path=ABS_LOGO_PATH
    ):
        self.lua_script_path = lua_script_path
        self.config_path = config_path
        self.logo_path = logo_path

        self.controller: MarelController = None
        self.start_listening_thread: threading.Thread = None

        if host:
            self.host = host
        else:
            config = self.load_config()
            self.host = config['host']

        ###Init the Gui Window layout###

        pady = 2
        padx = 2

        self.root = tk.Tk()
        self.root.title("Marel App")

        if platform.system() == "Windows":
            self.root.iconbitmap(bitmap=self.logo_path)
            XX, YY = 285, 305  # px
        else:
            XX, YY = 230, 230  # px

        self.root.minsize(XX, YY)
        self.root.maxsize(XX, YY)

        ### Row 0  HOST | INPUT
        row0 = tk.Frame(self.root)

        host_label = tk.Label(row0, text="Host:", width=5)
        self.host_entry = tk.Entry(row0, justify='right')
        self.host_entry.insert(tk.END, self.host)

        host_label.grid(row=0, column=0, columnspan=1, sticky='ew', padx=2)
        self.host_entry.grid(row=0, column=1, columnspan=1, sticky='ew', padx=2)

        ### Row 1 UPDATE STATUS | UPDATE BUTTON
        row1 = tk.Frame(self.root)
        self.update_status = tk.StringVar(value="----")
        update_status_label = tk.Label(row1, textvariable=self.update_status, relief='sunken', width=10)
        self.update_lua_button = tk.Button(row1, text="Update Lua App", command=self.update_lua_app, bg=COLOR_BLUE_GREY)

        update_status_label.grid(row=0, column=0, columnspan=1, sticky='ew', padx=2)
        self.update_lua_button.grid(row=0, column=2, columnspan=1, sticky='ew', padx=2)

        ### Row 2  Statys | Led | Start | Stop Button
        row2 = tk.Frame(self.root)

        # LED indicator
        status_label = tk.Label(row2, text='Status:', )
        self.led_canvas = tk.Canvas(row2, height=20, width=20)
        self.led = self.led_canvas.create_oval(5, 5, 16, 16, fill="red")

        w = 7 if platform.system() == 'Windows' else 5
        self.start_button = tk.Button(row2, text="Start", command=self.start_listening, bg=COLOR_LIGHT_GREEN, width=w)
        self.stop_button = tk.Button(
            row2, text="Stop", command=self.stop_listening, state='disable', bg=COLOR_LIGHT_RED, width=w
        )

        status_label.grid(row=0, column=0, columnspan=1, sticky='ew')
        self.led_canvas.grid(row=0, column=1, columnspan=1, sticky='ew', padx=2)
        self.start_button.grid(row=0, column=3, columnspan=1, sticky='ew', padx=2)
        self.stop_button.grid(row=0, column=4, columnspan=1, sticky='ew', padx=2)

        ### Row 3 Weight
        row3 = tk.Frame(self.root)
        # Weight display
        self.weight_value = tk.StringVar(value="-" * 7)
        weight_value_label = tk.Label(
            row3, textvariable=self.weight_value, height=2, border=1, relief='sunken',
            anchor='e', bg=COLOR_ROSE, fg=COLOR_WHITE, bd=5, font=('jetbrains mono', 18, 'bold'),
            width=12
        )
        weight_value_label.grid(row=0, column=0, columnspan=1, sticky='ew', padx=2)

        ### Row 4 Auto-Enter | Units
        row4 = tk.Frame(self.root)
        self.auto_enter_var = tk.BooleanVar()
        auto_enter_label = tk.Label(row4, text=' auto-enter:')
        self.auto_enter_button = tk.Button(row4, text='ON', command=self.auto_enter, bg=COLOR_BLUE_GREY, height=1, width=3)

        units_label = tk.Label(row4, text=' units:')
        default_unit = tk.StringVar(row4, value='kg')
        units_option = ('kg', 'g', 'lb', 'oz')
        self.units = tk.OptionMenu(row4, default_unit, *units_option, command=self.set_units)
        self.units.config(indicatoron=False, bg=COLOR_GREY, width=2)

        # tk.Label(row4, width=7).grid(row=0, column=0)
        auto_enter_label.grid(row=0, column=0, columnspan=1, sticky='ew', padx=2)
        self.auto_enter_button.grid(row=0, column=1, columnspan=1, sticky='ew', padx=2)
        units_label.grid(row=0, column=2, columnspan=1, sticky='ew', padx=2)
        self.units.grid(row=0, column=3, columnspan=1, sticky='ew', padx=2)

        ### Row 5 Version
        row5 = tk.Frame(self.root)
        version_label = tk.Label(
            row5, text=f'Version: {VERSION}', font=('jetbrains mono', 8, 'italic'), justify='left', width=50
        )
        version_label.grid(row=0, column=0, columnspan=1, sticky='e', padx=2)

        row0.pack(pady=pady, padx=padx, fill='both', expand=True)
        row1.pack(pady=pady, padx=padx, fill='both')
        row2.pack(pady=pady, padx=padx, fill='both')
        row3.pack(pady=pady, padx=padx, fill='both')
        row4.pack(pady=pady, padx=padx, fill='both')
        row5.pack(pady=pady, padx=padx, fill='both')

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.refresh_window()

    def run(self):
        """Start (run) the App"""
        self.root.mainloop()

    def start_listening(self):
        """Wrapper function for the MarelController start_listening methods."""
        self.start_button.config(state='disable')
        self.host = self.host_entry.get()
        self.save_config()

        if not self.controller:
            self.controller = MarelController(self.host)
            if self.controller.auto_enter is True:
                self.auto_enter_button.config(relief='sunken')

        else:
            self.controller.host = self.host

        # A thread is use here to prevent the GUI from freezing.
        self.start_listening_thread = threading.Thread(target=self.controller.start_listening, daemon=True)
        self.start_listening_thread.start()

    def stop_listening(self):
        """Wrapper function for the MarelController stop_listening methods."""
        self.stop_button.config(state='disable')
        if self.controller:
            self.controller.stop_listening()

        while self.controller.is_listening or self.controller.client.is_connecting:  # -------------------maybe not needed
            time.sleep(.1)

    def set_units(self, unit):
        """Wrapper function for the MarelController set_units methods."""
        if self.controller:
            self.controller.set_units(unit)
            time.sleep(.1)

    def auto_enter(self):
        """Change the value of the MarelController auto_enter attribute."""
        if self.controller:
            if self.controller.auto_enter is True:
                self.controller.auto_enter = False
                self.auto_enter_button.config(relief='raised', text='OFF')
            else:
                self.controller.auto_enter = True
                self.auto_enter_button.config(relief='sunken', text='ON')

    def update_lua_app(self):
        """Call `self.run_update_lua` from another thread."""
        # A thread is use here because the MarelController doesn't use one.
        threading.Thread(target=self.run_update_lua, daemon=True).start()

    def run_update_lua(self):
        """Wrapper function for the MarelController update_lua_app methods."""
        self.update_lua_button.config(state='disable')
        self.update_status.set(f"updating")

        if not self.controller:
            host = self.host_entry.get()
            self.controller = MarelController(host)

        flag = self.controller.update_lua_code(self.lua_script_path)

        match flag:
            case -1:
                self.update_status.set(f"N/A")
            case 1:
                self.update_status.set(f"Up-to-date")
            case 0:
                self.update_status.set(f"Failed")
            case _:
                raise ValueError(f'Gui.update_lua_methode got a value of {flag}')

        self.update_lua_button.config(state='normal')

    def refresh_led(self):
        if self.controller:
            if self.controller.client.is_connecting:
                self.led_canvas.itemconfig(self.led, fill="yellow")
            elif self.controller.is_listening and self.controller.client.is_connected:
                self.led_canvas.itemconfig(self.led, fill="green")
            else:
                self.led_canvas.itemconfig(self.led, fill="red")
        else:
            self.led_canvas.itemconfig(self.led, fill="red")

    def refresh_buttons(self):
        if self.controller and (self.controller.client.is_connecting or self.controller.is_listening):
            self.host_entry.config(state='disable')
            self.start_button.config(state='disable')
            self.stop_button.config(state='normal')
        else:
            self.host_entry.config(state='normal')
            self.start_button.config(state='normal')
            self.stop_button.config(state='disable')

    def refresh_weight(self):
        if self.controller:
            self.units.config(state='normal')
            self.auto_enter_button.config(state='normal')
            if self.controller.client.is_connecting:
                self.weight_value.set("-  ")

            elif self.controller.is_listening and self.controller.client.is_connected:
                if (weight := self.controller.get_weight(self.controller.units)) is not None:
                    if self.controller.units == 'kg':
                        self.weight_value.set(f"{weight:.04f} {self.controller.units} ")
                    elif self.controller.units == 'lb':
                        self.weight_value.set(f"{weight:.04f} {self.controller.units} ")
                    elif self.controller.units == 'oz':
                        self.weight_value.set(f"{weight:.03f} {self.controller.units} ")
                    elif self.controller.units == 'g':
                        self.weight_value.set(f"{weight:.01f} {self.controller.units} ")
                    else:
                        raise ValueError('Invalid weight units.')
                else:
                    self.weight_value.set("-  ")
            else:
                self.weight_value.set("-  ")
        else:
            self.weight_value.set("-  ")
            self.units.config(state='disable')
            self.auto_enter_button.config(state='disable')

    def refresh_window(self):
        self.refresh_buttons()
        self.refresh_weight()
        self.refresh_led()

        self.root.after(100, self.refresh_window)

    def on_close(self):
        if self.controller is not None:
            self.controller.stop_listening()
        self.root.destroy()

    def load_config(self):
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump({'host': self.host}, f)
