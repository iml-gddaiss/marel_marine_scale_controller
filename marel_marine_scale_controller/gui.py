import time

from marel_marine_scale_controller.marel_controller import Controller, COMM_PORT

import tkinter as tk

import threading

LUA_SCRIPT = "marel_app.lua"


def iter_row(r):
    while 1:
        yield r
        r += 1


class GUI:
    def __init__(self, host: str):
        self.listening_thread = None
        self.controller = None

        self.init_layout(host)

    def init_layout(self, host):
        self.root = tk.Tk()
        self.root.title("Marel Controller")
        #self.root.geometry('200x200')  # set the size of the window
        self.root.minsize(230, 180)  # Set the minimum width of the window
        self.root.maxsize(230, 180)

        row = iter_row(0)

        # HOST INPUT
        r=next(row)
        host_label = tk.Label(self.root, text="Host:", justify='left')
        host_label.grid(row=r, column=0, sticky='ew', padx=5)
        self.host_entry = tk.Entry(self.root, justify='right', width=15)
        self.host_entry.insert(tk.END, host)
        self.host_entry.grid(row=0, column=1, pady=5, padx=5, stick='ew')

        # UPDATE
        r = next(row)
        self.update_status = tk.StringVar(value="----")
        update_status_label = tk.Label(self.root, textvariable=self.update_status, width=10, relief='sunken')
        update_status_label.grid(row=r, column=0, pady=5, padx=5, sticky='ew')

        # Update Lua App Button
        self.update_lua_button = tk.Button(self.root, text="Update Lua App", width=12, command=self.update_lua_app)
        self.update_lua_button.grid(row=r, column=1, pady=5, padx=5, stick='ew')

        # LED indicator
        r = next(row)
        self.led_canvas = tk.Canvas(self.root, width=20, height=20)
        self.led_canvas.grid(row=r, column=0, pady=5)
        self.led = self.led_canvas.create_oval(5, 5, 15, 15, fill="red")

        # Start | Stop Button
        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop_listening, state='disable')
        self.stop_button.grid(row=r, column=1, pady=5, padx=5, sticky='e')

        self.start_button = tk.Button(self.root, text="Start", command=self.start_listening)
        self.start_button.grid(row=r, column=1, pady=5, padx=5,  sticky='w')


        # Weight display
        r = next(row)
        weight_label = tk.Label(self.root, text="Weight: ", font=10)
        weight_label.grid(row=r, column=0, sticky='ew', padx=5)
        self.weight_value = tk.StringVar(value="----")
        weight_value_label = tk.Label(self.root, textvariable=self.weight_value,
                                      font=16, height=2, border=1,
                                      width=12, relief='sunken')
        weight_value_label.grid(row=r, column=1, padx=5, pady=5, sticky='ew')

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.refresh_display()

    def run(self):
        self.root.mainloop()

    def start_listening(self):
        self.start_button.config(state='disable')
        if not self.controller:
            host = self.host_entry.get()
            # port = int(self.port_entry.get())
            self.controller = Controller(host)

        self.listening_thread = threading.Thread(target=self.controller.start_listening)
        self.listening_thread.start()

    def stop_listening(self):
        self.stop_button.config(state='disable')
        if self.controller:
            self.controller.stop_listening()

        while self.controller.is_listening or self.controller.is_connecting: #-------------------maybe not needed
            time.sleep(.1)

    def update_lua_app(self):
        threading.Thread(target=self.run_update_lua, daemon=True).start()

    def run_update_lua(self):
        self.update_lua_button.config(state='disable')
        self.update_status.set(f"updating")

        if not self.controller:
            host = self.host_entry.get()
            self.controller = Controller(host)

        flag = self.controller.update_lua_code(LUA_SCRIPT)

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
        #self.port_entry.config(state='disable')

    def enable_input(self):
        self.host_entry.config(state='normal')
        #self.port_entry.config(state='normal')

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
            # values = self.controller.get_latest_values()
            # self.value_text.delete(1.0, tk.END)
            # for name, value in values.items():
            #     self.value_text.insert(tk.END, f"{name}: {value}\n")

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
            #self.update_lua_button.config(state='disable')

    def refresh_weight(self):
        if self.controller:
            if self.controller.is_listening:
                weight = self.controller.get_weight()
                if weight is not None:
                    self.weight_value.set(f"{weight:.4f} {self.controller.units}")
            else:
                self.weight_value.set("-----")
        else:
            self.weight_value.set("-----")

    def refresh_display(self):
        self.refresh_buttons()
        self.refresh_weight()
        self.refresh_led()

        self.root.after(100, self.refresh_display)

    def on_close(self):
        if self.controller is not None:
            self.controller.stop_listening()
        self.root.destroy()


if __name__ == "__main__":
    gui = GUI("localhost")
    #gui = GUI("192.168.0.202")
    gui.run()

