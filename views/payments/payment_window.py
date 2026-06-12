import logging
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from .payment_form import PaymentForm
from .payment_info import PaymentInfo
from utils.view_helpers import center_window, close_win, show_warning, show_error
from utils.utils import iso_to_traditional, format_currency

logger = logging.getLogger(__name__)

# Configurar tema y colores
ctk.set_appearance_mode("light")  # "light" o "dark"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class PaymentWindow():
    def __init__(self, model, frame, controller):
        self.model = model
        self.frame = frame

        checks_model   = getattr(controller, 'checks_model',    None)
        supplier_credit = getattr(controller, 'supplier_credit', None)
        self.payment_form = PaymentForm(self, model, frame, checks_model=checks_model, supplier_credit=supplier_credit)

        self.controller = controller
        self.controller.set_pay_view(self)
        self.controller.set_form_view(self.payment_form)

        self.payment_form.set_controller(self.controller)

        self.payment_info = PaymentInfo(self.model)

    # Ventana para registrar un nuevo pago
    def open_payment_window(self, parent):

        btn_color = "#009688"
        btn_hover = "#00796B"

        self.supplier_id_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.debt_var = tk.StringVar()
        self.formatted_debt_var = tk.StringVar()
        self.supplier_credit_var = tk.StringVar()
        self.formatted_s_credit_var = tk.StringVar()
        self.suppliers = self.model.core.get_all_suppliers()
            
        win = ctk.CTkToplevel(self.frame)
        win.title("Registrar Pago a Proveedor")
        center_window(win, 1100, 600)
        win.transient(parent)
        win.grab_set()

        win.protocol("WM_DELETE_WINDOW", lambda: close_win(win, parent, self.clear_supplier_field))
        
        # Configurar grilla principal
        for i in range(6):
            win.grid_rowconfigure(i, weight=0)
        win.grid_rowconfigure(3, weight=1)
        win.grid_columnconfigure(0, weight=1)
        win.grid_columnconfigure(1, weight=1)

        select_supplier_frame = ctk.CTkFrame(win,fg_color="#f0f0f0")
        select_supplier_frame.grid(row=1, column=0, columnspan=2, pady=(5,0), sticky="ew")    

        select_supplier_frame.grid_columnconfigure(0, weight=0)  # botón seleccionar
        select_supplier_frame.grid_columnconfigure(1, weight=0)  # entry
        select_supplier_frame.grid_columnconfigure(2, weight=0)  # espacio flexible empuja a los extremos
        select_supplier_frame.grid_columnconfigure(3, weight=0)  # debt_frame
        select_supplier_frame.grid_columnconfigure(4, weight=0)  # refresh_btn

        select_supplier_btn = ctk.CTkButton(
            select_supplier_frame,
            width=140,
            text="Seleccionar Proveedor",
            fg_color=btn_color,
            hover_color=btn_hover,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.list_of_supplier(win)
        )
        select_supplier_btn.grid(row=0, column=0, padx=(10, 5), sticky="w")

        select_supplier_entry = ctk.CTkEntry(
            select_supplier_frame,
            textvariable=self.search_var,
            width=200,
            font=ctk.CTkFont(size=12),
        )
        select_supplier_entry.grid(row=0, column=1, sticky="w")

        debt_frame = ctk.CTkFrame(
            select_supplier_frame,
            fg_color=btn_color,
            corner_radius=12
        )        
        debt_frame.grid(row=0, column=2, padx=(10, 5), pady=5, sticky="w")

        debt_lbl = ctk.CTkLabel(
            debt_frame,
            text="Deuda Proveedor",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#f8fffe"
        )
        debt_lbl.grid(row=0, column=0, padx=15, pady=5, sticky="w")

        debt_entry = ctk.CTkEntry(
            debt_frame,
            textvariable=self.formatted_debt_var,
            width=120,
            corner_radius=10,
            fg_color="white",
            state='readonly'
        )
        debt_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        credit_frame = ctk.CTkFrame(
            select_supplier_frame,
            fg_color=btn_color,
            corner_radius=12
        )
        credit_frame.grid(row=0, column=3, padx=(0, 5), pady=5, sticky="w")

        ctk.CTkLabel(
            credit_frame,
            text="Saldo a Favor",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#f8fffe"
        ).grid(row=0, column=0, padx=15, pady=5, sticky="w")

        ctk.CTkEntry(
            credit_frame,
            textvariable=self.formatted_s_credit_var,
            width=120,
            corner_radius=10,
            fg_color="white",
            state='readonly'
        ).grid(row=0, column=1, padx=5, pady=5, sticky="w")        

        refresh_btn = ctk.CTkButton(
            select_supplier_frame,
            width=150,
            height=35,
            text="Mostrar Todas las Compras",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.load_purchase_history(False)
        )
        refresh_btn.grid(row=0, column=4, padx=(0, 10), sticky="e")

        # notebook para las tablas
        payment_notebook = ttk.Notebook(win)
        payment_notebook.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

        # add frames to the notebook
        payment_notebook.add(self.set_movement_tree(payment_notebook), text='Movimientos')
        payment_notebook.add(self.set_purchase_tree(payment_notebook), text='Registros de Compra')

        self.load_payment_movement()

        # frame inferior (botones y cantidad)
        buttons_frame = ctk.CTkFrame(win, corner_radius=20)
        buttons_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
        for i in range(5):
            buttons_frame.grid_columnconfigure(i, weight=1)

        # Botón Registrar Compra
        confirm_btn = ctk.CTkButton(
            buttons_frame,
            text="Registrar Pago Multiple",
            fg_color="#3C8A3E",
            hover_color="#45a049",
            height=40,
            width=90,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda: self.payment_form.add_payment_win(
                win, 
                self.supplier_id_var.get(),
                purchase_id=None,
                amount=self.debt_var.get()
            )
        )
        confirm_btn.grid(row=0, column=0, padx=5, pady=10)

        # Pagar compra
        confirm_btn = ctk.CTkButton(
            buttons_frame,
            text="Registrar Pago",
            fg_color="#3C8A3E",
            hover_color="#45a049",
            height=40,
            width=90,
            font=ctk.CTkFont(size=14, weight="bold"),
            command= lambda: self.pay_for_a_purchase(win)
        )
        confirm_btn.grid(row=0, column=1, padx=5, pady=10)

        # Botón Registrar Compra
        info_btn = ctk.CTkButton(
            buttons_frame,
            text="Info Registro de Pago",
            fg_color="#898A3C",
            hover_color="#b5ae4e",
            height=40,
            width=90,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda: self.open_payment_info(win)
        )
        info_btn.grid(row=0, column=2, padx=5, pady=10)

        # Botón Registrar Compra
        confirm_btn = ctk.CTkButton(
            buttons_frame,
            text="Eliminar Registro de Pago",
            fg_color="#050D06",
            hover_color="#4f4f4f",
            height=40,
            width=90,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        confirm_btn.grid(row=0, column=3, padx=5, pady=10)

        # Botón Cerrar
        close_win_btn = ctk.CTkButton(
            buttons_frame,
            text="Cerrar",
            fg_color="#E74C3C",
            hover_color="#C0392B",
            height=40,
            width=90,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda: close_win(win, parent, self.clear_supplier_field)
        )
        close_win_btn.grid(row=0, column=4, padx=(15,0), pady=10)

        self.load_purchase_history(False)
    
    ## -- Limpiar el campo de supplier-- ##
    def clear_supplier_field(self):
        self.supplier_id_var.set('')

    ## -- Configura la tabla de movimientos -- ##
    def set_movement_tree(self, win):
        # frame para movimientos
        movement_frame = ctk.CTkFrame(win)
        movement_frame.pack(fill='both', expand=True)

        self.movement_tree = ttk.Treeview(movement_frame, show="headings", height=8)
        self.movement_tree["columns"] = ("ID", "PROVEEDOR", "CUIT", "MONTO", "METODO DE PAGO", "OBSERVACION", "FECHA")
        col_widths = {"ID": 50, "PROVEEDOR": 180, "CUIT": 130, "MONTO": 100, "METODO DE PAGO": 130, "OBSERVACION": 150, "FECHA": 100}
        for col in self.movement_tree["columns"]:
            self.movement_tree.heading(col, text=col.capitalize())
            self.movement_tree.column(col, width=col_widths.get(col, 120), anchor="center")
        self.movement_tree.pack(side="left", fill="both", expand=True)

        # scrollbar 
        scroll = ttk.Scrollbar(movement_frame, orient="vertical", command=self.movement_tree.yview)
        self.movement_tree.configure(yscroll=scroll.set)
        scroll.pack(side="right", fill="y")
        
        return movement_frame

    ## -- Configura la tabla de compras -- ##
    def set_purchase_tree(self, notebook):
        purchase_frame = ctk.CTkFrame(notebook)
        purchase_frame.pack(fill='both', expand=True)

        self.purchase_tree = ttk.Treeview(purchase_frame, show="headings", height=8)
        self.purchase_tree["columns"] = ("ID", "supplier_id", "Cuit Proveedor", "Nombre Proveedor", "Tipo Comprobante", "Fecha",
                                         "Fecha Venc.", "Estado", "Saldo Pendiente", "Total")

        col_widths = {
            "ID":               50,
            "supplier_id":       0,
            "Cuit Proveedor":  110,
            "Nombre Proveedor":150,
            "Tipo Comprobante": 110,
            "Fecha":            85,
            "Fecha Venc.":      85,
            "Estado":           80,
            "Saldo Pendiente":  100,
            "Total":            90,
        }
        for col in self.purchase_tree["columns"]:
            if col == "supplier_id":
                self.purchase_tree.column(col, width=0, stretch=False)
                continue
            self.purchase_tree.heading(col, text=col)
            self.purchase_tree.column(col, width=col_widths.get(col, 100),
                                      anchor="center", minwidth=50, stretch=True)

        sx = ttk.Scrollbar(purchase_frame, orient="horizontal", command=self.purchase_tree.xview)
        sy = ttk.Scrollbar(purchase_frame, orient="vertical",   command=self.purchase_tree.yview)
        self.purchase_tree.configure(xscrollcommand=sx.set, yscrollcommand=sy.set)

        sx.pack(side="bottom", fill="x")
        sy.pack(side="right",  fill="y")
        self.purchase_tree.pack(side="left", fill="both", expand=True)

        # Tags de color por estado
        self.purchase_tree.tag_configure("PENDIENTE", background="#FFF9C4")
        self.purchase_tree.tag_configure("PAGADA",    background="#E8F5E9")
        self.purchase_tree.tag_configure("BORRADOR",  background="#F5F5F5")
        self.purchase_tree.tag_configure("orow",      background="white")

        return purchase_frame

    ## -- Info de Pago -- ##
    def open_payment_info(self, parent):
        try:
            selected = self.movement_tree.selection()

            if not selected:
                show_error("Por favor: selecciona un registro de pago")
                return

            iid = selected[0]
            values = self.movement_tree.item(iid, "values")
            self.payment_info.show_payment_info(parent, values)

        except ValueError as e:
            logger.error("Error al seleccionar registro de pago: %s", e)
            return

    ## -- Pago de una compra -- ##
    def pay_for_a_purchase(self, parent):

        try:

            selected = self.purchase_tree.selection()

            if not selected:
                show_warning('Por favor selecciona una compra')
                return

            iid = selected[0]
            values = self.purchase_tree.item(iid, "values")

            if values[7] in ("PAGADA", "CANCELADA"):
                show_warning(f'No puede pagar una compra: {values[7]}')
                return

            purchase_id = values[0]
            supplier_id = values[1]

            self.supplier_id_var.set(supplier_id)

            supplier_data = self.model.core.find_supplier_by_id(supplier_id)
            self.search_var.set(supplier_data[2])

            self.load_purchase_history(True)

            self.payment_form.add_payment_win(
                parent=parent,
                supplier_id=supplier_id,
                purchase_id=purchase_id,
                amount=values[8]
            )

        except ValueError as e:
            show_warning(f'Error en la selección de la compra: {e}')

    ## --  Carga de tabla de movimientos -- ##
    def load_payment_movement(self, supplier_id=None):
        if supplier_id is None:
            payments = self.model.payment.get_all_payments()

        else:
            payments = self.model.payment.get_all_payments(supplier_id)

        # Limpiar tabla
        for item in self.movement_tree.get_children():
            self.movement_tree.delete(item)
        # Cargar productos
        for p in payments:
            self.movement_tree.insert(
                parent='', index='end', iid=p[0],
                values=(
                   p[0],  # id
                   p[1],  # nombre proveedor
                   p[2],  # cuit
                   p[4],  # monto
                   p[5],  # metodo
                   p[6],  # observation
                   iso_to_traditional(p[12])  # fecha
                ),
                tag="orow"
            )
            
        self.movement_tree.tag_configure('orow', background="white", foreground='black')     

    ## -- Funcion para cargar compras -- ##
    def load_purchase_history(self, filter):

        if filter:
            selected_supplier = self.supplier_id_var.get()
            if not selected_supplier:
                show_warning("Atención", "Primero selecciona un proveedor.")
                return
            
            debt = self.model.purchase.get_debt_of_supplier(selected_supplier)
            credit_amount = self.model.credit.get_credit_amount_of_supplier(selected_supplier)
            
            # Monto deuda
            self.debt_var.set(debt)
            self.formatted_debt_var.set(format_currency(debt))

            # Monto saldo a favor
            self.supplier_credit_var.set(credit_amount)
            self.formatted_s_credit_var.set(format_currency(credit_amount))
            purchases = self.model.purchase.get_all_confirmed_purchases(selected_supplier)

        else:
            self.supplier_id_var.set('')
            self.search_var.set('')

            # Monto deuda
            self.debt_var.set('')
            self.formatted_debt_var.set('')

            # Monto saldo a favor
            self.supplier_credit_var.set('')
            self.formatted_s_credit_var.set('')
            purchases = self.model.purchase.get_all_confirmed_purchases()
            self.load_payment_movement()

        # Limpiar tabla
        for item in self.purchase_tree.get_children():
            self.purchase_tree.delete(item)

        # Cargar compras
        for p in purchases:

            state = p[9]

            self.purchase_tree.insert(
                "",
                "end",
                iid=p[0],
                values=(
                    p[0],      # id compra
                    p[1],      # supplier_id
                    p[2],      # cuit
                    p[3],      # nombre
                    p[4],
                    iso_to_traditional(p[7]),
                    iso_to_traditional(p[8]),
                    p[9],
                    format_currency(p[11]),
                    format_currency(p[12])
                ),
                tag=state if state in ("PENDIENTE", "PAGADA", "BORRADOR") else "orow"
            )

    ## -- Busqueda -- ##
    def list_of_supplier(self, parent):
        win = ctk.CTkToplevel(parent)
        win.title("Lista de proveedores")
        win.geometry("500x400")
        win.grab_set()
        win.transient(parent)

        self.find_search_var = tk.StringVar()

        win.rowconfigure(0, weight=1)
        win.rowconfigure(1, weight=3)
        
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
            textvariable=self.find_search_var,
            font=ctk.CTkFont(size=12),
            placeholder_text="Ingrese nombre del proveedor..."
        )
        self.find_entry.grid(row=0, column=1, padx=5)
        self.find_entry.focus()
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
            self.supplier_tree.insert("", "end", iid=s[0], values=(s[1], s[2]))

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
        query = self.find_search_var.get().lower()
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

    ## -- Seleccion de un proveedor -- ##
    def on_click(self, win, parent):
        selected = self.supplier_tree.selection()

        try:
            # primer fila seleccionada
            if not selected:
                return
            iid = selected[0]
            values = self.supplier_tree.item(iid, "values")

            self.supplier_id_var.set(iid)
            self.search_var.set(values[1])

            win.after(800, lambda: close_win(win, parent))
            self.load_payment_movement(self.supplier_id_var.get())
            self.load_purchase_history(True)
        except ValueError as e:
            show_warning(f'Error en la seleccion del proveedor: {e}')  

    def refresh_supplier_table(self):
        for item in self.supplier_tree.get_children():
            self.supplier_tree.delete(item)

        for s in self.suppliers:
            self.supplier_tree.insert(
                parent='', index='end', iid=s[0],
                values=(
                    s[1],   # cuit
                    s[2]   # name
                ),
                tag="orow"
            )

        self.supplier_tree.tag_configure('orow', background="white", foreground='black')