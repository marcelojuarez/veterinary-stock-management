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

    """ Crear todos los widgets del formulario """
    def create_widgets(self):
        self.create_find_frame()
        self.create_tree_frame()
        self.create_buttons_frame()

    def create_tree_frame(self):
        pass


    def create_buttons_frame(self):
        """ Crear frame para botones de supplier"""

        manage_frame = tk.LabelFrame(self.frame, borderwidth=2)
        manage_frame.grid(row=5, column= 0,padx=[10, 20], pady=20, ipadx=[6])
        
        save_btn = tk.Button(manage_frame, text='Guardar', width=15, borderwidth=3, bg="blue", fg='black')
        update_btn = tk.Button(manage_frame, text='Actualizar', width=15, borderwidth=3, bg="#17E574", fg='black')
        delete_btn = tk.Button(manage_frame, text='Borrar', width=15, borderwidth=3, bg="#D6C52F", fg='black')
        add_btn = tk.Button(manage_frame, text='Agregar', width=15, borderwidth=3, bg="#B817E5", fg='black')
        clear_btn = tk.Button(manage_frame, text='Limpiar', width=15, borderwidth=3, bg="#E51717", fg='black')

        save_btn.grid(row= 0, column=0, padx=5, pady=5)
        update_btn.grid(row= 0, column=1, padx=5, pady=5)
        delete_btn.grid(row= 0, column=2, padx=5, pady=5)
        add_btn.grid(row= 0, column=3, padx=5, pady=5)
        clear_btn.grid(row= 0, column=4, padx=5, pady=5)

    def create_find_frame(self):
        pass