import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from .payment_form import PaymentForm 
from views.view_helpers import close_win

class PaymentWindow():
    def __init__(self, model, controller, frame):
        self.model = model
        self.controller = controller
        self.frame = frame
        self.payment_form = PaymentForm(model, controller, frame)

    # Ventana para registrar un nuevo pago
    def open_payment_window(self, parent):
            
        pay_win = ctk.CTkToplevel(self.frame)
        pay_win.title("Registrar Pago a Proveedor")
        pay_win.geometry("1100x750")
        pay_win.grab_set()

        pay_win.protocol("WM_DELETE_WINDOW", lambda: self.close_win(pay_win, parent))

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

        # --- funcion para cargar movimientos ---
        def load_payment_movement():
            selected_supplier = self.supplier_var.get()
            if not selected_supplier:
                messagebox.showwarning("Atención", "Primero selecciona un proveedor.")
                return

            # Limpiar tabla
            for item in movement_tree.get_children():
                movement_tree.delete(item)

            supplier_id = self.model.find_suppplier_by_cuit(selected_supplier)[0]

            # Cargar productos
            for p in self.model.get_all_payment_of_supplier(supplier_id):
                movement_tree.insert("", "end", values=(p[0], p[2], p[5], p[9]))

        supplier_combo = ctk.CTkComboBox(
            pay_win, 
            variable=self.payment_form.supplier_var, 
            values=proveedores, 
            width=250,
            command= lambda value:load_payment_movement()
        )
        supplier_combo.grid(row=0, column=1, padx=10, pady=(15, 5), sticky="w")

        # frame para movimientos
        movement_frame = ctk.CTkFrame(pay_win)
        movement_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

        movement_tree = ttk.Treeview(movement_frame, show="headings", height=8)
        movement_tree["columns"] = ("ID", "CUIT PROVEEDOR", "MONTO", "METODO DE PAGO", "saldo ANTERIOR", "saldo POSTERIOR", "FECHA")
        for col in movement_tree["columns"]:
            movement_tree.heading(col, text=col.capitalize())
            movement_tree.column(col, width=150, anchor="center")
        movement_tree.pack(side="left", fill="both", expand=True)

        #  scrollbar 
        scroll = ttk.Scrollbar(movement_frame, orient="vertical", command=movement_tree.yview)
        movement_tree.configure(yscroll=scroll.set)
        scroll.pack(side="right", fill="y")

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
            command=lambda: self.payment_form.add_payment_win(pay_win)
        )
        confirm_btn.grid(row=0, column=2, padx=5, pady=10)

        # Botón Cerrar
        close_win_btn = ctk.CTkButton(
            buttons_frame,
            text="Cerrar",
            fg_color="#E74C3C",
            hover_color="#C0392B",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: close_win(pay_win, parent)
        )
        close_win_btn.grid(row=0, column=4, padx=5, pady=10)

