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
        
    def set_controller(self, controller):
        """Asignar controller después de la inicialización"""
        print(f"DEBUG: Asignando controller: {controller}")
        self.controller = controller
        print(f"DEBUG: Controller asignado correctamente: {self.controller}")
        
    def setup_variables(self):
        """Configurar variables del formulario"""
        self.id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.desc_var = tk.StringVar()
        self.brand_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.stock_var = tk.StringVar()
        self.qnt_var = tk.StringVar()
        self.find_var = tk.StringVar()
        
        self.form_vars = [
            self.id_var,
            self.name_var,
            self.desc_var,
            self.brand_var,
            self.price_var,
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
        manage_frame = tk.LabelFrame(self.frame, borderwidth=2)
        manage_frame.grid(row=2, column=0, sticky='w', padx=[10,20], pady=20, ipadx=[6])

        new_btn = tk.Button(manage_frame, text="Nuevo", width=15, borderwidth=3, bg="#17BCE5", fg='black', command=lambda: self.open_add_window())
        update_btn = tk.Button(manage_frame, text="Actualizar", width=15, borderwidth=3, bg="#17E574", fg='black')
        delete_btn = tk.Button(manage_frame, text="Borrar", width=15, borderwidth=3, bg="#D6C52F", fg='black', command=lambda: self.controller.delete_product())
        clear_btn = tk.Button(manage_frame, text="Limpiar", width=15, borderwidth=3, bg="#B817E5", fg='black')
        add_btn = tk.Button(manage_frame, text="Agregar", width=15, borderwidth=3, bg="#E51717", fg='black')

        new_btn.grid(row=0, column=0, padx=5, pady=5)
        update_btn.grid(row=0, column=1, padx=5, pady=5)
        delete_btn.grid(row=0, column=2, padx=5, pady=5)
        clear_btn.grid(row=0, column=3, padx=5, pady=5)
        add_btn.grid(row=0, column=4, padx=5, pady=5)
    
    def create_find_frame(self):
        """Crear frame para formulario de producto"""
        find_frame = tk.LabelFrame(self.frame, borderwidth=2)
        find_frame.grid(row=0, column=0, sticky='w', padx=[10,200], pady=[0,20], ipadx=[6])

        find_btn = tk.Button(find_frame, text="Buscar", borderwidth=3, bg="#FFFFFF", fg='black', command=lambda: self.controller.find_product())
        find_btn.grid(row=0, column=2, padx=5, pady=5)

        tk.Label(find_frame, text='Buscar:', anchor='e', width=5).grid(row=0, column=0, padx=5)
        self.find_entry = tk.Entry(find_frame, width=30, textvariable=self.find_var)
        self.find_entry.grid(row=0, column=1, padx=5, pady=5)

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

        self.stock_tree['columns'] = ('Id', "Name", "Description", "Brand", "Price", "Qnt")
        self.stock_tree['displaycolumns'] = self.stock_tree['columns']
        self.stock_tree.column("Id", anchor=tk.W, width=80, stretch=False)
        self.stock_tree.column("Name", anchor=tk.W, width=180, stretch=False)
        self.stock_tree.column("Description", anchor=tk.W, width=350, stretch=False)
        self.stock_tree.column("Brand", anchor=tk.W, width=180, stretch=False)
        self.stock_tree.column("Price", anchor=tk.W, width=100, stretch=False)
        self.stock_tree.column("Qnt", anchor=tk.W, width=60, stretch=False)

        self.stock_tree.heading('Id', text='Código ↕', anchor=tk.W, 
                           command=lambda: self.sort_tree('Id'))
        self.stock_tree.heading('Name', text='Nombre ↕', anchor=tk.W,
                            command=lambda: self.sort_tree('Name'))
        self.stock_tree.heading('Description', text='Descripción ↕', anchor=tk.W,
                            command=lambda: self.sort_tree('Name'))
        self.stock_tree.heading('Brand', text='Marca ↕', anchor=tk.W,
                            command=lambda: self.sort_tree('Brand'))
        self.stock_tree.heading('Price', text='Precio ↕', anchor=tk.W,
                            command=lambda: self.sort_tree('Price'))
        self.stock_tree.heading('Qnt', text='Stock ↕', anchor=tk.W,
                            command=lambda: self.sort_tree('Quantity'))
        

        self.stock_tree.tag_configure('orow', background="#FFFFFF")
        self.stock_tree.grid(row=0, column=0, padx=10, pady=(0, 20), sticky="nsew")

    def open_add_window(self):
        add_win = tk.Toplevel(self.frame)
        add_win.title("Agregar nuevo producto")

        tk.Label(add_win, text="Código:").grid(row=0, column=0, padx=5, pady=5)
        id_entry = tk.Entry(add_win, textvariable=self.id_var)
        id_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(add_win, text="Nombre:").grid(row=1, column=0, padx=5, pady=5)
        name_entry = tk.Entry(add_win, textvariable=self.name_var)
        name_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(add_win, text="Descripción:").grid(row=2, column=0, padx=5, pady=5)
        desc_entry = tk.Entry(add_win, textvariable=self.desc_var)
        desc_entry.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(add_win, text="Marca:").grid(row=3, column=0, padx=5, pady=5)
        brand_entry = tk.Entry(add_win, textvariable=self.brand_var)
        brand_entry.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(add_win, text="Precio:").grid(row=4, column=0, padx=5, pady=5)
        price_entry = tk.Entry(add_win, textvariable=self.price_var)
        price_entry.grid(row=4, column=1, padx=5, pady=5)

        tk.Label(add_win, text="Cantidad:").grid(row=5, column=0, padx=5, pady=5)
        qnt_entry = tk.Entry(add_win, textvariable=self.qnt_var)
        qnt_entry.grid(row=5, column=1, padx=5, pady=5)

        tk.Button(add_win, text="Agregar", command=lambda: self.controller.add_new_product(add_win)).grid(row=6, column=0, columnspan=2, pady=10)


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
            'id': self.id_var.get().strip(),
            'name': self.name_var.get().strip(),
            'desc': self.desc_var.get().strip(),
            'brand': self.brand_var.get().strip(),
            'price': self.price_var.get().strip(),
            'qnt': self.qnt_var.get().strip(),
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
            
            return {
                'id': product_id,
                'name': values[1],
                'desc': values[2],
                'brand': values[3],
                'price': float(values[4]),
                'qnt': int(values[5]),
            }
        except (IndexError, ValueError):
            return None

    def refresh_stock_table(self, products):
        """Refrescar tabla de stock con nuevos datos"""
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)
        
        for product in products:
            self.stock_tree.insert(parent='', index='end', iid=product[0], text="", 
                                  values=product, tag="orow")
        
        self.stock_tree.tag_configure('orow', background="white", foreground='black')

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
                
                if column in ['Price', 'Quantity']:
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
