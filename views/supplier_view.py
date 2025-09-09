import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import random as rd
from models.supplier import SupplierModel

class SupplierView():
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.model = SupplierModel()
        self.frame = tk.Frame(parent, bg="#79858C")
        self.create_widgets()
        self.load_data()

    """ Crear todos los widgets del formulario """
    def create_widgets(self):
        self.create_find_frame()
        self.create_tree_frame()
        self.create_buttons_frame()

    def create_find_frame(self):
        find_frame = ttk.Frame(self.frame)
        find_frame.grid(row=0, column=0, padx=10, pady=10, sticky='w')


    def create_tree_frame(self):
        """ Crea el frame para la tabla de Proveedores"""
        tree_frame = ttk.Frame(self.frame)
        tree_frame.grid(row=1, column=0, padx=10, pady=10, sticky='w')

        # Treeview
        self.supplier_tree = ttk.Treeview(tree_frame, show='headings', height=25)

        # Scrollbar vertical para los proveedores
        scrl_bar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.supplier_tree.yview)
        scrl_bar.grid(row=0, column=1, sticky='ns')
        self.supplier_tree.configure(yscrollcommand=scrl_bar.set)
                           
        self.supplier_tree['columns'] = ("ID","NOMBRE", "RAZON SOCIAL", "ACTIVO")
        self.supplier_tree['displaycolumns'] = self.supplier_tree['columns']
        self.supplier_tree.column("ID", anchor=tk.W, width=80,stretch=False)
        self.supplier_tree.column("RAZON SOCIAL", anchor=tk.W, width=80,stretch=False)
        self.supplier_tree.column("NOMBRE", anchor=tk.W, width=180,stretch=False)
        self.supplier_tree.column("ACTIVO", anchor=tk.W, width=100,stretch=False)

        self.supplier_tree.heading('ID', text='ID ↕')
        self.supplier_tree.heading('RAZON SOCIAL', text='RAZON SOCIAL ↕')
        self.supplier_tree.heading('NOMBRE', text='NOMBRE ↕')
        self.supplier_tree.heading('ACTIVO', text='ACTIVO ↕')

        self.supplier_tree.tag_configure('orow', background="#FFFFFF")
        self.supplier_tree.grid(row=0, column= 0,padx=[10, 10], pady=20, ipadx=[6])

    def create_buttons_frame(self):
        """ Crear frame para botones de supplier"""

        manage_frame = tk.LabelFrame(self.frame, borderwidth=2)
        manage_frame.grid(row=2, column= 0,padx=[10, 20], pady=20, ipadx=[6])
        
        save_btn = tk.Button(manage_frame, text='Guardar', width=15, borderwidth=3, bg="blue", fg='black')
        update_btn = tk.Button(manage_frame, text='Actualizar', width=15, borderwidth=3, bg="#17E574", fg='black')
        delete_btn = tk.Button(manage_frame, text='Borrar', width=15, borderwidth=3, bg="#D6C52F", fg='black')
        add_btn = tk.Button(manage_frame, text='Agregar', width=15, borderwidth=3, bg="#B817E5", fg='black', command=lambda: self.add_supplier_window())
        clear_btn = tk.Button(manage_frame, text='Limpiar', width=15, borderwidth=3, bg="#E51717", fg='black')

        save_btn.grid(row= 0, column=0, padx=5, pady=5)
        update_btn.grid(row= 0, column=1, padx=5, pady=5)
        delete_btn.grid(row= 0, column=2, padx=5, pady=5)
        add_btn.grid(row= 0, column=3, padx=5, pady=5)
        clear_btn.grid(row= 0, column=4, padx=5, pady=5)

    def add_supplier_window(self):
        add_win = tk.Toplevel(self.frame)
        add_win.title("Agregar nuevo proveedor")
        add_win.geometry("300x200")

        name_lbl = ttk.Label(add_win, text='Nombre:')
        name_lbl.grid(row=0, column=0, padx=5, pady=5, sticky='nw')

        self.name_entry = ttk.Entry(add_win)
        self.name_entry.grid(row=0, column=1, pady=5, sticky='nw')

        company_name_lbl = ttk.Label(add_win, text='Razon Social:')
        company_name_lbl.grid(row=1, column=0, padx=5, pady=5, sticky='nw')

        self.company_name_entry = ttk.Entry(add_win)
        self.company_name_entry.grid(row=1, column=1, pady=5, sticky='nw')

        finish_btn = ttk.Button(add_win, text="Agregar", command=lambda: self.on_add_btn_click())
        finish_btn.grid(row=2, column=1)

    def get_supplier_data(self):
        return {
            'name': self.name_entry.get(),
            'company_name': self.company_name_entry.get()
        }
        

    def load_data(self):
        try:
            data = self.controller.show_suppliers()
            for d in data:
                self.supplier_tree.insert('', 'end', values=d)
        except ValueError as e:
            self.show_error(e)

    def refresh_supplier_table(self):
        pass

    def show_error(self, message):
        messagebox.showerror("Error", message)

    def show_succes(self, message):
        messagebox.showinfo("Éxito", message)

    def show_warting(self, message):
        messagebox.showwarning('Advertencia', message) 
    


            
