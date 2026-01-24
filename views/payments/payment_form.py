import tkinter as tk
import customtkinter as ctk
from utils.utils import normalize_decimal

from views.view_helpers import close_win, show_warning

class PaymentForm:

    def __init__(self, pay_win, model, frame, controller=None):
        self.pay_win = pay_win
        self.model = model
        self.frame = frame
        self.controller = controller

    def setup_payment_variables(self, supplier_var, purchase_id, amount):
        self.supplier_var = tk.StringVar()
        self.supplier_var.set(supplier_var)

        self.amount_var = tk.StringVar()

        if purchase_id is not None and amount is not None:
            self.purchase_id = tk.StringVar()

            self.amount_var.set(amount)
            self.purchase_id.set(purchase_id)

        else:
            self.purchase_id = None

        # variables pago
        self.method_var = tk.StringVar()
        self.num_receipt_var = tk.StringVar()
        self.observation_var = tk.StringVar()

        self.opt_num_var = tk.StringVar()
        self.origin_var = tk.StringVar()
        self.destinatation_var = tk.StringVar()

        self.bank_var = tk.StringVar()

        self.check_num_var = tk.StringVar()

    def set_controller(self, controller):
        """Asignar controller después de la inicialización"""
        print(f"DEBUG: Asignando controller: {controller}")
        self.controller = controller
        print(f"DEBUG: Controller asignado correctamente: {self.controller}")

    ## -- Formulario de pago -- ##
    def add_payment_win(self, parent, supplier_cuit, purchase_id=None, amount=None):

        if supplier_cuit == '':
            show_warning('Por favor selecciona un Proveedor')
            return

        if normalize_decimal(self.pay_win.debt_var.get()) <= 0:
            show_warning(f'Atención. No se registra Deuda al proveedor: {supplier_cuit}')
            return

        self.setup_payment_variables(supplier_cuit, purchase_id, amount)

        """Ventana para registrar un nuevo pago"""

        if self.supplier_var.get() == "":
            show_warning("Por favor seleccione un Proveedor")
            return

        self.add_pay_win = ctk.CTkToplevel(parent if parent else self.frame)
        self.add_pay_win.title("Registrar nuevo pago")

        self.add_pay_win.columnconfigure(0, weight=0)
        self.add_pay_win.columnconfigure(1, weight=1)

        self.add_pay_win.protocol("WM_DELETE_WINDOW", lambda: close_win(self.add_pay_win, parent))
        
        # Hacer que la ventana sea modal
        self.add_pay_win.transient(parent)
        self.add_pay_win.grab_set()
        
        # Centrar la ventana
        self.add_pay_win.geometry("380x360+{}+{}".format(
            self.add_pay_win.winfo_screenwidth()//2 - 175,
            self.add_pay_win.winfo_screenheight()//2 - 190
        ))
        
        # Título
        title_label = ctk.CTkLabel(
            self.add_pay_win,
            text="Nuevo Pago",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(20, 20))

        cuit_lbl = ctk.CTkLabel(self.add_pay_win, text="Cuit:", font=ctk.CTkFont(size=12, weight="bold"))
        cuit_lbl.grid(row=1, column=0, padx=(20,10), pady=5)

        cuit_entry = ctk.CTkEntry(
            self.add_pay_win,
            textvariable=self.supplier_var,
            width=200,
            height=35,
            state='readonly',
            font=ctk.CTkFont(size=12)
        )
        cuit_entry.grid(row=1, column=1, padx=(15,20), pady=5)

        # monto
        amount_lbl = ctk.CTkLabel(self.add_pay_win, text="Monto:", font=ctk.CTkFont(size=12, weight="bold"))
        amount_lbl.grid(row=2, column=0, padx=(20,10), pady=5)

        amount_entry = ctk.CTkEntry(
            self.add_pay_win, 
            textvariable=self.amount_var,
            width=200,
            height=35
        )
        amount_entry.grid(row=2, column=1, padx=(15,20), pady=5)

        # id recibo
        id_receipt_lbl = ctk.CTkLabel(self.add_pay_win, text="Numero de recibo:", font=ctk.CTkFont(size=12, weight="bold"))
        id_receipt_lbl.grid(row=3, column=0, padx=(20,10), pady=5)

        id_receipt_entry = ctk.CTkEntry(
            self.add_pay_win,
            textvariable=self.num_receipt_var,
            width=200,
            height=35,
            font=ctk.CTkFont(size=12),
        )
        id_receipt_entry.grid(row=3, column=1, padx=(15,20), pady=5)

        # observaciones
        ob_lbl = ctk.CTkLabel(self.add_pay_win, text="Observaciones:", font=ctk.CTkFont(size=12, weight="bold"))
        ob_lbl.grid(row=4, column=0, padx=(20,10), pady=5)

        ob_entry = ctk.CTkEntry(
            self.add_pay_win,
            textvariable=self.observation_var,
            width=200,
            height=50,
            font=ctk.CTkFont(size=12),            
        )
        ob_entry.grid(row=4, column=1, padx=(15,20), pady=5)

        # metodo de pago
        method_lbl = ctk.CTkLabel(self.add_pay_win, text="Metodo de Pago:", font=ctk.CTkFont(size=12, weight="bold"))
        method_lbl.grid(row=5, column=0, padx=(20,10), pady=5)

        method_combo = ctk.CTkComboBox(
            self.add_pay_win,
            values=["EFECTIVO", "TRANSFERENCIA", "CHEQUE"],
            variable=self.method_var,
            width=200,
            height=35,
            font=ctk.CTkFont(size=12),
            state="readonly",
            command=lambda value: self.render_dynamic_fields(parent)
        )
        method_combo.set("-")
        method_combo.grid(row=5, column=1, padx=(15,20), pady=5)

        self.dynamic_frame = ctk.CTkFrame(self.add_pay_win, fg_color="transparent")
        self.dynamic_frame.grid(row=6, column=0, columnspan=2, pady=10)

        self.dynamic_frame.columnconfigure(0, weight=0)
        self.dynamic_frame.columnconfigure(1, weight=1)

    ## -- Renderiza distintos campos segun el metodo de pago -- ##
    def render_dynamic_fields(self, parent):
        method = self.method_var.get()

        # limpiar todo antes de agregar nuevos widgets
        self.clear_dynamic_frame()

        if method == "TRANSFERENCIA":
            self.add_pay_win.geometry("380x550")

            op_num_lbl = ctk.CTkLabel(self.dynamic_frame, text="Numero de operacion:", font=ctk.CTkFont(size=12, weight="bold"))
            op_num_lbl. grid(row=0, column=0, padx=20, pady=5)

            op_num_entry = ctk.CTkEntry(
                self.dynamic_frame,
                textvariable=self.opt_num_var,
                width=200,
                height=35,
                font=ctk.CTkFont(size=12),
            )
            op_num_entry.grid(row=0, column=1, padx=(0,40), pady=5)

            origin_lbl = ctk.CTkLabel(self.dynamic_frame, text="CBU/Alias (Cuenta Emisora):", font=ctk.CTkFont(size=12, weight="bold"))
            origin_lbl. grid(row=1, column=0, padx=20, pady=5)

            origin_entry = ctk.CTkEntry(
                self.dynamic_frame,
                textvariable=self.origin_var,
                width=200,
                height=35,
                font=ctk.CTkFont(size=12),
            )
            origin_entry.grid(row=1, column=1, padx=(0,40), pady=5)

            destino_lbl = ctk.CTkLabel(self.dynamic_frame, text="CBU/Alias (Cuenta Receptora):", font=ctk.CTkFont(size=12, weight="bold"))
            destino_lbl. grid(row=2, column=0, padx=20, pady=5)

            destino_entry = ctk.CTkEntry(
                self.dynamic_frame,
                textvariable=self.destinatation_var,
                width=200,
                height=35,
                font=ctk.CTkFont(size=12),
            )
            destino_entry.grid(row=2, column=1, padx=(0,40), pady=5)

            self.render_buttons(parent, 9)

        elif method == "CHEQUE":
            self.add_pay_win.geometry("380x550")

            # banco que emite el cheque
            check_bank_lbl = ctk.CTkLabel(self.dynamic_frame, text="Banco:", font=ctk.CTkFont(size=12, weight="bold"))
            check_bank_lbl. grid(row=0, column=0, padx=20, pady=5)

            check_bank_entry = ctk.CTkEntry(
                self.dynamic_frame,
                textvariable=self.bank_var,
                width=200,
                height=35,
                font=ctk.CTkFont(size=12),
            )
            check_bank_entry.grid(row=0, column=1, padx=(0,40), pady=5)

            # Numero de cheque
            check_num_lbl = ctk.CTkLabel(self.dynamic_frame, text="Numero de cheque:", font=ctk.CTkFont(size=12, weight="bold"))
            check_num_lbl.grid(row=1, column=0, padx=20, pady=5)

            check_num_entry = ctk.CTkEntry(
                self.dynamic_frame,
                textvariable=self.check_num_var,
                width=200,
                height=35,
                font=ctk.CTkFont(size=12),
            )
            check_num_entry.grid(row=1, column=1, padx=(0,40), pady=5)

            self.render_buttons(parent, 8)
        
        elif method == "EFECTIVO":
            self.add_pay_win.geometry("380x400")
            self.render_buttons(parent, 6)

    ## -- Renderiza botones de accion -- ##
    def render_buttons(self, parent, row_num):
        # Botones
        button_frame = ctk.CTkFrame(self.dynamic_frame, fg_color="transparent")
        button_frame.grid(row=row_num, column=0, columnspan=2, pady=15)

        add_button = ctk.CTkButton(button_frame, text="Agregar Pago", width=120, height=35, font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#4CAF50", hover_color="#45a049", command=lambda: self.controller.register_payment(self.supplier_var, self.add_pay_win, parent, self.purchase_id))
        add_button.grid(row=0, column=0, padx=15, pady=15)

        cancel_button = ctk.CTkButton(button_frame, text="Cancelar", width=120, height=35, font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#757575", hover_color="#616161", command= lambda: close_win(self.add_pay_win, parent))
        cancel_button.grid(row=0, column=1, padx=15, pady=15) 

    ## -- Elimina campos dinamicos -- ##
    def clear_dynamic_frame(self):
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()

    ## -- Se obtienen datos del formulario de pago -- ##
    def get_payment_data(self):
        """Obtener datos del formulario de pago"""
        return {
            'amount': self.amount_var.get().strip(),
            'method': self.method_var.get().strip(),
            'receipt_number': self.num_receipt_var.get().strip(),
            'observation': self.observation_var.get().strip(),
            'operation_num': self.opt_num_var.get().strip(),
            'origin': self.origin_var.get().strip(),
            'destination': self.destinatation_var.get().strip(),
            'bank': self.bank_var.get().strip(),
            'check_number': self.check_num_var.get().strip()
        }
