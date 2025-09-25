import tkinter as tk
from tkinter import ttk, messagebox
from models.stock import StockModel
import random

class StockView():
    def __init__(self, parent, controller=None):
        self.controller = controller
        self.frame = tk.Frame(parent, bg="#79858C")
        self.stock_model = StockModel()
        self.setup_variables()
        self.create_widgets()
        self.edit_item = None
        self.edit_entry = None
        self.edit_column = None
        self.original_value = None
        
    def set_controller(self, controller):
        """Asignar controller después de la inicialización"""
        print(f"DEBUG: Asignando controller: {controller}")
        self.controller = controller
        print(f"DEBUG: Controller asignado correctamente: {self.controller}")
        
    def setup_variables(self):
        """Configurar variables del formulario"""
        self.id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.pack_var = tk.StringVar()
        self.profit_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.iva_var = tk.StringVar()
        self.stock_var = tk.StringVar()
        self.qnt_var = tk.StringVar()
        self.find_var = tk.StringVar()
        
        self.form_vars = [
            self.id_var,
            self.name_var,
            self.pack_var,
            self.profit_var,
            self.price_var,
            self.iva_var,
            self.qnt_var,
            self.find_var
        ]

        self.sort_column = None
        self.sort_reverse = False
    
    def create_widgets(self):
        """Crear todos los widgets de la vista"""
        self.create_find_frame()
        self.create_tree_frame()
        self.create_buttons_frame()
    
    def create_buttons_frame(self):
        """Crear frame para botones de stock"""
        manage_frame = tk.LabelFrame(self.frame, borderwidth=2, text="Acciones")
        manage_frame.grid(row=2, column=0, sticky='w', padx=[10,20], pady=20, ipadx=6)

        btn_style = {
            "width": 35,
            "height": 2,
            "borderwidth": 2,
            "fg": "black",
            "font": ("Arial", 12, "bold")
        }

        new_btn = tk.Button(manage_frame, text="📦 Nuevo producto", bg="#B3E5FC", command=lambda: self.open_add_window(), **btn_style)
        update_btn = tk.Button(manage_frame, text="✏️ Editar", bg="#C8E6C9", **btn_style)
        delete_btn = tk.Button(manage_frame, text="🗑️ Eliminar", bg="#FFCDD2", command=lambda: self.controller.delete_product(), **btn_style)
        clear_btn = tk.Button(manage_frame, text="🔄 Mostrar todo", bg="#E1BEE7", command=lambda: self.controller.refresh_stock_table(), **btn_style)

        new_btn.grid(row=0, column=0, padx=5, pady=5)
        update_btn.grid(row=0, column=1, padx=5, pady=5)
        delete_btn.grid(row=0, column=2, padx=5, pady=5)
        clear_btn.grid(row=0, column=3, padx=5, pady=5)
    
    def create_find_frame(self):
        """Crear frame para formulario de producto"""
        find_frame = tk.LabelFrame(self.frame, borderwidth=2)
        find_frame.grid(row=0, column=0, sticky='w', padx=[10,200], pady=[0,20], ipadx=6)

        # Label
        tk.Label(find_frame, text='🔍 Buscar producto:', anchor='e', width=20, font=("Arial", 13, "bold")).grid(row=0, column=0, padx=5)

        # Campo de texto
        self.find_entry = tk.Entry(find_frame, width=35, textvariable=self.find_var, font=("Arial", 10))
        self.find_entry.grid(row=0, column=1, padx=5, pady=5)

        # Botón de búsqueda
        find_btn = tk.Button(
            find_frame,
            text="Buscar",
            width=18,
            height=2,
            borderwidth=2,
            bg="#BBDEFB",  # azul pastel
            fg="black",
            font=("Arial", 12, "bold"),
            command=lambda: self.controller.find_product()
        )
        find_btn.grid(row=0, column=2, padx=5, pady=5)


    def create_tree_frame(self):
        """Crear frame para tabla de stock"""
        tree_frame = tk.Frame(self.frame)
        tree_frame.grid(row=1, column=0, padx=10, pady=10, sticky='w')

        # Treeview
        self.stock_tree = ttk.Treeview(tree_frame, show="headings", height=25)

        # Scrollbar vertical
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.stock_tree.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.stock_tree.configure(yscrollcommand=scrollbar.set)

        self.stock_tree['columns'] = (
            "Id", "Name", "Package", "Profit", "CostPrice", "SalePrice",
            "Iva", "SalePriceWithIva", "ValidityDate", "LastPriceUpdate", "Stock"
        )

        self.stock_tree['displaycolumns'] = self.stock_tree['columns']

        # Definición de columnas
        self.stock_tree.column("Id", anchor=tk.W, width=80, stretch=False)
        self.stock_tree.column("Name", anchor=tk.W, width=180, stretch=False)
        self.stock_tree.column("Package", anchor=tk.W, width=120, stretch=False)
        self.stock_tree.column("Profit", anchor=tk.CENTER, width=80, stretch=False)
        self.stock_tree.column("CostPrice", anchor=tk.E, width=100, stretch=False)
        self.stock_tree.column("SalePrice", anchor=tk.E, width=100, stretch=False)
        self.stock_tree.column("Iva", anchor=tk.CENTER, width=60, stretch=False)
        self.stock_tree.column("SalePriceWithIva", anchor=tk.E, width=120, stretch=False)
        self.stock_tree.column("ValidityDate", anchor=tk.CENTER, width=120, stretch=False)
        self.stock_tree.column("LastPriceUpdate", anchor=tk.CENTER, width=150, stretch=False)
        self.stock_tree.column("Stock", anchor=tk.CENTER, width=80, stretch=False)

        # Encabezados
        self.stock_tree.heading("Id", text="Código ↕", anchor=tk.W,
                                command=lambda: self.sort_tree("Id"))
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
        self.stock_tree.heading("Iva", text="% Iva ↕", anchor=tk.CENTER,
                                command=lambda: self.sort_tree("Iva"))
        self.stock_tree.heading("SalePriceWithIva", text="P. Venta C/Iva ↕", anchor=tk.E,
                                command=lambda: self.sort_tree("SalePriceWithIva"))
        self.stock_tree.heading("ValidityDate", text="Fecha Vigencia ↕", anchor=tk.CENTER,
                                command=lambda: self.sort_tree("ValidityDate"))
        self.stock_tree.heading("LastPriceUpdate", text="Fecha Ult. Modif. Precio ↕", anchor=tk.CENTER,
                                command=lambda: self.sort_tree("LastPriceUpdate"))
        self.stock_tree.heading("Stock", text="Stock ↕", anchor=tk.CENTER,
                                command=lambda: self.sort_tree("Stock"))

        
        # Bind para doble click
        self.stock_tree.bind('<Double-Button-1>', self.on_double_click)
        # Bind para Enter y Escape
        self.stock_tree.bind('<Return>', self.save_edit)
        self.stock_tree.bind('<Escape>', self.cancel_edit)
        

        self.stock_tree.tag_configure('orow', background="#FFFFFF")
        self.stock_tree.tag_configure("low_stock", background="#FFB3B3")   # rojo suave
        self.stock_tree.tag_configure("medium_stock", background="#FFF2B3") # amarillo suave

        self.stock_tree.grid(row=0, column=0, padx=10, pady=(0, 20), sticky="nsew")

    def open_add_window(self):
        add_win = tk.Toplevel(self.frame)
        add_win.title("Agregar nuevo artículo")

        tk.Label(add_win, text="Código:").grid(row=0, column=0, padx=5, pady=5)
        id_entry = tk.Entry(add_win, textvariable=self.id_var)
        id_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(add_win, text="Nombre Artículo:").grid(row=1, column=0, padx=5, pady=5)
        name_entry = tk.Entry(add_win, textvariable=self.name_var)
        name_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(add_win, text="Envase:").grid(row=2, column=0, padx=5, pady=5)
        pack_combo = ttk.Combobox(add_win, textvariable=self.pack_var, state="readonly")
        pack_combo['values'] = ("UNIDAD", "CAJA", "FRASCO", "AMPOLLA", "SOBRE", "OTRO")
        pack_combo.current(0)  
        pack_combo.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(add_win, text="% Rentabilidad:").grid(row=3, column=0, padx=5, pady=5)
        rent_entry = tk.Entry(add_win, textvariable=self.profit_var)
        rent_entry.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(add_win, text="P. Costo:").grid(row=4, column=0, padx=5, pady=5)
        price_entry = tk.Entry(add_win, textvariable=self.price_var)
        price_entry.grid(row=4, column=1, padx=5, pady=5)

        tk.Label(add_win, text="% Iva:").grid(row=5, column=0, padx=5, pady=5)
        iva_combo = ttk.Combobox(add_win, textvariable=self.iva_var, state="readonly")
        iva_combo['values'] = ("21%", "10.5%", "0%")
        iva_combo.current(0)  
        iva_combo.grid(row=5, column=1, padx=4, pady=5)

        tk.Label(add_win, text="Cantidad de Artículos:").grid(row=6, column=0, padx=5, pady=5)
        qnt_entry = tk.Entry(add_win, textvariable=self.qnt_var)
        qnt_entry.grid(row=6, column=1, padx=5, pady=5)

        tk.Button(add_win, text="Agregar", 
                command=lambda: self.controller.add_new_product(add_win)).grid(row=7, column=0, pady=10, padx=5, sticky="e")

        tk.Button(add_win, text="Cancelar", 
                command=add_win.destroy).grid(row=7, column=1, pady=10, padx=5, sticky="w")



    def generate_random_id(self):
        """Generar ID aleatorio para producto"""
        numeric = '1234567890'
        item_id = ''
        for i in range(4):
            randno = random.randrange(0, len(numeric))
            item_id += numeric[randno]
        self.id_entry.set(item_id)

    def get_form_data(self):
        """Obtener datos del formulario"""
        return {
            'Id': self.id_var.get().strip(),
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
            (id, name, pack, profit, cost_price, price, 
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
                values=(id, name, pack, profit, cost_price, price, iva, price_with_iva, 
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
            
            if self.sort_column == column:
                self.sort_reverse = not self.sort_reverse
            else:
                self.sort_reverse = False
                self.sort_column = column
            
            column_index = self.stock_tree['columns'].index(column)
            
            def sort_key(item):
                value = item[1][column_index]
                
                if column in ['Price', 'Stock']:
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return 0
                
                elif column == 'Id':
                    try:
                        return int(value)
                    except (ValueError, TypeError):
                        return str(value).lower()
                
                else:
                    return str(value).lower()
            
            data.sort(key=sort_key, reverse=self.sort_reverse)
            
            for index, (child, values) in enumerate(data):
                self.stock_tree.move(child, '', index)
            
            self.update_sort_indicators(column)
            
        except Exception as e:
            print(f"Error al ordenar: {e}")


    def update_sort_indicators(self, sorted_column):
        """Actualizar indicadores de ordenamiento en headers"""
        
        column_texts = {
            'Id': 'Código',
            'Name': 'Nombre', 
            'Description': 'Descripción', 
            'Brand': 'Marca',
            'Price': 'Precio',
            'Cost Price': 'Precio Costo',
            'Iva': 'Iva',
            'Quantity': 'Stock'
        }
        
        for col in self.stock_tree['columns']:
            base_text = column_texts[col]
            
            if col == sorted_column:
                indicator = ' ↑' if not self.sort_reverse else ' ↓'
                text = base_text + indicator
            else:
                text = base_text + ' ↕'
            
            self.stock_tree.heading(col, text=text)
