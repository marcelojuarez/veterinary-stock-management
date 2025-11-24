import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from .payment_form import PaymentFormView 
from controllers.payment_controller import PaymentController
from views.view_helpers import close_win

class PaymentWindow():
    def __init__(self, model, frame):
        self.model = model
        self.frame = frame

        self.payment_form = PaymentFormView(model, frame)
        self.controller = PaymentController(self.payment_form, self)
        self.payment_form.set_controller(self.controller)

    # Ventana para registrar un nuevo pago
    def open_payment_window(self, parent):

        self.supplier_var = tk.StringVar()
            
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

        # --- Proveedor ---
        ctk.CTkLabel(
            pay_win, text="Proveedor:", font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=(15, 5), sticky="e")

        proveedores = [f"{p[1]}" for p in self.model.get_all_suppliers()]  # nombre (CUIT)

        supplier_combo = ctk.CTkComboBox(
            pay_win, 
            variable=self.supplier_var, 
            values=proveedores, 
            width=250,
            command= lambda value:self.load_payment_movement()
        )
        supplier_combo.grid(row=0, column=1, padx=10, pady=(15, 5), sticky="w")

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
                   label1.grid(row=i, column=0, padx=20, pady=10, sticky="w")
                              
                   label2 = ctk.CTkLabel(payment_info, text=info, font=ctk.CTkFont(size=12))
                   label2.grid(row=i, column=1) 

                print(fields)
            elif method == 'CHEQUE':
                data = self.model.get_check_data(payment_id)

                fields = {
                    'Numero de cheque:': data[0],
                    'Banco:': data[1]
                }

                for i, (label, info) in enumerate(fields.items(), start=0):
                   label1 = ctk.CTkLabel(payment_info, text=label, font=ctk.CTkFont(size=15, weight="bold"))
                   label1.grid(row=i, column=0, padx=10, pady=10, sticky="w")
                              
                   label2 = ctk.CTkLabel(payment_info, text=info, font=ctk.CTkFont(size=15))
                   label2.grid(row=i, column=1) 

                print(fields)

        self.movement_tree.bind("<Button-1>", on_row_click)

        # --- Frame inferior (botones y cantidad) ---
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

        # cargar movimientos
        
    def clear_supplier_field(self):
        self.supplier_var.set('')

    # --- funcion para cargar movimientos ---
    def load_payment_movement(self, selected_supplier=None):
        if selected_supplier is None:
            selected_supplier = self.supplier_var.get()

        if not selected_supplier:
            messagebox.showwarning("Atención", "Primero selecciona un proveedor.")
            return

        # Limpiar tabla
        for item in self.movement_tree.get_children():
            self.movement_tree.delete(item)

        supplier_id = self.model.find_suppplier_by_cuit(selected_supplier)[0]
        payments = self.model.get_all_payment_of_supplier(supplier_id)
        # Cargar productos
        for p in payments:
            self.movement_tree.insert(
                parent='', index='end', iid=p[0],
                values=(
                   p[0],
                   selected_supplier,
                   p[3], 
                   p[4],
                   p[11],
                   p[12],
                   p[13]                   
                ),
                tag="orow"
            )
            
        self.movement_tree.tag_configure('orow', background="white", foreground='black')        



