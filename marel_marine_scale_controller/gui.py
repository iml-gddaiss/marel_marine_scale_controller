import tkinter as tk
from tkinter import ttk

from marel_marine_scale_controller.marel_controller import Controller

import tkinter as tk
import threading



class GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Controller GUI")

        self.host_label = tk.Label(self.root, text="Host:")
        self.host_label.grid(row=0, column=0)
        self.host_entry = tk.Entry(self.root)
        self.host_entry.insert(tk.END, "localhost")
        self.host_entry.grid(row=0, column=1)

        self.port_label = tk.Label(self.root, text="Port:")
        self.port_label.grid(row=1, column=0)
        self.port_entry = tk.Entry(self.root)
        self.port_entry.insert(tk.END, "5000")
        self.port_entry.grid(row=1, column=1)

        self.start_button = tk.Button(self.root, text="Start", command=self.start_listening)
        self.start_button.grid(row=2, column=0)

        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop_listening)
        self.stop_button.config(state='disable')
        self.stop_button.grid(row=2, column=1)

        self.value_label = tk.Label(self.root, text="Values:")
        self.value_label.grid(row=3, column=0)
        self.value_text = tk.Text(self.root, height=10, width=50)
        self.value_text.grid(row=4, column=0, columnspan=2)

        self.thread = None

        self.controller = None

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.update_values()

    def run(self):
        self.root.mainloop()

    def start_listening(self):
        self.start_button.config(state='disable')
        if not self.controller:
            host = self.host_entry.get()
            port = int(self.port_entry.get())
            self.controller = Controller(host, port)

        self.thread = threading.Thread(target=self.controller.start_listening)
        self.thread.start()

    def stop_listening(self):
        self.stop_button.config(state='disable')
        if self.controller:
            self.controller.stop_listening()

    def disable_input(self):
        self.host_entry.config(state='disable')
        self.port_entry.config(state='disable')

    def enable_input(self):
        self.host_entry.config(state='normal')
        self.port_entry.config(state='normal')

    def update_values(self):
        if self.controller:
            values = self.controller.get_latest_values()
            self.value_text.delete(1.0, tk.END)
            for name, value in values.items():
                self.value_text.insert(tk.END, f"{name}: {value}\n")

            if self.controller.is_connecting:
                self.disable_input()
                self.start_button.config(state='disable')
                self.stop_button.config(state='normal')
            else:
                if self.controller.is_running:
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


        self.root.after(100, self.update_values)

    def on_close(self):
        if self.controller is not None:
            self.controller.stop_listening()
        self.root.destroy()


if __name__ == "__main__":
    HOST = "localhost"
    PORT = 5

    gui = GUI()
    gui.run()
