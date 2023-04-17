
import os
import json
import threading
import time
import tkinter as tk
from pathlib import Path

from marel_marine_scale_controller import LUA_SCRIPT_PATH, CONFIG_PATH
from marel_marine_scale_controller.marel_controller import Controller

PROGRAM_DIRECTORY = Path(__file__).parent

ABS_LUA_SCRIPT_PATH = str(PROGRAM_DIRECTORY.joinpath(LUA_SCRIPT_PATH))
ABS_CONFIG_PATH = str(PROGRAM_DIRECTORY.joinpath(CONFIG_PATH))
ABS_LOGO_PATH = str(PROGRAM_DIRECTORY.joinpath("static/logo.ico"))


def load_config():
    with open(ABS_CONFIG_PATH, 'r') as f:
        return json.load(f)


def save_config(config):
    with open(ABS_CONFIG_PATH, 'w') as f:
        json.dump(config, f)


def iter_row(r):
    while 1:
        yield r
        r += 1


class GUI:
    def __init__(self, host: str = None):
        self.listening_thread = None
        self.controller = None

        if host:
            self.host = host
        else:
            config = load_config()
            self.host = config['host']

        self.init_layout()

    def init_layout(self):
        self.root = tk.Tk()

        self.root.title("Marel Marine Scale")

        if "nt" == os.name:
            self.root.iconbitmap(bitmap=ABS_LOGO_PATH)

        self.root.minsize(int(230*1.1), int(210*1.1))

        row = iter_row(0)

        # HOST INPUT
        r=next(row)
        host_label = tk.Label(self.root, text="Host:", justify='right', width=4)
        host_label.grid(row=r, column=1, columnspan=2, sticky='ew', padx=5)
        self.host_entry = tk.Entry(self.root, justify='right', width=15)
        self.host_entry.insert(tk.END, self.host)
        self.host_entry.grid(row=0, column=3, columnspan=4, pady=5, padx=5, stick='ew')

        # UPDATE
        r = next(row)
        self.update_status = tk.StringVar(value="----")
        update_status_label = tk.Label(self.root, textvariable=self.update_status, width=10, relief='sunken')
        update_status_label.grid(row=r, column=0, columnspan=3, pady=5, padx=5, sticky='ew')

        # Update Lua App Button
        self.update_lua_button = tk.Button(self.root, text="Update Lua App", width=12, command=self.update_lua_app, bg='#AAC8C1')
        self.update_lua_button.grid(row=r, column=3, columnspan=4, pady=5, padx=5, stick='ew')

        # LED indicator
        r = next(row)
        status_label = tk.Label(self.root, text='Status: ', width=6)
        status_label.grid(row=r, column=1, columnspan=2, pady=5, sticky='e')
        self.led_canvas = tk.Canvas(self.root, width=20, height=20)
        self.led_canvas.grid(row=r, column=3, columnspan=1, pady=5, sticky='w')
        self.led = self.led_canvas.create_oval(5, 5, 15, 15, fill="red")

        # Start | Stop Button
        self.start_button = tk.Button(self.root, text="Start", command=self.start_listening, width=4, bg='#AAC893')
        self.start_button.grid(row=r, column=2, columnspan=3, pady=5, padx=5,  sticky='e')

        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop_listening, state='disable', width=4, bg='#E2C8C8')
        self.stop_button.grid(row=r, column=5, columnspan=3, pady=5, padx=5, sticky='e')

        # Weight display
        r = next(row)

        self.weight_value = tk.StringVar(value="-"*7)
        weight_value_label = tk.Label(self.root, textvariable=self.weight_value, width=15,
                                      font=('jetbrains mono', 18, 'bold'), height=2, border=1,
                                      relief='sunken',
                                      anchor='e',
                                      bg="#F7B7C2", fg="#FFFFFF", bd=5)

        weight_value_label.grid(row=r, column=1, columnspan=5, padx=5, pady=5, sticky='w', )

        # Unit selection

        default_unit = tk.StringVar(self.root, value='kg')
        units_option = ('kg', 'g')
        self.units = tk.OptionMenu(self.root, default_unit, *units_option, command=self.set_units)
        self.units.config(indicatoron=False, width=4, bg='#C0C0C0')
        self.units.grid(row=r, column=6, columnspan=2, pady=1, padx=1,  sticky='e')

        # auto-enter
        self.auto_enter_var = tk.BooleanVar()

        r = next(row)
        self.auto_enter_button = tk.Button(self.root, text='auto-enter', command=self.auto_enter, width=10, bg='#AAC8C1')
        self.auto_enter_button.grid(row=r, column=2, columnspan=4, pady=1, padx=1,  sticky='e')


        self.root.grid_columnconfigure(0, weight=1)#, uniform="fred")
        self.root.grid_columnconfigure(1, weight=1)#, uniform="fred")
        self.root.grid_columnconfigure(2, weight=1)#, uniform="fred")
        self.root.grid_columnconfigure(3, weight=1)#, uniform="fred")
        self.root.grid_columnconfigure(4, weight=1)#, uniform="fred")
        self.root.grid_columnconfigure(5, weight=1)#, uniform="fred")
        self.root.grid_columnconfigure(6, weight=1)#, uniform="fred")

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.root.grid_propagate(False)

        self.refresh_display()

    def run(self):
        self.root.mainloop()

    def start_listening(self):
        self.start_button.config(state='disable')
        self.host = self.host_entry.get()
        save_config({'host': self.host})

        if not self.controller:
            self.controller = Controller(self.host)
            if self.controller.auto_enter is True:
                self.auto_enter_button.config(relief='sunken')

        else:
            self.controller.host = self.host

        self.listening_thread = threading.Thread(target=self.controller.start_listening)
        self.listening_thread.start()

    def stop_listening(self):
        self.stop_button.config(state='disable')
        if self.controller:
            self.controller.stop_listening()

        while self.controller.is_listening or self.controller.is_connecting: #-------------------maybe not needed
            time.sleep(.1)

    def set_units(self, unit):
        if self.controller:
            self.controller.set_units(unit)
            time.sleep(.1)

    def auto_enter(self):
        if self.controller:
            if self.controller.auto_enter is True:
                self.controller.auto_enter = False
                self.auto_enter_button.config(relief='raised')
            else:
                self.controller.auto_enter = True
                self.auto_enter_button.config(relief='sunken')

            print(self.controller.auto_enter)

    def update_lua_app(self):
        threading.Thread(target=self.run_update_lua, daemon=True).start()

    def run_update_lua(self):
        self.update_lua_button.config(state='disable')
        self.update_status.set(f"updating")

        if not self.controller:
            host = self.host_entry.get()
            self.controller = Controller(host)

        flag = self.controller.update_lua_code(ABS_LUA_SCRIPT_PATH)

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

    def disable_input(self):
        self.host_entry.config(state='disable')

    def enable_input(self):
        self.host_entry.config(state='normal')

    def refresh_led(self):
        if self.controller:
            if self.controller.is_listening:
                self.led_canvas.itemconfig(self.led, fill="green")
            elif self.controller.is_connecting:
                self.led_canvas.itemconfig(self.led, fill="yellow")
            else:
                self.led_canvas.itemconfig(self.led, fill="red")
        else:
            self.led_canvas.itemconfig(self.led, fill="red")

    def refresh_buttons(self):
        if self.controller:
            if self.controller.is_connecting:
                self.disable_input()
                self.start_button.config(state='disable')
                self.stop_button.config(state='normal')
            else:
                if self.controller.is_listening:
                    self.disable_input()
                    self.start_button.config(state='disable')
                    self.stop_button.config(state='normal')
                else:
                    self.enable_input()
                    self.start_button.config(state='normal')
                    self.stop_button.config(state='disable')
        else:
            self.enable_input()
            self.start_button.config(state='normal')
            self.stop_button.config(state='disable')

    def refresh_weight(self):
        if self.controller:
            self.units.config(state='normal')
            self.auto_enter_button.config(state='normal')

            if self.controller.is_listening:
                weight = self.controller.get_weight()
                if weight is not None:
                    if self.controller.units == 'kg':
                        self.weight_value.set(f"{weight:.04f} {self.controller.units} ")
                    else:
                        self.weight_value.set(f"{weight:.01f} {self.controller.units} ")
            else:
                self.weight_value.set("-  ")
        else:
            self.weight_value.set("-  ")
            self.units.config(state='disable')
            self.auto_enter_button.config(state='disable')

    def refresh_display(self):
        self.refresh_buttons()
        self.refresh_weight()
        self.refresh_led()

        self.root.after(100, self.refresh_display)

    def on_close(self):
        if self.controller is not None:
            self.controller.stop_listening()
        self.root.destroy()


def main():
    gui = GUI()
    gui.run()


main()