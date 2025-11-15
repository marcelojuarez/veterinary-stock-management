import tkinter as tk
import customtkinter as ctk
from views.view_helpers import close_win, show_warning

class PaymentForm:

    def __init__(self, model, controller, frame):
        self.model = model
        self.controller = controller
        self.frame = frame

        # variables pago
        self.supplier_var = tk.StringVar()
        self.amount_var = tk.StringVar()
        self.method_var = tk.StringVar()
        self.id_receipt_var = tk.StringVar()
        self.observations_var = tk.StringVar()

    def add_payment_win(self, parent):
        """Ventana para registrar un nuevo pago"""

        if self.supplier_var == "":
            show_warning("Por favor seleccione un Proveedor")
            return

        add_pay_win = ctk.CTkToplevel(parent if parent else self.frame)
        add_pay_win.title("Registrar nuevo pago")

        add_pay_win.protocol("WM_DELETE_WINDOW", lambda: close_win(add_pay_win, parent))
        
        # Hacer que la ventana sea modal
        add_pay_win.transient(parent)
        add_pay_win.grab_set()
        
        # Centrar la ventana
        add_pay_win.geometry("350x450+{}+{}".format(
            add_pay_win.winfo_screenwidth()//2 - 200,
            add_pay_win.winfo_screenheight()//2 - 250
        ))
        
        # Título
        title_label = ctk.CTkLabel(
            add_pay_win,
            text="Nuevo Pago",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(20, 20))

        cuit_lbl = ctk.CTkLabel(add_pay_win, text="Cuit:", font=ctk.CTkFont(size=12, weight="bold"))
        cuit_lbl.grid(row=1, column=0, padx=(15,10))

        cuit_entry = ctk.CTkEntry(
            add_pay_win,
            textvariable=self.supplier_var,
            width=200,
            height=35,
            font=ctk.CTkFont(size=12)
        )
        cuit_entry.grid(row=1, column=1, padx=10, pady=10)

        # monto
        amount_lbl = ctk.CTkLabel(add_pay_win, text="Monto:", font=ctk.CTkFont(size=12, weight="bold"))
        amount_lbl.grid(row=2, column=0, padx=(15,10))

        amount_entry = ctk.CTkEntry(
            add_pay_win, 
            textvariable=self.amount_var,
            width=200,
            height=35
        )
        amount_entry.grid(row=2, column=1, padx=10, pady=10)

        # metodo de pago
        method_lbl = ctk.CTkLabel(add_pay_win, text="Metodo de Pago:", font=ctk.CTkFont(size=12, weight="bold"))
        method_lbl.grid(row=3, column=0, padx=(15,10))
        
        method_combo = ctk.CTkComboBox(
            add_pay_win,
            values=["EFECTIVO", "TRANSFERENCIA", "CHEQUE"],
            variable=self.method_var,
            width=200,
            height=35,
            font=ctk.CTkFont(size=12),
            state="readonly"
        )
        method_combo.set("EFECTIVO")
        method_combo.grid(row=3, column=1, padx=10, pady=10)

        # id recibo
        id_receipt_lbl = ctk.CTkLabel(add_pay_win, text="Id Recibo:", font=ctk.CTkFont(size=12, weight="bold"))
        id_receipt_lbl.grid(row=4, column=0, padx=(15,10))

        id_receipt_entry = ctk.CTkEntry(
            add_pay_win,
            textvariable=self.id_receipt_var,
            width=200,
            height=35,
            font=ctk.CTkFont(size=12),
        )
        id_receipt_entry.grid(row=4, column=1, padx=10, pady=10)

        # observaciones
        ob_lbl = ctk.CTkLabel(add_pay_win, text="Observaciones:", font=ctk.CTkFont(size=12, weight="bold"))
        ob_lbl.grid(row=5, column=0, padx=(15,10))

        ob_entry = ctk.CTkEntry(
            add_pay_win,
            textvariable=self.observations_var,
            width=200,
            height=50,
            font=ctk.CTkFont(size=12),            
        )
        ob_entry.grid(row=5, column=1, padx=10, pady=10)

        # Botones
        button_frame = ctk.CTkFrame(add_pay_win, fg_color="transparent")
        button_frame.grid(row=6, column=0, columnspan=2, pady=30)

        add_button = ctk.CTkButton(button_frame, text="Agregar Pago", width=120, height=35, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#4CAF50", hover_color="#45a049", command=lambda: self.controller.register_payment(self.supplier_var))
        add_button.grid(row=0, column=0, padx=10)

        cancel_button = ctk.CTkButton(button_frame, text="Cancelar", width=120, height=35, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#757575", hover_color="#616161", command= lambda: close_win(add_pay_win, parent))
        cancel_button.grid(row=0, column=1, padx=10)        

    
    def get_payment_data(self):
        return {
            'monto': self.amount_var.get().strip(),
            'metodo': self.method_var.get().strip(),
            'id_recibo': self.id_receipt_var.get().strip(),
            'observaciones': self.observations_var.get().strip()
        }
