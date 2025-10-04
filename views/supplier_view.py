import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import random as rd
from tkinter import PhotoImage
from models.supplier import SupplierModel

class SupplierView():
    def __init__(self, parent, controller=None):
        self.controller = controller
        self.model = SupplierModel()
        self.frame = tk.Frame(parent, bg="#79858C")
        self.setup_variables()
        self.create_widgets()

    def set_controller(self, controller):
        """Asignar controller después de la inicialización"""
        print(f"DEBUG: Asignando controller: {controller}")
        self.controller = controller
        print(f"DEBUG: Controller asignado correctamente: {self.controller}")

    def setup_variables(self):
        # variables proveedor
        self.name_var = tk.StringVar()
        self.cuit_var = tk.StringVar()
        self.home_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.find_var = tk.StringVar()

        # variables producto
        self.name_product_var = tk.StringVar()
        self.description_var = tk.StringVar()
        self.brand_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.quantity_var = tk.StringVar()

    """ Crear todos los widgets del formulario """
    def create_widgets(self):
        self.create_find_frame()
        self.create_tree_frame()
        self.create_buttons_frame()

    def create_find_frame(self):
        """Crear frame para formulario de producto"""
        find_frame = tk.LabelFrame(self.frame, borderwidth=2)
        find_frame.grid(row=0, column=0, sticky='w', padx=[10,200], pady=[0,20], ipadx=[6])

        find_btn = tk.Button(find_frame, text="Buscar", borderwidth=3, bg="#FFFFFF", fg='black')
        find_btn.grid(row=0, column=2, padx=5, pady=5)

        tk.Label(find_frame, text='Buscar:', anchor='e', width=5).grid(row=0, column=0, padx=5)
        self.find_entry = tk.Entry(find_frame, width=30, textvariable=self.find_var)
        self.find_entry.grid(row=0, column=1, padx=5, pady=5)


    def create_tree_frame(self):
        """ Crea el frame para la tabla de Proveedores"""
        tree_frame = ttk.Frame(self.frame)
        tree_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')

        # Treeview
        self.supplier_tree = ttk.Treeview(tree_frame, show='headings', height=25)

        # Scrollbar vertical para los proveedores
        scrl_bar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.supplier_tree.yview)
        scrl_bar.grid(row=0, column=2, sticky='ns')
        self.supplier_tree.configure(yscrollcommand=scrl_bar.set)
                           
        self.supplier_tree['columns'] = ("Id","Nombre", "Cuit", "Domicilio", "Telefono", "Email")
        self.supplier_tree['displaycolumns'] = self.supplier_tree['columns']
        self.supplier_tree.column("Id", anchor=tk.W, width=80,stretch=False)
        self.supplier_tree.column("Nombre", anchor=tk.W, width=180,stretch=False)
        self.supplier_tree.column("Cuit", anchor=tk.W, width=140,stretch=False)
        self.supplier_tree.column("Domicilio", anchor=tk.W, width=140,stretch=False)
        self.supplier_tree.column("Telefono", anchor=tk.W, width=140,stretch=False)
        self.supplier_tree.column("Email", anchor=tk.W, width=140,stretch=False)

        self.supplier_tree.heading('Id', text='ID ↕')
        self.supplier_tree.heading('Nombre', text='Nombre↕')
        self.supplier_tree.heading('Cuit', text='Cuit ↕')
        self.supplier_tree.heading('Domicilio', text='Domicilio ↕')
        self.supplier_tree.heading('Telefono', text='Telefono ↕')
        self.supplier_tree.heading('Email', text='Email ↕')

        self.supplier_tree.tag_configure('orow', background="#FFFFFF")
        self.supplier_tree.grid(row=0, column= 1,padx=[20, 20], pady=20, ipadx=[6], sticky='nsew')

    def create_buttons_frame(self):
        """ Crear frame para botones de supplier"""

        manage_frame = tk.LabelFrame(self.frame, borderwidth=2)
        manage_frame.grid(row=2, column= 0,padx=[10, 20], pady=20, ipadx=[6])
        
        save_btn = tk.Button(manage_frame, text='Guardar', width=15, borderwidth=3, bg="blue", fg='black')
        update_btn = tk.Button(manage_frame, text='Info', width=15, borderwidth=3, bg="#17E574", fg='black', command=lambda: self.controller.supplier_info())
        delete_btn = tk.Button(manage_frame, text='Borrar', width=15, borderwidth=3, bg="#D6C52F", fg='black', command=lambda:self.controller.delete_supplier())
        add_btn = tk.Button(manage_frame, text='Agregar', width=15, borderwidth=3, bg="#B817E5", fg='black', command=lambda: self.open_add_window())
        clear_btn = tk.Button(manage_frame, text='Limpiar', width=15, borderwidth=3, bg="#E51717", fg='black')

        save_btn.grid(row= 0, column=0, padx=5, pady=5)
        update_btn.grid(row= 0, column=1, padx=5, pady=5)
        delete_btn.grid(row= 0, column=2, padx=5, pady=5)
        add_btn.grid(row= 0, column=3, padx=5, pady=5)
        clear_btn.grid(row= 0, column=4, padx=5, pady=5)

    def open_add_window(self):
        add_win = tk.Toplevel(self.frame)
        add_win.title("Agregar nuevo proveedor")

        # posicion y tamaño del frame
        x_root = self.frame.winfo_x() 
        y_root = self.frame.winfo_y()
        width_root = self.frame.winfo_width()
        height_root = self.frame.winfo_height()

        width_win = 300
        height_win = 240

        # centro
        x = x_root + (width_root // 2) - (width_win // 2)
        y = y_root + (height_root // 2) - (height_win // 2)

        add_win.geometry(f"{width_win}x{height_win}+{x}+{y}")

        ttk.Label(add_win, text='Nombre:').grid(row=1, column=0, padx=5, pady=5, sticky='nw')
        name_entry = ttk.Entry(add_win, textvariable=self.name_var)
        name_entry.grid(row=1, column=1, padx=5, pady=5, sticky='nw')

        ttk.Label(add_win, text='Cuit:').grid(row=2, column=0, padx=5, pady=5, sticky='nw')
        cuit_entry = ttk.Entry(add_win, textvariable=self.cuit_var)
        cuit_entry.grid(row=2, column=1, padx=5, pady=5, sticky='nw')

        ttk.Label(add_win, text='Domicilio:').grid(row=3, column=0, padx=5, pady=5, sticky='nw')
        cuit_entry = ttk.Entry(add_win, textvariable=self.home_var)
        cuit_entry.grid(row=3, column=1, padx=5, pady=5, sticky='nw')

        ttk.Label(add_win, text='Telefono:').grid(row=4, column=0, padx=5, pady=5, sticky='nw')
        cuit_entry = ttk.Entry(add_win, textvariable=self.phone_var)
        cuit_entry.grid(row=4, column=1, padx=5, pady=5, sticky='nw')

        ttk.Label(add_win, text='Email:').grid(row=5, column=0, padx=5, pady=5, sticky='nw')
        cuit_entry = ttk.Entry(add_win, textvariable=self.email_var)
        cuit_entry.grid(row=5, column=1, padx=5, pady=5, sticky='nw')

        finish_btn = ttk.Button(add_win, text="Agregar", command=lambda: self.controller.add_new_supplier(add_win))
        finish_btn.grid(row=6, column=1)

    def open_add_product_window(self, id):
        add_product_win = tk.Toplevel(self.frame)
        add_product_win.title("Agregar Productos")

        # posicion y tamaño del frame
        x_root = self.frame.winfo_x() 
        y_root = self.frame.winfo_y()
        width_root = self.frame.winfo_width()
        height_root = self.frame.winfo_height()

        width_win = 400
        height_win = 300

        # centro
        x = x_root + (width_root // 2) - (width_win // 2)
        y = y_root + (height_root // 2) - (height_win // 2)

        add_product_win.geometry(f"{width_win}x{height_win}+{x}+{y}")

        fields = [
            ("Nombre: ", self.name_product_var),
            ("Descripcion: ", self.description_var),
            ("Marca: ", self.brand_var),
            ("Precio:", self.price_var),
            ("Cantidad: ", self.quantity_var)
        ]

        for i, (label_text, var) in enumerate(fields, start=1):
            label = ttk.Label(add_product_win, text=label_text)
            label.grid(row=i, column=0, padx=20, pady=10, sticky="w")

            entry = ttk.Entry(
                add_product_win,
                textvariable=var
            )

            entry.grid(row=i, column=1, padx=20, pady=10)

        add_btn = ttk.Button(add_product_win, text="Agregar", command=lambda:self.controller.add_supplier_product(id))
        add_btn.grid(row=6, column=0)

        finish_btn = ttk.Button(add_product_win, text="Listo", command=add_product_win.destroy)
        finish_btn.grid(row=6, column=1)


    def get_supplier_data(self):
        return {
            'nombre': self.name_var.get().strip(),
            'cuit': self.cuit_var.get().strip(),
            'domicilio': self.home_var.get().strip(),
            'telefono': self.phone_var.get().strip(),
            'email': self.email_var.get().strip(),
        }
    
    def get_product_data(self):
        return {
            'name': self.name_product_var.get().strip(),
            'description': self.description_var.get().strip(),
            'brand': self.brand_var.get().strip(),
            'price': self.price_var.get().strip(),
            'quantity': self.quantity_var.get().strip(),
        }
        

    def refresh_supplier_table(self, suppliers):
        for item in self.supplier_tree.get_children():
            self.supplier_tree.delete(item)

        for supplier in suppliers:
            print(supplier)
            self.supplier_tree.insert(parent='', index='end', iid=supplier[0], values=supplier, tag="orow")

        self.supplier_tree.tag_configure('orow', background="white", foreground='black')


    def open_info_window(self, supplier):
        info_win = tk.Toplevel(self.frame)
        info_win.title(f'Proveedor: {supplier}')

        # posicion y tamaño del frame
        x_root = self.frame.winfo_x() 
        y_root = self.frame.winfo_y()
        width_root = self.frame.winfo_width()
        height_root = self.frame.winfo_height()

        width_win = 300
        height_win = 240

        # centro
        x = x_root + (width_root // 2) - (width_win // 2)
        y = y_root + (height_root // 2) - (height_win // 2)

        info_win.geometry(f"{width_win}x{height_win}+{x}+{y}")


    def show_error(self, message):
        messagebox.showerror("Error", message)

    def show_success(self, message):
        messagebox.showinfo("Éxito", message)

    def show_warning(self, message):
        messagebox.showwarning('Advertencia', message) 
    
