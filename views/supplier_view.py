import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from views.payments.payment_window import PaymentWindow
from views.purchases.purchase_window import PurchaseWindow
from utils.view_helpers import center_window, close_win

# Configurar tema y colores
ctk.set_appearance_mode("light")  # "light" o "dark"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class SupplierView():
    def __init__(
            self, 
            parent, 
            controller, 
            purchase_controller, 
            payment_controller, 
            invoice_controller, 
            receipt_controller,
            supplier_model,
            stock_model
        ):

        self.model = supplier_model
        self.stock_model = stock_model

        self.controller = controller
        self.purchase_controller = purchase_controller

        self.payment_controller = payment_controller
        
        self.invoice_controller = invoice_controller
        
        self.receipt_controller = receipt_controller

        self.frame = ctk.CTkFrame(parent, fg_color="#f0f0f0")

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
        self.city_var = tk.StringVar()
        self.province_var = tk.StringVar()
        self.country_var = tk.StringVar()
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
            font=ctk.CTkFont(size=12, weight="bold"),
            placeholder_text="Digite nombre, CUIT o teléfono del proveedor",
        )

        self.find_entry.grid(row=0, column=1, padx=10, pady=15)
        self.find_entry.bind("<KeyRelease>", self.on_key_release)
        self.search_after_id = None

        self.showing_active_debts = False

        self.filter_debts_btn = ctk.CTkButton(
            find_frame, text="Filtrar Por Deuda Activa",
            fg_color="#009688", hover_color="#00796B",
            width=190,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.manage_filter_debts_btn()
        )
        self.filter_debts_btn.grid(row=0, column=2, padx=10, pady=15)

    def create_tree_frame(self):
        """ Crea el frame para la tabla de Proveedores"""
        tree_frame = ctk.CTkFrame(self.frame)
        tree_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        tree_frame.grid_rowconfigure(1, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # Titulo de la tabla
        table_title = ctk.CTkLabel(
            tree_frame,
            text="📋 Proveedores registrados",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        table_title.pack(pady=(10,5))

        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            'Treeview',
            background='#f9f9f9',
            fieldbackground='#f9f9f9',
            foreground='#333333',
            rowheight=20,
            font=('Segoe UI', 8)
        )
        style.configure(
            'Treeview.Heading',
            background='#e6e6e6',
            foreground='#000000',
            font=('Segoe UI', 9, 'bold')
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
        scrl_bar_x = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.supplier_tree.xview)
        self.supplier_tree.configure(yscrollcommand=scrl_bar.set, xscrollcommand=scrl_bar_x.set)
                           
        self.supplier_tree['columns'] = (
            "Id", "Nombre", "Cuit", "Domicilio", "Ciudad", "Provincia", "Telefono", "Email", "Condicion Iva", "Últ. Act. deuda"
        )
        self.supplier_tree['displaycolumns'] = self.supplier_tree['columns']
        self.supplier_tree.column("Id", anchor=tk.W, width=30,stretch=True)
        self.supplier_tree.column("Nombre", anchor=tk.W, width=200,stretch=True)
        self.supplier_tree.column("Cuit", anchor=tk.W, width=100,stretch=True)
        self.supplier_tree.column("Domicilio", anchor=tk.W, width=180,stretch=True)
        self.supplier_tree.column("Ciudad", anchor=tk.W, width=150,stretch=True)
        self.supplier_tree.column("Provincia", anchor=tk.W, width=150,stretch=True)
        self.supplier_tree.column("Telefono", anchor=tk.W, width=110,stretch=True)
        self.supplier_tree.column("Email", anchor=tk.W, width=180, stretch=True)
        self.supplier_tree.column("Condicion Iva", anchor=tk.W, width=120, stretch=True)
        self.supplier_tree.column("Últ. Act. deuda", anchor=tk.W, width=100, stretch=True)

        for col in self.supplier_tree["columns"]:
            self.supplier_tree.heading(
                col,
                text=col,
                command=lambda c=col: self.sort_by_column(c)
            )

        self.supplier_tree.tag_configure('orow', background="#FFFFFF")
        scrl_bar_x.pack(side="bottom", fill="x")
        scrl_bar.pack(side="right", fill="y")
        self.supplier_tree.pack(fill="both", expand=True, padx=(10, 0), pady=(0, 0))

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
            ('➕ Agregar proveedor',          lambda: self.open_add_window(manage_frame)),
            ('👥 Ver detalle',             lambda: self.controller.supplier_info(manage_frame)),
            ('🗑️ Eliminar proveedor',           lambda: self.controller.delete_supplier()),
            ('🛒 Registrar compra', lambda: self.purchase_window.open_purchase_window(self.frame)),
            ('💰 Registrar pago',   lambda: self.payment_window.open_payment_window(manage_frame)),
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
        center_window(add_win, 550, 600)
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
        title_label.pack(pady=(20, 2))

        ctk.CTkLabel(
            card_frame,
            text="Solo el nombre es obligatorio. El resto de los campos son opcionales.",
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        ).pack(pady=(0, 12))

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

            return widget

        
        name_entry = add_field(0, "Nombre Completo: *",
                  ctk.CTkEntry(form_frame, textvariable=self.name_var, width=200))
        
        name_entry.focus()
        
        add_field(1, "Cuit: ", 
                  ctk.CTkEntry(form_frame, textvariable=self.cuit_var, width=200))
        
        add_field(2, "Domicilio: ",
                  ctk.CTkEntry(form_frame, textvariable=self.home_var, width=200))
        
        add_field(3, "Ciudad: ",
                  ctk.CTkEntry(form_frame, textvariable=self.city_var, width=200))

        add_field(4, "Provincia: ",
                  ctk.CTkEntry(form_frame, textvariable=self.province_var, width=200))
        
        add_field(5, "País: ",
                  ctk.CTkEntry(form_frame, textvariable=self.country_var, width=200))
        
        add_field(6, "Telefono: ",
                  ctk.CTkEntry(form_frame, textvariable=self.phone_var, width=200))

        add_field(7, "Email: ",
                  ctk.CTkEntry(form_frame, textvariable=self.email_var, width=200))
        
        add_field(8, "Condicion IVA: ",
                  ctk.CTkComboBox(
                      form_frame,  
                      values=["RESP. INSCRIPTO", "MONOTRIBUTISTA", "EXENTO", "NO RESPONSABLE"], 
                      variable=self.iva_condition, 
                      width=200
                    )
        )

        self.iva_condition.set('RESP. INSCRIPTO')

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
        add_win.bind("<Return>", lambda event: finish_btn.invoke())

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
            if query in " ".join(str(f or "") for f in s).lower()
        ]
        
        # Insertar solo los resultados filtrados
        for s in filtered:
            self.supplier_tree.insert(
                parent='', index='end', iid=s[0],
                values=(
                    s[0],   # id
                    s[2],   # name
                    s[1],   # cuit
                    s[3],   # address
                    s[4],   # city
                    s[5],   # province
                    s[7],   # phone
                    s[8],   # email
                    s[9],   # condicion iva
                    s[10]    # last act debt
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
                    supplier[3],   # address
                    supplier[4],   # city
                    supplier[5],   # province
                    supplier[7],   # phone
                    supplier[8],   # email
                    supplier[9],    # condicion iva
                    supplier[10]    # last act debt
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
        self.city_var.set('')
        self.province_var.set('')
        self.country_var.set('')
        self.phone_var.set('')
        self.iva_condition.set('')

    def get_supplier_data(self):
        return {
            'name': self.name_var.get().strip(),
            'cuit': self.cuit_var.get().strip(),
            'address': self.home_var.get().strip(),
            'city': self.city_var.get().strip(),
            'province': self.province_var.get().strip(),
            'country': self.country_var.get().strip(),
            'phone': self.phone_var.get().strip(),
            'email': self.email_var.get().strip(),
            'iva_condition': self.iva_condition.get().strip()
        }
    
    def sort_by_column(self, col):
        # Si es la misma columna, invertimos el orden
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False

        self.sort_column = col

        # Obtener datos visibles
        data = [
            (self.supplier_tree.set(k, col), k)
            for k in self.supplier_tree.get_children('')
        ]

        # Intentar ordenar como número
        try:
            data.sort(
                key=lambda t: float(t[0].replace(",", "").replace("$", "")),
                reverse=self.sort_reverse
            )
        except ValueError:
            data.sort(
                key=lambda t: t[0].lower(),
                reverse=self.sort_reverse
            )

        # Reordenar filas
        for index, (val, k) in enumerate(data):
            self.supplier_tree.move(k, '', index)

        # Actualizar flechas en encabezados
        for c in self.supplier_tree["columns"]:
            self.supplier_tree.heading(c, text=c)

        arrow = " ↓" if self.sort_reverse else " ↑"
        self.supplier_tree.heading(col, text=col + arrow)

    def manage_filter_debts_btn(self):
        if not self.showing_active_debts:
            # mostrar los proveedores con los cuales se posee una deuda activa
            s_with_act_debts = self.controller.filter_suppliers_w_act_debts()
            self.refresh_supplier_table(s_with_act_debts)
            self.showing_active_debts = True
            self.filter_debts_btn.configure(text ="Ver todos")

        else: 
            # mostrar todos los proveedores
            self.controller.refresh_supplier_table()
            self.showing_active_debts = False
            self.filter_debts_btn.configure(text = "Filtrar Por Deuda Activa")