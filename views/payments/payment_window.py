import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from tksheet import Sheet
from .payment_form import PaymentFormView 
from controllers.payment_controller import PaymentController
from views.view_helpers import close_win, show_warning

# Configurar tema y colores
ctk.set_appearance_mode("light")  # "light" o "dark"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class PaymentWindow():
    def __init__(self, model, frame):
        self.model = model
        self.frame = frame

        self.payment_form = PaymentFormView(model, frame)
        self.controller = PaymentController(self.payment_form, self)
        self.payment_form.set_controller(self.controller)

    # Ventana para registrar un nuevo pago
    def open_payment_window(self, parent):
        btn_color = "#009688"
        btn_hover = "#00796B"

        self.supplier_var = tk.StringVar()
        self.suppliers = self.model.get_all_suppliers()
            
        pay_win = ctk.CTkToplevel(self.frame)
        pay_win.title("Registrar Pago a Proveedor")
        pay_win.geometry("1100x750")
        pay_win.grab_set()

        pay_win.protocol("WM_DELETE_WINDOW", lambda: close_win(pay_win, parent, self.clear_supplier_field))

        # Configurar grilla principal
        for i in range(6):
            pay_win.grid_rowconfigure(i, weight=0)
        pay_win.grid_rowconfigure(3, weight=1)
        pay_win.grid_columnconfigure(0, weight=1)
        pay_win.grid_columnconfigure(1, weight=1)

        select_supplier_frame = ctk.CTkFrame(pay_win,fg_color="#f0f0f0")
        select_supplier_frame.grid(row=1, column=0)

        select_supplier_btn = ctk.CTkButton(
            select_supplier_frame,
            width=120,
            text="Seleccionar Proveedor:",
            fg_color=btn_color,
            hover_color=btn_hover,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.list_of_supplier(pay_win)
        )
        select_supplier_btn.grid(row=0, column=0, padx=(0,10), pady=(15, 5), sticky="e")

        select_supplier_entry = ctk.CTkEntry(
            select_supplier_frame,
            textvariable=self.supplier_var,
            font=ctk.CTkFont(size=12),
        )
        select_supplier_entry.grid(row=0, column=1, pady=(15, 5), sticky="e")

        # frame para movimientos
        movement_frame = ctk.CTkFrame(pay_win)
        movement_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

        self.movement_tree = ttk.Treeview(movement_frame, show="headings", height=8)
        self.movement_tree["columns"] = ("ID", "CUIT PROVEEDOR", "MONTO", "METODO DE PAGO", "saldo ANTERIOR", "saldo POSTERIOR", "FECHA")
        for col in self.movement_tree["columns"]:
            self.movement_tree.heading(col, text=col.capitalize())
            self.movement_tree.column(col, width=150, anchor="center")
        self.movement_tree.pack(side="left", fill="both", expand=True)

        # scrollbar 
        scroll = ttk.Scrollbar(movement_frame, orient="vertical", command=self.movement_tree.yview)
        self.movement_tree.configure(yscroll=scroll.set)
        scroll.pack(side="right", fill="y")

        # presiona fila para mostrar info
        def on_row_click(event):
            row_id = self.movement_tree.identify_row(event.y)
            col_id = self.movement_tree.identify_column(event.x)
            if not row_id:
                return
            
            if col_id == "#4":
                data = self.movement_tree.item(row_id, "values")
                if data[3] == 'EFECTIVO':
                    return
                show_details(movement_frame, data[0], data[3])

        def show_details(parent, payment_id, method):
            payment_info = ctk.CTkToplevel(parent)
            payment_info.title(f"{method}")
            payment_info.grid()
            
            payment_info.protocol("WM_DELETE_WINDOW", lambda: close_win(payment_info, parent))
            payment_info.transient(parent)
            payment_info.grab_set()

            payment_info.columnconfigure(0, weight=1)
            payment_info.columnconfigure(1, weight=2)

            print(f'id pago: {payment_id}')
            print(f'metodo: {method}')

            if method == 'TRANSFERENCIA':
                data = self.model.get_transfer_data(payment_id)

                fields = {
                    'Numero de operacion:': data[0],
                    'CBU/Alias(Origen):': data[1],
                    'CBU/Alias(Destino):': data[2]
                }

                for i, (label, info) in enumerate(fields.items(), start=0):
                   label1 = ctk.CTkLabel(payment_info, text=label, font=ctk.CTkFont(size=15, weight="bold"))
                   label1.grid(row=i, column=0, padx=(10,0), pady=10)
                              
                   label2 = ctk.CTkLabel(payment_info, text=info, font=ctk.CTkFont(size=12))
                   label2.grid(row=i, column=1, padx=(0,10)) 

                print(fields)
            elif method == 'CHEQUE':
                data = self.model.get_check_data(payment_id)

                fields = {
                    'Numero de cheque:': data[0],
                    'Banco:': data[1]
                }

                for i, (label, info) in enumerate(fields.items(), start=0):
                   label1 = ctk.CTkLabel(payment_info, text=label, font=ctk.CTkFont(size=15, weight="bold"))
                   label1.grid(row=i, column=0, padx=(10,0), pady=10)
                              
                   label2 = ctk.CTkLabel(payment_info, text=info, font=ctk.CTkFont(size=15))
                   label2.grid(row=i, column=1, padx=(0,10))

                print(fields)

        self.movement_tree.bind("<Button-1>", on_row_click)

        # frame inferior (botones y cantidad)
        buttons_frame = ctk.CTkFrame(pay_win)
        buttons_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        for i in range(5):
            buttons_frame.grid_columnconfigure(i, weight=1)

        # Botón Registrar Compra
        confirm_btn = ctk.CTkButton(
            buttons_frame,
            text="Registrar nuevo pago",
            fg_color="#4CAF50",
            hover_color="#45a049",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.payment_form.add_payment_win(pay_win, self.supplier_var.get())
        )
        confirm_btn.grid(row=0, column=1, padx=5, pady=10)

        # Botón Registrar Compra
        confirm_btn = ctk.CTkButton(
            buttons_frame,
            text="Eliminar registro de pago",
            fg_color="#4CAF50",
            hover_color="#45a049",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        confirm_btn.grid(row=0, column=2, padx=5, pady=10)

        # Botón Cerrar
        close_win_btn = ctk.CTkButton(
            buttons_frame,
            text="Cerrar",
            fg_color="#E74C3C",
            hover_color="#C0392B",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: close_win(pay_win, parent, self.clear_supplier_field)
        )
        close_win_btn.grid(row=0, column=4, padx=5, pady=10)
        
    def clear_supplier_field(self):
        self.supplier_var.set('')

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
            self.load_payment_movement()
        except ValueError as e:
            show_warning(f'Error en la seleccion del proveedor: {e}')

    #  funcion para cargar movimientos 
    def load_payment_movement(self, supplier_id=None, supplier_cuit=None):
        if supplier_id is None and supplier_cuit is None:
            print("aca")
            supplier_cuit = self.supplier_var.get()
            result = self.model.find_supplier_by_cuit(supplier_cuit)
            supplier_id = result[0]
            print(f'{supplier_id}')
            print(f'{supplier_cuit}')


        if not supplier_id or not supplier_cuit:
            messagebox.showwarning("Atención", "Primero selecciona un proveedor.")
            return

        # Limpiar tabla
        for item in self.movement_tree.get_children():
            self.movement_tree.delete(item)

        payments = self.model.get_all_payment_of_supplier(supplier_id)
        payments_sorted = sorted(payments, key=lambda x: x[0], reverse=True)

        # Cargar productos
        for p in payments_sorted:
            self.movement_tree.insert(
                parent='', index='end', iid=p[0],
                values=(
                   p[0],
                   supplier_cuit,
                   p[3], 
                   p[4],
                   p[11],
                   p[12],
                   p[13]                   
                ),
                tag="orow"
            )
            
        self.movement_tree.tag_configure('orow', background="white", foreground='black')     

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
