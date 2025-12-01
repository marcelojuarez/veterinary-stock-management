import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
from models.stock import StockModel
from services.daily_sales_report import DailySalesReportService

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class SalesView:
    def __init__(self, parent, controller=None):
        self.controller = controller
        self.frame = ctk.CTkFrame(parent, fg_color="#f0f0f0")
        self.stock_model = StockModel()
        self.setup_variables()
        self.create_layout()

    # --------------------------------------------------------------------
    # VARIABLES
    # --------------------------------------------------------------------
    def setup_variables(self):
        self.search_var = tk.StringVar()
        self.total_var = tk.StringVar(value="TOTAL: $0.00")
        self.client_var = tk.StringVar()
        self.items_in_sale = []  # lista de productos (id, qty, price)
        self.sale_paid_var = tk.BooleanVar(value=True)
        self.last_sale_id = None
        self.all_products = []  # Nuevo

    # --------------------------------------------------------------------
    # LAYOUT PRINCIPAL
    # --------------------------------------------------------------------
    def create_layout(self):
        """Crea toda la interfaz de la vista de ventas"""
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(2, weight=1)

        self.create_header()
        self.create_product_selector()
        self.create_client_section()
        self.create_sales_table()
        self.create_footer_buttons()
        self.load_available_products()

    # --------------------------------------------------------------------
    # HEADER - Gestión de ventas
    # --------------------------------------------------------------------
    def create_header(self):
        header = ctk.CTkFrame(self.frame)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))

        title = ctk.CTkLabel(header, text="🧾 Gestión de Ventas",
                             font=ctk.CTkFont(size=17, weight="bold"))
        title.grid(row=0, column=0, padx=15, pady=10)

        search_entry = ctk.CTkEntry(
            header,
            textvariable=self.search_var,
            width=300,
            height=35,
            placeholder_text="Buscar producto..."
        )
        search_entry.grid(row=0, column=1, padx=10)
        search_entry.bind("<KeyRelease>", lambda event: self.controller.search_products_live())

        search_btn = ctk.CTkButton(
            header, text="Buscar",
            width=120, height=35,
            fg_color="#009688", hover_color="#00796B",
            command=lambda: self.controller.search_products_live()
        )
        search_btn.grid(row=0, column=2, padx=10)

        today_btn = ctk.CTkButton(
            header, text="📅 Ventas del día",
            width=150, height=35,
            fg_color="#009688", hover_color="#00796B",
            command=lambda: self.controller.show_today_sales()
        )
        today_btn.grid(row=0, column=3, padx=10)

    # --------------------------------------------------------------------
    # PANEL IZQUIERDO - STOCK DISPONIBLE
    # --------------------------------------------------------------------
    def create_product_selector(self):
        selector_frame = ctk.CTkFrame(self.frame)
        selector_frame.grid(row=1, column=0, rowspan=2, padx=10, pady=10, sticky="nsew")

        label = ctk.CTkLabel(selector_frame, text="📦 Productos disponibles",
                             font=ctk.CTkFont(size=15, weight="bold"))
        label.pack(pady=(10, 5))

        self.product_tree = ttk.Treeview(selector_frame, show="headings", height=12)
        self.product_tree["columns"] = ("Cod.", "Nombre", "P. Venta", "Stock")

        for col, w in zip(self.product_tree["columns"], [80, 300, 100, 80]):
            self.product_tree.column(col, width=w, anchor="center")
            self.product_tree.heading(col, text=col)

        self.product_tree.pack(padx=10, pady=10, fill="both", expand=True)

        add_btn = ctk.CTkButton(
            selector_frame,
            text="➕ Agregar producto",
            width=180, height=35,
            fg_color="#4CAF50", hover_color="#45a049",
            command=lambda: self.add_selected_product()
        )
        add_btn.pack(pady=(5, 10))

    # --------------------------------------------------------------------
    # PANEL DERECHO - CLIENTE + CARRITO
    # --------------------------------------------------------------------
    def create_client_section(self):
        client_frame = ctk.CTkFrame(self.frame, fg_color="#fafafa")
        client_frame.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

        # --- Combo de cliente ---
        ctk.CTkLabel(client_frame, text="Cliente:",
                    font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, padx=10, pady=10, sticky="w"
        )

        self.client_combo = ctk.CTkComboBox(
            client_frame,
            variable=self.client_var,
            values=self.controller.get_client_names(),
            width=250,
            height=35,
            state="readonly",
            command=self.on_client_selected
        )
        self.client_combo.set("Consumidor Final")
        self.client_combo.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.client_combo.bind("<Button-1>", self.refresh_client_list)
        self.client_combo.bind("<FocusIn>", self.refresh_client_list)

        # --- Campos de datos ---
        ctk.CTkLabel(client_frame, text="CUIT / DNI:",
                    font=ctk.CTkFont(size=13)).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.client_cuit_var = tk.StringVar()
        ctk.CTkEntry(client_frame, textvariable=self.client_cuit_var,
                    width=250, height=35, state="disabled").grid(row=1, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(client_frame, text="Dirección:",
                    font=ctk.CTkFont(size=13)).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.client_address_var = tk.StringVar()
        ctk.CTkEntry(client_frame, textvariable=self.client_address_var,
                    width=250, height=35, state="disabled").grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        ctk.CTkLabel(client_frame, text="Forma de pago:",
                font=ctk.CTkFont(size=13)).grid(row=3, column=0, padx=10, pady=10, sticky="w")

        self.sale_paid_switch = ctk.CTkSwitch(
            client_frame,
            text="Pagada / Fiada",
            variable=self.sale_paid_var,
            onvalue=True,
            offvalue=False,
            width=80
        )
        self.sale_paid_switch.grid(row=3, column=1, padx=10, pady=10, sticky="w")


    def create_sales_table(self):
        table_frame = ctk.CTkFrame(self.frame)
        table_frame.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

        label = ctk.CTkLabel(table_frame, text="🧾 Productos en la venta",
                             font=ctk.CTkFont(size=15, weight="bold"))
        label.pack(pady=(10, 5))

        self.sale_tree = ttk.Treeview(table_frame, show="headings", height=10)
        self.sale_tree["columns"] = ("Cod.", "Nombre", "Cant.", "Precio Unit.", "Subtotal")

        for col, w in zip(self.sale_tree["columns"], [80, 300, 80, 100, 120]):
            self.sale_tree.column(col, width=w, anchor="center")
            self.sale_tree.heading(col, text=col)

        self.sale_tree.pack(padx=10, pady=10, fill="x")

        total_label = ctk.CTkLabel(
            table_frame,
            textvariable=self.total_var,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#333333"
        )
        total_label.pack(pady=(5, 15))

    # --------------------------------------------------------------------
    # FOOTER - ACCIONES
    # --------------------------------------------------------------------
    def create_footer_buttons(self):
        footer = ctk.CTkFrame(self.frame)
        footer.grid(row=3, column=0, columnspan=2, padx=10, pady=15, sticky="ew")
        W, H = 250, 40

        buttons = [
            # CAMBIAR el comando de "Procesar venta":
            ("💰 Procesar venta", "#009688", "#00796B", self.process_sale_with_confirmation),
            ("🧾 Generar remito", "#009688", "#00796B", lambda: self.generate_delivery_note()),
            ("🗑️ Eliminar producto", "#009688", "#00796B", self.delete_selected_product),
            ("🧹 Limpiar", "#009688", "#00796B", self.clear_sale)
        ]

        for i, (text, color, hover, cmd) in enumerate(buttons):
            ctk.CTkButton(
                footer,
                text=text,
                width=W,
                height=H,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=color,
                hover_color=hover,
                command=cmd
            ).grid(row=0, column=i, padx=10, pady=10)

    # --------------------------------------------------------------------
    # LÓGICA DE FUNCIONAMIENTO
    # --------------------------------------------------------------------
    def add_selected_product(self):
        try:
            selected = self.product_tree.selection()
            if not selected:
                messagebox.showwarning("Advertencia", "Seleccione un producto.")
                return

            item = self.product_tree.item(selected[0])["values"]
            product_id, name, price, stock = item
            price, stock = float(price), int(stock)

            # Ventana emergente para cantidad
            qty_win = ctk.CTkToplevel(self.frame)
            qty_win.title(f"Agregar {name}")
            qty_win.geometry("320x220")
            qty_win.transient(self.frame)
            qty_win.grab_set()

            ctk.CTkLabel(qty_win, text=f"Agregar '{name}'", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(15, 5))
            ctk.CTkLabel(qty_win, text=f"Stock disponible: {stock}", font=ctk.CTkFont(size=13)).pack()

            qty_var = tk.StringVar(value="1")
            qty_entry = ctk.CTkEntry(qty_win, textvariable=qty_var, width=80, height=35, justify="center")
            qty_entry.pack(pady=10)
            qty_entry.focus()

            def confirm_add():
                self.controller.add_product_to_sale(product_id, name, price, stock, qty_var.get())
                self.refresh_sale_table()
                self.update_total()
                qty_win.destroy()

            ctk.CTkButton(qty_win, text="Agregar", width=120, height=35,
                          fg_color="#4CAF50", hover_color="#45a049", command=confirm_add).pack(pady=(10, 5))
            ctk.CTkButton(qty_win, text="Cancelar", width=120, height=35,
                          fg_color="#757575", hover_color="#616161", command=qty_win.destroy).pack(pady=(0, 10))

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo agregar el producto: {e}")

    def open_today_sales_window(self, rows):
        """Ventana con tabla para mostrar ventas del día"""
        win = ctk.CTkToplevel(self.frame)
        win.title("Ventas del día")
        win.geometry("700x600")
        win.transient(self.frame)
        win.grab_set()

        title = ctk.CTkLabel(win, text="📅 Ventas del día",
                            font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=10)

        # Tabla
        tree = ttk.Treeview(win, show="headings", height=10)
        tree["columns"] = ("ID", "Fecha", "Cliente", "Estado", "Total")

        widths = [60, 150, 250, 100, 100]
        for col, w in zip(tree["columns"], widths):
            tree.column(col, width=w, anchor="center")
            tree.heading(col, text=col)

        for sale_id, date, total, cliente, estado in rows:
            tree.insert("", "end", values=(
                sale_id,
                date,
                cliente if cliente else "Consumidor Final",
                estado.upper(),
                f"${total:.2f}"
            ))

        tree.pack(padx=15, pady=10, fill="both", expand=True)

        # Botones
        btn_frame = ctk.CTkFrame(win)
        btn_frame.pack(pady=10)

        export_btn = ctk.CTkButton(
            btn_frame,
            text="🖨 Imprimir / Exportar",
            width=180,
            fg_color="#0078D4",
            hover_color="#005A9E",
            command=lambda: self.export_sales_day(rows)
        )
        export_btn.grid(row=0, column=0, padx=5)

        close_btn = ctk.CTkButton(
            btn_frame,
            text="Cerrar",
            width=140,
            fg_color="#757575",
            hover_color="#616161",
            command=win.destroy
        )
        close_btn.grid(row=0, column=1, padx=5)

    def export_sales_day(self, rows):
        pdf = DailySalesReportService().generate(rows)
        messagebox.showinfo("PDF generado", f"Archivo guardado:\n\n{pdf}\n\nPuedes imprimirlo.")

    def generate_delivery_note(self):
        if not self.last_sale_id:
            self.show_warning("Primero debe procesar una venta.")
            return

        try:
            pdf = self.controller.create_delivery_note(self.last_sale_id)
            self.show_success(f"Remito generado correctamente:\n{pdf}")
        except Exception as e:
            self.show_error(f"Error al generar remito: {e}")

    def refresh_sale_table(self):
        self.sale_tree.delete(*self.sale_tree.get_children())
        for pid, name, qty, price in self.items_in_sale:
            subtotal = round(price * qty, 2)
            name = next((self.product_tree.item(r)["values"][1] for r in self.product_tree.get_children() if self.product_tree.item(r)["values"][0] == pid), "")
            self.sale_tree.insert("", "end", values=(pid, name, qty, price, subtotal))

    def update_total(self):
        total = sum(q * p for _, _, q, p in self.items_in_sale)
        self.total_var.set(f"TOTAL: ${total:.2f}")

    def clear_sale(self):
        self.sale_tree.delete(*self.sale_tree.get_children())
        self.items_in_sale.clear()
        self.total_var.set("TOTAL: $0.00")

    def delete_selected_product(self):
        try:
            selected_item = self.sale_tree.selection()[0]
            pid = self.sale_tree.item(selected_item)["values"][0]
            self.sale_tree.delete(selected_item)
            self.items_in_sale = [
                (p, n, q, pr) for (p, n, q, pr) in self.items_in_sale if p != pid
            ]
            self.update_total()
        except IndexError:
            messagebox.showwarning("Advertencia", "Seleccione un producto para eliminar.")

    def delete_item(self):
        """Eliminar item seleccionado de la venta"""
        if not self.sales_view.ask_confirmation("¿Eliminar artículo?"):
            return

        if self.sales_view.delete_selected_product():
            self.sales_view.show_success("Artículo eliminado correctamente.")
        else:
            self.sales_view.show_warning("Seleccione el artículo que desea eliminar.")

    def load_available_products(self):
        """Cargar productos disponibles y guardar en caché"""
        try:
            products = self.stock_model.get_all_products()
            self.all_products = [p for p in products if p[11] > 0]  # Solo productos con stock
            
            # Mostrar todos los productos inicialmente
            self.refresh_product_tree(self.all_products)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los productos: {e}")

    def refresh_product_tree(self, products):
        """Actualizar la tabla de productos con la lista proporcionada"""
        self.product_tree.delete(*self.product_tree.get_children())
        
        for p in products:
            (pid, _, name, _, _, _, _, 
            _, price_with_iva, _, _, qty) = p
            
            if qty > 0:  # Solo mostrar productos con stock
                self.product_tree.insert("", "end", values=(pid, name, price_with_iva, qty))


    def on_client_selected(self, selected_name):
        """Actualizar datos del cliente al cambiar selección"""
        try:
            data = self.controller.get_client_data(selected_name)
            if data:
                self.client_cuit_var.set(data.get("cuit", ""))
                self.client_address_var.set(data.get("domicilio", ""))
            else:
                self.client_cuit_var.set("")
                self.client_address_var.set("")
        except Exception as e:
            self.show_error(f"No se pudieron cargar los datos del cliente: {e}")

    def refresh_client_list(self, event=None):
        names = self.controller.get_client_names()
        self.client_combo.configure(values=names)

        # Mantiene selección válida
        if self.client_var.get() not in names:
            self.client_combo.set("Consumidor Final")

    def show_sale_confirmation(self):
        """Mostrar ventana de confirmación con preview de la venta"""
        
        # Validar que haya productos
        if not self.items_in_sale:
            self.show_warning("No hay productos en la venta")
            return False
        
        confirm_win = ctk.CTkToplevel(self.frame)
        confirm_win.title("Confirmar Venta")
        confirm_win.geometry("650x650")
        confirm_win.transient(self.frame)
        confirm_win.grab_set()
        confirm_win.resizable(False, False)  # Evitar redimensionar
        
        confirm_win.update_idletasks()
        x = (confirm_win.winfo_screenwidth() // 2) - (325)
        y = (confirm_win.winfo_screenheight() // 2) - (325)
        confirm_win.geometry(f"650x650+{x}+{y}")
        
        title = ctk.CTkLabel(
            confirm_win,
            text="🧾 Resumen de la Venta",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=(15, 8)) 
        
        client_frame = ctk.CTkFrame(confirm_win, fg_color="#f5f5f5")
        client_frame.pack(padx=15, pady=5, fill="x")
        
        client_name = self.client_var.get()
        client_cuit = self.client_cuit_var.get()
        client_address = self.client_address_var.get()
        is_paid = "PAGADA" if self.sale_paid_var.get() else "FIADA"
        
        ctk.CTkLabel(
            client_frame,
            text="📋 Datos del Cliente",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(8, 3))
        
        ctk.CTkLabel(
            client_frame,
            text=f"Cliente: {client_name}",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=15, pady=1)  
        
        if client_cuit:
            ctk.CTkLabel(
                client_frame,
                text=f"CUIT/DNI: {client_cuit}",
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w", padx=15, pady=1)
        
        if client_address:
            ctk.CTkLabel(
                client_frame,
                text=f"Dirección: {client_address}",
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w", padx=15, pady=1)
        
        ctk.CTkLabel(
            client_frame,
            text=f"Estado de pago: {is_paid}",
            font=ctk.CTkFont(size=12, weight="bold"),  # Reducido de 13 a 12
            text_color="#009688" if self.sale_paid_var.get() else "#f44336"
        ).pack(anchor="w", padx=15, pady=(1, 8))  # Reducido padding
        
        # Frame de productos - MÁS COMPACTO
        products_frame = ctk.CTkFrame(confirm_win)
        products_frame.pack(padx=15, pady=5, fill="both", expand=True)  # Reducido padding
        
        ctk.CTkLabel(
            products_frame,
            text="📦 Productos",
            font=ctk.CTkFont(size=14, weight="bold")  # Reducido de 15 a 14
        ).pack(pady=(8, 3))  # Reducido padding
        
        # Tabla de productos - ALTURA REDUCIDA
        preview_tree = ttk.Treeview(products_frame, show="headings", height=6)  # Reducido de 8 a 6
        preview_tree["columns"] = ("Cant.", "Producto", "P. Unit.", "Subtotal")
        
        widths = [60, 280, 100, 100]
        for col, w in zip(preview_tree["columns"], widths):
            preview_tree.column(col, width=w, anchor="center")
            preview_tree.heading(col, text=col)
        
        # Agregar productos
        total = 0
        for pid, name, qty, price in self.items_in_sale:
            # Obtener nombre del producto
            product_name = name
            if not product_name:
                for item in self.product_tree.get_children():
                    values = self.product_tree.item(item)["values"]
                    if values[0] == pid:
                        product_name = values[1]
                        break
            
            subtotal = round(price * qty, 2)
            total += subtotal
            
            preview_tree.insert("", "end", values=(
                qty,
                product_name,
                f"${price:.2f}",
                f"${subtotal:.2f}"
            ))
        
        preview_tree.pack(padx=8, pady=5, fill="both", expand=True)  # Reducido padding
        
        # Frame de totales - MÁS COMPACTO
        totals_frame = ctk.CTkFrame(confirm_win, fg_color="#e8f5e9")
        totals_frame.pack(padx=15, pady=5, fill="x")  # Reducido padding
        
        # Cantidad total de items
        total_items = sum(qty for _, _, qty, _ in self.items_in_sale)
        
        ctk.CTkLabel(
            totals_frame,
            text=f"Total de productos: {len(self.items_in_sale)} | Total de unidades: {total_items}",
            font=ctk.CTkFont(size=12)  # Reducido y combinado en una línea
        ).pack(pady=(8, 3))
        
        ctk.CTkLabel(
            totals_frame,
            text=f"TOTAL A PAGAR: ${total:.2f}",
            font=ctk.CTkFont(size=20, weight="bold"),  # Reducido de 22 a 20
            text_color="#2e7d32"
        ).pack(pady=(3, 10))  # Reducido padding
        
        # Variable para capturar la respuesta
        result = {"confirmed": False}
        
        # Frame de botones - SIEMPRE VISIBLE
        button_frame = ctk.CTkFrame(confirm_win, fg_color="transparent")
        button_frame.pack(pady=10, side="bottom")  # Cambio importante: side="bottom"
        
        def confirm():
            result["confirmed"] = True
            confirm_win.destroy()
        
        def cancel():
            result["confirmed"] = False
            confirm_win.destroy()
        
        confirm_btn = ctk.CTkButton(
            button_frame,
            text="✅ Confirmar y Procesar",
            width=200,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#4CAF50",
            hover_color="#45a049",
            command=confirm
        )
        confirm_btn.grid(row=0, column=0, padx=10)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="❌ Cancelar",
            width=150,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#757575",
            hover_color="#616161",
            command=cancel
        )
        cancel_btn.grid(row=0, column=1, padx=10)
        
        # Esperar a que se cierre la ventana
        confirm_win.wait_window()
        
        return result["confirmed"]

    def process_sale_with_confirmation(self):
        """Procesar venta con confirmación previa"""
        if self.show_sale_confirmation():
            # Si el usuario confirma, proceder con la venta
            self.controller.confirm_sale()

    # Utilidades
    def show_success(self, msg): messagebox.showinfo("Éxito", msg)
    def show_error(self, msg): messagebox.showerror("Error", msg)
    def show_warning(self, msg): messagebox.showwarning("Advertencia", msg)
