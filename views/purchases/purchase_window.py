import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

from .purchase_form import PurchaseForm
from utils.utils import iso_to_traditional, format_currency
from utils.view_helpers import center_window, close_win, show_warning, show_error
from .purchase_info_invoice_view import PurchaseInfoInvoiceView
from .purchase_info_receipt_view import PurchaseInfoReceiptView
from views.supplier_doc.supplier_invoice_form import SupplierInvoiceForm
from views.supplier_doc.supplier_receipt_form import SupplierReceiptForm
from controllers.purchase_filter_controller import PurchaseFilterController

class PurchaseWindow():
    def __init__(self, model, stock_model, frame, controller, invoice_controller, receipt_controller):
        self.model = model
        self.frame = frame
        
        self.purchase_filter = PurchaseFilterController(self.model)

        self.invoice_controller = invoice_controller
        self.invoice_controller.set_purchase_view(self)
        
        self.receipt_controller = receipt_controller
        self.receipt_controller.set_purchase_view(self)

        self.invoice_form = SupplierInvoiceForm(self, frame, invoice_controller, self.model)
        self.receipt_form = SupplierReceiptForm(self, frame, receipt_controller)

        # Set controller
        self.controller = controller
        self.controller.set_view(self)

        self.purchase_info_receipt = PurchaseInfoReceiptView(self.model, self.controller)
        self.purchase_info_invoice = PurchaseInfoInvoiceView(self.model, self.controller)
        self.purchase_form = PurchaseForm(self.model, stock_model, self.controller)

        self.controller.set_receipt_view(self.purchase_info_receipt)
        self.controller.set_invoice_view(self.purchase_info_invoice)
        self.controller.set_form_view(self.purchase_form)

    def open_purchase_window(self, parent):

        btn_color = "#009688"
        btn_hover = "#00796B"

        self.supplier_var = tk.StringVar()
        self.purchase_filter.set_supplier_var(self.supplier_var)
        self.date_var = tk.StringVar()

        self.suppliers = self.model.core.get_all_suppliers()

        win = ctk.CTkToplevel(self.frame)
        win.title("Registrar Compra a Proveedor")

        win.grab_set()
        win.transient(parent)

        win.protocol("WM_DELETE_WINDOW",lambda: close_win(win, parent))

        width_win = 1250
        height_win = 650

        btn_color = "#009688"
        btn_hover = "#00796B"

        center_window(win, width_win, height_win)
        win.configure(fg_color="#e0e0e0")

        # Configurar grilla principal
        for i in range(6):
            win.grid_rowconfigure(i, weight=0)
        win.grid_rowconfigure(3, weight=1)
        win.grid_columnconfigure(0, weight=1)
        win.grid_columnconfigure(1, weight=1)  

        select_supplier_frame = ctk.CTkFrame(win, fg_color="#f0f0f0")
        select_supplier_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=(10, 5), ipady=8, sticky="ew")

        # Configuración de grilla
        select_supplier_frame.grid_columnconfigure(0, weight=0)
        select_supplier_frame.grid_columnconfigure(1, weight=0)
        select_supplier_frame.grid_columnconfigure(2, weight=1)
        select_supplier_frame.grid_columnconfigure(3, weight=0)

        select_supplier_btn = ctk.CTkButton(
            select_supplier_frame,
            width=150,
            text="Seleccionar proveedor",
            fg_color=btn_color,
            hover_color=btn_hover,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.list_of_supplier(win)
        )
        select_supplier_btn.grid(row=0, column=0, padx=(10, 5), pady=6, sticky="w")

        select_supplier_entry = ctk.CTkEntry(
            select_supplier_frame,
            textvariable=self.supplier_var,
            font=ctk.CTkFont(size=13)
        )
        select_supplier_entry.grid(row=0, column=1, padx=5, pady=6, sticky="w")

        refresh_purchase_list_btn = ctk.CTkButton(
            select_supplier_frame,
            width=150,
            height=35,
            text="Mostrar todas las compras",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.load_purchases(False)
        )
        refresh_purchase_list_btn.grid(row=0, column=2, padx=(5, 10), pady=6)

        filter_for_date_btn = ctk.CTkButton(
            select_supplier_frame,
            width=150,
            text="Filtrar por fecha",
            fg_color=btn_color,
            hover_color=btn_hover,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.purchase_filter.filter_by_date(self.date_var.get())
        )
        filter_for_date_btn.grid(row=0, column=3, padx=(10, 5), pady=6, sticky="w")

        date_entry = ctk.CTkEntry(
            select_supplier_frame,
            textvariable=self.date_var,
            font=ctk.CTkFont(size=13),
        )
        date_entry.grid(row=0, column=4, padx=5, pady=6, sticky="w")

        # frame para productos
        product_frame = ctk.CTkFrame(win)
        product_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

        # tree view de productos
        self.purchase_tree = ttk.Treeview(product_frame, show="headings", height=8)
        self.purchase_tree["columns"] = ("Id", "Cuit", "Nombre", "Tipo Comprobante", "Fecha", 
                                        "Fecha Venc.", "Estado", "Saldo Pendiente", "Total")
        for col in self.purchase_tree["columns"]:
            self.purchase_tree.heading(col, text=col)
            if col == "Id":
                self.purchase_tree.column(col, width=60, anchor="center")
            else:
                self.purchase_tree.column(col, width=150, anchor="center")

        # Fix: forzar el estilo para que no pise los tag colors de las filas
        style = ttk.Style()
        style.map("Treeview", background=[("selected", "#0078d4")])

        # Tags para colores de filas
        self.purchase_tree.tag_configure('purchase_draft',   background="#ffebee", foreground="#b71c1c")
        self.purchase_tree.tag_configure('purchase_pending', background="#fff9e6", foreground="#6d4c00")
        self.purchase_tree.tag_configure('purchase_paid',    background="#e8f5e9", foreground="#1b5e20")
        self.purchase_tree.tag_configure('orow',             background="#ffffff", foreground="#000000")

        scroll_y = ttk.Scrollbar(product_frame, orient="vertical", command=self.purchase_tree.yview)
        scroll_x = ttk.Scrollbar(product_frame, orient="horizontal", command=self.purchase_tree.xview)
        self.purchase_tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.purchase_tree.pack(fill="both", expand=True)

        # set treeview on purchase filter controller
        self.purchase_filter.set_treeview(self.purchase_tree)

        # Leyenda de colores
        legend_frame = ctk.CTkFrame(win, fg_color="transparent")
        legend_frame.grid(row=3, column=0, columnspan=2, sticky="se", padx=16, pady=(0, 2))

        for color, fg, text in [
            ("#ffebee", "#b71c1c", " Borrador "),
            ("#fff9e6", "#6d4c00", " Pendiente de pago "),
            ("#e8f5e9", "#1b5e20", " Pagada "),
        ]:
            dot = tk.Frame(legend_frame, bg=color, width=14, height=14, relief="solid", bd=1)
            dot.pack(side="left", padx=(6, 2), pady=4)
            ctk.CTkLabel(legend_frame, text=text, font=ctk.CTkFont(size=11),
                         text_color=fg).pack(side="left")

        # --- Frame inferior (botones y cantidad) ---
        buttons_frame = ctk.CTkFrame(win)  # ← sin fg_color, usa el gris por defecto
        buttons_frame.grid(
            row=4, column=0, columnspan=2,
            padx=10, pady=(5, 15), sticky="ew"
        )
        for i in range(5):
            buttons_frame.grid_columnconfigure(i, weight=1)

        # boton Registrar Comprapo
        confirm_btn = ctk.CTkButton(
            buttons_frame,
            text="Registrar nueva compra",
            fg_color="#009688",
            hover_color="#00796B",
            height=40,
            width=90,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.open_doc_type(win)
        )
        confirm_btn.grid(row=0, column=0, padx=5, pady=10)

        add_item_btn = ctk.CTkButton(
            buttons_frame,
            text="Agregar productos a comprar",
            fg_color="#009688",
            hover_color="#00796B",
            height=40,
            width=90,            
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.open_add_item_win(win)
        ) 
        add_item_btn.grid(row=0, column=1, padx=5, pady=10)

        # boton para ver el detalle de una compra
        update_stock_btn = ctk.CTkButton(
            buttons_frame,
            text="Detalle de compra",
            fg_color="#2980B9",
            hover_color="#0B5D94",
            height=40,
            width=90,            
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.open_purchase_info(win)
        )
        update_stock_btn.grid(row=0, column=2, padx=5, pady=10)

        # boton para ver el detalle de una compra
        delete_purchase_btn = ctk.CTkButton(
            buttons_frame,
            text="Eliminar registro de compra",
            fg_color="#2980B9",
            hover_color="#0B5D94",
            height=40,
            width=90,            
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.delete_purchase
        )
        delete_purchase_btn.grid(row=0, column=3, padx=(5,15), pady=10)

        # boton Cerrar
        close_win_btn = ctk.CTkButton(
            buttons_frame,
            text="Cerrar",
            fg_color="#E74C3C",
            hover_color="#C0392B",
            height=40,
            width=90,            
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: close_win(win, parent)
        )
        close_win_btn.grid(row=0, column=4, padx=5, pady=10)

        self.load_purchases(False)

    ## -- Eliminar un registro de compra (BORRADOR) -- ##
    def delete_purchase(self):
        try:
            selected = self.purchase_tree.selection()
            if not selected:
                show_error('Por favor seleccione un Registro de Compra')
                return 
            
            iid = selected[0]
            values = self.purchase_tree.item(iid, "values")
            
            if values[6] != 'BORRADOR':
                show_error('Error. No puede eliminar una compra ya confirmada.') 
                return
            
            self.controller.delete_purchase(purchase_id=values[0], doc_type=values[2])

        except ValueError as e:
            print(f'Error al obtener la compra: {e}')
            return

    ## -- Ventana para agregar productos a una compra -- ##
    def open_add_item_win(self, parent):
        try:
            selected = self.purchase_tree.selection()
            if not selected:
                show_error('Por favor seleccione un Registro de Compra')
                return 

            iid = selected[0]
            values = self.purchase_tree.item(iid, "values")

            if values[6] != 'BORRADOR':
                show_warning('Error, no puede agregar productos a una factura ya confirmada')
                return

            self.purchase_form.show_actual_products(parent, values)

        except ValueError as e:
            print(f'Error al obtener la compra: {e}')
            return

    ## -- Tipo de comprobante -- ##
    def open_doc_type(self, parent):
        """Ventana para elegir un tipo de comprobante"""

        if self.supplier_var.get() == "":
            show_warning("Por favor seleccione un proveedor")
            return

        # Crear ventana modal
        self.doc_type_win = ctk.CTkToplevel(parent)
        self.doc_type_win.title("Seleccionar Documento")
        self.doc_type_win.configure(fg_color="#e0e0e0")
        self.doc_type_win.transient(parent)
        self.doc_type_win.grab_set()

        # Tamaño fijo de la ventana
        width_win = 350
        height_win = 220

        # Obtener info del padre para centrar
        x_root = parent.winfo_x()
        y_root = parent.winfo_y()
        width_root = parent.winfo_width()
        height_root = parent.winfo_height()

        # Calcular centro de la ventana
        x = x_root + (width_root // 2) - (width_win // 2)
        y = y_root + (height_root // 2) - (height_win // 2)

        # Aplicar geometría centrada
        self.doc_type_win.geometry(f"{width_win}x{height_win}+{x}+{y}")

        # Fondo gris
        self.doc_type_win.configure(fg_color="#e0e0e0")

        # --- s centrado ---
        card_frame = ctk.CTkFrame(
            self.doc_type_win,
            fg_color="white",
            corner_radius=20
        )
        card_frame.pack(expand=True, padx=20, pady=20, fill="both")

        # Contenedor de botones
        btn_frame = ctk.CTkFrame(card_frame, fg_color="white")
        btn_frame.pack(expand=True)

        btn_style = {
            "height": 60,
            "width": 200,
            "font": ctk.CTkFont(size=14, weight="bold")
        }

        # Botón Factura
        invoice_btn = ctk.CTkButton(
            btn_frame,
            text="Factura",
            fg_color="#009688",
            hover_color="#00796B",
            command=lambda: self.handle_selection("Factura", parent),
            **btn_style
        )
        invoice_btn.pack(pady=10)

        # Botón Otro Comprobante
        other_btn = ctk.CTkButton(
            btn_frame,
            text="Remito",
            fg_color="#3498DB",
            hover_color="#2980B9",
            command=lambda: self.handle_selection("Otro Comprobante", parent),
            **btn_style
        )
        other_btn.pack(pady=10)

    ## -- Info de la compra -- ##
    def open_purchase_info(self, parent):
        try:
            selected = self.purchase_tree.selection()
            if not selected:
                show_error('Por favor seleccione un Registro de Compra')
                return 

            iid = selected[0]
            values = self.purchase_tree.item(iid, "values")
            doc_type = values[3]

            if doc_type == 'REMITO':
                self.purchase_info_receipt.show_purchase_info(parent, values)      
            else:
                self.purchase_info_invoice.show_purchase_info(parent, values) 

        except ValueError as e:
            print(f'Error al obtener la compra: {e}')

    def handle_selection(self, doc_type, parent):
        """Función que se ejecuta al presionar cualquiera de los botones."""

        if doc_type == "Factura":
            self.invoice_form.open_invoice_form(parent, self.supplier_var.get())
        elif doc_type == "Otro Comprobante":
            self.receipt_form.open_receipt_form(parent, self.supplier_var.get())
        else:
            print('Error')
        
        # Cerrar la ventana emergente
        self.doc_type_win.grab_release()
        self.doc_type_win.destroy()

    ## -- Supplier Selection -- ##
    def list_of_supplier(self, parent):
        win = ctk.CTkToplevel(parent)
        win.title("Lista de proveedores")

        width_win = 500
        height_win = 400

        win.transient(parent)
        win.grab_set()

        # centrar ventana
        x_root = self.frame.winfo_x() 
        y_root = self.frame.winfo_y()
        width_root = self.frame.winfo_width()
        height_root = self.frame.winfo_height()        

        x = x_root + (width_root // 2) - (width_win // 2)
        y = y_root + (height_root // 2) - (height_win // 2)

        win.geometry(f"{width_win}x{height_win}+{x}+{y}")

        win.rowconfigure(0, weight=1)
        win.rowconfigure(1, weight=3)

        self.search_var = tk.StringVar()
    
        btn_color = "#009688"
        btn_hover = "#00796B"

        find_frame = ctk.CTkFrame(win)
        find_frame.grid(row=0,column=0)

        find_frame.columnconfigure(0, weight=1)
        find_frame.columnconfigure(1, weight=2)
        find_frame.columnconfigure(2, weight=1)

        find_lbl = ctk.CTkLabel(
            find_frame, 
            text="Buscar:",
            font=ctk.CTkFont(size=15, weight='bold')
        )
        find_lbl.grid(row=0, column=0, padx=(10, 5), pady=(0, 5))

        self.find_entry = ctk.CTkEntry(
            find_frame,
            width=300,
            height=35,
            textvariable=self.search_var,
            font=ctk.CTkFont(size=12),
            placeholder_text="Ingrese nombre del proveedor..."
        )
        self.find_entry.grid(row=0, column=1, padx=5)
        win.after(100,self.find_entry.focus)

        self.find_entry.bind("<KeyRelease>", self.on_key_release)
        self.search_after_id = None

        select_btn = ctk.CTkButton(
            find_frame,
            text="Seleccionar",
            font=ctk.CTkFont(size=12, weight='bold'),
            width=50,
            height=30,
            fg_color=btn_color,
            hover_color=btn_hover,
            command=lambda: self.on_click(win, parent),
        )
        select_btn.grid(row=0, column=2, padx=5)
        win.bind("<Return>", lambda event: select_btn.invoke())

        tree_frame = ctk.CTkFrame(win)
        tree_frame.grid(row=1, column=0)

        self.supplier_tree = ttk.Treeview(tree_frame, show='headings', height=10)
        self.supplier_tree["columns"] = ("cuit", "nombre")

        for col in self.supplier_tree["columns"]:
            self.supplier_tree.heading(col, text=col.capitalize())
            self.supplier_tree.column(col, anchor="center")

        self.supplier_tree.pack(side="left", fill="both", expand=True)

        for s in self.suppliers:
            self.supplier_tree.insert("", "end", values=(s[1], s[2]))

        # scrollbar
        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.supplier_tree.yview)
        self.supplier_tree.configure(yscroll=scroll.set)
        scroll.pack(side="right", fill="y")    

    def on_key_release(self, event):
        # Cancela búsquedas previas si el usuario sigue escribiendo
        if self.search_after_id:
            self.find_entry.after_cancel(self.search_after_id)
        
        # Ejecuta la búsqueda después de 150 ms
        self.search_after_id = self.find_entry.after(200, self.update_treeview_filter)

    def update_treeview_filter(self):
        query = self.find_entry.get().lower()
        # se verifica si el campo de busqueda esta vacio
        if query == "":
            self.refresh_supplier_table()
            return
        
        # limpia el tree view
        for row in self.supplier_tree.get_children():
            self.supplier_tree.delete(row)
            
        # # Filtrar la lista de proveedores
        filtered = [
            s for s in self.suppliers
            if query in s[1] or query in s[2].lower()
        ]
        
        # Insertar solo los resultados filtrados
        for s in filtered:
            self.supplier_tree.insert(
                parent='', index='end', iid=s[0],
                values=(
                    s[1],   # cuit
                    s[2]   # name
                ),
                tag="orow"
            )

        self.supplier_tree.tag_configure('orow', background="white", foreground='black')  

    def on_click(self, win, parent):
        selected = self.supplier_tree.selection()

        try:
            # primer fila seleccionada
            if not selected:
                return
            iid = selected[0]
            values = self.supplier_tree.item(iid, "values")
            self.supplier_var.set(values[0])
            self.search_var.set(values[0])

            def action():
                if parent.winfo_exists():
                    self.load_purchases(True)

                if win.winfo_exists():
                    close_win(win, parent)

            win.after(500, action)

        except ValueError as e:
            show_warning(f'Error en la seleccion del proveedor: {e}')

    def refresh_supplier_table(self):
        for item in self.supplier_tree.get_children():
            self.supplier_tree.delete(item)

        for supplier in self.suppliers:
            self.supplier_tree.insert(
                parent='', index='end', iid=supplier[0],
                values=(
                    supplier[1],   # cuit
                    supplier[2]   # name
                ),
                tag="orow"
            )

        self.supplier_tree.tag_configure('orow', background="white", foreground='black') 

    ## -- Cargar tabla de compras -- ## 
    def load_purchases(self, filter):
        if filter:
            selected_supplier = self.supplier_var.get()

            if not selected_supplier:
                return
            
            purchases = self.model.purchase.get_all_purchases(selected_supplier)

        else:
            self.supplier_var.set('')
            self.date_var.set('')
            purchases = self.model.purchase.get_all_purchases()

        # Limpiar tabla
        for item in self.purchase_tree.get_children():
            self.purchase_tree.delete(item)

        # Cargar compras
        for p in purchases:
            estado = p[8]  # índice correcto del estado
            if estado == 'BORRADOR':
                tag = "purchase_draft"
            elif estado == 'PAGADA':
                tag = "purchase_paid"
            else:
                tag = "purchase_pending"  # CONFIRMADA / pendiente de pago

            self.purchase_tree.insert(
                parent="", index="end", iid=p[0],
                values=(
                    p[0],                    # id
                    p[1],                    # cuit
                    p[2],                    # nombre
                    p[3],                    # tipo doc
                    iso_to_traditional(p[6]),# fecha
                    iso_to_traditional(p[7]),# fecha venc
                    p[8],                    # estado
                    format_currency(p[10]),  # saldo pend
                    format_currency(p[11])   # total
                ),
                tags=(tag,)
            )