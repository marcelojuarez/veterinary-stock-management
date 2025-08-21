import tkinter as tk
from tkinter import ttk
from config.settings import settings

class App():
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()

    def setup_window(self):
        view_config = settings['VIEW_CONFIG']
        self.root.title(view_config['window-title'])
        self.root.geometry(view_config['window-size'])

    def run(self):
        self.root.mainloop()