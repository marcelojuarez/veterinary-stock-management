import logging
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

from .purchase_form import PurchaseForm

logger = logging.getLogger(__name__)
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
        self.receipt_form = SupplierReceiptForm(self, frame, receipt_controller, self.model)

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

        self.supplier_id_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.purchase_filter.set_supplier_id_var(self.supplier_id_var)
        self.purchase_filter.set_search_var(self.search_var)
        self.date_var = tk.StringVar()
        self.invoice_number_var = tk.StringVar()

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
        select_supplier_frame.grid(row=1, column=0, columnspan=2, pady=(5,0), sticky="ew")

        # Configuración de grilla
        select_supplier_frame.grid_columnconfigure(0, weight=0)
        select_supplier_frame.grid_columnconfigure(1, weight=0)
        select_supplier_frame.grid_columnconfigure(2, weight=1)
        select_supplier_frame.grid_columnconfigure(3, weight=0)

        select_supplier_btn = ctk.CTkButton(
            select_supplier_frame,
            width=150,
            text="Seleccionar Proveedor",
            fg_color=btn_color,
            hover_color=btn_hover,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.list_of_supplier(win)
        )
        select_supplier_btn.grid(row=0, column=0, padx=(10, 5), pady=5, sticky="w")

        select_supplier_entry = ctk.CTkEntry(
            select_supplier_frame,
            textvariable=self.search_var,
            width=200,
            font=ctk.CTkFont(size=12)
        )
        select_supplier_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        refresh_purchase_list_btn = ctk.CTkButton(
            select_supplier_frame,
            width=150,
            height=35,
            text="Mostrar todas las compras",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.load_purchases(False)
        )
        refresh_purchase_list_btn.grid(row=0, column=2, padx=(5, 10), pady=5)

        filter_for_date_btn = ctk.CTkButton(
            select_supplier_frame,
            width=180,
            text="Filtrar por fecha",
            fg_color=btn_color,
            hover_color=btn_hover,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.purchase_filter.filter_by_date(self.date_var.get(), self.invoice_number_var)
        )
        filter_for_date_btn.grid(row=0, column=3, padx=(10, 5), pady=5, sticky="w")

        date_entry = ctk.CTkEntry(
            select_supplier_frame,
            textvariable=self.date_var,
            font=ctk.CTkFont(size=12),
        )
        date_entry.grid(row=0, column=4, padx=5, pady=5, sticky="w")

        filter_for_invoice_btn = ctk.CTkButton(
            select_supplier_frame,
            width=180,
            text="Filtrar por N° de factura",
            fg_color=btn_color,
            hover_color=btn_hover,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.purchase_filter.filter_by_invoice_number(self.invoice_number_var.get())
        )
        filter_for_invoice_btn.grid(row=1, column=3, padx=(10, 5), pady=5, sticky="w")

        invoice_entry = ctk.CTkEntry(
            select_supplier_frame,
            textvariable=self.invoice_number_var,
            font=ctk.CTkFont(size=12),
        )
        invoice_entry.grid(row=1, column=4, padx=5, pady=5, sticky="w")

        # frame para productos
        product_frame = ctk.CTkFrame(win)
        product_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

        # tree view de productos
        self.purchase_tree = ttk.Treeview(product_frame, show="headings", height=8)
        self.purchase_tree["columns"] = ("Id", "Cuit", "Nombre", "Tipo Comprobante", "Fecha", 
                                        "Fecha Venc.", "Estado", "Saldo Pendiente", "Total")
        column_widths = {
            "Id": 50,
            "Cuit": 110,
            "Nombre": 180,
            "Tipo Comprobante": 140,
            "Fecha": 90,
            "Fecha Venc.": 110,
            "Estado": 110,
            "Saldo Pendiente": 140,
            "Total": 120
        }

        for col in self.purchase_tree["columns"]:
            self.purchase_tree.heading(col, text=col)
            self.purchase_tree.column(col, width=column_widths[col], anchor="center", stretch=False)

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
            logger.error("Error al obtener la compra: %s", e)
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
            logger.error("Error al obtener la compra: %s", e)
            return

    ## -- Tipo de comprobante -- ##
    def open_doc_type(self, parent):
        """Ventana para elegir un tipo de comprobante"""

        if self.supplier_id_var.get() == "":
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
            logger.error("Error al obtener la compra: %s", e)

    def handle_selection(self, doc_type, parent):

        if self.doc_type_win.winfo_exists():
            self.doc_type_win.grab_release()
            self.doc_type_win.destroy()

        def open_next():
            if doc_type == "Factura":
                self.invoice_form.open_invoice_form(parent, self.supplier_id_var.get())
            else:
                self.receipt_form.open_receipt_form(parent, self.supplier_id_var.get())

        parent.after(10, open_next)

    ## -- Supplier Selection -- ##
    def list_of_supplier(self, parent):
        win = ctk.CTkToplevel(parent)
        win.title("Lista de proveedores")

        width_win = 570
        height_win = 480

        win.transient(parent)
        win.grab_set()

        x = self.frame.winfo_x() + (self.frame.winfo_width() // 2) - (width_win // 2)
        y = self.frame.winfo_y() + (self.frame.winfo_height() // 2) - (height_win // 2)
        win.geometry(f"{width_win}x{height_win}+{x}+{y}")

        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(1, weight=1)

        btn_color = "#009688"
        btn_hover = "#00796B"

        # ---------- BUSCADOR ----------
        find_frame = ctk.CTkFrame(win)
        find_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=10)

        find_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            find_frame,
            text="Buscar:",
            font=ctk.CTkFont(size=15, weight='bold')
        ).grid(row=0, column=0, padx=(15,10), pady=12, sticky="w")

        search_after_id = [None]

        find_entry = ctk.CTkEntry(
            find_frame,
            height=36,
            font=ctk.CTkFont(size=12, weight='bold'),
            placeholder_text="Ingrese nombre del proveedor..."
        )

        find_entry.focus()
        find_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        select_btn = ctk.CTkButton(
            find_frame,
            text="Seleccionar",
            font=ctk.CTkFont(size=12, weight='bold'),
            width=110,
            height=34,
            fg_color=btn_color,
            hover_color=btn_hover,
            command=lambda: on_click(),
        )
        select_btn.grid(row=0, column=2, padx=(10,15), pady=10)

        # ---------- TABLA ----------
        tree_frame = ctk.CTkFrame(win)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))

        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        supplier_tree = ttk.Treeview(tree_frame, show='headings')
        supplier_tree["columns"] = ("cuit", "nombre")

        for col in supplier_tree["columns"]:
            supplier_tree.heading(col, text=col.capitalize())
            supplier_tree.column(col, anchor="center")

        supplier_tree.grid(row=0, column=0, sticky="nsew")

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=supplier_tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")

        supplier_tree.configure(yscroll=scroll.set)

        for s in self.suppliers:
            supplier_tree.insert("", "end", iid=s[0], values=(s[1], s[2]))

        # ---------- FUNCIONES ----------
        def refresh_table():
            for item in supplier_tree.get_children():
                supplier_tree.delete(item)

            for s in self.suppliers:
                supplier_tree.insert('', 'end', iid=s[0], values=(s[1], s[2]), tag="orow")

            supplier_tree.tag_configure('orow', background="white", foreground='black')

        def update_filter():
            if not win.winfo_exists():
                return

            query = find_entry.get().lower()

            if query == "":
                refresh_table()
                return

            for row in supplier_tree.get_children():
                supplier_tree.delete(row)

            filtered = [s for s in self.suppliers if query in s[1] or query in s[2].lower()]

            for s in filtered:
                supplier_tree.insert('', 'end', iid=s[0], values=(s[1], s[2]), tag="orow")

            supplier_tree.tag_configure('orow', background="white", foreground='black')

        def on_key_release(event):
            if not win.winfo_exists():
                return

            if search_after_id[0]:
                find_entry.after_cancel(search_after_id[0])

            search_after_id[0] = find_entry.after(200, update_filter)

        def on_click():
            selected = supplier_tree.selection()

            if not selected:
                return

            iid = selected[0]
            values = supplier_tree.item(iid, "values")

            self.supplier_id_var.set(iid)
            self.search_var.set(values[1])
            self.invoice_number_var.set('')

            if search_after_id[0]:
                find_entry.after_cancel(search_after_id[0])

            def action():
                if parent.winfo_exists():
                    self.load_purchases(True)

                if win.winfo_exists():
                    close_win(win, parent)

            action()

        def on_close():
            if search_after_id[0]:
                find_entry.after_cancel(search_after_id[0])

            win.destroy()

        find_entry.bind("<KeyRelease>", on_key_release)

        win.protocol("WM_DELETE_WINDOW", on_close)
        win.bind("<Return>", lambda event: select_btn.invoke())
 

    ## -- Cargar tabla de compras -- ## 
    def load_purchases(self, filter):
        if filter:
            selected_supplier = self.supplier_id_var.get()

            if not selected_supplier:
                return
            
            purchases = self.model.purchase.get_all_purchases(selected_supplier)

        else:
            self.search_var.set('')
            self.supplier_id_var.set('')
            self.date_var.set('')
            self.invoice_number_var.set('')
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