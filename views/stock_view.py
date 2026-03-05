import tkinter as tk
import customtkinter as ctk
import csv
import os
from datetime import datetime
from decimal import Decimal
from models.stock import StockModel
from tkinter import ttk, messagebox, filedialog
from utils.view_helpers import center_window, close_win, show_error
from utils.utils import iso_to_traditional, format_currency, string_to_2_dec, string_to_flex_dec, norm_to_2_dec, flex_dec
from views.stock_movement_view import StockMovementView
from models.stock_movement import StockMovementModel

# Configurar tema y colores
ctk.set_appearance_mode("light")  # "light" o "dark"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class StockView():
    def __init__(self, parent, controller, stock_model):
        self.controller = controller
        self.frame = ctk.CTkFrame(parent, fg_color="#f0f0f0")
        self.stock_model = stock_model
        self.movement_view = StockMovementView(StockMovementModel())
        self.create_widgets()
        self.edit_item = None
        self.edit_entry = None
        self.edit_column = None
        self.original_value = None

        self.sort_column = None
        self.sort_reverse = False

    def create_widgets(self):
        """Crear todos los widgets de la vista"""
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=0)  # search bar
        self.frame.grid_rowconfigure(1, weight=0)  # stats bar
        self.frame.grid_rowconfigure(2, weight=1)  # table
        self.frame.grid_rowconfigure(3, weight=0)  # buttons
        self.create_find_frame()
        self.create_stats_frame()
        self.create_tree_frame()
        self.create_buttons_frame()
    
    def create_buttons_frame(self):
        """Crear frame para botones de stock"""
        manage_frame = ctk.CTkFrame(self.frame)
        manage_frame.grid(row=3, column=0, padx=10, pady=20, sticky="ew")
        manage_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        W = 250
        H = 40
        btn_color = "#009688"
        btn_hover = "#00796B"

        update_btn = ctk.CTkButton(
            manage_frame,
            text="✏️ Actualizar precio",
            width=W, height=H,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=btn_color, hover_color=btn_hover,
            command=lambda: self.open_update_price_window(manage_frame)
        )

        delete_btn = ctk.CTkButton(
            manage_frame,
            text="🗑️ Eliminar producto",
            width=W, height=H,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=btn_color, hover_color=btn_hover,
            command=lambda: self.controller.delete_product()
        )

        bulk_update_btn = ctk.CTkButton(
            manage_frame,
            text="📈 Actualización masiva",
            width=W, height=H,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=btn_color, hover_color=btn_hover,
            command=lambda: self.open_bulk_update_window()
        )

        edit_btn = ctk.CTkButton(
            manage_frame,
            text="✏️ Editar producto",
            width=W, height=H,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=btn_color, hover_color=btn_hover,
            command=self.open_edit_product_window
        )

        export_btn = ctk.CTkButton(
            manage_frame,
            text="📤 Exportar CSV",
            width=W, height=H,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#5C6BC0", hover_color="#3949AB",
            command=self.export_to_csv
        )

        delete_btn.grid(row=1, column=0, padx=10, pady=10)
        update_btn.grid(row=1, column=1, padx=10, pady=10)
        bulk_update_btn.grid(row=1, column=2, padx=10, pady=10)
        edit_btn.grid(row=1, column=3, padx=10, pady=10)
        export_btn.grid(row=1, column=4, padx=10, pady=10)

    
    def create_find_frame(self):
        """Crear frame para formulario de producto"""
        self.find_var = tk.StringVar()
        btn_color = "#009688"
        btn_hover = "#00796B"
        W = 150
        H = 35

        find_frame = ctk.CTkFrame(self.frame)
        find_frame.grid(row=0, column=0, sticky='w', padx=10, pady=10)

        search_label = ctk.CTkLabel(
            find_frame,
            text='🔍 Buscar producto:',
            font=ctk.CTkFont(size=14, weight="bold")
        )
        search_label.grid(row=0, column=0, padx=15, pady=15)

        find_entry = ctk.CTkEntry(
            find_frame,
            width=600,
            height=35,
            textvariable=self.find_var,
            font=ctk.CTkFont(size=12),
            placeholder_text="Ingrese nombre del producto..."
        )
        
        find_entry.grid(row=0, column=1, padx=10, pady=15)
        find_entry.bind("<KeyRelease>", lambda event: self.controller.find_product_live(self.find_var.get()))

        history_btn = ctk.CTkButton(
            find_frame,
            text="📋 Historial Global",
            width=W, height=H,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=btn_color, hover_color=btn_hover,
            command=lambda: self.movement_view.open(self.frame)
        )
        history_btn.grid(row=0, column=2, padx=15, pady=15)

        history_product_btn = ctk.CTkButton(
            find_frame,
            text="📋 Historial Producto",
            width=W, height=H,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=btn_color, hover_color=btn_hover,
            command=self._open_product_history
        )
        history_product_btn.grid(row=0, column=3, padx=15, pady=15)

    def create_stats_frame(self):
        """Barra de estadísticas rápidas del inventario"""
        self.stats_frame = ctk.CTkFrame(self.frame, fg_color="#f8f8f8", corner_radius=8)
        self.stats_frame.grid(row=1, column=0, padx=10, pady=(0, 4), sticky="ew")

        # 4 cards: total productos, stock bajo, sin stock, valor inventario
        for i in range(4):
            self.stats_frame.grid_columnconfigure(i, weight=1)

        def make_card(col, icon, label, var, color):
            card = ctk.CTkFrame(self.stats_frame, fg_color="white", corner_radius=8)
            card.grid(row=0, column=col, padx=8, pady=8, sticky="ew")
            ctk.CTkLabel(card, text=f"{icon}  {label}",
                         font=ctk.CTkFont(size=11), text_color="#757575").pack(pady=(8, 0))
            ctk.CTkLabel(card, textvariable=var,
                         font=ctk.CTkFont(size=18, weight="bold"),
                         text_color=color).pack(pady=(2, 8))

        self._stat_total     = tk.StringVar(value="—")
        self._stat_low       = tk.StringVar(value="—")
        self._stat_no_stock  = tk.StringVar(value="—")
        self._stat_value     = tk.StringVar(value="—")

        make_card(0, "📦", "Total productos",    self._stat_total,    "#1565C0")
        make_card(1, "⚠️",  "Stock bajo (< 3)",  self._stat_low,     "#E65100")
        make_card(2, "❌", "Sin stock",           self._stat_no_stock, "#C62828")
        make_card(3, "💰", "Valor inventario",   self._stat_value,    "#2E7D32")

    def update_stats(self, products):
        """Recalcular las estadísticas a partir de la lista de productos visible."""
        if not products:
            self._stat_total.set("0")
            self._stat_low.set("0")
            self._stat_no_stock.set("0")
            self._stat_value.set("$0,00")
            return

        total     = len(products)
        low       = sum(1 for p in products if 0 < float(p[12] or 0) < 3)
        no_stock  = sum(1 for p in products if float(p[12] or 0) == 0)
        try:
            valor = sum(
                float(p[5] or 0) * float(p[12] or 0)   # cost_price * quantity
                for p in products
            )
            valor_fmt = f"${valor:,.0f}".replace(",", ".")
        except Exception:
            valor_fmt = "—"

        self._stat_total.set(str(total))
        self._stat_low.set(str(low))
        self._stat_no_stock.set(str(no_stock))
        self._stat_value.set(valor_fmt)

    def create_tree_frame(self):
        """Crear frame para tabla de stock"""
        tree_frame = ctk.CTkFrame(self.frame)
        tree_frame.grid(row=2, column=0, padx=10, pady=10, sticky='nsew')
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(1,weight=1)

        # Título de la tabla
        table_title = ctk.CTkLabel(
            tree_frame,
            text="Inventario de Productos",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        table_title.grid(row=0, column=0, pady=(15, 10))

        # Frame interno para la tabla y scrollbar
        table_container = tk.Frame(tree_frame, bg="white")
        table_container.grid(row=1, column=0, padx=15, pady=(0, 15), sticky='nsew')
        table_container.grid_columnconfigure(0, weight=1)
        table_container.grid_rowconfigure(0, weight=1)

        # Configurar el estilo del Treeview para que se vea más moderno
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar colores del Treeview
        style.configure('Treeview',
                       background='#ffffff',
                       foreground='#ffffff',
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
        self.stock_tree = ttk.Treeview(table_container, show="headings", height=20)
        self.stock_tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbar vertical con estilo
        scrollbar = ttk.Scrollbar(table_container, orient='vertical', command=self.stock_tree.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.stock_tree.configure(yscrollcommand=scrollbar.set)

        self.stock_tree['columns'] = (
            "Id", "Name", "Package", "ListPrice", "Discount", "CostPrice", "Profit", 
            "SalePrice", "Iva", "SalePriceWithIva", "ValidityDate", "LastPriceUpdate", "Stock"
        )

        self.stock_tree['displaycolumns'] = self.stock_tree['columns']

        # Definición de columnas
        self.stock_tree.column("Id", anchor=tk.W, width=60, stretch=False)
        self.stock_tree.column("Name", anchor=tk.W, width=250, stretch=True)
        self.stock_tree.column("Package", anchor=tk.W, width=120, stretch=True)
        self.stock_tree.column("ListPrice", anchor=tk.E, width=100, stretch=True)
        self.stock_tree.column("Discount", anchor=tk.E, width=100, stretch=True)
        self.stock_tree.column("CostPrice", anchor=tk.E, width=100, stretch=True)
        self.stock_tree.column("Profit", anchor=tk.CENTER, width=80, stretch=False)
        self.stock_tree.column("SalePrice", anchor=tk.E, width=100, stretch=True)
        self.stock_tree.column("Iva", anchor=tk.CENTER, width=60, stretch=False)
        self.stock_tree.column("SalePriceWithIva", anchor=tk.E, width=120, stretch=True)
        self.stock_tree.column("ValidityDate", anchor=tk.CENTER, width=100, stretch=True)
        self.stock_tree.column("LastPriceUpdate", anchor=tk.CENTER, width=100, stretch=True)
        self.stock_tree.column("Stock", anchor=tk.CENTER, width=80, stretch=False)

        # Encabezados
        self.stock_tree.heading("Id", text="Cód.", anchor=tk.W,
                                command=lambda: self.sort_tree("Id"))
        self.stock_tree.heading("Name", text="Nombre Artículo", anchor=tk.W,
                                command=lambda: self.sort_tree("Name"))
        self.stock_tree.heading("Package", text="Envase", anchor=tk.W,
                                command=lambda: self.sort_tree("Package"))
        self.stock_tree.heading("ListPrice", text="P. Lista", anchor=tk.E,
                                command=lambda: self.sort_tree("ListPrice"))
        self.stock_tree.heading("Discount", text="% Dto.", anchor=tk.E,
                                command=lambda: self.sort_tree("Discount"))                
        self.stock_tree.heading("CostPrice", text="P. Costo", anchor=tk.E,
                                command=lambda: self.sort_tree("CostPrice"))
        self.stock_tree.heading("Profit", text="% Rent.", anchor=tk.CENTER,
                                command=lambda: self.sort_tree("Profit"))
        self.stock_tree.heading("SalePrice", text="P. Venta", anchor=tk.E,
                                command=lambda: self.sort_tree("SalePrice"))
        self.stock_tree.heading("Iva", text="% Iva", anchor=tk.CENTER,
                                command=lambda: self.sort_tree("Iva"))
        self.stock_tree.heading("SalePriceWithIva", text="P. Venta C/Iva", anchor=tk.E,
                                command=lambda: self.sort_tree("SalePriceWithIva"))
        self.stock_tree.heading("ValidityDate", text="Fecha Vig.", anchor=tk.CENTER,
                                command=lambda: self.sort_tree("ValidityDate"))
        self.stock_tree.heading("LastPriceUpdate", text="F. Ult. Modif.", anchor=tk.CENTER,
                                command=lambda: self.sort_tree("LastPriceUpdate"))
        self.stock_tree.heading("Stock", text="Stock", anchor=tk.CENTER,
                                command=lambda: self.sort_tree("Stock"))
        
        # Bind para doble click
        self.stock_tree.bind('<Double-Button-1>', self.on_double_click)
        # Bind para Enter y Escape
        self.stock_tree.bind('<Return>', self.save_edit)
        self.stock_tree.bind('<Escape>', self.cancel_edit)

        # Tags para colores de filas
        self.stock_tree.tag_configure('orow', background="#FFFFFF")
        self.stock_tree.tag_configure("low_stock", background="#ffebee")   # rojo muy suave
        self.stock_tree.tag_configure("medium_stock", background="#fff3e0") # naranja muy suave

        self.stock_tree.grid(row=0, column=0, sticky="nsew")

    def open_update_price_window(self, parent):
        """Abrir ventana para actualizar precio de producto seleccionado"""
        try:
            product_id = self.get_selected_product()
            if not product_id:
                self.show_warning("Seleccione un producto para actualizar el precio")
                return
                    
            product = self.stock_model.get_product_by_id(product_id)
            if not product:
                self.show_error(f"Producto {product_id} no encontrado")
                return

            _, name, _, profit, _, _, cost_price, _, iva, _, _, _, _ = product

            window = ctk.CTkToplevel(self.frame)
            window.title(f"Actualizar Precio - {name}")
            window.transient(parent)
            window.grab_set()
            center_window(window, 550, 480)

            # Información básica
            info_label = ctk.CTkLabel(
                window, 
                text=f"Producto: {name} | Código: {product_id} \n" \
                    f"Costo Real: ${cost_price} | Costo Final: ${norm_to_2_dec(cost_price)} ",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            info_label.pack(pady=20)

            main_frame = ctk.CTkFrame(window)
            main_frame.pack(padx=20, pady=10, fill="both", expand=True)

            method_label = ctk.CTkLabel(main_frame, text="Método:", font=ctk.CTkFont(size=16, weight="bold"))
            method_label.pack(pady=(15, 5))

            method_var = tk.StringVar(value="cost_price")
            
            # Opciones
            cost_radio = ctk.CTkRadioButton(main_frame, text="Por Precio de Costo", variable=method_var, value="cost_price")
            cost_radio.pack(pady=2)
            
            profit_radio = ctk.CTkRadioButton(main_frame, text="Por Rentabilidad (%)", variable=method_var, value="profit")
            profit_radio.pack(pady=2)

            # Campos de entrada
            input_frame = ctk.CTkFrame(main_frame, bg_color="gray38")
            input_frame.pack(pady=15, padx=20, fill="x")

            cost_var = tk.StringVar(value=cost_price)
            profit_var = tk.StringVar(value=profit)

            # Precio Costo
            cost_label = ctk.CTkLabel(input_frame, text="Precio de Costo:")
            cost_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            
            cost_entry = ctk.CTkEntry(input_frame, textvariable=cost_var, width=150)
            cost_entry.grid(row=0, column=1, padx=10, pady=10)

            # Rentabilidad
            profit_label = ctk.CTkLabel(input_frame, text="Rentabilidad (%):")
            profit_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
            
            profit_entry = ctk.CTkEntry(input_frame, textvariable=profit_var, width=150)
            profit_entry.grid(row=1, column=1, padx=10, pady=10)

            result_var = tk.StringVar()
            result_label = ctk.CTkLabel(main_frame, text="Resultado:", font=ctk.CTkFont(size=12, weight="bold"))
            result_label.pack(pady=(10, 5))
            
            result_display = ctk.CTkLabel(main_frame, textvariable=result_var, font=ctk.CTkFont(size=12))
            result_display.pack()

            def update_interface():
                method = method_var.get()
                if method == "cost_price":
                    cost_entry.configure(state="normal")
                    profit_entry.configure(state="disabled")
                    profit_var.set(profit)
                    try:
                        self.new_cost = string_to_flex_dec(cost_var.get())

                        if self.new_cost is None:
                            raise ValueError

                        self.profit = Decimal(profit)

                        profit_rate = self.profit / Decimal('100')
                        profit_amount = self.new_cost * profit_rate
                        self.new_sale_price = self.new_cost + profit_amount

                        if Decimal(iva) == Decimal('21.00'):
                            self.price_with_iva = self.new_sale_price * Decimal('1.21')
                        elif Decimal(iva) == Decimal('10.5'):
                            self.price_with_iva = self.new_sale_price * Decimal('1.105')
                        else:
                            self.price_with_iva = self.new_sale_price

                        # Normalizacion
                        self.new_sale_price = flex_dec(self.new_sale_price)
                        self.price_with_iva = flex_dec(self.price_with_iva)
                        
                        result_var.set(
                            f"Precio De Costo: ${self.new_cost} | "\
                            f"Rentabilidad: {self.profit}% \n"\
                            f"Precio De Venta: ${self.new_sale_price} | "\
                            f"Con IVA: ${self.price_with_iva}")
                        
                    except ValueError:
                        result_var.set("Valor inválido - Ingrese un número")

                else:
                    cost_entry.configure(state="disabled")
                    profit_entry.configure(state="normal")
                    cost_var.set(cost_price)
                    try:
                        
                        self.new_profit = string_to_2_dec(profit_var.get())

                        if self.new_profit is None:
                            raise ValueError

                        self.cost = Decimal(cost_price)

                        profit_rate = self.new_profit / Decimal('100')
                        profit_amount = self.cost * profit_rate
                        self.new_sale_price = self.cost + profit_amount
                        
                        if Decimal(iva) == Decimal('21.00'):
                            self.price_with_iva = self.new_sale_price * Decimal('1.21')
                        elif Decimal(iva) == Decimal('10.5'):
                            self.price_with_iva = self.new_sale_price * Decimal('1.105')
                        else:
                            self.price_with_iva = self.new_sale_price
                            
                        # Normalizacion
                        self.new_sale_price = flex_dec(self.new_sale_price)
                        self.price_with_iva = flex_dec(self.price_with_iva)

                        result_var.set(
                            f"Precio De Costo: ${self.cost} | "\
                            f"Rentabilidad: {self.new_profit}% \n"\
                            f"Precio De Venta: ${self.new_sale_price} | "\
                            f"Con IVA: ${self.price_with_iva}")
                        
                    except ValueError:
                        result_var.set("Valor inválido - Ingrese un número")

            method_var.trace('w', lambda *args: update_interface())
            cost_var.trace('w', lambda *args: update_interface() if method_var.get() == "cost_price" else None)
            profit_var.trace('w', lambda *args: update_interface() if method_var.get() == "profit" else None)

            update_interface()

            # Botones
            button_frame = ctk.CTkFrame(window, fg_color="transparent")
            button_frame.pack(pady=20)

            def save_update():
                try:

                    method = method_var.get()
                    
                    if method == "cost_price":
                        final_cost = self.new_cost
                        final_profit = self.profit 

                    else:
                        final_cost = self.cost
                        final_profit = self.new_profit 

                    # Validaciones para el precio costo
                    if final_cost is None:
                        raise ValueError('Formato incorrecto en PRECIO COSTO')

                    if final_cost <= Decimal('0.00'):
                        raise ValueError('El nuevo precio de COSTO no puede ser menor o igual a $0.00')
                    
                    # Validaciones para la rentabilidad
                    if final_profit is None:
                        raise ValueError('Formato incorrecto en RENTABILIDAD')

                    if final_profit < Decimal('0.00'):
                        raise ValueError('El nuevo porcentaje de RENTABILIDAD no puede ser un valor NEGATIVO')

                    product_data = {
                        "Profit": str(final_profit),
                        "CostPrice": str(final_cost),
                        "SalePrice": str(self.new_sale_price),
                        "PriceWIva": str(self.price_with_iva),
                    }

                    result = self.stock_model.update_p_price_and_related_sales_amount(
                        product_id, product_data)
                    if result:
                        self.controller.refresh_stock_table()
                        self.show_success("Precio actualizado correctamente")

                    else:
                        show_error('Ocurrio un error')
                    window.destroy()

                except ValueError as e:
                    self.show_error(f"Error. {e}")


            save_button = ctk.CTkButton(button_frame, text="Guardar", width=100, height=35, 
                fg_color="#4CAF50", hover_color="#45a049", command=save_update)
            save_button.pack(side="left", padx=10)

            window.bind("<Return>", lambda events: save_button.invoke())            

            cancel_button = ctk.CTkButton(button_frame, text="Cancelar", width=100, height=35, 
                fg_color="#757575", hover_color="#616161", command=window.destroy)
            cancel_button.pack(side="left", padx=10)

        except Exception as e:
            self.show_error(f"Error al abrir ventana de actualización: {str(e)}")

    def open_bulk_update_window(self):
        """Ventana para actualización masiva de precios por fecha"""
        try:
            window = ctk.CTkToplevel(self.frame)
            window.title("Actualización Masiva de Precios")
            window.grab_set()
            center_window(window, 500, 450)

            # Título
            title_label = ctk.CTkLabel(
                window, 
                text="Actualización Masiva de Precios",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title_label.pack(pady=20)

            # Frame principal
            main_frame = ctk.CTkFrame(window)
            main_frame.pack(padx=20, pady=10, fill="both", expand=True)

            # Selección de fecha
            date_label = ctk.CTkLabel(
                main_frame, 
                text="Actualizar productos con fecha de precio:",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            date_label.pack(pady=(20, 10))

            # Obtener fechas disponibles
            available_dates = self.stock_model.get_available_price_dates()
            
            date_var = tk.StringVar()
            if available_dates:
                date_combo = ctk.CTkComboBox(
                    main_frame,
                    values=available_dates,
                    variable=date_var,
                    width=200,
                    height=35
                )
                date_combo.pack(pady=5)
                date_combo.set(available_dates[0])  # Seleccionar la primera fecha
            else:
                no_dates_label = ctk.CTkLabel(main_frame, text="No hay fechas disponibles")
                no_dates_label.pack(pady=10)
                return

            # Porcentaje de aumento
            percent_label = ctk.CTkLabel(
                main_frame, 
                text="Porcentaje de aumento (%):",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            percent_label.pack(pady=(20, 5))

            percent_var = tk.StringVar(value="10")
            percent_entry = ctk.CTkEntry(
                main_frame,
                textvariable=percent_var,
                width=100,
                height=35,
                font=ctk.CTkFont(size=14)
            )
            percent_entry.pack(pady=5)

            # Preview de productos afectados
            preview_label = ctk.CTkLabel(
                main_frame,
                text="",
                font=ctk.CTkFont(size=12)
            )
            preview_label.pack(pady=20)

            def update_preview():
                try:
                    selected_date = date_var.get()
                    if selected_date:
                        count = self.stock_model.count_products_by_date(selected_date)
                        preview_label.configure(text=f"Se actualizarán {count} productos con fecha {selected_date}")
                except:
                    preview_label.configure(text="Error al obtener preview")

            # Actualizar preview cuando cambie la fecha
            date_var.trace('w', lambda *args: update_preview())
            update_preview()  # Preview inicial

            # Botones
            button_frame = ctk.CTkFrame(window, fg_color="transparent")
            button_frame.pack(pady=20)

            def apply_bulk_update():
                try:
                    selected_date = date_var.get()
                    percent_increase = float(percent_var.get())
                    
                    if not selected_date:
                        self.show_error("Seleccione una fecha")
                        return
                        
                    if percent_increase <= 0:
                        self.show_error("El porcentaje debe ser mayor a 0")
                        return

                    # Confirmar la operación
                    count = self.stock_model.count_products_by_date(selected_date)
                    if self.ask_confirmation(
                        f"¿Está seguro de aumentar {percent_increase}% el precio de {count} productos con fecha {selected_date}?"
                    ):
                        updated_count = self.stock_model.bulk_update_prices_by_date(selected_date, percent_increase)
                        self.controller.refresh_stock_table()
                        window.destroy()
                        self.show_success(f"Se actualizaron {count} productos correctamente")

                except ValueError:
                    self.show_error("Ingrese un porcentaje válido")
                except Exception as e:
                    self.show_error(f"Error en actualización masiva: {str(e)}")

            apply_button = ctk.CTkButton(
                button_frame,
                text="Aplicar Actualización",
                width=150,
                height=40,
                fg_color="#4CAF50",
                hover_color="#45a049",
                command=apply_bulk_update
            )
            apply_button.pack(side="left", padx=10)

            cancel_button = ctk.CTkButton(
                button_frame,
                text="Cancelar",
                width=100,
                height=40,
                fg_color="#757575",
                hover_color="#616161",
                command=window.destroy
            )
            cancel_button.pack(side="left", padx=10)

        except Exception as e:
            self.show_error(f"Error al abrir ventana de actualización masiva: {str(e)}")
    
    def clear_form_fields(self):
        """Limpiar todos los campos del formulario"""
        for var in self.form_vars:
            var.set("")
        self.pack_var.set("UNIDAD")
        self.iva_var.set("21%")

    def get_find_data(self):
        """Obtener datos del formulario"""
        return {
            'name': self.find_var.get().strip(),
        }
        
    def get_selected_product(self):
        """Obtener producto seleccionado del tree"""
        try:
            selected_item = self.stock_tree.selection()[0]
            values = self.stock_tree.item(selected_item)['values']
            product_id = str(values[0])
            return product_id
        except (IndexError, ValueError):
            return None
    
    def on_double_click(self, event):
        """Manejar doble click para editar"""
        # Obtener item y columna clickeada
        item = self.stock_tree.selection()[0] if self.stock_tree.selection() else None
        if not item:
            return
        
        region = self.stock_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
            
        column = self.stock_tree.identify("column", event.x, event.y)
        if not column:
            return
            
        # Convertir columna a índice (column viene como '#1', '#2', etc.)
        column_index = int(column.replace('#', '')) - 1
        if column_index < 0 or column_index >= len(self.stock_tree['columns']):
            return
            
        column_name = self.stock_tree['columns'][column_index]
        
        # No permitir editar el ID
        if column_name in ['Id', 'ListPrice', 'Discount','CostPrice', 'Profit', 'SalePrice', \
                           'Iva', 'SalePriceWithIva', 'ValidityDate', 'LastPriceUpdate', 'Stock']:
            return
            
        self.start_edit(item, column_name, column)
    
    def start_edit(self, item, column_name, column):
        """Iniciar edición de una celda"""
        # Cancelar edición anterior si existe
        if self.edit_entry:
            self.cancel_edit()
        
        # Obtener posición y tamaño de la celda
        x, y, width, height = self.stock_tree.bbox(item, column)
        
        # Obtener valor actual
        current_value = self.stock_tree.set(item, column_name)
        
        # Crear Entry para edición
        self.edit_entry = tk.Entry(self.stock_tree)
        self.edit_entry.place(x=x, y=y, width=width, height=height)
        self.edit_entry.insert(0, current_value)
        self.edit_entry.select_range(0, tk.END)
        self.edit_entry.focus()
        
        # Guardar información de la edición
        self.edit_item = item
        self.edit_column = column_name
        self.original_value = current_value
        
        # Binds para el Entry
        self.edit_entry.bind('<Return>', self.save_edit)
        self.edit_entry.bind('<Escape>', self.cancel_edit)
        self.edit_entry.bind('<FocusOut>', self.cancel_edit)
    
    def save_edit(self, event=None):
        """Guardar la edición"""
        if not self.edit_entry:
            return
            
        try:
            new_value = self.edit_entry.get()
            
            # Validar según el tipo de columna
            if not self.validate_value(self.edit_column, new_value):
                self.cancel_edit()
                return
            
            product_id = self.stock_tree.set(self.edit_item, 'Id')

            # Actualizar en la base de datos
            success = self.controller.update_product_field(product_id, self.edit_column, new_value)
            
            if success:
                self.stock_tree.set(self.edit_item, self.edit_column, new_value)
                self.show_success(f"Producto actualizado correctamente")
            else:
                self.show_error("Error al actualizar el producto")
                
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
            
        finally:
            self.cleanup_edit()
    
    def cancel_edit(self, event=None):
        """Cancelar la edición"""
        self.cleanup_edit()
    
    def cleanup_edit(self):
        """Limpiar elementos de edición"""
        if self.edit_entry:
            self.edit_entry.destroy()
            self.edit_entry = None
        self.edit_item = None
        self.edit_column = None
        self.original_value = None
    
    def validate_value(self, column, value):
        """Validar valor según el tipo de columna"""
        try:
            if column == 'CostPrice':
                float_val = float(value)
                if float_val < 0:
                    self.show_error("El precio no puede ser negativo")
                    return False
            elif column == 'Stock':
                int_val = int(value)
                if int_val < 0:
                    self.show_error("La cantidad no puede ser negativa")
                    return False
            elif column in ['Name', 'Package']:
                if not value.strip():
                    self.show_error("Este campo no puede estar vacío")
                    return False
            return True
        except ValueError:
            self.show_error(f"Valor inválido para {column}")
            return False

    def refresh_stock_table(self, products):
        """Refrescar tabla de stock con nuevos datos"""
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)

        for product in products:
            (id, name, pack, list_price, discount, cost_price, profit, price,
            iva, price_with_iva, created_at, last_price_update, quantity) = product

            if quantity < 3:
                tag = "low_stock"
            elif quantity <= 5:
                tag = "medium_stock"
            else:
                tag = ""

            self.stock_tree.insert(
                "", "end",
                values=(
                    id, name, pack, format_currency(list_price), discount, format_currency(cost_price),
                    profit, format_currency(price), iva, format_currency(price_with_iva),
                    iso_to_traditional(created_at), iso_to_traditional(last_price_update), quantity),
                tags=(tag,)
            )

        self.update_stats(products)

        if self.sort_column:
            self.sort_tree(self.sort_column)

    def export_to_csv(self):
        """Exportar el inventario visible a CSV"""
        rows = self.stock_tree.get_children()
        if not rows:
            self.show_warning("No hay productos para exportar")
            return

        default_name = f"inventario_{datetime.now().strftime('%Y%m%d')}.csv"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
            initialfile=default_name,
            title="Guardar inventario como..."
        )
        if not filepath:
            return

        try:
            headers = ["Código", "Nombre", "Envase", "P. Lista", "Dto %", "P. Costo",
                       "% Rent.", "P. Venta", "IVA %", "P. Venta c/IVA",
                       "Fecha Vig.", "Últ. Modificación", "Stock"]
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for row in rows:
                    writer.writerow(self.stock_tree.item(row)["values"])

            self.show_success(f"Exportado correctamente:\n{filepath}")
        except Exception as e:
            self.show_error(f"Error al exportar: {e}")

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
    
    def sort_tree(self, column):
        """Ordenar tree por columna especificada"""
        try:
            data = []
            for child in self.stock_tree.get_children():
                values = self.stock_tree.item(child)['values']
                data.append((child, values))
            # Alternar orden
            if self.sort_column == column:
                self.sort_reverse = not self.sort_reverse
            else:
                self.sort_reverse = False
                self.sort_column = column
            
            # Posición de la columna en los values
            column_index = self.stock_tree['columns'].index(column)

            def sort_key(item):
                value = item[1][column_index]

                # Numéricos
                if column in ["ListPrice", "CostPrice", "Profit", "SalePrice", "SalePriceWithIva", "Stock"]:
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return 0

                # Id como número si se puede
                elif column == "Id":
                    try:
                        return int(value)
                    except (ValueError, TypeError):
                        return str(value).lower()

                # Fechas (siempre YYYY-MM-DD en DB)
                elif column in ["ValidityDate", "LastPriceUpdate"]:
                    return str(value)

                # Strings normales
                else:
                    return str(value).lower()
            
            data.sort(key=sort_key, reverse=self.sort_reverse)

            # Reordenar en el treeview
            for index, (child, values) in enumerate(data):
                self.stock_tree.move(child, '', index)
        
            self.update_sort_indicators(column)
            
        except Exception as e:
            print(f"Error al ordenar: {e}")


    def update_sort_indicators(self, sorted_column):
        """Actualizar indicadores de ordenamiento en headers"""
        
        column_texts = {
            "Id": "Cód.",
            "Name": "Nombre Artículo",
            "Package": "Envase",
            "Profit": "% Rent.",
            "CostPrice": "P. Costo",
            "SalePrice": "P. Venta",
            "Iva": "% Iva",
            "SalePriceWithIva": "P. Venta C/Iva",
            "ValidityDate": "Fecha Vig.",
            "LastPriceUpdate": "F. Ult. Modif.",
            "Stock": "Stock"
        }
        
        for col in self.stock_tree['columns']:
            base_text = column_texts.get(col, col)
            
            if col == sorted_column:
                indicator = ' ↑' if not self.sort_reverse else ' ↓'
                text = base_text + indicator
            else:
                text = base_text
            
            self.stock_tree.heading(col, text=text)

    def open_edit_product_window(self):
        """Ventana para editar nombre y envase del producto"""
        try:
            product_id = self.get_selected_product()
            if not product_id:
                self.show_warning("Seleccione un producto para editar")
                return

            product = self.stock_model.get_product_by_id(product_id)
            if not product:
                self.show_error(f"Producto {product_id} no encontrado")
                return

            _, name, pack, _, _, _, _, _, _, _, _, _, _ = product

            window = ctk.CTkToplevel(self.frame)
            window.title(f"Editar Producto - {name}")
            window.grab_set()
            window.resizable(False, False)
            center_window(window, 480, 320)

            # Card blanca
            card = ctk.CTkFrame(window, fg_color="white", corner_radius=20)
            card.pack(fill="both", expand=True, padx=20, pady=20)

            ctk.CTkLabel(
                card,
                text="Editar Producto",
                font=ctk.CTkFont(size=18, weight="bold")
            ).pack(pady=(20, 10))

            # Form
            form_frame = ctk.CTkFrame(card, fg_color="#f9f9f9", corner_radius=10)
            form_frame.pack(pady=10, padx=20, fill="x")

            name_var = tk.StringVar(value=name)
            pack_var = tk.StringVar(value=pack)

            def add_field(row, label, widget):
                ctk.CTkLabel(
                    form_frame,
                    text=label,
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color="black"
                ).grid(row=row, column=0, sticky="e", padx=(10, 10), pady=10)
                widget.grid(row=row, column=1, sticky="w", padx=(10, 10), pady=10)

            add_field(
                0, "Nombre:", 
                ctk.CTkEntry(
                    form_frame,
                    textvariable=name_var,
                    width=250,
                    height=35
                )
            )
            add_field(
                1,"Envase: ",
                ctk.CTkComboBox(
                    form_frame,
                    values=[
                        "UNIDAD",
                        "10 ML",
                        "20 ML",
                        "25 ML",
                        "50 ML",
                        "90 ML",
                        "100 ML",
                        "200 ML",
                        "250 ML",
                        "300 ML",
                        "500 ML",
                        "400 GR",
                        "5 KG",
                        "10 KG",
                        "12 KG",
                        "15 KG",
                        "20 KG",
                        "25 KG",
                        "40 DS",
                    ],
                    variable=pack_var,
                    width=200,
                    height=35
                )
            )

            # Botones
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(pady=20)

            def save():
                new_name = name_var.get().strip()
                new_pack = pack_var.get().strip()

                if not new_name:
                    self.show_error("El nombre no puede estar vacío")
                    return
                if not new_pack:
                    self.show_error("El envase no puede estar vacío")
                    return

                # Verificar si ya existe otro producto con ese nombre
                existing = self.stock_model.get_all_product_by_name(new_name)
                if existing:
                    for product in existing: 
                        if str(product[0]) != str(product_id) and product[1] == new_pack:
                            messagebox.showwarning("Error", f"Ya existe un producto con el nombre '{new_name}'.\n\n"
                            f"Código: {product[0]}\n"
                            f"Envase: {product[1]}\n\n"
                            "Elija un nombre diferente.")
                            return
                    
                
                self.controller.update_product_field(product_id, "Name", new_name)
                self.controller.update_product_field(product_id, "Package", new_pack)
                self.controller.refresh_stock_table()
                window.destroy()
                self.show_success("Producto actualizado correctamente")

            ctk.CTkButton(
                btn_frame, text="Guardar", width=150, height=40,
                fg_color="#009688", hover_color="#00796B",
                font=ctk.CTkFont(size=13, weight="bold"),
                command=save
            ).grid(row=0, column=0, padx=15)

            ctk.CTkButton(
                btn_frame, text="Cancelar", width=150, height=40,
                fg_color="#E74C3C", hover_color="#C0392B",
                font=ctk.CTkFont(size=13, weight="bold"),
                command=window.destroy
            ).grid(row=0, column=1, padx=15)

            window.bind("<Return>", lambda e: save())

        except Exception as e:
            self.show_error(f"Error al abrir ventana de edición: {str(e)}")

    def _open_product_history(self):
        product_id = self.get_selected_product()
        if not product_id:
            self.show_warning("Seleccione un producto para ver su historial")
            return
        product = self.stock_model.get_product_by_id(product_id)
        name = product[1] if product else None
        self.movement_view.open(self.frame, product_id=product_id, product_name=name)