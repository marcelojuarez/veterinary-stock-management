import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from tksheet import Sheet
from models.supplier import SupplierModel
from models.stock import StockModel
from controllers.payment_controller import PaymentController
from views.payments.payment_window import PaymentWindow
from views.view_helpers import close_win, show_warning

# Configurar tema y colores
ctk.set_appearance_mode("light")  # "light" o "dark"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class SupplierView():
    def __init__(self, parent,  stock_view, controller=None):
        self.controller = controller
        self.model = SupplierModel()
        self.stock_model = StockModel()
        self.stock_view = stock_view
        self.frame = ctk.CTkFrame(parent, fg_color="#f0f0f0")
        self.payment_window = PaymentWindow(self.model, self.frame)
        self.create_widgets()

    def set_controller(self, controller):
        """Asignar controller después de la inicialización"""
        print(f"DEBUG: Asignando controller: {controller}")
        self.controller = controller
        print(f"DEBUG: Controller asignado correctamente: {self.controller}")

    def setup_supplier_variables(self):
        # variables proveedor
        self.name_var = tk.StringVar()
        self.cuit_var = tk.StringVar()
        self.home_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.debt_var = tk.StringVar()

    def setup_product_variables(self):
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
        self.find_var = tk.StringVar()

        """Crear frame para formulario de proveedor"""
        find_frame = ctk.CTkFrame(self.frame)
        find_frame.grid(row=0, column=0, sticky='w', padx=10, pady=10)

        btn_color = "#009688"
        btn_hover = "#00796B"

        search_label = ctk.CTkLabel(
            find_frame, 
            text="Buscar Proveedor", 
            font=ctk.CTkFont(size=14, weight='bold')
        )
        search_label.grid(row=0, column=0, padx=15, pady=15)
        
        self.find_entry = ctk.CTkEntry(
            find_frame,
            width=600,
            height=35,
            textvariable=self.find_var,
            font=ctk.CTkFont(size=12),
            placeholder_text="Ingrese nombre del proveedor..."
        )

        self.find_entry.grid(row=0, column=1, padx=10, pady=15)
        
        find_btn = ctk.CTkButton(
            find_frame,
            text="Buscar",
            width=160,
            height=35,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=btn_color,
            hover_color=btn_hover,
            #command=lambda: self.controller.find_product(self.find_var)
        )

        find_btn.grid(row=0, column=2, padx=5, pady=5)

    def create_tree_frame(self):
        """ Crea el frame para la tabla de Proveedores"""
        tree_frame = ctk.CTkFrame(self.frame)
        tree_frame.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')

        # Titulo de la tabla
        table_title = ctk.CTkLabel(
            tree_frame,
            text="Proveedores",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        table_title.grid(row=0, column=0, pady=(15, 10))

        # Frame interno para la tabla y scrollbar
        table_container = tk.Frame(tree_frame, bg="white")
        table_container.grid(row=1, column=0, padx=15, pady=(0, 15), sticky='nsew')

        # Configurar el estilo del Treeview para que se vea más moderno
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar colores del Treeview
        style.configure('Treeview',
                       background='#ffffff',
                       foreground='#333333',
                       rowheight=30,
                       fieldbackground='#ffffff',
                       font=('Arial', 12))
        
        style.configure('Treeview.Heading',
                       background='#e0e0e0',
                       foreground='#333333',
                       font=('Arial', 12, 'bold'))
        
        style.map('Treeview',
                 background=[('selected', '#0078d4')])

        # Treeview
        self.supplier_tree = ttk.Treeview(table_container, show='headings', height=10)

        # Scrollbar vertical para los proveedores
        scrl_bar = ttk.Scrollbar(table_container, orient='vertical', command=self.supplier_tree.yview)
        scrl_bar.grid(row=0, column=3, sticky='ns')
        self.supplier_tree.configure(yscrollcommand=scrl_bar.set)
                           
        self.supplier_tree['columns'] = ("Id", "Nombre", "Cuit", "Domicilio", "Telefono", "Email", "Saldo Deuda", "Ultima actualizacion deuda")
        self.supplier_tree['displaycolumns'] = self.supplier_tree['columns']
        self.supplier_tree.column("Id", anchor=tk.W, width=50,stretch=False)
        self.supplier_tree.column("Nombre", anchor=tk.W, width=350,stretch=False)
        self.supplier_tree.column("Cuit", anchor=tk.W, width=200,stretch=False)
        self.supplier_tree.column("Domicilio", anchor=tk.W, width=350,stretch=False)
        self.supplier_tree.column("Telefono", anchor=tk.W, width=160,stretch=False)
        self.supplier_tree.column("Email", anchor=tk.W, width=200, stretch=False)
        self.supplier_tree.column("Saldo Deuda", anchor=tk.W, width=140, stretch=False)
        self.supplier_tree.column("Ultima actualizacion deuda", anchor=tk.W, width=140, stretch=False)

        self.supplier_tree.heading('Id', text='ID ↕')
        self.supplier_tree.heading('Nombre', text='Nombre↕')
        self.supplier_tree.heading('Cuit', text='Cuit ↕')
        self.supplier_tree.heading('Domicilio', text='Domicilio ↕')
        self.supplier_tree.heading('Telefono', text='Telefono ↕')
        self.supplier_tree.heading('Email', text='Email ↕')
        self.supplier_tree.heading('Saldo Deuda', text='Saldo Deuda ↕')
        self.supplier_tree.heading('Ultima actualizacion deuda', text='Ultima actualizacion deuda ↕')

        self.supplier_tree.tag_configure('orow', background="#FFFFFF")
        self.supplier_tree.grid(row=1, column=2, padx=[20, 20], pady=20, ipadx=[6], sticky='nsew')

    def create_buttons_frame(self):
        """ Crear frame para botones de supplier"""

        manage_frame = ctk.CTkFrame(self.frame)
        manage_frame.grid(row=2, column= 0,padx=[10, 20], pady=20, ipadx=[6])
        
        W = 240
        H = 35
        btn_color = "#009688"
        btn_hover = "#00796B"

        info_btn = ctk.CTkButton(
            manage_frame, 
            text='Info', 
            width=W, 
            height=H,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=btn_color,
            hover_color=btn_hover,
            command=lambda: self.controller.supplier_info()
        )

        delete_btn = ctk.CTkButton(
            manage_frame, 
            text='Borrar', 
            width=W, 
            height=H,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=btn_color,
            hover_color=btn_hover,
            command=lambda:self.controller.delete_supplier()
        )
        add_btn = ctk.CTkButton(
            manage_frame, 
            text='Agregar', 
            width=W, 
            height=H, 
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=btn_color,
            hover_color=btn_hover,
            command=lambda: self.open_add_window(manage_frame)
        )

        payment_btn = ctk.CTkButton(
            manage_frame, 
            text='Registrar Pago', 
            width=W, 
            height=H, 
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=btn_color,
            hover_color=btn_hover,
            command= lambda: self.payment_window.open_payment_window(manage_frame)
        )

        purchase_btn = ctk.CTkButton(
            manage_frame, 
            text='Registrar Compra', 
            width=W, 
            height=H,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=btn_color,
            hover_color=btn_hover,
            command=lambda: self.open_purchase_window(manage_frame)
        )
        
        info_btn.grid(row= 0, column=0, padx=5, pady=5)
        delete_btn.grid(row= 0, column=1, padx=5, pady=5)
        add_btn.grid(row= 0, column=2, padx=5, pady=5)
        payment_btn.grid(row= 0, column=3, padx=5, pady=5)
        purchase_btn.grid(row=0, column=4, padx=5, pady=5)

    def open_add_window(self, parent):
        self.setup_supplier_variables()

        add_win = ctk.CTkToplevel(self.frame)
        add_win.title("Agregar nuevo proveedor")

        add_win.protocol("WM_DELETE_WINDOW", lambda: close_win(add_win, parent))

        # Hacer que la ventana sea modal
        add_win.transient(self.frame)
        add_win.grab_set()

        # posicion y tamaño del frame
        x_root = self.frame.winfo_x() 
        y_root = self.frame.winfo_y()
        width_root = self.frame.winfo_width()
        height_root = self.frame.winfo_height()

        width_win = 305
        height_win = 280
        btn_color = "#009688"
        btn_hover = "#00796B"

        # centro
        x = x_root + (width_root // 2) - (width_win // 2)
        y = y_root + (height_root // 2) - (height_win // 2)

        add_win.geometry(f"{width_win}x{height_win}+{x}+{y}")

        # nombre
        name_lbl = ctk.CTkLabel(
            add_win, 
            text='Nombre:',
            font=ctk.CTkFont(size=14, weight="bold")
        )
        name_lbl.grid(row=1, column=0, padx=[10,5], pady=5, sticky='nw')
        
        name_entry = ctk.CTkEntry(add_win, textvariable=self.name_var)
        name_entry.grid(row=1, column=1, pady=5, sticky='nw')

        # cuit
        cuit_lbl = ctk.CTkLabel(
            add_win, 
            text='Cuit:',
            font=ctk.CTkFont(size=14, weight="bold")
            )
        cuit_lbl.grid(row=2, column=0, padx=[10,5], pady=5, sticky='nw')

        cuit_entry = ctk.CTkEntry(add_win, textvariable=self.cuit_var)
        cuit_entry.grid(row=2, column=1, pady=5, sticky='nw')

        # domicilio
        dom_lbl =  ctk.CTkLabel(
            add_win, 
            text='Domicilio:',
            font=ctk.CTkFont(size=14, weight="bold")
        )
        dom_lbl.grid(row=3, column=0, padx=[10,5], pady=5, sticky='nw')
        
        dom_entry = ctk.CTkEntry(add_win, textvariable=self.home_var)
        dom_entry.grid(row=3, column=1, pady=5, sticky='nw')

        # phone
        phone_lbl = ctk.CTkLabel(
            add_win, 
            text='Telefono:',
            font=ctk.CTkFont(size=14, weight="bold")
        )
        phone_lbl.grid(row=4, column=0, padx=[10,5], pady=5, sticky='nw')

        phone_entry = ctk.CTkEntry(add_win, textvariable=self.phone_var)
        phone_entry.grid(row=4, column=1, pady=5, sticky='nw')


        email_lbl = ctk.CTkLabel(
            add_win, 
            text='Email:',
            font=ctk.CTkFont(size=14, weight="bold")
        )
        email_lbl.grid(row=5, column=0, padx=[10,5], pady=5, sticky='nw')

        email_entry = ctk.CTkEntry(add_win, textvariable=self.email_var)
        email_entry.grid(row=5, column=1, pady=5, sticky='nw')

        deb_label = ctk.CTkLabel(
            add_win,
            text="Saldo Deuda:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        deb_label.grid(row=6, column=0, padx=[10,5], pady=5, sticky='nw')

        deb_entry = ctk.CTkEntry(add_win, textvariable=self.debt_var)
        deb_entry.grid(row=6, column=1, pady=5, sticky='nw')

        cancel_btn = ctk.CTkButton(
            add_win,
            text="Cancelar",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=lambda: close_win(add_win, parent, self.clear_form_supplier)
        )

        cancel_btn.grid(row=7, column=1, padx=6, pady=5)

        finish_btn = ctk.CTkButton(
            add_win, 
            text="Agregar", 
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=btn_color, 
            hover_color=btn_hover,
            command=lambda: self.controller.add_new_supplier(add_win)
        )
        finish_btn.grid(row=7, column=0,  padx=6, pady=5)


    def open_info_window(self, supplier):
        self.frame.update_idletasks()  # calcula la posicion antes de renderizar ventana

        info_win = ctk.CTkToplevel(self.frame)
        info_win.title(f'Proveedor: {supplier[2]}')

        # posicion y tamaño del frame
        x_root = self.frame.winfo_rootx()
        y_root = self.frame.winfo_rooty()
        width_root = self.frame.winfo_width()
        height_root = self.frame.winfo_height()

        width_win = 800
        height_win = 450
        btn_color = "#009688"
        btn_hover = "#00796B"

        x = x_root + (width_root // 2) - (width_win // 2)
        y = y_root + (height_root // 2) - (height_win // 2)
        info_win.geometry(f"{width_win}x{height_win}+{x}+{y}")

        info_win.grid_rowconfigure(0, weight=1)
        info_win.grid_rowconfigure(1, weight=0)
        info_win.grid_columnconfigure(0, weight=3)
        info_win.grid_columnconfigure(1, weight=1)

        # --- Tksheet con productos ---
        products = self.stock_model.get_all_products_by_cuit(supplier[1])
        products = [(p[0], p[2], p[3]) for p in products]

        sheet = Sheet(info_win)
        sheet.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 0))
        sheet.headers(["Id", "Nombre Artículo", "Envase"])
        sheet.set_sheet_data(products)

        # --- Panel de deuda ---
        self.debt = tk.StringVar(value=f'{supplier[6]}')
        self.last_update_debt = tk.StringVar(value=f'Ultima actualizacion deuda: \n {supplier[7]}')
        right_frame = ctk.CTkFrame(info_win, corner_radius=10)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=(10, 0))

        lbl_title = ctk.CTkLabel(right_frame, text="Deuda proveedor", font=("Arial", 16, "bold"))
        lbl_title.pack(pady=(20, 10))

        self.lbl_debt = ctk.CTkLabel(right_frame, text=f'${self.debt.get()}', font=("Arial", 24, "bold"), text_color="#059649")
        self.lbl_debt.pack(pady=10)

        lbl_note = ctk.CTkLabel(right_frame, textvariable=self.last_update_debt,  font=("Arial", 18, "bold"))
        lbl_note.pack(pady=10)

        # frame botones izquierda
        left_btn_frame = ctk.CTkFrame(info_win, fg_color="transparent")
        left_btn_frame.grid(row=1, column=0, sticky="ew", pady=15)
        left_btn_frame.grid_columnconfigure((0, 1), weight=1)

        # Botón Cancelar 
        cancel_btn = ctk.CTkButton(
            left_btn_frame,
            text='Cerrar',
            fg_color="#E74C3C",
            hover_color="#C0392B",
            text_color="white",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=info_win.destroy
        )
        cancel_btn.grid(row=0, column=1, padx=10, ipadx=5)

        # frame botones derecha
        right_btn_frame = ctk.CTkFrame(info_win, fg_color="transparent")
        right_btn_frame.grid(row=1, column=1, sticky="ew", pady=15)
        right_btn_frame.grid_columnconfigure(0, weight=1)

        # Botón Actualizar Deuda
        update_debt_btn = ctk.CTkButton(
            right_btn_frame,
            text='Actualizar Deuda',
            fg_color=btn_color,
            hover_color=btn_hover,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.update_debt_win(info_win, supplier)
        )
        update_debt_btn.grid(row=0, column=0, padx=10, ipadx=5)


    def update_debt_win(self, parent, supplier):
        update_win = ctk.CTkToplevel(parent)
        update_win.title("Actualizar Deuda Proveedor")

        update_win.grid_rowconfigure(0, weight=1)
        update_win.grid_columnconfigure(0, weight=1)

        # posicion y tamaño del frame
        x_root = parent.winfo_rootx()
        y_root = parent.winfo_rooty()
        width_root = parent.winfo_width()
        height_root = parent.winfo_height()

        width_win = 300
        height_win = 100
        btn_color = "#009688"
        btn_hover = "#00796B"

        x = x_root + (width_root // 2) - (width_win // 2)
        y = y_root + (height_root // 2) - (height_win // 2)
        update_win.geometry(f"{width_win}x{height_win}+{x}+{y}")

        update_frame = ctk.CTkFrame(update_win, fg_color='transparent')
        update_frame.grid(row=0, column=0, sticky='nsew')

        update_frame.columnconfigure(0, weight=1)
        update_frame.columnconfigure(1, weight=1)
        update_frame.rowconfigure(0, weight=1)
        update_frame.rowconfigure(1, weight=1)
        
        debt_lbl = ctk.CTkLabel(update_frame, text="Deuda:", font=ctk.CTkFont(size=18, weight="bold"))
        debt_lbl.grid(row=0, column=0,  padx=5, ipadx=5)

        debt_entry = ctk.CTkEntry(update_frame, textvariable=self.debt)
        debt_entry.grid(row=0, column=1,  padx=5, ipadx=5)

        # Botón Actualizar Deuda
        update_debt_btn = ctk.CTkButton(
            update_frame,
            text='Actualizar',
            fg_color=btn_color,
            hover_color=btn_hover,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=lambda: self.controller.update_debt(supplier, self.debt.get(), update_win)
        )
        update_debt_btn.grid(row=1, column=0, padx=10, ipadx=5)

        cancel_update_btn = ctk.CTkButton(
            update_frame,
            text='Cancelar',
            fg_color="#E74C3C",
            hover_color="#C0392B",
            font=ctk.CTkFont(size=15, weight="bold"),
            command= update_win.destroy
        )
        cancel_update_btn.grid(row=1, column=1, padx=10, ipadx=5)


    def open_purchase_window(self, parent):

        win = ctk.CTkToplevel(self.frame)
        win.title("Registrar Compra a Proveedor")
        win.geometry("750x550")
        win.grab_set()

        win.protocol("WM_DELETE_WINDOW",lambda: close_win(win, parent))

        # Configurar grilla principal
        for i in range(6):
            win.grid_rowconfigure(i, weight=0)
        win.grid_rowconfigure(3, weight=1)
        win.grid_columnconfigure(0, weight=1)
        win.grid_columnconfigure(1, weight=1)

        # --- Proveedor ---
        ctk.CTkLabel(
            win, text="Proveedor:", font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=(15, 5), sticky="e")

        proveedores = [f"{p[1]}" for p in self.model.get_all_suppliers()]  # nombre (CUIT)
        self.purchase_supplier_var = tk.StringVar()

        #  funcion para cargar productos 
        def load_products():
            selected_supplier = self.purchase_supplier_var.get()
            if not selected_supplier:
                tk.messagebox.showwarning("Atención", "Primero selecciona un proveedor.")
                return

            # Limpiar tabla
            for item in product_tree.get_children():
                product_tree.delete(item)

            # Cargar productos
            for p in self.stock_model.get_all_products_by_cuit(selected_supplier):
                product_tree.insert("", "end", values=(p[0], p[2], p[5], p[9]))       

        supplier_combo = ctk.CTkComboBox(
            win, 
            variable=self.purchase_supplier_var, 
            values=proveedores, 
            width=250,
            command=lambda value: load_products()
        )
        supplier_combo.grid(row=0, column=1, padx=10, pady=(15, 5), sticky="w")

        # frame para productos
        product_frame = ctk.CTkFrame(win)
        product_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

        # tree view de productos
        product_tree = ttk.Treeview(product_frame, show="headings", height=8)
        product_tree["columns"] = ("id", "nombre", "precio", "stock")
        for col in product_tree["columns"]:
            product_tree.heading(col, text=col.capitalize())
            product_tree.column(col, width=150, anchor="center")
        product_tree.pack(side="left", fill="both", expand=True)

        #  scrollbar 
        scroll = ttk.Scrollbar(product_frame, orient="vertical", command=product_tree.yview)
        product_tree.configure(yscroll=scroll.set)
        scroll.pack(side="right", fill="y")

        # --- Frame inferior (botones y cantidad) ---
        buttons_frame = ctk.CTkFrame(win)
        buttons_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        for i in range(5):
            buttons_frame.grid_columnconfigure(i, weight=1)

        # Etiqueta cantidad
        qty_label = ctk.CTkLabel(buttons_frame, text="Cantidad recibida:", font=ctk.CTkFont(size=12))
        qty_label.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="e")

        qty_var = tk.StringVar(value="1")
        qty_entry = ctk.CTkEntry(buttons_frame, textvariable=qty_var, width=100)
        qty_entry.grid(row=0, column=1, padx=(0, 15), pady=10, sticky="w")

        # boton Registrar Compra
        confirm_btn = ctk.CTkButton(
            buttons_frame,
            text="Agrega nuevos productos",
            fg_color="#009688",
            hover_color="#00796B",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.controller.open_win_add_supplier_product(self.purchase_supplier_var.get())
        )
        confirm_btn.grid(row=0, column=2, padx=5, pady=10)

        # boton Actualizar Stock
        update_stock_btn = ctk.CTkButton(
            buttons_frame,
            text="Actualizar Stock",
            fg_color="#3498DB",
            hover_color="#2980B9",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.controller.register_purchase(
                product_tree, qty_var, win
            )
        )
        update_stock_btn.grid(row=0, column=3, padx=5, pady=10)

        # boton Cerrar
        close_win_btn = ctk.CTkButton(
            buttons_frame,
            text="Cerrar",
            fg_color="#E74C3C",
            hover_color="#C0392B",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: close_win(win, parent)
        )
        close_win_btn.grid(row=0, column=4, padx=5, pady=10)


    def open_add_product_window(self, supplier_cuit, parent=None):
        self.setup_product_variables()

        if self.purchase_supplier_var.get() == "":
            show_warning("Por favor seleccione un proveedor")
            return
        
        """Ventana para agregar nuevo producto con CustomTkinter"""
        add_win = ctk.CTkToplevel(parent if parent else self.frame)
        add_win.title("Agregar nuevo artículo")
        
        # Hacer que la ventana sea modal
        add_win.transient(parent)
        add_win.grab_set()
        
        # Centrar la ventana
        add_win.geometry("400x600+{}+{}".format(
            add_win.winfo_screenwidth()//2 - 200,
            add_win.winfo_screenheight()//2 - 250
        ))
        
        # Título
        title_label = ctk.CTkLabel(
            add_win,
            text="Nuevo Artículo",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(20, 20))
        
        # Campos del formulario
        fields = [
            ("Código:", self.stock_view.id_var),
            ("Cuit Proveedor:", self.stock_view.cuit_supplier),
            ("Nombre Artículo:", self.stock_view.name_var),
            ("Precio Costo:", self.stock_view.price_var),
            ("% Rentabilidad:", self.stock_view.profit_var),
            ("Cantidad de Artículos:", self.stock_view.qnt_var)
        ]

        print(f"Que es supplier cuit?: {supplier_cuit}")
        self.stock_view.cuit_supplier.set(supplier_cuit)
        print(f"Que es supplier cuit?: { self.stock_view.cuit_supplier.get()}")


        for i, (label_text, var) in enumerate(fields, start=0):
            label = ctk.CTkLabel(add_win, text=label_text, font=ctk.CTkFont(size=12))
            label.grid(row=i+1, column=0, padx=20, pady=10, sticky="w")
            
            entry = ctk.CTkEntry(
                add_win,
                textvariable=var,
                width=200,
                height=35,
                font=ctk.CTkFont(size=12)
            )
            entry.grid(row=i+1, column=1, padx=20, pady=10)

        # Combobox para Envase
        pack_label = ctk.CTkLabel(add_win, text="Envase:", font=ctk.CTkFont(size=12))
        pack_label.grid(row=7, column=0, padx=20, pady=10, sticky="w")
        
        pack_combo = ctk.CTkComboBox(
            add_win,
            values=["UNIDAD", "CAJA", "FRASCO", "AMPOLLA", "SOBRE", "OTRO"],
            variable=self.stock_view.pack_var,
            width=200,
            height=35,
            font=ctk.CTkFont(size=12),
            state="readonly"
        )
        pack_combo.set("UNIDAD")
        pack_combo.grid(row=7, column=1, padx=20, pady=10)

        # Combobox para IVA
        iva_label = ctk.CTkLabel(add_win, text="% Iva:", font=ctk.CTkFont(size=12))
        iva_label.grid(row=8, column=0, padx=20, pady=10, sticky="w")
        
        iva_combo = ctk.CTkComboBox(
            add_win,
            values=["21%", "10.5%", "0%"],
            variable=self.stock_view.iva_var,
            width=200,
            height=35,
            font=ctk.CTkFont(size=12),
            state="readonly"
        )
        iva_combo.set("21%")
        iva_combo.grid(row=8, column=1, padx=20, pady=10)

        # Botones
        button_frame = ctk.CTkFrame(add_win, fg_color="transparent")
        button_frame.grid(row=9, column=0, columnspan=2, pady=30)

        add_button = ctk.CTkButton(button_frame, text="Agregar", width=120, height=35, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#4CAF50", hover_color="#45a049", command=lambda: self.controller.add_supplier_product())
        add_button.grid(row=0, column=0, padx=10)

        cancel_button = ctk.CTkButton(button_frame, text="Cancelar", width=120, height=35, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#757575", hover_color="#616161", command=add_win.destroy)
        cancel_button.grid(row=0, column=1, padx=10)

    def refresh_supplier_table(self, suppliers):
        for item in self.supplier_tree.get_children():
            self.supplier_tree.delete(item)

        for supplier in suppliers:
            self.supplier_tree.insert(
                parent='', index='end', iid=supplier[0],
                values=(
                    supplier[0],   # id
                    supplier[2],   # name
                    supplier[1],   # cuit
                    supplier[3],   # home
                    supplier[4],   # phone
                    supplier[5],   # email
                    supplier[6],   # debt
                    supplier[7]    # last act debt
                ),
                tag="orow"
            )

        self.supplier_tree.tag_configure('orow', background="white", foreground='black')

    def clear_form_supplier(self):
        """Limpiar formulario proveedor"""
        self.email_var.set('')
        self.name_var.set('')
        self.cuit_var.set('')
        self.home_var.set('')
        self.phone_var.set('')
        self.debt_var.set('')

    def get_supplier_data(self):
        return {
            'name': self.name_var.get().strip(),
            'cuit': self.cuit_var.get().strip(),
            'home': self.home_var.get().strip(),
            'phone': self.phone_var.get().strip(),
            'email': self.email_var.get().strip(),
            'debt': self.debt_var.get()
        }
    
    def get_product_data(self):
        return {
            'name': self.name_product_var.get().strip(),
            'description': self.description_var.get().strip(),
            'brand': self.brand_var.get().strip(),
            'price': self.price_var.get().strip(),
            'quantity': self.quantity_var.get().strip(),
        }