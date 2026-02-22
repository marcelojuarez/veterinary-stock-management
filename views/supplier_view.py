import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from tksheet import Sheet
from models.supplier.__init__ import SupplierModel
from models.stock import StockModel
from views.payments.payment_window import PaymentWindow
from views.purchases.purchase_window import PurchaseWindow
from views.view_helpers import close_win, show_warning, center_window
from utils.utils import iso_to_traditional


# Configurar tema y colores
ctk.set_appearance_mode("light")  # "light" o "dark"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class SupplierView():
    def __init__(self, parent, controller, purchase_controller, payment_controller, invoice_controller, receipt_controller):

        self.model = SupplierModel()
        self.stock_model = StockModel()

        self.controller = controller
        self.purchase_controller = purchase_controller

        self.payment_controller = payment_controller
        
        self.invoice_controller = invoice_controller
        self.invoice_controller.set_model(self.model)
        
        self.receipt_controller = receipt_controller
        self.receipt_controller.set_model(self.model)

        self.frame = ctk.CTkFrame(parent, fg_color="#f0f0f0")

        self.purchase_controller.set_model(self.model)
        self.payment_controller.set_model(self.model)

        self.payment_window = PaymentWindow(self.model, self.frame, self.payment_controller)
        self.purchase_window = PurchaseWindow(self.model, self.stock_model, self.frame, self.purchase_controller, 
                                              self.invoice_controller, self.receipt_controller)

        self.create_widgets()
        # proveedores en memoria
        self.suppliers = self.model.core.get_all_suppliers()

        self.sort_column = None
        self.sort_reverse = False

    def setup_supplier_variables(self):
        # variables proveedor
        self.name_var = tk.StringVar()
        self.cuit_var = tk.StringVar()
        self.home_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.iva_condition = tk.StringVar()

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
            text="🔍 Buscar Proveedor", 
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
        self.find_entry.bind("<KeyRelease>", self.on_key_release)
        self.search_after_id = None
        '''
        find_btn = ctk.CTkButton(
            find_frame,
            text="!",
            width=60,
            height=35,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=btn_color,
            hover_color=btn_hover,
            command=lambda: show_warning("Ingrese un NOMBRE o CUIT para buscar un proveedor...")
        )

        find_btn.grid(row=0, column=2, padx=5, pady=5)
        '''

    def create_tree_frame(self):
        """ Crea el frame para la tabla de Proveedores"""
        tree_frame = ctk.CTkFrame(self.frame)
        tree_frame.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')
        tree_frame.grid_rowconfigure(1, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # Titulo de la tabla
        table_title = ctk.CTkLabel(
            tree_frame,
            text="📋 Proveedores registrados",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        table_title.pack(pady=(10,5))

        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            'Treeview',
            background='#f9f9f9',
            fieldbackground='#f9f9f9',
            foreground='#333333',
            rowheight=28,
            font=('Segoe UI', 10)
        )
        style.configure(
            'Treeview.Heading',
            background='#e6e6e6',
            foreground='#000000',
            font=('Segoe UI', 10, 'bold')
        )
        style.map('Treeview',
            background=[('selected', '#0078d4')]
        )
        style.map('Treeview.Heading',
            background=[('active', '#dcdcdc')]
        )

        # Treeview
        self.supplier_tree = ttk.Treeview(tree_frame, show='headings')

        # Scrollbar vertical para los proveedores
        scrl_bar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.supplier_tree.yview)
        self.supplier_tree.configure(yscrollcommand=scrl_bar.set)
                           
        self.supplier_tree['columns'] = (
            "Id", "Nombre", "Cuit", "Domicilio", "Telefono", "Email", "Condicion Iva", "Ultima actualizacion deuda"
        )
        self.supplier_tree['displaycolumns'] = self.supplier_tree['columns']
        self.supplier_tree.column("Id", anchor=tk.W, width=50,stretch=True)
        self.supplier_tree.column("Nombre", anchor=tk.W, width=200,stretch=True)
        self.supplier_tree.column("Cuit", anchor=tk.W, width=130,stretch=True)
        self.supplier_tree.column("Domicilio", anchor=tk.W, width=180,stretch=True)
        self.supplier_tree.column("Telefono", anchor=tk.W, width=110,stretch=True)
        self.supplier_tree.column("Email", anchor=tk.W, width=180, stretch=True)
        self.supplier_tree.column("Condicion Iva", anchor=tk.W, width=120, stretch=True)
        self.supplier_tree.column("Ultima actualizacion deuda", anchor=tk.W, width=150, stretch=True)

        self.supplier_tree.heading('Id', text='Cód ↕')
        self.supplier_tree.heading('Nombre', text='Nombre↕')
        self.supplier_tree.heading('Cuit', text='Cuit ↕')
        self.supplier_tree.heading('Domicilio', text='Domicilio ↕')
        self.supplier_tree.heading('Telefono', text='Telefono ↕')
        self.supplier_tree.heading('Email', text='Email ↕')
        self.supplier_tree.heading('Condicion Iva', text='Condicion Iva ↕')
        self.supplier_tree.heading('Ultima actualizacion deuda', text='Ultima actualizacion deuda ↕')

        self.supplier_tree.tag_configure('orow', background="#FFFFFF")
        scrl_bar.pack(side="right", fill="y")
        self.supplier_tree.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=20)

    def create_buttons_frame(self):
        manage_frame = ctk.CTkFrame(self.frame)
        manage_frame.grid(row=2, column=0, padx=10, pady=(5, 15), sticky='ew')

        for i in range(11):
            manage_frame.grid_columnconfigure(i, weight=1 if i % 2 == 0 else 0)

        W = 250
        H = 40
        btn_color = "#009688"
        btn_hover = "#00796B"

        buttons = [
            ('Info',             lambda: self.controller.supplier_info(manage_frame)),
            ('Borrar',           lambda: self.controller.delete_supplier()),
            ('Agregar',          lambda: self.open_add_window(manage_frame)),
            ('Registrar Pago',   lambda: self.payment_window.open_payment_window(manage_frame)),
            ('Registrar Compra', lambda: self.purchase_window.open_purchase_window(self.frame)),
        ]

        for i, (text, cmd) in enumerate(buttons):
            ctk.CTkButton(
                manage_frame,
                text=text,
                width=W,
                height=H,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=btn_color,
                hover_color=btn_hover,
                command=cmd
            ).grid(row=0, column=i * 2 + 1, padx=8, pady=15)

    def open_add_window(self, parent):
        self.setup_supplier_variables()

        add_win = ctk.CTkToplevel(self.frame)
        add_win.title("Agregar nuevo proveedor")

        add_win.protocol("WM_DELETE_WINDOW", lambda: close_win(add_win, parent))

        # Hacer que la ventana sea modal
        add_win.transient(self.frame)
        add_win.grab_set()
        btn_color = "#009688"
        btn_hover = "#00796B"
        center_window(add_win, 550, 480)
        add_win.configure(fg_color="#e0e0e0")

        card_frame = ctk.CTkFrame(
            add_win,
            fg_color="white",
            corner_radius=20
        )
        card_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title_label = ctk.CTkLabel(
            card_frame,
            text="Nuevo Proveedor",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="black"
        )
        title_label.pack(pady=20)

        # contenedor del formulario
        form_frame = ctk.CTkFrame(card_frame, fg_color="white")
        form_frame.pack(pady=5, padx=10, fill="x")

        def add_field(row, label, widget):
            field_lbl = ctk.CTkLabel(
                form_frame,
                text=label,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="black"
            )

            field_lbl.grid(row=row, column=0, sticky="e", padx=(10,10), pady=7)
            widget.grid(row=row, column=1, sticky="w", padx=(10,10), pady=7)

        
        add_field(0, "Nombre: ", 
                  ctk.CTkEntry(form_frame, textvariable=self.name_var, width=200))
        
        add_field(1, "Cuit: ", 
                  ctk.CTkEntry(form_frame, textvariable=self.cuit_var, width=200))
        
        add_field(2, "Domicilio: ",
                  ctk.CTkEntry(form_frame, textvariable=self.home_var, width=200))

        add_field(3, "Telefono: ",
                  ctk.CTkEntry(form_frame, textvariable=self.phone_var, width=200))

        add_field(4, "Email: ",
                  ctk.CTkEntry(form_frame, textvariable=self.email_var, width=200))
        
        add_field(5, "Condicion IVA: ",
                  ctk.CTkComboBox(
                      form_frame,  
                      values=["RESP. INS", "MONOTRIBUTISTA", "EXENTO", "NO RESPONSABLE"], 
                      variable=self.iva_condition, 
                      width=200
                    )
        )

        self.iva_condition.set('RESP. INS')

        btn_frame = ctk.CTkFrame(card_frame, fg_color="white")
        btn_frame.pack(pady=20)

        finish_btn = ctk.CTkButton(
            btn_frame, 
            text="Agregar", 
            fg_color=btn_color, 
            hover_color=btn_hover,
            height=40,
            width=160,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=lambda: self.controller.add_new_supplier(add_win)
        )
        finish_btn.grid(row=0, column=0, padx=15)

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            fg_color="#E74C3C",
            hover_color="#C0392B",
            height=40,
            width=160,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=lambda: close_win(add_win, parent, self.clear_form_supplier)
        )

        cancel_btn.grid(row=0, column=1, padx=15)     

    ## -- Ventana de informacion con productos y deuda -- ##
    def open_info_window(self, supplier, debt, parent):
        self.frame.update_idletasks()  # calcula la posicion antes de renderizar ventana

        info_win = ctk.CTkToplevel(self.frame)
        info_win.title(f'Proveedor: {supplier[2]} -- {supplier[1]}')
        info_win.transient(parent)
        info_win.grab_set()

        center_window(info_win, 1050, 450)

        info_win.grid_rowconfigure(0, weight=1)
        info_win.grid_rowconfigure(1, weight=0)
        info_win.grid_columnconfigure(0, weight=3)
        info_win.grid_columnconfigure(1, weight=1)

        # --- Tksheet con productos ---
        products = self.model.purchase.get_all_products_by_supplier_id(supplier_id=supplier[0])
        products = [(p[0], p[1], p[2], p[5]) for p in products]

        sheet = Sheet(info_win)
        sheet.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 0))
        sheet.headers(["Id", "Nombre Artículo", "Envase", "Stock"])
        sheet.set_sheet_data(products)
        sheet.set_column_widths([100, 300, 200, 50])

        # --- Panel de deuda ---
        self.debt = tk.StringVar(value=f'{debt}')
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
        left_btn_frame.grid(row=1, column=0, sticky="we", pady=15)
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
    
    def open_purchase_window(self, parent):

        win = ctk.CTkToplevel(self.frame)
        win.title("Registrar Compra a Proveedor")
        center_window(win, 750, 550)
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

        proveedores = [f"{p[1]}" for p in self.suppliers]  # nombre (CUIT)
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

    def on_key_release(self, event):
        # Cancela búsquedas previas si el usuario sigue escribiendo
        if self.search_after_id:
            self.find_entry.after_cancel(self.search_after_id)
        
        # Ejecuta la búsqueda después de 150 ms
        self.search_after_id = self.find_entry.after(200, self.update_treeview_filter)

    def update_treeview_filter(self):
        query = self.find_entry.get().lower()
        # se verifica si el campo de busqueda esta vacio
        if query == "":
            self.controller.refresh_supplier_table()
            return
        
        # limpia el tree view
        for row in self.supplier_tree.get_children():
            self.supplier_tree.delete(row)
            
        # # Filtrar la lista de proveedores
        filtered = [
            s for s in self.suppliers
            if query in s[1] or query in s[2].lower()
        ]
        
        # Insertar solo los resultados filtrados
        for s in filtered:
            self.supplier_tree.insert(
                parent='', index='end', iid=s[0],
                values=(
                    s[0],   # id
                    s[2],   # name
                    s[1],   # cuit
                    s[3],   # home
                    s[4],   # phone
                    s[5],   # email
                    s[6],   # condicion iva
                    iso_to_traditional(s[7])    # last act debt
                ),
                tag="orow"
            )

        self.supplier_tree.tag_configure('orow', background="white", foreground='black')

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
                    supplier[6],    # condicion iva
                    iso_to_traditional(supplier[7])    # last act debt
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
        self.iva_condition.set('')

    def get_supplier_data(self):
        return {
            'name': self.name_var.get().strip(),
            'cuit': self.cuit_var.get().strip(),
            'home': self.home_var.get().strip(),
            'phone': self.phone_var.get().strip(),
            'email': self.email_var.get().strip(),
            'iva_condition': self.iva_condition.get().strip()
        }
