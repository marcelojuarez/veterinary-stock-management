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
        self.create_widgets()

    def setup_variables(self):
        """Variables principales"""
        self.search_var = tk.StringVar()
        self.total_var = tk.StringVar(value="0.00")
        self.items_in_sale = []  # lista de productos agregados a la venta

    def create_widgets(self):
        """Crea todos los componentes de la vista"""
        self.create_header()
        self.create_product_selector()
        self.create_sales_table()
        self.create_footer_buttons()
        self.load_available_products()


    # --------------------------------------------------------------------
    # HEADER
    # --------------------------------------------------------------------
    def create_header(self):
        header = ctk.CTkFrame(self.frame)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        title = ctk.CTkLabel(header, text="🧾 Nueva venta / Presupuesto",
                             font=ctk.CTkFont(size=15, weight="bold"))
        title.grid(row=0, column=0, padx=15, pady=10)

        search_entry = ctk.CTkEntry(
            header,
            textvariable=self.search_var,
            width=400,
            height=35,
            placeholder_text="Buscar producto por nombre o código..."
        )
        search_entry.grid(row=0, column=1, padx=15, pady=10)

        search_btn = ctk.CTkButton(
            header,
            text="Buscar",
            width=140,
            height=35,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#009688",
            hover_color="#00796B",
            command=lambda: self.controller.search_product_for_sale(self.search_var.get())

        )
        search_btn.grid(row=0, column=2, padx=5, pady=10)

        view_sales_btn = ctk.CTkButton(
            header,
            text="📅 Ventas del día",
            width=200,
            height=35,
            fg_color="#009688",
            hover_color="#00796B",
            command=lambda: self.controller.show_today_sales()
        )
        view_sales_btn.grid(row=0, column=3, padx=5, pady=10)


    # --------------------------------------------------------------------
    # PRODUCT SELECTION
    # --------------------------------------------------------------------
    def create_product_selector(self):
        """Tabla para mostrar productos del stock"""
        selector_frame = ctk.CTkFrame(self.frame)
        selector_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        label = ctk.CTkLabel(selector_frame, text="Productos disponibles",
                             font=ctk.CTkFont(size=15, weight="bold"))
        label.pack(pady=(10, 5))

        self.product_tree = ttk.Treeview(selector_frame, show="headings", height=4)
        self.product_tree["columns"] = ("Cod.", "Nombre", "P. Venta", "Stock")

        for col, w in zip(self.product_tree["columns"], [80, 600, 150, 100]):
            self.product_tree.column(col, width=w, anchor="center")
            self.product_tree.heading(col, text=col)

        self.product_tree.pack(padx=10, pady=10, fill="x")

        add_btn = ctk.CTkButton(
            selector_frame,
            text="Agregar producto",
            width=180,
            height=35,
            fg_color="#4CAF50",
            hover_color="#45a049",
            command=lambda: self.add_selected_product()
        )
        add_btn.pack(pady=(0, 10))

    # --------------------------------------------------------------------
    # SALES TABLE
    # --------------------------------------------------------------------
    def create_sales_table(self):
        """Tabla de productos agregados a la venta"""
        table_frame = ctk.CTkFrame(self.frame)
        table_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")

        label = ctk.CTkLabel(table_frame, text="Productos en la venta",
                             font=ctk.CTkFont(size=15, weight="bold"))
        label.pack(pady=(10, 5))

        self.sale_tree = ttk.Treeview(table_frame, show="headings", height=6)
        self.sale_tree["columns"] = ("Cod.", "Nombre", "Cant.", "Precio Unit.", "Subtotal")

        for col, w in zip(self.sale_tree["columns"], [80, 600, 100, 120, 120]):
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
    # FOOTER BUTTONS
    # --------------------------------------------------------------------
    def create_footer_buttons(self):
        footer = ctk.CTkFrame(self.frame)
        footer.grid(row=3, column=0, padx=10, pady=15, sticky="w")
        W = 290
        H = 35

        new_sale_btn = ctk.CTkButton(
            footer,
            text="Facturar venta",
            width=W,
            height=H,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#009688",
            hover_color="#00796B",
            command=lambda: self.controller.confirm_sale("factura")
        )
        new_sale_btn.grid(row=0, column=0, padx=10, pady=10)

        budget_btn = ctk.CTkButton(
            footer,
            text="Generar presupuesto",
            width=W,
            height=H,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#009688",
            hover_color="#00796B",
            command=lambda: self.controller.confirm_sale("presupuesto")
        )
        budget_btn.grid(row=0, column=1, padx=10, pady=10)

        delete_btn = ctk.CTkButton(
            footer,
            text="Eliminar producto",
            width=W,
            height=H,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#009688",
            hover_color="#00796B",
            command=lambda: self.controller.delete_item()
        )
        delete_btn.grid(row=0, column=2, padx=10, pady=10)

        clear_btn = ctk.CTkButton(
            footer,
            text="Limpiar",
            width=W,
            height=H,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#009688",
            hover_color="#00796B",
            command=self.clear_sale
        )
        clear_btn.grid(row=0, column=3, padx=10, pady=10)


    # --------------------------------------------------------------------
    # LOGIC STUBS (para implementar en el controller)
    # --------------------------------------------------------------------
    def add_selected_product(self):
        """Abrir ventana para elegir cantidad y delegar la lógica al controller"""
        try:
            selected = self.product_tree.selection()
            if not selected:
                messagebox.showwarning("Advertencia", "Seleccione un producto del listado.")
                return

            item = self.product_tree.item(selected[0])["values"]
            product_id, name, price, stock = item
            price = float(price)
            stock = int(stock)

            # Ventana emergente para elegir cantidad
            qty_win = ctk.CTkToplevel(self.frame)
            qty_win.title(f"Agregar {name}")
            qty_win.geometry("350x250")
            qty_win.transient(self.frame)
            qty_win.grab_set()

            title = ctk.CTkLabel(qty_win, text=f"Agregar '{name}'", font=ctk.CTkFont(size=16, weight="bold"))
            title.pack(pady=(20, 10))

            stock_label = ctk.CTkLabel(qty_win, text=f"Stock disponible: {stock}", font=ctk.CTkFont(size=13))
            stock_label.pack(pady=5)

            qty_var = tk.StringVar(value="1")
            qty_entry = ctk.CTkEntry(qty_win, textvariable=qty_var, width=100, height=35, justify="center")
            qty_entry.pack(pady=10)
            qty_entry.focus()

            def confirm_add():
                quantity = self.controller.add_product_to_sale(
                    product_id, name, price, stock, qty_var.get()
                )
                if quantity:  # si el controlador devuelve True
                    self.refresh_sale_table()
                    self.update_total()
                    qty_win.destroy()
                    self.show_success(f"{qty_var.get()} {name} agregado")

            confirm_btn = ctk.CTkButton(qty_win, text="Agregar", width=120, height=35,
                                        fg_color="#4CAF50", hover_color="#45a049", command=confirm_add)
            confirm_btn.pack(pady=(10, 5))

            cancel_btn = ctk.CTkButton(qty_win, text="Cancelar", width=120, height=35,
                                    fg_color="#757575", hover_color="#616161", command=qty_win.destroy)
            cancel_btn.pack(pady=(0, 10))

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo agregar el producto: {e}")

    def update_total(self):
        """Actualizar el total mostrado"""
        total = sum(q * p for _, q, p in self.items_in_sale)
        self.total_var.set(f"TOTAL: ${total:.2f}")

    def clear_sale(self):
        """Limpiar los productos de la venta"""
        self.sale_tree.delete(*self.sale_tree.get_children())
        self.items_in_sale.clear()
        self.total_var.set("TOTAL: $0.00")

    def load_available_products(self):
        """Carga los productos desde el stock a la tabla de productos disponibles"""
        try:
            products = self.stock_model.get_all_products()
            self.product_tree.delete(*self.product_tree.get_children())

            for p in products:
                (pid, name, pack, profit, cost, price, iva, price_with_iva,
                created_at, last_update, quantity) = p
                
                # Solo mostrar si hay stock disponible
                if quantity > 0:
                    self.product_tree.insert(
                        "", "end",
                        values=(pid, name, price_with_iva, quantity)
                    )

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los productos: {e}")

    def delete_selected_product(self):
        """Eliminar producto seleccionado de la venta"""
        try:
            selected_item = self.sale_tree.selection()[0]
            values = self.sale_tree.item(selected_item)["values"]
            product_id = values[0]  # el ID real del producto

            # Eliminar visualmente del Treeview
            self.sale_tree.delete(selected_item)

            # Eliminar del listado interno
            self.items_in_sale = [
                (pid, qty, price)
                for (pid, qty, price) in self.items_in_sale
                if pid != product_id
            ]

            self.update_total()
            return True

        except IndexError:
            return False


    def refresh_sale_table(self):
        """Actualizar tabla de venta desde items_in_sale"""
        self.sale_tree.delete(*self.sale_tree.get_children())

        for pid, qty, price in self.items_in_sale:
            name = None
            for row in self.product_tree.get_children():
                vals = self.product_tree.item(row)["values"]
                if vals[0] == pid:
                    name = vals[1]
                    break
            subtotal = round(price * qty, 2)
            self.sale_tree.insert("", "end", values=(pid, name or "", qty, price, subtotal))

    def show_success(self, message):
        """Mostrar mensaje de éxito"""
        messagebox.showinfo("Éxito", message)

    def show_error(self, message):
        """Mostrar mensaje de error"""
        messagebox.showerror("Error", message)

    def show_warning(self, message):
        """Mostrar mensaje de advertencia"""
        messagebox.showwarning("Advertencia", message)

    def ask_confirmation(self, message):
        """Preguntar confirmación al usuario"""
        return messagebox.askquestion("Confirmación", message) == 'yes'

