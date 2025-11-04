import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
from models.stock import StockModel

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

        search_btn = ctk.CTkButton(
            header, text="Buscar",
            width=120, height=35,
            fg_color="#009688", hover_color="#00796B",
            command=lambda: self.controller.search_product_for_sale(self.search_var.get())
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
            command=self.on_client_selected  # 👈 Llamado cuando cambia selección
        )
        self.client_combo.set("Consumidor Final")
        self.client_combo.grid(row=0, column=1, padx=10, pady=10, sticky="w")

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
            ("💰 Procesar venta", "#009688", "#00796B", lambda: self.controller.confirm_sale("factura", self.client_var.get())),
            ("🧾 Generar presupuesto", "#009688", "#00796B", lambda: self.controller.confirm_sale("presupuesto")),
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

    def refresh_sale_table(self):
        self.sale_tree.delete(*self.sale_tree.get_children())
        for pid, qty, price in self.items_in_sale:
            subtotal = round(price * qty, 2)
            name = next((self.product_tree.item(r)["values"][1] for r in self.product_tree.get_children() if self.product_tree.item(r)["values"][0] == pid), "")
            self.sale_tree.insert("", "end", values=(pid, name, qty, price, subtotal))

    def update_total(self):
        total = sum(q * p for _, q, p in self.items_in_sale)
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
            self.items_in_sale = [(p, q, pr) for p, q, pr in self.items_in_sale if p != pid]
            self.update_total()
        except IndexError:
            messagebox.showwarning("Advertencia", "Seleccione un producto para eliminar.")

    def load_available_products(self):
        try:
            products = self.stock_model.get_all_products()
            self.product_tree.delete(*self.product_tree.get_children())
            for p in products:
                (pid, name, pack, profit, cost, price, iva, price_with_iva, created_at, last_update, qty) = p
                if qty > 0:
                    self.product_tree.insert("", "end", values=(pid, name, price_with_iva, qty))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los productos: {e}")

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


    # Utilidades
    def show_success(self, msg): messagebox.showinfo("Éxito", msg)
    def show_error(self, msg): messagebox.showerror("Error", msg)
    def show_warning(self, msg): messagebox.showwarning("Advertencia", msg)
