import customtkinter as ctk
from tkinter import ttk, messagebox

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class CustomersView:
    def __init__(self, parent):
        self.controller = None
        self.frame = ctk.CTkFrame(parent, fg_color="#f0f0f0")

        # Variables principales
        self.search_var = ctk.StringVar()

        # Permitir expansión sin cambiar visual
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # Layout general
        self.create_header()
        self.create_table_section()
        # footer se crea en attach_controller()

    # --------------------------------------------------------------------
    # HEADER (idéntico estilo que SalesView)
    # --------------------------------------------------------------------
    def create_header(self):
        header = ctk.CTkFrame(self.frame, fg_color="#e0e0e0", corner_radius=10)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 5))

        # 🔹 Alineamos todo hacia la izquierda (como en SalesView)
        header.grid_columnconfigure(0, weight=0)  # título
        header.grid_columnconfigure(1, weight=0)  # entry búsqueda
        header.grid_columnconfigure(2, weight=0)  # botón buscar
        header.grid_columnconfigure(3, weight=0)  # botón actualizar empuja al borde derecho

        # --- Título ---
        title = ctk.CTkLabel(
            header,
            text="👥 Gestión de Clientes",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#212121"
        )
        title.grid(row=0, column=0, padx=(15, 10), pady=8, sticky="w")

        # --- Campo de búsqueda ---
        search_entry = ctk.CTkEntry(
            header,
            textvariable=self.search_var,
            width=300,
            height=35,
            placeholder_text="Buscar cliente..."
        )
        search_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        search_entry.bind(
            "<KeyRelease>",
            lambda event: self.controller.filter_customers(self.search_var.get())
        )

        # --- Botón Buscar ---
        search_btn = ctk.CTkButton(
            header,
            text="Buscar",
            width=120,
            height=35,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#009688",
            hover_color="#00796B",
            corner_radius=8,
            command=lambda: self.controller.filter_customers(self.search_var.get()) if self.controller else None
        )
        search_btn.grid(row=0, column=2, padx=(5, 10), pady=5, sticky="w")

        # --- Botón Actualizar ---
        refresh_btn = ctk.CTkButton(
            header,
            text="Actualizar lista",
            width=150,
            height=35,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#009688",
            hover_color="#00796B",
            corner_radius=8,
            command=lambda: self.controller.refresh_customer_data() if self.controller else None
        )
        refresh_btn.grid(row=0, column=3, padx=(10, 40), pady=5, sticky="w")

        refresh_btn.grid(row=0, column=3, padx=(10, 20), pady=5, sticky="e")


    # --------------------------------------------------------------------
    # TABLE SECTION
    # --------------------------------------------------------------------
    def create_table_section(self):
        table_frame = ctk.CTkFrame(self.frame)
        table_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(
            table_frame,
            text="📋 Clientes registrados", 
            font=ctk.CTkFont(size=15, weight="bold")
        )
        label.pack(pady=(10, 5))

        # ----------------------------------------------------------------
        # Estilo unificado de Treeview
        # ----------------------------------------------------------------
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Custom.Treeview",
            background="#f9f9f9",
            fieldbackground="#f9f9f9",
            bordercolor="#d0d0d0",
            lightcolor="#d0d0d0",
            darkcolor="#d0d0d0",
            rowheight=28,
            font=("Segoe UI", 10)
        )
        style.configure(
            "Custom.Treeview.Heading",
            background="#e6e6e6",
            foreground="#000000",
            font=("Segoe UI", 10, "bold")
        )
        style.map("Custom.Treeview.Heading",
                  background=[("active", "#dcdcdc")])

        self.table = ttk.Treeview(
            table_frame,
            show="headings",
            height=12,
            style="Custom.Treeview"
        )

        self.table = ttk.Treeview(table_frame, show="headings", height=12)
        self.table["columns"] = ("ID", "Nombre", "CUIT", "Domicilio", "Teléfono")

        col_specs = {
            "ID": {"width": 60, "stretch": False},
            "Nombre": {"width": 250},
            "CUIT": {"width": 150},
            "Domicilio": {"width": 250},
            "Teléfono": {"width": 150},
        }

        for col, spec in col_specs.items():
            self.table.column(col, anchor="center", **spec)
            self.table.heading(col, text=col, anchor="center")

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscroll=scroll_y.set)
        scroll_y.pack(side="right", fill="y")
        self.table.pack(padx=10, pady=10, fill="both", expand=True)

    # --------------------------------------------------------------------
    # FOOTER BUTTONS
    # --------------------------------------------------------------------
    def create_footer_buttons(self):
        footer = ctk.CTkFrame(self.frame)
        footer.grid(row=2, column=0, padx=10, pady=20, sticky="ew")
        footer.grid_columnconfigure((0, 1, 2), weight=1)
        W, H = 250, 40

        buttons = [
            (" Borrar Cliente", self.delete_selected_customer),
            (" Agregar Cliente", self.open_add_customer_window),
            (" Ver Deudas", self.open_selected_customer_debts)
        ]
        for i, (text, cmd) in enumerate(buttons):
            ctk.CTkButton(
                footer,
                text=text,
                width=W,
                height=H,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="#009688",
                hover_color="#00796B",
                command=cmd
            ).grid(row=0, column=i, padx=20, pady=10)


    # --------------------------------------------------------------------
    # MODAL PARA AGREGAR CLIENTE
    # --------------------------------------------------------------------
    def open_add_customer_window(self):
        win = ctk.CTkToplevel(self.frame)
        win.title("Agregar nuevo cliente")
        win.geometry("480x420")
        win.transient(self.frame)
        win.grab_set()

        ctk.CTkLabel(
            win, text="Registrar nuevo cliente",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(20, 10))

        name_var = ctk.StringVar()
        cuit_var = ctk.StringVar()
        home_var = ctk.StringVar()
        phone_var = ctk.StringVar()

        form_frame = ctk.CTkFrame(win, fg_color="#f9f9f9", corner_radius=10)
        form_frame.pack(pady=10, padx=20, fill="x")

        entries = [
            ("Nombre:", name_var),
            ("CUIT:", cuit_var),
            ("Domicilio:", home_var),
            ("Teléfono:", phone_var)
        ]

        for i, (label, var) in enumerate(entries):
            ctk.CTkLabel(form_frame, text=label, anchor="e",
                         font=ctk.CTkFont(size=13)).grid(row=i, column=0, padx=10, pady=10, sticky="e")
            ctk.CTkEntry(form_frame, textvariable=var,
                         width=250, height=35).grid(row=i, column=1, padx=10, pady=10, sticky="w")

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=15)

        def save_and_close():
            data = {
                "nombre": name_var.get(),
                "cuit": cuit_var.get(),
                "domicilio": home_var.get(),
                "telefono": phone_var.get()
            }
            if self.controller:
                ok = self.controller.add_new_customer_window(data, win)
                if ok:
                    self.show_success("Cliente agregado correctamente.")
                    win.destroy()

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Guardar",
            width=150,
            height=40,
            fg_color="#009688",
            hover_color="#00796B",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=save_and_close
        )
        save_btn.grid(row=0, column=0, padx=15)

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            width=150,
            height=40,
            fg_color="#757575",
            hover_color="#616161",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=win.destroy
        )
        cancel_btn.grid(row=0, column=1, padx=15)

    # --------------------------------------------------------------------
    # CONTROLLER & HELPERS
    # --------------------------------------------------------------------
    def attach_controller(self, controller):
        self.controller = controller
        self.create_footer_buttons()

    def refresh_customer_table(self, customers):
        """Solo pinta la tabla - NO toca la DB"""
        try:
            # Limpiar tabla
            for row in self.table.get_children():
                self.table.delete(row)
                
            # Si no hay clientes, mostrar mensaje
            if not customers:
                # Opcional: mostrar mensaje de "no resultados"
                return
                
            # Insertar clientes
            for customer in customers:
                if isinstance(customer, dict):
                    # Si viene como diccionario desde DB
                    vals = (
                        customer.get("id"), 
                        customer.get("nombre"), 
                        customer.get("cuit"),
                        customer.get("domicilio"), 
                        customer.get("telefono")
                    )
                else:
                    # Si viene como tupla desde filtro en memoria
                    vals = customer
                    
                self.table.insert("", "end", values=vals)
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los clientes: {e}")

    def delete_selected_customer(self):
        selected = self.table.selection()
        if not selected:
            self.show_warning("Seleccione un cliente para eliminar.")
            return
        
        customer_id = self.table.item(selected[0])["values"][0]
        
        has_debt = self.controller.customer_has_debts(customer_id)
        if has_debt:
            resp = messagebox.askyesno(
            "⚠️ Cliente con deudas",
            "Este cliente tiene deudas pendientes.\n"
            "Si continúa, se eliminarán también las ventas asociadas.\n\n"
            "¿Desea eliminarlo de todos modos?"
            )
            if not resp: 
                return 
        
        self.controller.delete_customer(customer_id)

    def show_error(self, msg): messagebox.showerror("Error", msg)
    def show_warning(self, msg): messagebox.showwarning("Advertencia", msg)
    def show_success(self, msg): messagebox.showinfo("Éxito", msg)


    def open_selected_customer_debts(self):
        """Abre la ventana de deudas para el cliente seleccionado"""
        selected = self.table.selection()
        if not selected:
            self.show_warning("Seleccione un cliente para ver sus deudas.")
            return

        values = self.table.item(selected[0])["values"]
        cliente_id, cliente_nombre = values[0], values[1]

        if self.controller:
            self.controller.show_customer_debts(cliente_id, cliente_nombre)

    def open_debt_window(self, cliente_id, cliente_nombre, debts, total):
        """Muestra una ventana con las deudas del cliente"""
        win = ctk.CTkToplevel(self.frame)
        win.title(f"💳 Deudas de {cliente_nombre}")
        win.geometry("750x600")
        win.transient(self.frame)
        win.grab_set()

        self.debt_window = win

        # Título
        ctk.CTkLabel(
            win,
            text=f"Deudas pendientes de {cliente_nombre}",
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(pady=(15, 10))

        # ----------------------------------------------------------------
        # Tabla de deudas
        # ----------------------------------------------------------------
        cols = ("ID Venta", "Fecha", "Total", "Pagado", "Saldo", "Estado")
        self.debt_table = ttk.Treeview(win, columns=cols, show="headings", height=6)

        col_widths = [80, 160, 100, 100, 100, 100]

        for col, w in zip(cols, col_widths):
            self.debt_table.column(col, width=w, anchor="center")
            self.debt_table.heading(col, text=col, anchor="center")

        self.debt_table.pack(padx=10, pady=10, fill="x")


        for d in debts:
            self.debt_table.insert("", "end", values=d)

        # ----------------------------------------------------------------
        # Detalle de productos (vacío al inicio)
        # ----------------------------------------------------------------
        ctk.CTkLabel(
            win, text="📦 Detalle de productos de la venta seleccionada:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))

        cols_items = ("Producto", "Cantidad", "Precio", "Subtotal")
        self.debt_items_table = ttk.Treeview(win, columns=cols_items, show="headings", height=6)
        for col, w in zip(cols_items, [250, 100, 100, 100]):
            self.debt_items_table.column(col, width=w, anchor="center")
            self.debt_items_table.heading(col, text=col, anchor="center")
        self.debt_items_table.pack(padx=10, pady=5, fill="x")

        # ----------------------------------------------------------------
        # Total adeudado
        # ----------------------------------------------------------------
        self.debt_total_label = ctk.CTkLabel(
            win,
            text=f"Total adeudado: ${total:.2f}",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#333333"
        )
        self.debt_total_label.pack(pady=(10, 15))

        # ----------------------------------------------------------------
        # Botones inferiores
        # ----------------------------------------------------------------
        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=10)

        def mark_as_paid():
            selected = self.debt_table.selection()
            if not selected:
                messagebox.showwarning("Advertencia", "Seleccione una venta para registrar un pago.")
                return
            sale_id = self.debt_table.item(selected[0])["values"][0]
            self.open_payment_window(sale_id, cliente_id, cliente_nombre)

        ctk.CTkButton(
            btn_frame,
            text="Registrar Pago",
            width=200,
            height=35,
            fg_color="#009688",
            hover_color="#00796B",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=mark_as_paid
        ).grid(row=0, column=0, padx=15)

        ctk.CTkButton(
            btn_frame,
            text="❌ Cerrar",
            width=200,
            height=35,
            fg_color="#757575",
            hover_color="#616161",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=win.destroy
        ).grid(row=0, column=1, padx=15)

        # ----------------------------------------------------------------
        # Evento: seleccionar deuda -> cargar detalle de productos
        # ----------------------------------------------------------------
        def on_select_debt(event):
            selected = self.debt_table.selection()
            if not selected:
                return
            sale_id = self.debt_table.item(selected[0])["values"][0]
            # Pedimos al controlador el detalle de esta venta
            self.controller.load_sale_items_for_debt(sale_id)

        self.debt_table.bind("<<TreeviewSelect>>", on_select_debt)



    def update_debt_window(self, debts, total):
        """Actualiza los datos de la ventana de deudas abierta"""
        try:
            # Si la ventana o la tabla ya no existen, no hacemos nada
            if not hasattr(self, "debt_table") or not self.debt_table.winfo_exists():
                return

            # Limpiar tabla actual
            for row in self.debt_table.get_children():
                self.debt_table.delete(row)

            # Insertar nuevas deudas
            for d in debts:
                self.debt_table.insert("", "end", values=d)

            # Actualizar label de total
            if hasattr(self, "debt_total_label") and self.debt_total_label.winfo_exists():
                self.debt_total_label.configure(text=f"Total adeudado: ${total:.2f}")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar la ventana de deudas: {e}")

    def update_debt_items_table(self, items):
        """Actualiza el detalle de productos mostrado en la tabla inferior"""
        try:
            if not hasattr(self, "debt_items_table") or not self.debt_items_table.winfo_exists():
                return

            for row in self.debt_items_table.get_children():
                self.debt_items_table.delete(row)

            for i in items:
                self.debt_items_table.insert("", "end", values=i)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron mostrar los productos: {e}")

    def open_payment_window(self, sale_id, client_id, client_name):
        """Ventana de pago historial, monto, métodos, saldo."""
        # ================================================================
        #  CREAR VENTANA
        # ================================================================
        win = ctk.CTkToplevel(self.frame)
        win.title(f"Registrar Pago - Venta #{sale_id}")
        win.geometry("550x550")
        win.transient(self.frame)
        win.grab_set()

        # ================================================================
        #  CONSULTAR SALDO Y PAGOS
        # ================================================================
        info = self.controller.payment_model.get_sale_balance(sale_id)
        payments = self.controller.payment_model.get_payments_for_sale(sale_id)

        total_sale = info["total"]
        paid = info["paid"]
        balance = info["balance"]

        # ================================================================
        #  TÍTULO
        # ================================================================
        ctk.CTkLabel(
            win, text=f"Pago de Venta #{sale_id} - Cliente {client_name}",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)

        # ================================================================
        #  SALDO
        # ================================================================
        balance_label = ctk.CTkLabel(
            win,
            text=f"Saldo pendiente: ${balance:.2f}",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        balance_label.pack(pady=(0, 15))

        # ================================================================
        #  HISTORIAL DE PAGOS
        # ================================================================
        ctk.CTkLabel(
            win, text="Historial de Pagos", font=ctk.CTkFont(size=14, weight="bold")
        ).pack()

        columns = ("ID", "Fecha", "Monto", "Método")
        pay_table = ttk.Treeview(win, columns=columns, show="headings", height=5)

        for col, w in zip(columns, [50, 150, 100, 120]):
            pay_table.column(col, width=w, anchor="center")
            pay_table.heading(col, text=col, anchor="center")

        pay_table.pack(padx=10, pady=10, fill="x")

        for p in payments:
            pay_table.insert("", "end", values=p)

        # ================================================================
        #  FORMULARIO DE PAGO
        # ================================================================
        form_frame = ctk.CTkFrame(win)
        form_frame.pack(pady=10, padx=15, fill="x")

        # Entrada de monto
        ctk.CTkLabel(form_frame, text="Monto a pagar:").grid(row=0, column=0, pady=10, sticky="w")
        amount_var = ctk.StringVar()
        amount_entry = ctk.CTkEntry(form_frame, textvariable=amount_var, width=150)
        amount_entry.grid(row=0, column=1, pady=10, padx=10)

        # Método de pago
        ctk.CTkLabel(form_frame, text="Método:").grid(row=1, column=0, pady=10, sticky="w")
        method_var = ctk.StringVar(value="Efectivo")

        method_menu = ctk.CTkComboBox(
            form_frame,
            variable=method_var,
            values=["Efectivo", "Tarjeta", "Transferencia", "MercadoPago", "Otro"],
            width=150
        )
        method_menu.grid(row=1, column=1, pady=10, padx=10)

        # ================================================================
        #  VALIDACIÓN EN TIEMPO REAL
        # ================================================================
        def validate_amount(*args):
            val = amount_var.get().strip()
            try:
                num = float(val)
                if num <= 0 or num > balance:
                    amount_entry.configure(fg_color="#FFCDD2")  # rojo suave
                else:
                    amount_entry.configure(fg_color="white")
            except:
                amount_entry.configure(fg_color="#FFCDD2")

        amount_var.trace("w", validate_amount)

        # ================================================================
        #  FUNCIONES PARA LOS BOTONES
        # ================================================================
        def confirm_payment():
            val = amount_var.get().strip()
            try:
                amount = float(val)
            except:
                messagebox.showerror("Error", "Ingrese un monto válido.")
                return

            if amount <= 0:
                messagebox.showerror("Error", "El monto debe ser mayor a 0.")
                return
            
            if amount > balance:
                messagebox.showerror("Error", "El monto excede el saldo pendiente.")
                return

            # Registrar pago
            self.controller.register_payment(
                sale_id, client_id, amount, method_var.get(), win
            )

        def pay_full_balance():
            """Pagar el saldo completo usando los controles existentes"""
            amount_var.set(str(balance))
            # Mantener el método de pago que el usuario ya seleccionó
            # No necesitamos ventana adicional, usamos los controles existentes

        # ================================================================
        #  BOTONES INFERIORES - DISEÑO PROFESIONAL
        # ================================================================
        button_frame = ctk.CTkFrame(win, fg_color="transparent")
        button_frame.pack(pady=20)

        # Usar grid para alinear los 3 botones en una fila
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)

        ctk.CTkButton(
            button_frame,
            text="Pagar Saldo Completo",
            fg_color="#4CAF50",
            hover_color="#45a049",
            command=pay_full_balance,
            width=160,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, padx=5)

        ctk.CTkButton(
            button_frame,
            text="Registrar Pago",
            fg_color="#009688",
            hover_color="#00796B",
            command=confirm_payment,
            width=160,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=1, padx=5)

        ctk.CTkButton(
            button_frame,
            text="Cerrar",
            fg_color="#757575",
            hover_color="#616161",
            command=win.destroy,
            width=160,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=2, padx=5)

