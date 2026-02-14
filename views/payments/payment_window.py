import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from .payment_form import PaymentForm 
from .payment_info import PaymentInfo
from views.view_helpers import close_win, show_warning, show_error
from utils.utils import iso_to_traditional

# Configurar tema y colores
ctk.set_appearance_mode("light")  # "light" o "dark"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class PaymentWindow():
    def __init__(self, model, frame, controller):
        self.model = model
        self.frame = frame

        self.payment_form = PaymentForm(self, model, frame)

        self.controller = controller
        self.controller.set_pay_view(self)
        self.controller.set_form_view(self.payment_form) 

        self.payment_form.set_controller(self.controller)

        self.payment_info = PaymentInfo(self.model)

    # Ventana para registrar un nuevo pago
    def open_payment_window(self, parent):

        btn_color = "#009688"
        btn_hover = "#00796B"

        self.supplier_var = tk.StringVar()
        self.debt_var = tk.StringVar()
        self.suppliers = self.model.core.get_all_suppliers()
            
        win = ctk.CTkToplevel(self.frame)
        win.title("Registrar Pago a Proveedor")
        win.geometry("1100x600")
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
        select_supplier_frame.grid(row=1, column=0, pady=(10,10), sticky="ew")

        select_supplier_frame.grid_columnconfigure(0, weight=1)  # botón
        select_supplier_frame.grid_columnconfigure(1, weight=0)  # entry
        select_supplier_frame.grid_columnconfigure(2, weight=2)  # espacio flexible
        select_supplier_frame.grid_columnconfigure(3, weight=0)  # debt_frame

        select_supplier_btn = ctk.CTkButton(
            select_supplier_frame,
            width=140,
            text="Seleccionar Proveedor",
            fg_color=btn_color,
            hover_color=btn_hover,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.list_of_supplier(win)
        )
        select_supplier_btn.grid(row=0, column=0, padx=(0,10), pady=(15, 5), sticky="e")

        select_supplier_entry = ctk.CTkEntry(
            select_supplier_frame,
            textvariable=self.supplier_var,
            font=ctk.CTkFont(size=12),
        )
        select_supplier_entry.grid(row=0, column=1, pady=(15, 5), sticky="e")

        debt_frame = ctk.CTkFrame(
            select_supplier_frame,
            fg_color=btn_color,
            corner_radius=12
        )
        
        debt_frame.grid(row=0, column=3, padx=20, sticky="nsew")

        debt_lbl = ctk.CTkLabel(
            debt_frame,
            text="Deuda Proveedor",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#f8fffe"
        )
        debt_lbl.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")

        debt_entry = ctk.CTkEntry(
            debt_frame,
            textvariable=self.debt_var,
            width=120,
            corner_radius=10,
            fg_color="white",
            state='readonly'
        )
        debt_entry.grid(row=0, column=1, padx=5, pady=(10, 5), sticky="w")

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
            command=lambda: self.payment_form.add_payment_win(win, self.supplier_var.get())
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
        self.supplier_var.set('')

    ## -- Configura la tabla de movimientos -- ##
    def set_movement_tree(self, win):
        # frame para movimientos
        movement_frame = ctk.CTkFrame(win)
        movement_frame.pack(fill='both', expand=True)

        self.movement_tree = ttk.Treeview(movement_frame, show="headings", height=8)
        self.movement_tree["columns"] = ("ID", "CUIT PROVEEDOR", "MONTO", "METODO DE PAGO", "OBSERVACION", "FECHA")
        for col in self.movement_tree["columns"]:
            self.movement_tree.heading(col, text=col.capitalize())
            if col == "ID":
                self.movement_tree.column(col, width=100, anchor="center")
            else:
                self.movement_tree.column(col, width=150, anchor="center")
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
        self.purchase_tree["columns"] = ("ID", "Cuit Proveedor", "Tipo Comprobante", "Fecha", "Fecha Venc.", "Estado", "Saldo Pendiente", "Total")
        for col in self.purchase_tree["columns"]:
            self.purchase_tree.heading(col, text=col.capitalize())
            if col == "ID":
                self.purchase_tree.column(col, width=100, anchor="center")
            else:
                self.purchase_tree.column(col, width=150, anchor="center")
        self.purchase_tree.pack(side="left", fill="both", expand=True)   

        scrollbar = ttk.Scrollbar(purchase_frame, orient="vertical", command=self.purchase_tree.yview)
        self.purchase_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right",fill="y")

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
            print(f'Error al seleccionar el registro de pago: {e}')
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
            if values[5] == 'PAGADA' or values[5] == 'CANCELADA':
                show_warning(f'No puede pagar una compra: {values[5]}')
                return

            self.supplier_var.set(values[1])
            self.load_purchase_history(True)

            self.payment_form.add_payment_win(
                parent=parent, 
                supplier_cuit=values[1], 
                purchase_id=values[0], 
                amount=values[6]
            )

        except ValueError as e:
            show_warning(f'Error en la seleccion de la compra: {e}')

    ## -- Seleccion de un proveedor -- ##
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

            win.after(800, lambda: close_win(win, parent))
            self.load_payment_movement(self.supplier_var.get())
            self.load_purchase_history(True)
        except ValueError as e:
            show_warning(f'Error en la seleccion del proveedor: {e}')

    ## --  Carga de tabla de movimientos -- ##
    def load_payment_movement(self, supplier_cuit=None):
        if supplier_cuit is None:
            payments = self.model.payment.get_all_payments()

        else:
            payments = self.model.payment.get_all_payments(supplier_cuit)

        # Limpiar tabla
        for item in self.movement_tree.get_children():
            self.movement_tree.delete(item)
        # Cargar productos
        for p in payments:
            self.movement_tree.insert(
                parent='', index='end', iid=p[0],
                values=(
                   p[0], # id
                   p[1], # cuit
                   p[3], # monto
                   p[4], # metodo
                   p[5], # observation
                   iso_to_traditional(p[11]) # fecha    
                ),
                tag="orow"
            )
            
        self.movement_tree.tag_configure('orow', background="white", foreground='black')     

    ## -- Funcion para cargar compras -- ##
    def load_purchase_history(self, filter):

        if filter:
            selected_supplier = self.supplier_var.get()

            if not selected_supplier:
                show_warning("Atención", "Primero selecciona un proveedor.")
                return
            
            debt = self.model.purchase.get_debt_of_supplier(selected_supplier)

            self.debt_var.set(debt)
            purchases = self.model.purchase.get_all_confirmed_purchases(selected_supplier)

        else:
            purchases = self.model.purchase.get_all_confirmed_purchases()

        # Limpiar tabla
        for item in self.purchase_tree.get_children():
            self.purchase_tree.delete(item)

        # Cargar compras
        for p in purchases:
            self.purchase_tree.insert(
                parent="", index="end", iid=p[0],
                values=(
                    p[0], # id
                    p[1], # cuit
                    p[2], # comprobante
                    iso_to_traditional(p[5]), # fecha
                    iso_to_traditional(p[6]), # fecha venc
                    p[7], # estado
                    p[9], # saldo pend
                    p[10] # total
                ),
                tag="orow"
            )  

    ## -- Busqueda -- ##
    def list_of_supplier(self, parent):
        win = ctk.CTkToplevel(parent)
        win.title("Lista de proveedores")
        win.geometry("500x400")
        win.grab_set()
        win.transient(parent)

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
        
        print(query)
        
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

