import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from models.supplier import SupplierModel

class SupplierView():
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.model = SupplierModel()
        self.frame = tk.Frame(parent, bg="#79858C")
        self.create_widgets()

    def create_widgets(self):
        self.create_tree_view()
        self.create_buttons()

    def create_tree_view(self):
        pass


    def create_buttons(self):
        
        self.frame.rowconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=4)

        show_spl_btn = ttk.Button(self.frame, text="Mostrar Proveedores", command=self.controller.show_suppliers)
        show_spl_btn.grid(row=0, column=0)