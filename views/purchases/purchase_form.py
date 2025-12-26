import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import datetime

from views.view_helpers import show_warning, close_win
from models.stock import StockModel

class PurchaseForm():
    def __init__(self, model):
        self.model = model
        self.stock_model = StockModel()

        products = self.stock_model.get_all_products()
        self.products = [(p[0], p[2], p[3], p[11]) for p in products]

        self.entry_var = tk.StringVar()

    def set_controller(self, controller):
        """Asignar controller después de la inicialización"""
        print(f"DEBUG: Asignando controller: {controller}")
        self.controller = controller
        print(f"DEBUG: Controller asignado correctamente: {self.controller}")

    def setup_purchase_variables(self, supplier_cuit):
        self.supplier_var = tk.StringVar()
        self.supplier_var.set(supplier_cuit)

        self.exp = tk.StringVar()
        self.doc_type = tk.StringVar()
        self.total = tk.StringVar()
        self.obs = tk.StringVar()
        self.state = tk.StringVar()

    def show_actual_products(self, parent, values):
        product_win = ctk.CTkToplevel(parent)
        product_win.title("Agregar Nuevo Producto")
        product_win.withdraw()
        product_win.configure(fg_color="#e0e0e0")

        product_win.transient(parent)
        product_win.grab_set()

        x = (parent.winfo_screenwidth() // 2) - 300
        y = (parent.winfo_screenheight() // 2) - 250
        product_win.geometry(f"800x600+{x}+{y}")

        product_win.update_idletasks()
        product_win.deiconify()

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
            text='Buscar Producto:'
        )
        search_lbl.grid(row=0, column=0, padx=10, pady=10, sticky='w')

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
            text="Nuevo Producto"
        ).grid(row=0, column=0, pady=(10, 5), padx=10, sticky="ew")

        ctk.CTkButton(
            add_btn_frame,
            text="Seleccionar"
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
        mng_btn_frame.columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            mng_btn_frame,
            text="Aceptar",
            fg_color="#4CAF50",
            font=ctk.CTkFont(size=13, weight='bold'),
        ).grid(row=0, column=0, padx=10, pady=10, sticky="e")

        ctk.CTkButton(
            mng_btn_frame,
            text="Cancelar",
            fg_color="#757575",
            font=ctk.CTkFont(size=13, weight='bold'),
            command=lambda: close_win(product_win, parent)
        ).grid(row=0, column=1, padx=10, pady=10, sticky="w")


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

    def setup_product_variables(self):
        # variables producto
        self.name_product_var = tk.StringVar()
        self.description_var = tk.StringVar()
        self.brand_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.quantity_var = tk.StringVar()

    def open_add_purchase_window(self, parent, supplier_cuit):
        btn_color = "#009688"
        btn_hover = "#00796B"

        self.setup_purchase_variables(supplier_cuit)
        actual_date = datetime.datetime.now()
        formated_act_date = actual_date.strftime("%d/%m/%Y")

        if supplier_cuit == "":
            show_warning("Por favor seleccione un proveedor")
            return

        self.purchase_win = ctk.CTkToplevel(self.frame)
        self.purchase_win.title("Registrar Compra")

        # Modal
        self.purchase_win.transient(parent)
        self.purchase_win.grab_set()

        # Config grid
        self.purchase_win.columnconfigure(0, weight=0)
        self.purchase_win.columnconfigure(1, weight=1)

        # Cerrar ventana
        self.purchase_win.protocol("WM_DELETE_WINDOW",
                                lambda: close_win(self.purchase_win, parent))

        # Centrar
        self.purchase_win.geometry("500x450+{}+{}".format(
            self.purchase_win.winfo_screenwidth()//2 - 240,
            self.purchase_win.winfo_screenheight()//2 - 360
        ))

        # Título
        title = ctk.CTkLabel(
            self.purchase_win,
            text="Nueva Compra",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.grid(row=0, column=0, columnspan=2, pady=30)

        # CUIT proveedor
        cuit_lbl = ctk.CTkLabel(
            self.purchase_win,
            text="Cuit Proveedor:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        cuit_lbl.grid(row=1, column=0, padx=(20,10), pady=5)

        cuit_entry = ctk.CTkEntry(
            self.purchase_win,
            textvariable=self.supplier_var,
            width=230,
            height=35,
            font=ctk.CTkFont(size=14)
        )
        cuit_entry.grid(row=1, column=1, padx=(15,20), pady=5)
        cuit_entry.configure(state="readonly")

        # Fecha de vencimiento
        exp_lbl = ctk.CTkLabel(self.purchase_win, text="Vencimiento:", font=ctk.CTkFont(size=14, weight="bold"))
        exp_lbl.grid(row=2, column=0, padx=(20,10), pady=5)

        exp_entry = ctk.CTkEntry(
            self.purchase_win,
            textvariable=self.exp,
            width=230,
            height=35
        )
        self.exp.set(formated_act_date)
        exp_entry.grid(row=2, column=1, padx=(15,20), pady=5)

        # Tipo de Comprobante
        doc_lbl = ctk.CTkLabel(self.purchase_win, text="Tipo de Comprobante:", font=ctk.CTkFont(size=14, weight="bold"))
        doc_lbl.grid(row=3, column=0, padx=(15,20), pady=5)

        doc_combo = ctk.CTkComboBox(
            self.purchase_win,
            values=["FACTURA", "REMITO"],
            variable=self.doc_type,
            width=230,
            state="readonly"            
        )
        doc_combo.set("FACTURA")
        doc_combo.grid(row=3, column=1, padx=(15,20), pady=5)

        # Observaciones
        obs_lbl = ctk.CTkLabel(self.purchase_win, text="Observaciones:", font=ctk.CTkFont(size=14, weight="bold"))
        obs_lbl.grid(row=4, column=0, padx=(20,10), pady=5)

        obs_entry = ctk.CTkEntry(
            self.purchase_win,
            textvariable=self.obs,
            width=230,
            height=80
        )
        obs_entry.grid(row=4, column=1, padx=(15,20), pady=5)

        # Estado de compra
        state_lbl = ctk.CTkLabel(self.purchase_win, text="Estado:", font=ctk.CTkFont(size=14, weight="bold"))
        state_lbl.grid(row=5, column=0, padx=(20,10), pady=5)

        state_combo = ctk.CTkComboBox(
            self.purchase_win,
            values=["PENDIENTE", "PAGADA", "CANCELADA"],
            variable=self.state,
            width=230,
            state="readonly"
        )
        state_combo.set("")
        state_combo.grid(row=5, column=1, padx=(15,20), pady=5)

        # Total
        total_lbl = ctk.CTkLabel(self.purchase_win, text="Total:", font=ctk.CTkFont(size=14, weight="bold"))
        total_lbl.grid(row=6, column=0, padx=(20,10), pady=5)

        total_entry = ctk.CTkEntry(
            self.purchase_win,
            textvariable=self.total,
            width=230
        )
        total_entry.grid(row=6, column=1, padx=(15,20), pady=5)

        # Botón Guardar
        save_btn = ctk.CTkButton(
            self.purchase_win,
            text="Continuar",
            height=40,
            fg_color=btn_color,
            hover_color=btn_hover,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda: self.controller.register_purchase(self.purchase_win, parent)
        )
        save_btn.grid(row=7, column=0, columnspan=1, pady=20)

        cancel_btn = ctk.CTkButton(
            self.purchase_win,
            text="Cancelar",
            height=40,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=lambda: close_win(self.purchase_win, parent)
        )
        cancel_btn.grid(row=7, column=2, columnspan=1, pady=20)

    def open_add_purchase_product(self, supplier_cuit, parent=None):

        if supplier_cuit == "":
            show_warning("Por favor seleccione un proveedor")
            return
        
        """Ventana para agregar nuevo producto con CustomTkinter"""
        add_win = ctk.CTkToplevel(parent if parent else self.frame)
        add_win.title("Agregar nuevo artículo")
        
        # Hacer que la ventana sea modal
        add_win.transient(parent)
        add_win.grab_set()

        # Centrar la ventana
        add_win.geometry("400x600+{}+{}".format(
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
            ("Código:", self.stock_view.id_var),
            ("Cuit Proveedor:", self.stock_view.cuit_supplier),
            ("Nombre Artículo:", self.stock_view.name_var),
            ("Precio Costo:", self.stock_view.price_var),
            ("% Rentabilidad:", self.stock_view.profit_var),
            ("Cantidad de Artículos:", self.stock_view.qnt_var)
        ]

        self.stock_view.cuit_supplier.set(supplier_cuit)

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
            variable=self.stock_view.pack_var,
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
            variable=self.stock_view.iva_var,
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
            fg_color="#4CAF50", hover_color="#45a049", command=lambda: self.controller.add_supplier_product())
        add_button.grid(row=0, column=0, padx=10)

        cancel_button = ctk.CTkButton(button_frame, text="Cancelar", width=120, height=35, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#757575", hover_color="#616161", command=add_win.destroy)
        cancel_button.grid(row=0, column=1, padx=10)

    def clear_purchase_form(self):
        """Limpiar formulario de compra"""
        self.supplier_var.set('')
        self.exp.set('')
        self.doc_type.set('')
        self.total.set('')
        self.obs.set('')
        self.state.set('')

    def get_purchase_data(self):
        return{
            'supplier_cuit': self.supplier_var.get().strip(),
            'expiration': self.exp.get().strip(),
            'doc_type': self.doc_type.get().strip(),
            'observations': self.obs.get().strip(),
            'state': self.state.get().strip(), 
            'total': self.total.get().strip(),
        }