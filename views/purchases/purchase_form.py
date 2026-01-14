import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import datetime

from views.view_helpers import show_warning, show_error, close_win
from models.stock import StockModel

class PurchaseForm():
    def __init__(self, model, controller=None):
        self.model = model
        self.stock_model = StockModel()
        self.controller = controller

        products = self.stock_model.get_all_products()
        self.products = [(p[0], p[1], p[2], p[10]) for p in products]

        self.find_entry = tk.StringVar()

    def set_controller(self, controller):
        """Asignar controller después de la inicialización"""
        print(f"DEBUG: Asignando controller: {controller}")
        self.controller = controller
        print(f"DEBUG: Controller asignado correctamente: {self.controller}")


    # Muestra los productos actuales
    def show_actual_products(self, parent, purchase_values):
        self.supplier_var = tk.StringVar()
        self.supplier_var.set(purchase_values[1])

        product_win = ctk.CTkToplevel(parent)
        product_win.title("Agregar Nuevo Producto")
        product_win.withdraw()
        product_win.configure(fg_color="#e0e0e0")

        main_frame = ctk.CTkFrame(product_win, corner_radius=12, fg_color="white")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # frame principal
        main_frame.columnconfigure(0, weight=3)  
        main_frame.columnconfigure(1, weight=1)

        main_frame.rowconfigure(0, weight=0)     
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=0)    

        # Campo de Busqueda
        search_frame = ctk.CTkFrame(main_frame, height=30)
        search_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(15, 5),
            pady=10
        ) 

        search_lbl = ctk.CTkLabel(
            search_frame,
            text='Buscar Producto:',
            font=ctk.CTkFont(size=14, weight='bold')
        )
        search_lbl.grid(row=0, column=0, padx=10, pady=10, sticky='w')

        self.search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.find_entry,
            width=300,
            height=35,      
        )
        self.search_entry.grid(row=0, column=1, padx=10, pady=10, sticky='ew')
        self.search_entry.focus()

        self.search_after_id = None
        self.search_entry.bind("<KeyRelease>", self.on_key_release)

        # Tabla
        product_frame = ctk.CTkFrame(main_frame)
        product_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            columnspan=2,
        )

        # tabla de productos
        self.product_tree = ttk.Treeview(product_frame, show='headings', height=10)
        self.product_tree['columns'] = ('Id', 'Nombre', 'Envase', 'Stock')

        for col in self.product_tree['columns']:
            self.product_tree.heading(col, text=col.capitalize())
            if col == "Id":
                self.product_tree.column(col, width=50, anchor='center')
            else:
                self.product_tree.column(col, width=150, anchor='center')

        self.product_tree.pack(side='left', fill='both', expand=True)

        # scrollbar
        scroll_bar = ttk.Scrollbar(product_frame, orient='vertical', command=self.product_tree.yview)
        self.product_tree.configure(yscroll=scroll_bar.set)

        scroll_bar.pack(side='right', fill='y')

        self.load_products()

        add_btn_frame = ctk.CTkFrame(main_frame, height=30)
        add_btn_frame.grid(
            row=0,
            column=1,
            sticky="ns",
            padx=(5, 15),
            pady=10
        )
        add_btn_frame.columnconfigure(0, weight=1)

        # Ejemplo botones
        ctk.CTkButton(
            add_btn_frame,
            text="Nuevo Producto",
            font=ctk.CTkFont(size=12, weight='bold'),
            command=lambda:self.open_add_window(product_win)
        ).grid(row=0, column=0, pady=5, padx=10, sticky="ew")

        ctk.CTkButton(
            add_btn_frame,
            text="Seleccionar",
            font=ctk.CTkFont(size=12, weight='bold'),
            command= lambda: self.select_product(purchase_id=purchase_values[0], parent=product_win)
        ).grid(row=1, column=0, pady=5, padx=10, sticky="ew")

        mng_btn_frame = ctk.CTkFrame(main_frame)
        mng_btn_frame.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=15,
            pady=15
        )
        mng_btn_frame.columnconfigure(0, weight=1)
        mng_btn_frame.rowconfigure(0, weight=1)

        ctk.CTkButton(
            mng_btn_frame,
            text="Listo",
            fg_color="#4CAF50",
            font=ctk.CTkFont(size=13, weight='bold'),
            command=lambda: close_win(product_win, parent)
        ).grid(row=0, column=0, padx=10, pady=10)

        # Centrar ventana
        width_win = 800
        height_win = 600

        x_root = parent.winfo_x()
        y_root = parent.winfo_y()

        width_root = parent.winfo_width()
        height_root = parent.winfo_height()

        x = x_root + (width_root // 2) - (width_win // 2)
        y = y_root + (height_root // 2) - (height_win // 2)

        product_win.geometry(f"{width_win}x{height_win}+{x}+{y}")
        product_win.deiconify()

        product_win.transient(parent)
        product_win.grab_set()

    def setup_new_product_variables(self):
        """Configurar variables del formulario"""

        self.name_var = tk.StringVar()
        self.pack_var = tk.StringVar()
        self.profit_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.iva_var = tk.StringVar()
        self.qnt_var = tk.StringVar()
        self.sale_price_var = tk.StringVar()
        self.final_price = tk.StringVar() # sale_price + iva_amount
        

    def open_add_window(self, parent):
        """Ventana para agregar nuevo producto con CustomTkinter"""
        add_win = ctk.CTkToplevel(parent)
        add_win.title("Agregar nuevo artículo")

        # se configuran las string vars
        self.setup_new_product_variables()
        
        # Hacer que la ventana sea modal
        add_win.transient(parent)
        add_win.grab_set()
    
        # Centrar la ventana

        width_win = 480
        height_win = 560

        x_parent = parent.winfo_x() 
        y_parent = parent.winfo_y()
        width_parent = parent.winfo_width()
        height_parent = parent.winfo_height()

        # centro
        x = x_parent + (width_parent // 2) - (width_win // 2)
        y = y_parent + (height_parent // 2) - (height_win // 2)

        add_win.geometry(f"{width_win}x{height_win}+{x}+{y}")
        
        card_frame = ctk.CTkFrame(
            add_win,
            fg_color='white',
            corner_radius=20
        )
        card_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Título
        title_label = ctk.CTkLabel(
            card_frame,
            text="Nuevo Artículo",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=20)

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
        
        add_field(0, "Nombre Artículo: ", 
                ctk.CTkEntry(form_frame, textvariable=self.name_var, width=200))
        
        add_field(1, "Envase: ",
                ctk.CTkComboBox(form_frame, values=["UNIDAD", "CAJA", "FRASCO", "AMPOLLA", "SOBRE", "OTRO"], 
                variable=self.pack_var, width=200, height=35))

        self.pack_var.set("UNIDAD")

        add_field(2, "Stock: ",
                ctk.CTkEntry(form_frame, textvariable=self.qnt_var, state='readonly', width=200))

        self.qnt_var.set("0")
        
        add_field(3, "Precio Costo: ", 
                ctk.CTkEntry(form_frame, textvariable=self.price_var, width=200))
        
        add_field(4, "% Rentabilidad: ",
                ctk.CTkEntry(form_frame, textvariable=self.profit_var, width=200))
        
        self.profit_var.set('0')

        add_field(5, "% Iva: ",
                ctk.CTkComboBox(form_frame, values=["21.0", "10.5", "0"], 
                variable=self.iva_var, width=200, height=35))
        
        self.iva_var.set("21.0")
        
        add_field(6, "% Precio venta: ",
                ctk.CTkEntry(form_frame, textvariable=self.sale_price_var, width=200))
        
        self.sale_price_var.set('0')

        add_field(7, "% Precio final: ",
                ctk.CTkEntry(form_frame, textvariable=self.final_price, width=200))
        
        self.final_price.set('0')

        def recalc(*args):
            try:
                cost_price = max(0, float(self.price_var.get() or 0))
                profit = max(0, float(self.profit_var.get() or 0))
                iva = float(self.iva_var.get() or 0)

                if profit > 99:
                    show_error('Error. El porcentaje de rentabilidad no puede ser mayor al 99%')
                    self.profit_var.set('0')
                    return
                
                # precio con rentabilidad
                profit_amount = cost_price * (profit / 100)
                sale_price = cost_price + profit_amount
                
                # precio con rentabilidad e iva
                iva_amount = sale_price * (iva / 100)
                sale_price_with_iva = sale_price + iva_amount

                self.sale_price_var.set(sale_price)
                self.final_price.set(sale_price_with_iva)

            except ValueError as e:
                print(f'Error: {e}')

        self.price_var.trace_add("write", recalc)
        self.profit_var.trace_add("write", recalc)
        self.iva_var.trace_add("write", recalc)

        # Botones
        button_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        button_frame.pack(pady=20)

        add_button = ctk.CTkButton(button_frame, text="Agregar", width=120, height=35, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#4CAF50", hover_color="#45a049", command=lambda: self.controller.add_new_product(add_win))
        add_button.grid(row=0, column=0, padx=10)

        cancel_button = ctk.CTkButton(button_frame, text="Cancelar", width=120, height=35, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#757575", hover_color="#616161", command=lambda: close_win(add_win, parent))
        cancel_button.grid(row=0, column=1, padx=10)

    # Seleccionar Producto
    def select_product(self, purchase_id, parent):
        try:
            selected = self.product_tree.selection()
            if not selected:
                show_error('Por favor seleccione un producto')
                return
            
            iid = selected[0]
            values = self.product_tree.item(iid, "values")
            self.open_add_purchase_item(purchase_id, parent=parent)
            self.load_item_info(product_id=values[0])

        except ValueError as e:
            show_error(f'Ocurrio un error: {e}')

    # Configuracion de Variables - Items de compra
    def setup_purchase_items_variables(self, purchase_id):
        # variables producto
        self.purchase_id = tk.StringVar()
        self.purchase_id.set(purchase_id)

        self.product_id = tk.StringVar()
        self.product_name = tk.StringVar()
        self.product_pack = tk.StringVar()
        self.quantity = tk.StringVar()
        self.cost_price = tk.StringVar()
        self.iva_rate = tk.StringVar()
        
        self.discount = tk.StringVar()
        self.discount_amount = tk.StringVar()

        self.subtotal = tk.StringVar()
        
        self.iva_amount = tk.StringVar()
        self.total_item_var = tk.StringVar()

    # Formulario para agregar items en la compra
    def open_add_purchase_item(self, purchase_id, parent):

        if self.supplier_var.get() == "":
            show_warning("Por favor seleccione un proveedor")
            return
        
        self.setup_purchase_items_variables(purchase_id)

        """Ventana para agregar nuevo producto con CustomTkinter"""
        add_win = ctk.CTkToplevel(parent)
        add_win.configure(fg_color="#e0e0e0")
        add_win.title("Agregar nuevo artículo")
        
        # Hacer que la ventana sea modalxz
        add_win.transient(parent)
        add_win.grab_set()

        # Centrar la ventana
        add_win.geometry("800x450+{}+{}".format(
            add_win.winfo_screenwidth()//2 - 200,
            add_win.winfo_screenheight()//2 - 250
        ))

        card_frame = ctk.CTkFrame(
            add_win,
            fg_color='white',
            corner_radius=20
        )
        card_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Título
        title_label = ctk.CTkLabel(
            card_frame,
            text="Nuevo Artículo",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=20)

        form_frame = ctk.CTkFrame(card_frame, fg_color='white')
        form_frame.pack(pady=5, padx=(10,0), fill='x')

        def add_field(row, column,label, witget):
            field_lbl = ctk.CTkLabel(
                form_frame,
                text=label,
                font=ctk.CTkFont(size=13, weight='bold'),
                text_color='black',
            )
            field_lbl.grid(row=row, column=column, sticky="e", padx=10, pady=7)

            witget.grid(row=row, column=column+1, padx=(10,20), pady=7, sticky='w')

        add_field(0, 0,"Id Compra:",
                ctk.CTkEntry(form_frame, textvariable=self.purchase_id, state='readonly', width=200))
        
        add_field(1, 0, "Id Producto:",
                ctk.CTkEntry(form_frame, textvariable=self.product_id, state='readonly', width=200))
        
        add_field(2, 0, "Nombre:",
                ctk.CTkEntry(form_frame, textvariable=self.product_name, width=200))
        
        add_field(3, 0, "Envase:",
                ctk.CTkComboBox(form_frame,  values=["UNIDAD", "CAJA", "FRASCO", "AMPOLLA", "SOBRE", "OTRO"], variable=self.product_pack, width=200))
        
        add_field(4, 0, "Stock:",
                ctk.CTkEntry(form_frame, textvariable=self.quantity, width=200))
        
        add_field(5, 0, "Precio Costo:",
                ctk.CTkEntry(form_frame, textvariable=self.cost_price, width=200))

        add_field(0, 2, "Porcentaje Iva:",
                ctk.CTkComboBox(form_frame, values=["21", "10.5", "0"],variable=self.iva_rate, width=200))

        add_field(1, 2, "Porcentaje Descuento:",
                ctk.CTkEntry(form_frame, textvariable=self.discount, width=200))
        
        add_field(2, 2, "Monto Descuento:",
                ctk.CTkEntry(form_frame, textvariable=self.discount_amount, state='readonly', width=200))
        
        add_field(3, 2, "SubTotal:",
                ctk.CTkEntry(form_frame, textvariable=self.subtotal, state='readonly', width=200))
        
        add_field(4, 2, "Importe Iva:",
                ctk.CTkEntry(form_frame, textvariable=self.iva_amount, state='readonly', width=200))

        add_field(5, 2, "Total:",
                ctk.CTkEntry(form_frame, textvariable=self.total_item_var, state='readonly', width=200))
        
        self.discount.set("0")

        def recalc(*args):
            try:
                qty = max(0, float(self.quantity.get() or 0))
                cost = float(self.cost_price.get() or 0)
                iva = float(self.iva_rate.get() or 0)
                discount = float(self.discount.get() or 0)

                if discount > 99:
                    show_error('Error. No puede colocar un descuento mayor al 100%')
                    return
                
                self.discount_amount.set(((qty * cost) * discount) // 100)
                print(self.discount_amount.get())

                subtotal = qty * cost - float(self.discount_amount.get())

                iva_amount = subtotal * (iva / 100)
                total = subtotal + iva_amount

                self.subtotal.set(round(subtotal, 2))
                self.iva_amount.set(round(iva_amount, 2))
                self.total_item_var.set(round(total, 2))

            except ValueError:
                pass

        self.quantity.trace_add("write", recalc)
        self.cost_price.trace_add("write", recalc)
        self.iva_rate.trace_add("write", recalc)
        self.discount.trace_add("write", recalc) 

        # Botones
        button_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        button_frame.pack(pady=20)

        add_button = ctk.CTkButton(button_frame, text="Agregar", width=120, height=35, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#4CAF50", hover_color="#45a049", command=lambda: self.controller.add_purchase_item(win=add_win, parent=parent))
        add_button.grid(row=0, column=0, padx=10)

        cancel_button = ctk.CTkButton(button_frame, text="Cancelar", width=120, height=35, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#757575", hover_color="#616161", command=add_win.destroy)
        cancel_button.grid(row=0, column=1, padx=10)

    def load_item_info(self, product_id):
        product_data = self.stock_model.get_product_by_id(product_id)

        self.product_id.set(product_data[0])
        self.product_name.set(product_data[1])
        self.product_pack.set(product_data[2])
        self.cost_price.set(product_data[4])
        self.iva_rate.set(product_data[6])

    ## -- Busqueda de un producto -- ##
    def on_key_release(self, event):
        if self.search_after_id:
            self.search_entry.after_cancel(self.search_after_id)

        self.search_after_id = self.search_entry.after(200, self.update_tree_view_filter)

    def update_tree_view_filter(self):
        query = self.find_entry.get().lower()

        if query == "":
            self.load_products()
            return
        
        for p in self.product_tree.get_children():
            self.product_tree.delete(p)

        # Filtro de lista de productos
        filtered = [
            p for p in self.products
            if query in str(p[0]) or query in p[1].lower()
        ]

        for f in filtered:
            self.product_tree.insert(
                parent='', index='end', iid=f[0], values=f
            )

    def load_products(self):
        # limpio la tabla
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)

        # cargo los productos
        for p in self.products:
            self.product_tree.insert(
                parent='', index='end', iid=p[0],
                values=p,
                tags='orow'
            )

        self.product_tree.tag_configure('orow', background="white", foreground='black')   
    
    ## -- -- ##

    ## -- Obtener los datos de un nuevo producto -- ##

    def get_new_product_data(self):
        """Obtener datos del formulario"""
        return {
            'Name': self.name_var.get().strip(),
            'Package': self.pack_var.get().strip(),
            'Profit': self.profit_var.get().strip(),
            'CostPrice': self.price_var.get().strip(),
            'Iva': self.iva_var.get().strip(),
            'Stock': self.qnt_var.get().strip(),
            'SalePrice': self.sale_price_var.get().strip(),
            'PriceWIva': self.final_price.get().strip()
        }

    ## -- -- ##

    ## -- Obtener los datos de los items de compra -- ##
    def get_purchase_item_data(self):
        return{
            'purchase_id': self.purchase_id.get().strip(),
            'product_id': self.product_id.get().strip(),
            'product_name': self.product_name.get().strip(),
            'pack': self.product_pack.get().strip(),
            'qty': self.quantity.get().strip(), 
            'cost': self.cost_price.get().strip(),
            'iva_rate': self.iva_rate.get().strip(),
            'discount': self.discount.get().strip(),
            'discount_amount': self.discount_amount.get().strip(),
            'subtotal': self.subtotal.get().strip(),
            'iva_amount': self.iva_amount.get().strip(),
            'total': self.total_item_var.get().strip()
        }
    ## -- -- ##
