import tkinter as tk
import customtkinter as ctk
from decimal import Decimal
from tkcalendar import DateEntry
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from views.client_selector import ClientSelectorDialog
from services.daily_sales_report import DailySalesReportService
from utils.view_helpers import center_window, show_error
from utils.utils import iso_to_traditional, norm_to_2_dec, format_currency, string_to_2_dec, traditional_to_iso

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class SalesView:
    def __init__(self, parent, controller, stock_model, customer_model):
        self.controller = controller
        self.frame = ctk.CTkFrame(parent, fg_color="#f0f0f0")
        self.stock_model = stock_model
        self.customer_model = customer_model
        self.setup_variables()
        self.create_layout()

    # --------------------------------------------------------------------
    # VARIABLES
    # --------------------------------------------------------------------
    def setup_variables(self):
        self.search_var = tk.StringVar()
        self.total_var = tk.StringVar(value="TOTAL: $0,00")
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
        header.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))

        title = ctk.CTkLabel(header, text="🧾 Gestión de Ventas",
                             font=ctk.CTkFont(size=15, weight="bold"))
        title.grid(row=0, column=0, padx=15, pady=10)

        search_entry = ctk.CTkEntry(
            header,
            width=300,
            height=35,
            placeholder_text="Buscar producto...",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        search_entry.grid(row=0, column=1, padx=10)
        search_entry.bind("<KeyRelease>", lambda event: self.controller.search_products_live())

        search_btn = ctk.CTkButton(
            header, text="Buscar",
            width=120, height=35,
            fg_color="#009688", hover_color="#00796B",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.controller.search_products_live()
        )
        search_btn.grid(row=0, column=2, padx=10)

        today_btn = ctk.CTkButton(
            header, text="📅 Ver ventas",
            width=150, height=35,
            fg_color="#009688", hover_color="#00796B",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.controller.show_today_sales()
        )
        today_btn.grid(row=0, column=2, padx=10)

    # --------------------------------------------------------------------
    # PANEL IZQUIERDO - STOCK DISPONIBLE
    # --------------------------------------------------------------------
    def create_product_selector(self):
        selector_frame = ctk.CTkFrame(self.frame)
        selector_frame.grid(row=1, column=0, rowspan=2, padx=10, pady=10, sticky="nsew")

        label = ctk.CTkLabel(selector_frame, text="📦 Productos disponibles",
                            font=ctk.CTkFont(size=16, weight="bold"))
        label.pack(pady=(10, 5))

        tree_frame = tk.Frame(selector_frame)
        tree_frame.pack(padx=10, pady=10, fill="both", expand=True)
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        self.product_tree = ttk.Treeview(tree_frame, show="headings", height=12)
        self.product_tree["columns"] = ("Cód.", "Nombre", "Envase", "P. Venta", "Stock")

        for col, w in zip(self.product_tree["columns"], [40, 260, 100, 80, 50]):
            self.product_tree.column(col, width=w)
            self.product_tree.heading(col, text=col)

        scroll_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.product_tree.yview)
        scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.product_tree.xview)
        self.product_tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.product_tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")



        # Frame para botones (para que queden uno al lado del otro)
        button_frame = ctk.CTkFrame(selector_frame, fg_color="transparent")
        button_frame.pack(pady=(5, 10))

        add_btn = ctk.CTkButton(
            button_frame,
            text="➕ Agregar producto",
            width=180, height=35,
            fg_color="#4CAF50", hover_color="#45a049",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.add_selected_product()
        )
        add_btn.grid(row=0, column=0, padx=5)

        # NUEVO: Botón de honorarios
        honorarios_btn = ctk.CTkButton(
            button_frame,
            text="💼 Agregar honorarios",
            width=180, height=35,
            fg_color="#2196F3", hover_color="#1976D2",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.add_honorarios
        )
        honorarios_btn.grid(row=0, column=1, padx=5)

    ## -- Crea la tabla de productos en la venta -- ##
    def create_sales_table(self):
        table_frame = ctk.CTkFrame(self.frame)
        table_frame.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        table_frame.rowconfigure(1, weight=1)  # el treeview ocupa el espacio
        table_frame.columnconfigure(0, weight=1)

        label = ctk.CTkLabel(table_frame, text="🧾 Productos en la venta",
                            font=ctk.CTkFont(size=16, weight="bold"))
        label.grid(row=0, column=0, pady=(10, 5))

        self.sale_tree = ttk.Treeview(table_frame, show="headings", height=10)
        self.sale_tree["columns"] = ("Cód.", "Nombre", "Envase", "Cant.", "Precio Unit.", "Subtotal")

        for col, w in zip(self.sale_tree["columns"], [60, 300, 80, 60, 100, 120]):
            self.sale_tree.column(col, width=w, anchor="center")
            self.sale_tree.heading(col, text=col)

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.sale_tree.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.sale_tree.xview)
        self.sale_tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.sale_tree.grid(row=1, column=0, padx=(10,0), pady=(10,0), sticky="nsew")
        scroll_y.grid(row=1, column=1, sticky="ns", pady=(10,0))
        scroll_x.grid(row=2, column=0, sticky="ew", padx=(10,0))

        total_label = ctk.CTkLabel(
            table_frame,
            textvariable=self.total_var,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#333333"
        )
        total_label.grid(row=3, column=0, pady=(5, 15))

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
            #("🧾 Generar remito", "#009688", "#00796B", lambda: self.generate_delivery_note()),
            ("🗑️ Eliminar producto", "#009688", "#00796B", self.delete_selected_product),
            ("🧹 Limpiar", "#009688", "#00796B", self.clear_sale)
        ]
        footer.columnconfigure((0, 1, 2), weight=1)
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
            p_data = self.stock_model.get_product_by_id(item[0])

            product_id, name, pack, _, _, _ ,_ , _, _, \
            price_with_iva, _, _, stock = p_data
            price = norm_to_2_dec(price_with_iva)

            # Ventana emergente para cantidad
            qty_win = ctk.CTkToplevel(self.frame)
            card_frame = ctk.CTkFrame(qty_win, fg_color="white", corner_radius=20)
            card_frame.pack(fill="both", expand=True, padx=20, pady=20)
            qty_win.title(f"Agregar Producto")
            qty_win.transient(self.frame)
            qty_win.grab_set()
            center_window(qty_win, 420, 270)

            ctk.CTkLabel(
                card_frame, 
                text=f"AGREGAR: \n {name} {pack}", 
                font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(15, 5))
            ctk.CTkLabel(card_frame, text=f"Stock disponible: {stock}", font=ctk.CTkFont(size=13)).pack()

            qty_var = tk.StringVar()
            qty_entry = ctk.CTkEntry(card_frame, textvariable=qty_var, width=80, height=35, justify="center")
            qty_entry.pack(pady=10)
            qty_var.set("1")
            qty_entry.focus()
            qty_entry.icursor("end")

            def confirm_add():
                self.controller.add_product_to_sale(product_id, name, pack, price, stock, qty_var.get())
                self.refresh_sale_table()
                self.update_total()
                qty_win.destroy()

            confirm_btn = ctk.CTkButton(card_frame, text="Agregar", width=120, height=35,
                          fg_color="#4CAF50", hover_color="#45a049", command=confirm_add)
            confirm_btn.pack(pady=(10, 5))

            qty_win.bind("<Return>", lambda event: confirm_btn.invoke())

            ctk.CTkButton(card_frame, text="Cancelar", width=120, height=35,
                          fg_color="#757575", hover_color="#616161", command=qty_win.destroy).pack(pady=(0, 10))

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo agregar el producto: {e}")

    def export_sales_day(self, rows, fecha_desde, fecha_hasta):
        pdf = DailySalesReportService().generate(
            rows,
            fecha_desde,
            fecha_hasta
        )

        messagebox.showinfo(
            "PDF generado",
            f"Archivo guardado:\n\n{pdf}"
        )

    ## -- Permite generar el remito asociado a una venta -- ##
    def generate_delivery_note(self):
        if not self.last_sale_id:
            self.show_warning("Primero debe procesar una venta.")
            return

        try:
            pdf = self.controller.create_delivery_note(self.last_sale_id)
            self.show_success(f"Remito generado correctamente:\n{pdf}")
        except Exception as e:
            self.show_error(f"Error al generar remito: {e}")

    ## -- Refresca la tabla de productos en la venta -- ##
    def refresh_sale_table(self):
        self.sale_tree.delete(*self.sale_tree.get_children())
        
        for item in self.items_in_sale:
            # Puede tener 4 o 5 elementos (con o sin observaciones)
            if len(item) == 6:
                pid, name, pack, qty, price, observations = item
                # Mostrar nombre con preview de observaciones
                display_name = f"{name} - {observations[:40]}..." if len(observations) > 40 else f"{name} - {observations}"
            else:
                pid, name, pack, qty, price = item
                display_name = name if name else self._get_product_name(pid)
            
            subtotal = norm_to_2_dec(price * qty)
            self.sale_tree.insert("", "end", values=(pid, display_name, pack, qty, format_currency(price), format_currency(subtotal)))

    def _get_product_name(self, pid):
        """Helper para obtener nombre del producto por ID"""
        for item in self.product_tree.get_children():
            values = self.product_tree.item(item)["values"]
            if values[0] == pid:
                return values[1]
        return "Producto desconocido"

    ## -- Actualiza el monto total en la tabla de productos en la venta -- ##
    def update_total(self):
        """Calcular total manejando items con y sin observaciones"""
        total = Decimal('0.00')
        for item in self.items_in_sale:
            if len(item) == 6:  # Tiene observaciones (honorarios)
                _, _, _, qty, price, _ = item
            else:  # Producto normal
                _, _, _, qty, price = item

            total += qty * price
        
        total = norm_to_2_dec(total)
        self.total_var.set(f"TOTAL: ${format_currency(total)}")

    ## -- Elimina todos los productos de la tabla de productos en la venta -- ##
    def clear_sale(self):
        if not self.last_sale_id:
            if not self.ask_confirmation("¿Eliminar todos los artículos agregados?"):
                return

        self.sale_tree.delete(*self.sale_tree.get_children())
        self.items_in_sale.clear()
        self.total_var.set("TOTAL: $0,00")

    ## -- Elimina un producto seleccionado en la tabla de productos en la venta -- ##
    def delete_selected_product(self):
        try:
            
            selected_item = self.sale_tree.selection()[0]
            if not self.ask_confirmation("¿Eliminar artículo?"):
                return
            
            pid = self.sale_tree.item(selected_item)["values"][0]
            self.sale_tree.delete(selected_item)
            self.items_in_sale = [
                item for item in self.items_in_sale if item[0] != pid
            ]
            self.update_total()
        except IndexError:
            messagebox.showwarning("Advertencia", "Seleccione un producto para eliminar.")

    def load_available_products(self):
        """Cargar productos disponibles y guardar en caché"""
        try:
            products = self.stock_model.get_all_products()
            self.all_products = [p for p in products if p[12] > 0]  # Solo productos con stock
            
            # Mostrar todos los productos inicialmente
            self.refresh_product_tree(self.all_products)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los productos: {e}")

    def refresh_product_tree(self, products):
        """Actualizar la tabla de productos con la lista proporcionada"""
        self.product_tree.delete(*self.product_tree.get_children())
        
        for p in products:
            (pid, name, pack, _, _, _, _, _, 
            _, price_with_iva, _, _, qty) = p
            
            if qty > 0:  # Solo mostrar productos con stock
                self.product_tree.insert(
                    "", 
                    "end", 
                    values=(pid, name, pack, format_currency(price_with_iva), qty)
                )

    def show_sale_confirmation(self):
        """Mostrar ventana de confirmación con preview de la venta"""
        # Validar que haya productos
        if not self.items_in_sale:
            self.show_warning("No hay productos en la venta")
            return False
        if self.client_var.get() == "":
            self.show_warning("Seleccione un cliente específico o Consumidor Final")
            return False
        
        confirm_win = ctk.CTkToplevel(self.frame)
        confirm_win.withdraw()
        confirm_win.title("Confirmar Venta")
        confirm_win.transient(self.frame)
        confirm_win.grab_set()
        confirm_win.resizable(False, False) 
        confirm_win.update_idletasks()
        scroll_frame = ctk.CTkScrollableFrame(confirm_win, height=420)
        scroll_frame.pack(padx=10, pady=(5,0), fill="both", expand=True)
        
        
        title = ctk.CTkLabel(
            scroll_frame,
            text="🧾 Resumen de la Venta",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=(15, 8)) 
        
        client_frame = ctk.CTkFrame(scroll_frame, fg_color="#f5f5f5", corner_radius=10)
        client_frame.pack(padx=15, pady=5, fill="x")
        
        client_name = self.client_var.get()
        client_cuit = self.client_cuit_var.get()
        client_address = self.client_address_var.get()
        is_paid = "PAGADA" if self.payment_type_var.get() == "PAID" else "CON DEUDA"
        
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

        client_iva = self.client_iva_var.get()
        if client_iva:
            ctk.CTkLabel(
                client_frame,
                text=f"Cond. IVA: {client_iva}",
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w", padx=15, pady=1)
        
        ctk.CTkLabel(
            client_frame,
            text=f"Estado de pago: {is_paid}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#009688" if self.payment_type_var.get() == "PAID" else "#f44336"
        ).pack(anchor="w", padx=15, pady=(1, 8))
        
        # Frame de productos - MÁS COMPACTO
        products_frame = ctk.CTkFrame(scroll_frame)
        products_frame.pack(padx=15, pady=5, fill="x")  
        
        ctk.CTkLabel(
            products_frame,
            text="📦 Productos",
            font=ctk.CTkFont(size=14, weight="bold")  
        ).pack(pady=(8, 3))  
        
        n_items = len(self.items_in_sale)
        tree_height = min(max(n_items, 2), 5)  # mínimo 2 filas, máximo 5
        preview_tree = ttk.Treeview(products_frame, show="headings", height=tree_height)
        preview_tree["columns"] = ("Cant.", "Producto", "Envase", "P. Unit.", "Subtotal")

        scroll_y = ttk.Scrollbar(products_frame, orient="vertical", command=preview_tree.yview)
        preview_tree.configure(yscrollcommand=scroll_y.set)
        scroll_y.pack(side="right", fill="y", padx=(0, 10))
        
        widths = [40, 280, 80, 100, 100]
        for col, w in zip(preview_tree["columns"], widths):
            preview_tree.column(col, width=w, anchor="center")
            preview_tree.heading(col, text=col)
        
        # Agregar productos (dentro del método show_sale_confirmation)
        total = 0
        for item in self.items_in_sale:
            # Manejar items con y sin observaciones
            if len(item) == 6:
                pid, name, pack, qty, price, observations = item
                product_name = f"{name}\n({observations[:50]}...)" if len(observations) > 50 else f"{name}\n({observations})"
            else:
                pid, name, pack, qty, price = item
                product_name = name
                if not product_name:
                    for tree_item in self.product_tree.get_children():
                        values = self.product_tree.item(tree_item)["values"]
                        if values[0] == pid:
                            product_name = values[1]
                            break
            
            subtotal = norm_to_2_dec(price * qty)
            total += subtotal
            
            preview_tree.insert("", "end", values=(
                qty,
                product_name,
                pack,
                f"${format_currency(price)}",
                f"${format_currency(subtotal)}"
            ))

        # Se normaliza el total
        total = norm_to_2_dec(total)
        preview_tree.pack(padx=8, pady=5, fill="x")
        
        # Frame de totales
        totals_frame = ctk.CTkFrame(scroll_frame, fg_color="#e8f5e9")
        totals_frame.pack(padx=15, pady=5, fill="x")

        # Cantidad total de items
        total_items = sum(item[3] for item in self.items_in_sale)

        ctk.CTkLabel(
            totals_frame,
            text=f"Total de productos: {len(self.items_in_sale)} | Total de unidades: {total_items}",
            font=ctk.CTkFont(size=12)
        ).pack(pady=(8, 3))

        # Desglose neto + IVA por alícuota
        total_neto = Decimal('0.00')
        iva_breakdown = {}  # { "21.0": Decimal, ... }

        for item in self.items_in_sale:
            if len(item) == 6:
                pid, _, _, qty, price, _ = item
            else:
                pid, _, _, qty, price = item

            qty_d   = Decimal(str(qty))
            price_d = Decimal(str(price))

            try:
                product = self.stock_model.get_product_by_id(pid)
                iva_pct = Decimal(str(product[8])) if product and product[8] else Decimal('0.00')
            except Exception:
                iva_pct = Decimal('0.00')

            divisor   = Decimal('1') + iva_pct / Decimal('100')
            net_unit  = price_d / divisor
            line_net  = norm_to_2_dec(net_unit * qty_d)
            line_iva  = norm_to_2_dec(net_unit * qty_d * (iva_pct / Decimal('100')))

            total_neto += line_net

            key = f"{iva_pct}"
            if key not in iva_breakdown:
                iva_breakdown[key] = Decimal('0.00')
            iva_breakdown[key] += line_iva

        total_neto = norm_to_2_dec(total_neto)

        # Separador
        sep_frame = ctk.CTkFrame(totals_frame, fg_color="#c8e6c9", height=1)
        sep_frame.pack(fill="x", padx=15, pady=(4, 0))

        # Subtotal neto
        neto_frame = ctk.CTkFrame(totals_frame, fg_color="transparent")
        neto_frame.pack(fill="x", padx=20, pady=(4, 0))
        ctk.CTkLabel(neto_frame, text="Subtotal neto:",
                     font=ctk.CTkFont(size=12)).pack(side="left")
        ctk.CTkLabel(neto_frame, text=f"${format_currency(total_neto)}",
                     font=ctk.CTkFont(size=12)).pack(side="right")

        # IVA por alícuota
        for pct_key in sorted(iva_breakdown.keys(), key=lambda x: Decimal(x), reverse=True):
            iva_val = norm_to_2_dec(iva_breakdown[pct_key])
            if iva_val == Decimal('0.00'):
                continue
            pct_f = Decimal(pct_key)
            label = f"IVA {pct_f}%:" if pct_f > 0 else "Exento:"
            iva_row = ctk.CTkFrame(totals_frame, fg_color="transparent")
            iva_row.pack(fill="x", padx=20, pady=1)
            ctk.CTkLabel(iva_row, text=label,
                         font=ctk.CTkFont(size=12)).pack(side="left")
            ctk.CTkLabel(iva_row, text=f"${format_currency(iva_val)}",
                         font=ctk.CTkFont(size=12)).pack(side="right")

        # Retenciones (si aplica)
        retenciones = self.get_retenciones()
        total_ret = Decimal('0.00')
        if retenciones:
            sep2 = ctk.CTkFrame(totals_frame, fg_color="#c8e6c9", height=1)
            sep2.pack(fill="x", padx=15, pady=(4, 0))
            for concepto, monto in [
                ("Ret. IVA:", retenciones.get('IVA', 0)),
                ("Ret. IIBB:", retenciones.get('IIBB', 0)),
                ("Ret. Ganancias:", retenciones.get('GAN', 0)),
            ]:
                monto_d = norm_to_2_dec(Decimal(str(monto)))
                if monto_d > Decimal('0.00'):
                    total_ret += monto_d
                    ret_row = ctk.CTkFrame(totals_frame, fg_color="transparent")
                    ret_row.pack(fill="x", padx=20, pady=1)
                    ctk.CTkLabel(ret_row, text=concepto,
                                 font=ctk.CTkFont(size=12),
                                 text_color="#c62828").pack(side="left")
                    ctk.CTkLabel(ret_row, text=f"-${format_currency(monto_d)}",
                                 font=ctk.CTkFont(size=12),
                                 text_color="#c62828").pack(side="right")

        # Separador final
        sep3 = ctk.CTkFrame(totals_frame, fg_color="#388e3c", height=2)
        sep3.pack(fill="x", padx=15, pady=(6, 0))

        # Total a pagar (descontando retenciones)
        total_a_pagar = norm_to_2_dec(total - total_ret)

        total_row = ctk.CTkFrame(totals_frame, fg_color="transparent")
        total_row.pack(fill="x", padx=20, pady=(4, 10))
        ctk.CTkLabel(total_row,
                     text="TOTAL A PAGAR:",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#2e7d32").pack(side="left")
        ctk.CTkLabel(total_row,
                     text=f"${format_currency(total_a_pagar)}",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#2e7d32").pack(side="right")
        
        # Variable para capturar la respuesta
        result = {"confirmed": False}
        
        # Frame de botones
        button_frame = ctk.CTkFrame(confirm_win, fg_color="transparent")
        button_frame.pack(pady=10, side="bottom")
        
        def confirm():
            result["confirmed"] = True
            confirm_win.destroy()
        
        def cancel():
            result["confirmed"] = False
            confirm_win.destroy()
        
        confirm_btn = ctk.CTkButton(
            button_frame,
            text="Confirmar y Procesar",
            width=200,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#4CAF50",
            hover_color="#45a049",
            command=confirm
        )
        confirm_btn.grid(row=0, column=0, padx=10)
        confirm_win.bind("<Return>", lambda event: confirm_btn.invoke())
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancelar",
            width=150,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#757575",
            hover_color="#616161",
            command=cancel
        )
        cancel_btn.grid(row=0, column=1, padx=10)
        center_window(confirm_win, 800, 700)

        # Esperar a que se cierre la ventana
        confirm_win.deiconify()
        confirm_win.wait_window()
        
        return result["confirmed"]
    
    def open_sales_query_window(self):
        """Ventana completa de consulta de ventas con filtros por fecha"""
        width_win = 1000
        height_win = 720
        
        win = ctk.CTkToplevel(self.frame)
        win.title("Consulta de Ventas")
        win.transient(self.frame)
        win.grab_set()
        center_window(win, width_win, height_win)

        # ================================================================
        # HEADER
        # ================================================================
        header = ctk.CTkFrame(win, fg_color="#009688", height=60, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="📊 Consulta de Ventas",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        ).pack(side="left", padx=20, pady=15)

        # ================================================================
        # PANEL DE FILTROS
        # ================================================================
        filter_frame = ctk.CTkFrame(win, fg_color="#f5f5f5", corner_radius=10)
        filter_frame.pack(fill="x", padx=15, pady=10)

        # Variables para filtros
        fecha_desde_var = tk.StringVar(value=iso_to_traditional((datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")))
        fecha_hasta_var = tk.StringVar(value=iso_to_traditional(datetime.now().strftime("%Y-%m-%d")))
        estado_var = tk.StringVar(value="Todos")

        # --- Fila 1: Fechas ---
        row1 = ctk.CTkFrame(filter_frame, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(
            row1,
            text="Desde:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(0, 5))

        fecha_desde_entry = DateEntry(
            row1,
            textvariable=fecha_desde_var,
            width=12,
            background='#009688',
            foreground='white',
            borderwidth=2,
            date_pattern='dd/mm/yyyy'
        )
        fecha_desde_entry.pack(side="left", padx=5)

        ctk.CTkLabel(
            row1,
            text="Hasta:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(15, 5))

        fecha_hasta_entry = DateEntry(
            row1,
            textvariable=fecha_hasta_var,
            width=12,
            background='#009688',
            foreground='white',
            borderwidth=2,
            date_pattern='dd/mm/yyyy'
        )
        fecha_hasta_entry.pack(side="left", padx=5)

        # Botones de rangos rápidos
        quick_btns = ctk.CTkFrame(row1, fg_color="transparent")
        quick_btns.pack(side="left", padx=20)

        def set_today():
            hoy = datetime.now().strftime("%d/%m/%Y")
            fecha_desde_var.set(hoy)
            fecha_hasta_var.set(hoy)
            fecha_desde_entry.set_date(datetime.now())
            fecha_hasta_entry.set_date(datetime.now())
            load_sales()

        def set_this_week():
            hoy = datetime.now()
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            fecha_desde_var.set(inicio_semana.strftime("%d/%m/%Y"))
            fecha_hasta_var.set(hoy.strftime("%d/%m/%Y"))
            fecha_desde_entry.set_date(inicio_semana)
            fecha_hasta_entry.set_date(hoy)
            load_sales()

        def set_this_month():
            hoy = datetime.now()
            inicio_mes = hoy.replace(day=1)
            fecha_desde_var.set(inicio_mes.strftime("%d/%m/%Y"))
            fecha_hasta_var.set(hoy.strftime("%d/%m/%Y"))
            fecha_desde_entry.set_date(inicio_mes)
            fecha_hasta_entry.set_date(hoy)
            load_sales()

        ctk.CTkButton(
            quick_btns, text="Hoy", width=60, height=28,
            fg_color="#2196F3", hover_color="#1976D2",
            command=set_today
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            quick_btns, text="Semana", width=60, height=28,
            fg_color="#2196F3", hover_color="#1976D2",
            command=set_this_week
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            quick_btns, text="Mes", width=60, height=28,
            fg_color="#2196F3", hover_color="#1976D2",
            command=set_this_month
        ).pack(side="left", padx=2)

        # --- Fila 2: Filtro de estado ---
        row2 = ctk.CTkFrame(filter_frame, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(
            row2,
            text="Estado:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(0, 5))

        estado_combo = ctk.CTkComboBox(
            row2,
            variable=estado_var,
            values=["Todos", "Pagada", "Pendiente", "Parcial"],
            width=120,
            height=32,
            state="readonly"
        )
        estado_combo.pack(side="left", padx=5)

        # Botón consultar
        ctk.CTkButton(
            row2,
            text="🔍 Consultar",
            width=130,
            height=35,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#009688",
            hover_color="#00796B",
            command=lambda: load_sales()
        ).pack(side="left", padx=20)

        # ================================================================
        # RESUMEN DE RESULTADOS
        # ================================================================
        summary_frame = ctk.CTkFrame(win, fg_color="transparent")
        summary_frame.pack(fill="x", padx=15, pady=5)

        summary_label = ctk.CTkLabel(
            summary_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#666666"
        )
        summary_label.pack(side="left", padx=10)

        total_label = ctk.CTkLabel(
            summary_frame,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#009688"
        )
        total_label.pack(side="right", padx=10)

        # ================================================================
        # TABLA DE RESULTADOS
        # ================================================================
        table_frame = ctk.CTkFrame(win)
        table_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # Estilo
        style = ttk.Style()
        style.configure(
            "Sales.Treeview",
            rowheight=20,
            font=("Segoe UI", 8)
        )
        style.configure(
            "Sales.Treeview.Heading",
            font=("Segoe UI", 9, "bold")
        )

        cols = ("ID", "Fecha", "Hora", "Cliente", "Estado", "Total", "Pagado", "Saldo")
        sales_tree = ttk.Treeview(
            table_frame,
            columns=cols,
            show="headings",
            height=15,
            style="Sales.Treeview"
        )

        column_widths = {
            "ID": 50,
            "Fecha": 90,
            "Hora": 70,
            "Cliente": 160,
            "Estado": 100,
            "Total": 110,
            "Pagado": 110,
            "Saldo": 110
        }

        for col in cols:
            anchor = "w" if col == "Cliente" else "center"
            stretch = True if col == "Cliente" else False

            sales_tree.heading(col, text=col, anchor="center")
            sales_tree.column(col, width=column_widths[col], anchor=anchor, stretch=stretch)

        # Scrollbar
        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=sales_tree.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=sales_tree.xview)
        sales_tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        sales_tree.pack(fill="both", expand=True)

        # Tags para colores
        sales_tree.tag_configure("paid", background="#E8F5E9")
        sales_tree.tag_configure("pending", background="#FFEBEE")
        sales_tree.tag_configure("partial", background="#FFF3E0")

        # ================================================================
        # FUNCIÓN PARA CARGAR VENTAS
        # ================================================================
        def load_sales():
            """Cargar ventas según filtros"""
            try:
                # Limpiar tabla
                for item in sales_tree.get_children():
                    sales_tree.delete(item)

                # Obtener filtros
                fecha_desde = traditional_to_iso(fecha_desde_var.get())
                fecha_hasta = traditional_to_iso(fecha_hasta_var.get())
                estado = estado_var.get()

                # Mapeo de estados
                estado_filter = None
                if estado == "Pagada":
                    estado_filter = "paid"
                elif estado == "Pendiente":
                    estado_filter = "pending"
                elif estado == "Parcial":
                    estado_filter = "partial"

                # Obtener ventas desde el controlador
                ventas = self.controller.get_sales_by_date_range(
                    fecha_desde, fecha_hasta, estado_filter
                )

                # Llenar tabla
                total_ventas = Decimal('0.00')
                total_pagado = Decimal('0.00')
                total_saldo = Decimal('0.00')

                for venta in ventas:
                    sale_id, fecha, total, cliente_nombre, estado_venta, pagado = venta
                    
                    total_d = Decimal(total)
                    pagado_d = Decimal(pagado)

                    # Si la venta está pagada y no tiene registro de cobro posterior
                    # (contado), el monto pagado es el total
                    if estado_venta == 'paid' and pagado_d == Decimal('0.00'):
                        pagado_d = total_d

                    # Calcular saldo
                    saldo = total_d - pagado_d
                    
                    # Formatear fecha y hora
                    try:
                        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S")
                        fecha_str = fecha_dt.strftime("%d/%m/%Y")
                        hora_str = fecha_dt.strftime("%H:%M")
                    except:
                        fecha_str = fecha[:10] if len(fecha) >= 10 else fecha
                        hora_str = fecha[11:16] if len(fecha) >= 16 else ""
                    
                    # Estado en español
                    estado_texto = {
                        "paid": "Pagada",
                        "pending": "Pendiente",
                        "partial": "Parcial"
                    }.get(estado_venta, estado_venta.upper())
                    
                    # Tag según estado
                    tag = estado_venta if estado_venta in ["paid", "pending", "partial"] else ""
                    
                    sales_tree.insert("", "end", values=(
                        sale_id,
                        fecha_str,
                        hora_str,
                        cliente_nombre if cliente_nombre else "Consumidor Final",
                        estado_texto,
                        f"${format_currency(total_d)}",
                        f"${format_currency(pagado_d)}",
                        f"${format_currency(saldo)}"
                    ), tags=(tag,))
                    
                    total_ventas += total_d
                    total_pagado += pagado_d
                    total_saldo += saldo

                # Actualizar resumen
                summary_label.configure(
                    text=f"📊 {len(ventas)} ventas encontradas"
                )
                total_label.configure(
                    text=f"Total: ${format_currency(total_ventas)} | Pagado: ${format_currency(total_pagado)}" \
                         f" | Saldo: ${format_currency(total_saldo)}"
                )

            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar ventas: {e}")

        # ================================================================
        # BOTONES INFERIORES
        # ================================================================
        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=15)

        def export_results():
            """Exportar resultados a PDF"""
            if len(sales_tree.get_children()) == 0:
                messagebox.showwarning("Advertencia", "No hay ventas para exportar")
                return
            
            # Recopilar datos de la tabla
            ventas_export = []
            for item in sales_tree.get_children():
                ventas_export.append(sales_tree.item(item)["values"])
            
            # Llamar al método de exportación existente
            self.export_sales_day(ventas_export, fecha_desde_var.get(), fecha_hasta_var.get())

        ctk.CTkButton(
            btn_frame,
            text="📄 Exportar PDF",
            width=180,
            height=40,
            fg_color="#FF9800",
            hover_color="#F57C00",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=export_results
        ).grid(row=0, column=0, padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Cerrar",
            width=150,
            height=40,
            fg_color="#757575",
            hover_color="#616161",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=win.destroy
        ).grid(row=0, column=1, padx=10)

        # Cargar ventas inicialmente (último mes)
        load_sales()

    def process_sale_with_confirmation(self):
        """Procesar venta con confirmación previa"""
        if self.show_sale_confirmation():
            # Si el usuario confirma, proceder con la venta
            self.controller.confirm_sale()

    # Client Selector
    def create_client_section(self):
        """Sección de cliente MEJORADA con retenciones"""
        client_frame = ctk.CTkFrame(self.frame, fg_color="#fafafa")
        client_frame.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

        # --- Cliente con botón de búsqueda ---
        ctk.CTkLabel(
            client_frame, 
            text="Cliente:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Frame para entry + botón
        client_select_frame = ctk.CTkFrame(client_frame, fg_color="transparent")
        client_select_frame.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.client_var = tk.StringVar(value="")
        self.client_entry = ctk.CTkEntry(
            client_select_frame,
            textvariable=self.client_var,
            width=200,
            height=35,
            state="readonly"
        )
        self.client_entry.grid(row=0, column=0, padx=(0, 5))

        search_client_btn = ctk.CTkButton(
            client_select_frame,
            text="🔍 Buscar",
            width=120,
            height=35,
            fg_color="#009688",
            hover_color="#00796B",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.open_client_selector
        )
        search_client_btn.grid(row=0, column=1)

        # --- CUIT / DNI ---
        ctk.CTkLabel(
            client_frame, 
            text="CUIT / DNI:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.client_cuit_var = tk.StringVar()
        ctk.CTkEntry(
            client_frame, 
            textvariable=self.client_cuit_var,
            width=250, 
            height=35, 
            state="disabled"
        ).grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # --- Dirección ---
        ctk.CTkLabel(
            client_frame, 
            text="Dirección:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        self.client_address_var = tk.StringVar()
        ctk.CTkEntry(
            client_frame, 
            textvariable=self.client_address_var,
            width=250, 
            height=35, 
            state="disabled"
        ).grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # --- Condición IVA ---
        ctk.CTkLabel(
            client_frame,
            text="Cond. IVA:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=3, column=0, padx=10, pady=5, sticky="w")

        self.client_iva_var = tk.StringVar()
        ctk.CTkEntry(
            client_frame,
            textvariable=self.client_iva_var,
            width=250,
            height=35,
            state="disabled"
        ).grid(row=3, column=1, padx=10, pady=5, sticky="w")

        # --- Forma de pago ---
        ctk.CTkLabel(
            client_frame, 
            text="Forma de pago:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=4, column=0, padx=10, pady=10, sticky="w")

        self.payment_type_var = tk.StringVar(value="PAID")

        payment_frame = ctk.CTkFrame(client_frame, fg_color="transparent")
        payment_frame.grid(row=4, column=1, padx=10, pady=10, sticky="w")

        self.radio_paid = ctk.CTkRadioButton(
            payment_frame,
            text="Pagada",
            variable=self.payment_type_var,
            value="PAID"
        )
        self.radio_paid.grid(row=0, column=0, padx=(0, 15))

        self.radio_credit = ctk.CTkRadioButton(
            payment_frame,
            text="Cuenta Corriente",
            variable=self.payment_type_var,
            value="CREDIT"
        )
        self.radio_credit.grid(row=0, column=1)
        
        # Checkbox para mostrar/ocultar retenciones
        self.tiene_retenciones_var = tk.BooleanVar(value=False)
        retenciones_check = ctk.CTkCheckBox(
            client_frame,
            text="El cliente realiza retenciones",
            variable=self.tiene_retenciones_var,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.open_retenciones_dialog
        )
        retenciones_check.grid(row=5, column=0, columnspan=2, padx=10, pady=(15, 5), sticky="w")

    def get_retenciones(self):
        """Obtener datos de retenciones del formulario"""
        if not self.tiene_retenciones_var.get():
            return None
        
        try:
            return {
                'IVA': string_to_2_dec(self.retencion_iva_var.get() or string_to_2_dec("0")),
                'IIBB': string_to_2_dec(self.retencion_iibb_var.get() or string_to_2_dec("0")),
                'GAN': string_to_2_dec(self.retencion_ganancias_var.get() or string_to_2_dec("0")),
                'certificado': self.certificado_var.get().strip()
            }
        except ValueError:
            self.show_error("Ingrese valores numéricos válidos para las retenciones")
            return None
        
    def open_client_selector(self):
        """Abrir diálogo de selección de cliente"""        
        
        dialog = ClientSelectorDialog(
            self.frame, 
            self.customer_model,
            self.client_var.get()
        )
        
        selected = dialog.get_selected()
        
        if selected:
            self.client_var.set(selected)
            self.on_client_selected(selected)
    
    def on_client_selected(self, selected_name):
        try:
            if selected_name == "Consumidor Final":
                self.client_cuit_var.set("")
                self.client_address_var.set("")
                self.client_iva_var.set("Consumidor Final")

                # Forzar Pagada
                self.payment_type_var.set("PAID")

                # Deshabilitar Fiada
                self.radio_credit.configure(state="disabled")
                return

            # Cliente normal
            self.radio_credit.configure(state="normal")

            client_data = self.customer_model.get_client_by_name(selected_name)

            if client_data:
                self.client_cuit_var.set(client_data[2] or "")
                self.client_address_var.set(client_data[3] or "")
                self.client_iva_var.set(client_data[4] or "")
            else:
                self.client_cuit_var.set("")
                self.client_address_var.set("")
                self.client_iva_var.set("")

        except Exception as e:
            self.show_error(f"No se pudieron cargar los datos del cliente: {e}")

    def add_honorarios(self):
        """Abrir diálogo para agregar honorarios"""
        # Buscar el ID del producto honorarios
        honorarios_id = self.stock_model.get_honorarios_id()
        
        if not honorarios_id:
            self.show_error("No se encontró el producto 'HONORARIOS' en el stock." \
                            "\n\nPor favor, contacte al administrador.")
            return
        
        self.show_honorarios_dialog(honorarios_id)

    def show_honorarios_dialog(self, honorarios_id):
        """Diálogo para ingresar detalles de honorarios"""
        dialog = ctk.CTkToplevel(self.frame)
        dialog.title("Agregar Honorarios")
        
        # Centrar ventana
        dialog.update_idletasks()
        dialog.transient(self.frame)
        dialog.grab_set()
        dialog.resizable(False, False)
        center_window(dialog, 500, 490)
        
        # Título
        ctk.CTkLabel(
            dialog, 
            text="💼 Honorarios Profesionales",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(15, 10))
        
        # Frame de contenido
        content_frame = ctk.CTkFrame(dialog, fg_color="#f5f5f5")
        content_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Monto
        ctk.CTkLabel(
            content_frame, 
            text="Monto del servicio:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(pady=(15, 5), anchor="w", padx=15)
        
        price_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        price_frame.pack(pady=5, padx=15, fill="x")
        
        ctk.CTkLabel(
            price_frame,
            text="$",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=(0, 5))
        
        price_var = tk.StringVar()
        price_entry = ctk.CTkEntry(
            price_frame,
            textvariable=price_var,
            width=150,
            height=35,
            font=ctk.CTkFont(size=13)
        )
        price_entry.pack(side="left")
        price_entry.focus()
        
        # Descripción del servicio
        ctk.CTkLabel(
            content_frame,
            text="Descripción del servicio prestado:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(pady=(15, 5), anchor="w", padx=15)
        
        obs_text = tk.Text(
            content_frame,
            height=8,
            width=50,
            font=("bold",12),
            wrap="word"
        )
        obs_text.pack(padx=15, pady=5)
        
        # Texto placeholder
        placeholder = """Ejemplo:
            Vacunación antiaftosa
            150 cabezas de ganado
            Campo La Esperanza - Lote 5
            Fecha: 28/01/2026"""
        
        obs_text.insert("1.0", placeholder)
        obs_text.config(fg="black")
        
        # Limpiar placeholder al hacer clic
        def clear_placeholder(event):
            if obs_text.get("1.0", tk.END).strip() == placeholder.strip():
                obs_text.delete("1.0", tk.END)
                obs_text.config(fg="black")
        
        obs_text.bind("<FocusIn>", clear_placeholder)
        
        def confirm_honorarios():
            try:
                price = string_to_2_dec(price_var.get())  # Precio que el usuario ingresa

                if price is None:
                    messagebox.showerror("Error", "Ingrese un monto válido para los honorarios")
                    return

                observations = obs_text.get("1.0", tk.END).strip()
                
                if price <= Decimal('0.00'):
                    messagebox.showwarning("Error", "El monto debe ser mayor a 0")
                    return
                
                # Agregar honorario a la venta
                self.items_in_sale.append((
                    honorarios_id, 
                    'HONORARIOS', 
                    'UNIDAD',
                    1,
                    price,           
                    observations
                ))
                self.refresh_sale_table()
                self.update_total()
                self.show_success("Honorarios agregados correctamente")
                dialog.destroy()
                
            except ValueError as e:
                messagebox.showerror("Error", f"Ingrese un monto válido (solo números) {e}")
        
        # Botones
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=15)
        
        ctk.CTkButton(
            button_frame,
            text="✓ Agregar",
            width=150,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#4CAF50",
            hover_color="#45a049",
            command=confirm_honorarios
        ).grid(row=0, column=0, padx=10)
        
        ctk.CTkButton(
            button_frame,
            text="✗ Cancelar",
            width=150,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#757575",
            hover_color="#616161",
            command=dialog.destroy
        ).grid(row=0, column=1, padx=10)

    def open_retenciones_dialog(self):
        if not self.tiene_retenciones_var.get():
            return

        win = ctk.CTkToplevel(self.frame)
        win.title("Retenciones")
        win.transient(self.frame)
        win.grab_set()
        win.resizable(False, False)

        center_window(win, 350, 280)

        ctk.CTkLabel(
            win,
            text="Retenciones del Cliente",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)

        form = ctk.CTkFrame(win)
        form.pack(padx=2, pady=10, fill="both")

        # IVA
        ctk.CTkLabel(form, text="Retención IVA:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, padx=10 ,pady=5, sticky="w")
        self.retencion_iva_var = tk.StringVar(value="0")
        ctk.CTkEntry(form, textvariable=self.retencion_iva_var, width=120).grid(row=0, column=1,pady=5, sticky="ew")

        # IIBB
        ctk.CTkLabel(form, text="Retención IIBB:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=1, column=0, padx=10,pady=5, sticky="w")
        self.retencion_iibb_var = tk.StringVar(value="0")
        ctk.CTkEntry(form, textvariable=self.retencion_iibb_var, width=120).grid(row=1, column=1, pady=5, sticky="ew")

        # GAN
        ctk.CTkLabel(form, text="Retención Ganancias:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.retencion_ganancias_var = tk.StringVar(value="0")
        ctk.CTkEntry(form, textvariable=self.retencion_ganancias_var, width=120).grid(row=2, column=1, pady=5, sticky="ew")

        # Certificado
        ctk.CTkLabel(form, text="N° Certificado:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=3, column=0, padx=10,pady=5, sticky="w")
        self.certificado_var = tk.StringVar()
        ctk.CTkEntry(form, textvariable=self.certificado_var, width=150).grid(row=3, column=1, pady=5, sticky="ew")

        def confirm():
            win.destroy()

        btn = ctk.CTkButton(
            win,
            text="Guardar",
            width=120,
            fg_color="#4CAF50",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=confirm
        )
        btn.pack(pady=10)

    # Utilidades
    def show_success(self, msg): messagebox.showinfo("Éxito", msg)
    def show_error(self, msg): messagebox.showerror("Error", msg)
    def show_warning(self, msg): messagebox.showwarning("Advertencia", msg)
    def ask_confirmation(self, message):
        """Preguntar confirmación al usuario"""
        return messagebox.askquestion("Confirmación", message) == 'yes'