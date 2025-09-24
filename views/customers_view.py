import tkinter as tk
from tkinter import ttk, messagebox
from models.customer import CustomerModel

class CustomersView:
    def __init__(self, parent, controller=None):
        self.controller = controller
        self.model = CustomerModel()
        self.frame = tk.Frame(parent, bg="#79858C")
        self.setup_variables()
        self.create_widgets()

    def set_controller(self, controller):
        """Asignar controller después de la inicialización"""
        self.controller = controller

    def setup_variables(self):
        self.name_var = tk.StringVar()
        self.cuit_var = tk.StringVar()
        self.home_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.debt_amount_var = tk.DoubleVar()
        self.find_var = tk.StringVar()

    def create_widgets(self):
        self.create_find_frame()
        self.create_tree_frame()
        self.create_buttons_frame()

    def create_find_frame(self):
        find_frame = tk.LabelFrame(self.frame, borderwidth=2)
        find_frame.grid(row=0, column=0, sticky='w', padx=10, pady=10, ipadx=6)

        tk.Label(find_frame, text='Buscar:').grid(row=0, column=0, padx=5)
        self.find_entry = tk.Entry(find_frame, textvariable=self.find_var, width=30)
        self.find_entry.grid(row=0, column=1, padx=5)
        find_btn = tk.Button(find_frame, text="Buscar", command=self.search_customer)
        find_btn.grid(row=0, column=2, padx=5)

    def create_tree_frame(self):
        tree_frame = ttk.Frame(self.frame)
        tree_frame.grid(row=1, column=0, padx=10, pady=10, sticky='w')

        self.customer_tree = ttk.Treeview(tree_frame, show='headings', height=20)
        scrl_bar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.customer_tree.yview)
        scrl_bar.grid(row=0, column=1, sticky='ns')
        self.customer_tree.configure(yscrollcommand=scrl_bar.set)

        self.customer_tree['columns'] = ("Id","Nombre","Cuit","Domicilio","Telefono","Monto Deuda")
        for col in self.customer_tree['columns']:
            self.customer_tree.column(col, anchor=tk.W, width=100, stretch=False)
            self.customer_tree.heading(col, text=col + " ↕")

        self.customer_tree.tag_configure('orow', background="#FFFFFF")
        self.customer_tree.grid(row=0, column=0, padx=10, pady=10)

        self.customer_tree.bind("<Double-1>", self.on_double_click)

    def create_buttons_frame(self):
        manage_frame = tk.LabelFrame(self.frame, borderwidth=2)
        manage_frame.grid(row=2, column=0, padx=10, pady=10, ipadx=6)

        add_btn = tk.Button(manage_frame, text='Agregar', width=15, command=self.open_add_window)
        update_btn = tk.Button(manage_frame, text='Actualizar deuda', width=15, command=self.update_debt)
        delete_btn = tk.Button(manage_frame, text='Borrar', width=15, command=self.delete_customer)
        clear_btn = tk.Button(manage_frame, text='Limpiar', width=15, command=self.clear_form)

        add_btn.grid(row=0, column=0, padx=5, pady=5)
        update_btn.grid(row=0, column=1, padx=5, pady=5)
        delete_btn.grid(row=0, column=2, padx=5, pady=5)
        clear_btn.grid(row=0, column=3, padx=5, pady=5)

    def open_add_window(self):
        add_win = tk.Toplevel(self.frame)
        add_win.title("Agregar nuevo cliente")

        ttk.Label(add_win, text='Nombre:').grid(row=0, column=0, padx=5, pady=5, sticky='nw')
        ttk.Entry(add_win, textvariable=self.name_var).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(add_win, text='Cuit:').grid(row=1, column=0, padx=5, pady=5, sticky='nw')
        ttk.Entry(add_win, textvariable=self.cuit_var).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(add_win, text='Domicilio:').grid(row=2, column=0, padx=5, pady=5, sticky='nw')
        ttk.Entry(add_win, textvariable=self.home_var).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(add_win, text='Telefono:').grid(row=3, column=0, padx=5, pady=5, sticky='nw')
        ttk.Entry(add_win, textvariable=self.phone_var).grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(add_win, text='Monto Deuda:').grid(row=5, column=0, padx=5, pady=5, sticky='nw')
        ttk.Entry(add_win, textvariable=self.debt_amount_var).grid(row=5, column=1, padx=5, pady=5)

        ttk.Button(add_win, text="Agregar", command=lambda: self.controller.add_new_customer(add_win)).grid(row=6, column=1, pady=10)

    def get_customer_data(self):
        return {
            'nombre': self.name_var.get().strip(),
            'cuit': self.cuit_var.get().strip(),
            'domicilio': self.home_var.get().strip(),
            'telefono': self.phone_var.get().strip(),
            'monto_deuda': self.debt_amount_var.get()
        }

    def refresh_customer_table(self, customers):
        for item in self.customer_tree.get_children():
            self.customer_tree.delete(item)
        for customer in customers:
            self.customer_tree.insert(parent='', index='end', iid=customer[0], values=customer, tag='orow')
        self.customer_tree.tag_configure('orow', background='white')

    def search_customer(self):
        if self.controller:
            self.controller.search_customer(self.find_var.get())

    def update_debt(self):
        selected = self.customer_tree.selection()
        if not selected:
            self.show_error("Seleccioná un cliente")
            return

        row_id = selected[0]
        col = "#6"  # Columna Monto Deuda

        # Obtener posición y tamaño de la celda
        x, y, width, height = self.customer_tree.bbox(row_id, col)
        value = self.customer_tree.set(row_id, column=col)

        # Crear Entry sobre la celda
        self.edit_box = tk.Entry(self.customer_tree)
        self.edit_box.place(x=x, y=y, width=width, height=height)
        self.edit_box.insert(0, value)
        self.edit_box.focus()

        # Guardar con Enter
        self.edit_box.bind("<Return>", lambda e: self.save_edit(row_id, col))
        # Cancelar con Escape
        self.edit_box.bind("<Escape>", lambda e: self.edit_box.destroy())


    def delete_customer(self):
        if self.controller:
            selected = self.customer_tree.selection()
            if not selected:
                self.show_error("Seleccioná un cliente")
                return
            customer_id = self.customer_tree.item(selected[0])['values'][0]
            self.controller.delete_customer(customer_id)

    def clear_form(self):
        self.name_var.set("")
        self.cuit_var.set("")
        self.home_var.set("")
        self.phone_var.set("")
        self.debt_amount_var.set(0.0)

    def show_error(self, message):
        messagebox.showerror("Error", message)

    def show_success(self, message):
        messagebox.showinfo("Éxito", message)

    def show_warning(self, message):
        messagebox.showwarning("Advertencia", message)

    def save_edit(self, row_id, col):
        new_value = self.edit_box.get()
        self.customer_tree.set(row_id, column=col, value=new_value)
        self.edit_box.destroy()

        # Llamar al controlador para actualizar la deuda en la base
        customer_id = self.customer_tree.item(row_id)['values'][0]
        self.controller.update_customer_debt(customer_id, float(new_value))

    def on_double_click(self, event):
        row_id = self.customer_tree.identify_row(event.y)
        col = self.customer_tree.identify_column(event.x)

        # Solo permitir edición en la columna Monto Deuda
        if col != "#6":  # Ajusta si tu columna es diferente
            return

        x, y, width, height = self.customer_tree.bbox(row_id, col)
        value = self.customer_tree.set(row_id, column=col)

        self.edit_box = tk.Entry(self.customer_tree)
        self.edit_box.place(x=x, y=y, width=width, height=height)
        self.edit_box.insert(0, value)
        self.edit_box.focus()

        self.edit_box.bind("<Return>", lambda e: self.save_edit(row_id, col))
        self.edit_box.bind("<Escape>", lambda e: self.edit_box.destroy())

