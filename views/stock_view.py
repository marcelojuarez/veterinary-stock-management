import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
from models.stock import StockModel
from views.view_helpers import close_win, show_warning
import random

# Configurar tema y colores
ctk.set_appearance_mode("light")  # "light" o "dark"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class StockView():
    def __init__(self, parent, controller=None):
        self.controller = controller
        # Usar CTkFrame en lugar de tk.Frame
        self.frame = ctk.CTkFrame(parent, fg_color="#f0f0f0")
        self.stock_model = StockModel()
        self.create_widgets()
        self.edit_item = None
        self.edit_entry = None
        self.edit_column = None
        self.original_value = None

        self.sort_column = None
        self.sort_reverse = False
        
    def set_controller(self, controller):
        """Asignar controller después de la inicialización"""
        self.controller = controller
        
    def setup_variables(self):
        """Configurar variables del formulario"""
        self.cuit_supplier = tk.StringVar()
        self.name_var = tk.StringVar()
        self.pack_var = tk.StringVar()
        self.profit_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.iva_var = tk.StringVar()
        self.stock_var = tk.StringVar()
        self.qnt_var = tk.StringVar()
        
        self.form_vars = [
            self.cuit_supplier,
            self.name_var,
            self.pack_var,
            self.profit_var,
            self.price_var,
            self.iva_var,
            self.qnt_var,
        ]

    
    def create_widgets(self):
        """Crear todos los widgets de la vista"""
        self.create_find_frame()
        self.create_tree_frame()
        self.create_buttons_frame()
    
    def create_buttons_frame(self):
        """Crear frame para botones de stock"""
        manage_frame = ctk.CTkFrame(self.frame)
        manage_frame.grid(row=2, column=0, sticky='w', padx=10, pady=20)

        W = 280
        H = 35
        btn_color = "#009688"
        btn_hover = "#00796B"

        new_btn = ctk.CTkButton(
            manage_frame,
            text="📦 Nuevo producto",
            width=W,
            height=H,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=btn_color,
            hover_color=btn_hover,
            command=lambda: self.open_add_window(manage_frame)
        )
        
        update_btn = ctk.CTkButton(
            manage_frame,
            text="✏️ Actualizar precio",
            width=W,
            height=H,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=btn_color,
            hover_color=btn_hover,
            command=lambda: self.open_update_price_window()
        )
        
        delete_btn = ctk.CTkButton(
            manage_frame,
            text="🗑️ Eliminar producto",
            width=W,
            height=H,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=btn_color,
            hover_color=btn_hover,
            command=lambda: self.controller.delete_product()
        )

        bulk_update_btn = ctk.CTkButton(
            manage_frame,
            text="📈 Actualización masiva",
            width=W,
            height=H,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=btn_color,
            hover_color=btn_hover,
            command=lambda: self.open_bulk_update_window()
        )

        new_btn.grid(row=1, column=0, padx=10, pady=10)
        delete_btn.grid(row=1, column=1, padx=10, pady=10)
        update_btn.grid(row=1, column=2, padx=10, pady=10)
        bulk_update_btn.grid(row=1, column=4, padx=10, pady=10)
    
    def create_find_frame(self):
        """Crear frame para formulario de producto"""
        self.find_var = tk.StringVar()

        btn_color = "#009688"
        btn_hover = "#00796B"

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
        
        find_btn = ctk.CTkButton(
            find_frame,
            text="!",
            width=60,
            height=35,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=btn_color,
            hover_color=btn_hover,
            command=lambda: show_warning("Ingrese un NOMBRE, CUIT o ENVASE para buscar un Producto")
        )
        find_btn.grid(row=0, column=2, padx=15, pady=15)

    def create_tree_frame(self):
        """Crear frame para tabla de stock"""
        tree_frame = ctk.CTkFrame(self.frame)
        tree_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')

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
        self.stock_tree = ttk.Treeview(table_container, show="headings", height=15)

        # Scrollbar vertical con estilo
        scrollbar = ttk.Scrollbar(table_container, orient='vertical', command=self.stock_tree.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.stock_tree.configure(yscrollcommand=scrollbar.set)

        self.stock_tree['columns'] = (
            "Id", "SupplierCuit","Name", "Package", "Profit", "CostPrice", "SalePrice",
            "Iva", "SalePriceWithIva", "ValidityDate", "LastPriceUpdate", "Stock"
        )

        self.stock_tree['displaycolumns'] = self.stock_tree['columns']

        # Definición de columnas
        self.stock_tree.column("Id", anchor=tk.W, width=60, stretch=False)
        self.stock_tree.column("SupplierCuit", anchor=tk.W, width=150, stretch=False)
        self.stock_tree.column("Name", anchor=tk.W, width=250, stretch=False)
        self.stock_tree.column("Package", anchor=tk.W, width=120, stretch=False)
        self.stock_tree.column("Profit", anchor=tk.CENTER, width=80, stretch=False)
        self.stock_tree.column("CostPrice", anchor=tk.E, width=100, stretch=False)
        self.stock_tree.column("SalePrice", anchor=tk.E, width=100, stretch=False)
        self.stock_tree.column("Iva", anchor=tk.CENTER, width=60, stretch=False)
        self.stock_tree.column("SalePriceWithIva", anchor=tk.E, width=120, stretch=False)
        self.stock_tree.column("ValidityDate", anchor=tk.CENTER, width=120, stretch=False)
        self.stock_tree.column("LastPriceUpdate", anchor=tk.CENTER, width=120, stretch=False)
        self.stock_tree.column("Stock", anchor=tk.CENTER, width=80, stretch=False)

        # Encabezados
        self.stock_tree.heading("Id", text="Cód. ↕", anchor=tk.W,
                                command=lambda: self.sort_tree("Id"))
        self.stock_tree.heading("SupplierCuit", text="Cuit Proveedor ↕", anchor=tk.W,
                                command=lambda: self.sort_tree("SupplierCuit"))
        self.stock_tree.heading("Name", text="Nombre Artículo ↕", anchor=tk.W,
                                command=lambda: self.sort_tree("Name"))
        self.stock_tree.heading("Package", text="Envase ↕", anchor=tk.W,
                                command=lambda: self.sort_tree("Package"))
        self.stock_tree.heading("Profit", text="% Rent. ↕", anchor=tk.CENTER,
                                command=lambda: self.sort_tree("Profit"))
        self.stock_tree.heading("CostPrice", text="P. Costo ↕", anchor=tk.E,
                                command=lambda: self.sort_tree("CostPrice"))
        self.stock_tree.heading("SalePrice", text="P. Venta ↕", anchor=tk.E,
                                command=lambda: self.sort_tree("SalePrice"))
        self.stock_tree.heading("Iva", text="% Iva", anchor=tk.CENTER,
                                command=lambda: self.sort_tree("Iva"))
        self.stock_tree.heading("SalePriceWithIva", text="P. Venta C/Iva ↕", anchor=tk.E,
                                command=lambda: self.sort_tree("SalePriceWithIva"))
        self.stock_tree.heading("ValidityDate", text="Fecha Vig. ↕", anchor=tk.CENTER,
                                command=lambda: self.sort_tree("ValidityDate"))
        self.stock_tree.heading("LastPriceUpdate", text="F. Ult. Modif. ↕", anchor=tk.CENTER,
                                command=lambda: self.sort_tree("LastPriceUpdate"))
        self.stock_tree.heading("Stock", text="Stock ↕", anchor=tk.CENTER,
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

    def open_add_window(self, parent):
        """Ventana para agregar nuevo producto con CustomTkinter"""
        add_win = ctk.CTkToplevel(self.frame)
        add_win.title("Agregar nuevo artículo")

        # se configuran las string vars
        self.setup_variables()
        
        # Hacer que la ventana sea modal
        add_win.transient(self.frame)
        add_win.grab_set()
        
        # Centrar la ventana
        add_win.geometry("400x535+{}+{}".format(
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
            ("Cuit Proveedor:", self.cuit_supplier),
            ("Nombre Artículo:", self.name_var),
            ("Precio Costo:", self.price_var),
            ("% Rentabilidad:", self.profit_var),
            ("Cantidad de Artículos:", self.qnt_var)
        ]

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
            variable=self.pack_var,
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
            variable=self.iva_var,
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
            fg_color="#4CAF50", hover_color="#45a049", command=lambda: self.controller.add_new_product(add_win))
        add_button.grid(row=0, column=0, padx=10)

        cancel_button = ctk.CTkButton(button_frame, text="Cancelar", width=120, height=35, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#757575", hover_color="#616161", command=lambda: close_win(add_win, parent, self.clear_form_fields))
        cancel_button.grid(row=0, column=1, padx=10)

    def open_update_price_window(self):
        """Abrir ventana para actualizar precio de producto seleccionado con CustomTkinter"""
        try:
            product_id = self.get_selected_product()
            if not product_id:
                self.show_warning("Seleccione un producto para actualizar el precio")
                return
                    
            product = self.stock_model.get_product_by_id(product_id)
            if not product:
                self.show_error(f"Producto {product_id} no encontrado")
                return

            print(f'Producto seleccionado: {product}')

            _, _, name, pack, profit, cost_price, sale_price, iva, _, _, _, stock = product

            window = ctk.CTkToplevel(self.frame)
            window.title(f"Actualizar Precio - {name}")
            window.grab_set()
            window.geometry("450x450+{}+{}".format(window.winfo_screenwidth()//2 - 225, window.winfo_screenheight()//2 - 225))

            # Información básica
            info_label = ctk.CTkLabel(
                window, 
                text=f"Producto: {name} | Código: {product_id} | Costo: ${cost_price}",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            info_label.pack(pady=20)

            main_frame = ctk.CTkFrame(window)
            main_frame.pack(padx=20, pady=10, fill="both", expand=True)

            method_label = ctk.CTkLabel(main_frame, text="Método:", font=ctk.CTkFont(size=16, weight="bold"))
            method_label.pack(pady=(15, 5))

            method_var = tk.StringVar(value="sale_price")
            
            sale_radio = ctk.CTkRadioButton(main_frame, text="Por Precio de Venta", variable=method_var, value="sale_price")
            sale_radio.pack(pady=2)
            
            profit_radio = ctk.CTkRadioButton(main_frame, text="Por Rentabilidad (%)", variable=method_var, value="profit")
            profit_radio.pack(pady=2)

            # Campos de entrada
            input_frame = ctk.CTkFrame(main_frame)
            input_frame.pack(pady=15, padx=20, fill="x")

            sale_var = tk.StringVar(value=str(sale_price))
            profit_var = tk.StringVar(value=str(profit))

            sale_label = ctk.CTkLabel(input_frame, text="Precio de Venta:")
            sale_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            
            sale_entry = ctk.CTkEntry(input_frame, textvariable=sale_var, width=150)
            sale_entry.grid(row=0, column=1, padx=10, pady=10)

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
                if method == "sale_price":
                    sale_entry.configure(state="normal")
                    profit_entry.configure(state="disabled")
                    try:
                        new_sale = float(sale_var.get())
                        new_profit = round(((new_sale - cost_price) / cost_price) * 100, 2)
                        
                        if iva == "21%":
                            price_with_iva = round(new_sale * 1.21, 2)
                        elif iva == "10.5%":
                            price_with_iva = round(new_sale * 1.105, 2)
                        else:
                            price_with_iva = new_sale
                            
                        result_var.set(f"Precio: ${new_sale} | Rentabilidad: {new_profit}% | Con IVA: ${price_with_iva}")
                    except:
                        result_var.set("Valor inválido")
                else:
                    sale_entry.configure(state="disabled")
                    profit_entry.configure(state="normal")
                    try:
                        new_profit = float(profit_var.get())
                        new_sale = round(cost_price * (1 + new_profit / 100), 2)
                        
                        if iva == "21%":
                            price_with_iva = round(new_sale * 1.21, 2)
                        elif iva == "10.5%":
                            price_with_iva = round(new_sale * 1.105, 2)
                        else:
                            price_with_iva = new_sale
                            
                        result_var.set(f"Precio: ${new_sale} | Rentabilidad: {new_profit}% | Con IVA: ${price_with_iva}")
                    except:
                        result_var.set("Valor inválido")

            method_var.trace('w', lambda *args: update_interface())
            sale_var.trace('w', lambda *args: update_interface() if method_var.get() == "sale_price" else None)
            profit_var.trace('w', lambda *args: update_interface() if method_var.get() == "profit" else None)

            update_interface()

            # Botones
            button_frame = ctk.CTkFrame(window, fg_color="transparent")
            button_frame.pack(pady=20)

            def save_update():
                try:
                    method = method_var.get()
                    
                    if method == "sale_price":
                        new_sale_price = float(sale_var.get())
                        new_profit = round(((new_sale_price - cost_price) / cost_price) * 100, 2)
                    else:
                        new_profit = float(profit_var.get())
                        new_sale_price = round(cost_price * (1 + new_profit / 100), 2)

                    if iva == "21%":
                        price_with_iva = round(new_sale_price * 1.21, 2)
                    elif iva == "10.5%":
                        price_with_iva = round(new_sale_price * 1.105, 2)
                    else:
                        price_with_iva = new_sale_price

                    product_data = {
                        "Name": name,
                        "Package": pack,
                        "Profit": new_profit,
                        "CostPrice": cost_price,
                        "SalePrice": new_sale_price,
                        "Iva": iva,
                        "PriceWIva": price_with_iva,
                        "Stock": stock,
                    }

                    self.stock_model.update_product(product_id, product_data)
                    self.controller.refresh_stock_table()
                    window.destroy()
                    self.show_success("Precio actualizado correctamente")

                except ValueError:
                    self.show_error("Por favor ingrese valores numéricos válidos")
                except Exception as e:
                    self.show_error(f"Error al actualizar precio: {str(e)}")

            save_button = ctk.CTkButton(button_frame, text="Guardar", width=100, height=35, 
                fg_color="#4CAF50", hover_color="#45a049", command=save_update)
            save_button.pack(side="left", padx=10)

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
            window.geometry("500x450+{}+{}".format(
                window.winfo_screenwidth()//2 - 250,
                window.winfo_screenheight()//2 - 200
            ))

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

    # def generate_random_id(self):
    #     """Generar ID aleatorio para producto"""
    #     numeric = '1234567890'
    #     item_id = ''
    #     for i in range(4):
    #         randno = random.randrange(0, len(numeric))
    #         item_id += numeric[randno]
    #     self.id_var.set(item_id)
    
    def clear_form_fields(self):
        """Limpiar todos los campos del formulario"""
        for var in self.form_vars:
            var.set("")
        self.pack_var.set("UNIDAD")
        self.iva_var.set("21%")

    def get_form_data(self):
        """Obtener datos del formulario"""
        return {
            'Cuit_supplier': self.cuit_supplier.get().strip(),
            'Name': self.name_var.get().strip(),
            'Package': self.pack_var.get().strip(),
            'Profit': self.profit_var.get().strip(),
            'CostPrice': self.price_var.get().strip(),
            'Iva': self.iva_var.get().strip(),
            'Stock': self.qnt_var.get().strip(),
        }

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
            product_id = str(values[0]).zfill(4)
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
        if column_name == 'Id':
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
            (id, cuit_supplier, name, pack, profit, cost_price, price, 
            iva, price_with_iva, created_at, last_price_update, quantity) = product

            # Decidir el tag según stock
            if quantity < 3:
                tag = "low_stock"
            elif quantity <= 5:
                tag = "medium_stock"
            else:
                tag = ""

            # Insertar en la Treeview
            self.stock_tree.insert(
                "", "end", 
                values=(id, cuit_supplier, name, pack, profit, cost_price, price, iva, price_with_iva, 
                        created_at, last_price_update, quantity), 
                tags=(tag,)
            )

        if self.sort_column:
            self.sort_tree(self.sort_column)


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
                if column in ["Profit", "CostPrice", "SalePrice", "SalePriceWithIva", "Stock"]:
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
            "SupplierCuit": "Cuit Proveedor",
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
                text = base_text + ' ↕'
            
            self.stock_tree.heading(col, text=text)

