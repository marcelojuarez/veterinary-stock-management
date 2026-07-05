import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import logging

from .new_product_form import NewProductForm
from utils.view_helpers import  show_error, close_win
from .new_purchase_item_form import NewPurchaseItemForm

class PurchaseForm():
    def __init__(self, model, stock_model, controller):
        self.model = model
        self.controller = controller

        self.find_entry = tk.StringVar()
        self.new_product_form = NewProductForm(self.controller)
        self.new_purchase_i_form = NewPurchaseItemForm(self.controller, stock_model)
        self.controller.set_new_p_form(self.new_product_form)
        self.controller.set_new_p_i_form(self.new_purchase_i_form)

    # Muestra los productos actuales
    def show_actual_products(self, parent, purchase_values):
        logger = logging.getLogger(__name__)

        self.supplier_var = tk.StringVar()
        self.supplier_var.set(purchase_values[1])

        local_find_entry = tk.StringVar()

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
            textvariable=local_find_entry,
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

        new_p_btn = ctk.CTkButton(
            add_btn_frame,
            text="Nuevo producto",
            font=ctk.CTkFont(size=12, weight='bold'),
            command=lambda:self.new_product_form.open_add_window(product_win)
        )
        new_p_btn.grid(row=0, column=0, pady=5, padx=10, sticky="ew")

        select_btn = ctk.CTkButton(
            add_btn_frame,
            text="Seleccionar",
            font=ctk.CTkFont(size=12, weight='bold'),
            command= lambda: self.select_product(purchase_id=purchase_values[0], parent=product_win)
        )
        select_btn.grid(row=1, column=0, pady=5, padx=10, sticky="ew")

        product_win.bind('<Return>', lambda event: select_btn.invoke())        

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

        def on_close():
            try:
                local_find_entry.set("")
                product_win.destroy()
                parent.after(50, lambda: parent.focus_force())
            except Exception as e:
                logger.error("Error al cerrar la ventana: %s", e)       

        ctk.CTkButton(
            mng_btn_frame,
            text="Listo",
            fg_color="#4CAF50",
            font=ctk.CTkFont(size=13, weight='bold'),
            command=on_close
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

        product_win.protocol("WM_DELETE_WINDOW", on_close)       
        product_win.transient(parent)
        product_win.grab_set()
        
    # Seleccionar Producto
    def select_product(self, purchase_id, parent):
        try:
            selected = self.product_tree.selection()
            if not selected:
                show_error('Por favor seleccione un producto')
                return
            
            iid = selected[0]
            values = self.product_tree.item(iid, "values")

            # Determinar si la factura discrimina IVA consultando el modelo
            discrimina_iva = self.controller.get_discrimina_iva(purchase_id)

            self.new_purchase_i_form.open_add_purchase_item(
                purchase_id, parent=parent, discrimina_iva=discrimina_iva
            )
            self.new_purchase_i_form.load_item_info(product_id=values[0])

        except ValueError as e:
            show_error(f'Ocurrio un error: {e}')

    ## -- Busqueda de un producto -- ##
    def on_key_release(self, event):
        if self.search_after_id:
            self.search_entry.after_cancel(self.search_after_id)

        self.search_after_id = self.search_entry.after(200, self.update_tree_view_filter)

    def update_tree_view_filter(self):
        query = self.search_entry.get().lower()

        if query == "":
            self.load_products()
            return
        
        for p in self.product_tree.get_children():
            self.product_tree.delete(p)

        # Filtro de lista de productos
        filtered = [
            p for p in self.controller.products
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
        for p in self.controller.products:
            self.product_tree.insert(
                parent='', index='end', iid=p[0],
                values=p,
                tags='orow'
            )

        self.product_tree.tag_configure('orow', background="white", foreground='black')