import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
from decimal import Decimal
from utils.view_helpers import close_win, show_warning, ask_confirmation

class PaymentForm:

    def __init__(self, pay_win, model, frame, controller=None, checks_model=None):
        self.pay_win = pay_win
        self.model = model
        self.frame = frame
        self.controller = controller
        self.checks_model = checks_model   # ← cartera de cheques
        self._selected_check = None        # cheque elegido de la cartera

    def setup_payment_variables(self, supplier_id, supplier_cuit, purchase_id, amount):
        self.supplier_id_var = tk.StringVar()
        self.supplier_cuit_var = tk.StringVar()

        self.supplier_id_var.set(supplier_id)
        self.supplier_cuit_var.set(supplier_cuit)

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
    def add_payment_win(self, parent, supplier_id, purchase_id=None, amount=None):
        if supplier_id.strip() == '':
            show_warning('Por favor selecciona un Proveedor')
            return

        supplier_data = self.model.core.find_supplier_by_id(supplier_id)

        if Decimal(self.pay_win.debt_var.get()) <= Decimal('0.00'):
            show_warning(f'Atención. No se registra Deuda al proveedor: '\
                         f'{supplier_data[1]} - {supplier_data[2]}')
            return

        self.setup_payment_variables(supplier_id, supplier_data[1], purchase_id, amount)

        """Ventana para registrar un nuevo pago"""

        if self.supplier_cuit_var.get() == "":
            show_warning("Por favor seleccione un Proveedor")
            return

        self.add_pay_win = ctk.CTkToplevel(parent if parent else self.frame)
        self.add_pay_win.title("Registrar nuevo pago")
        self.add_pay_win.resizable(True, True)

        # Limitar tamaño máximo a la pantalla disponible
        sw = self.add_pay_win.winfo_screenwidth()
        sh = self.add_pay_win.winfo_screenheight()
        win_w, win_h = 640, min(560, sh - 80)
        self.add_pay_win.geometry("{}x{}+{}+{}".format(
            win_w, win_h,
            sw // 2 - win_w // 2,
            sh // 2 - win_h // 2
        ))
        self.add_pay_win.minsize(520, 400)

        self.add_pay_win.protocol("WM_DELETE_WINDOW", lambda: close_win(self.add_pay_win, parent))
        self.add_pay_win.transient(parent)
        self.add_pay_win.grab_set()

        # Contenedor scrollable
        self.add_pay_win.rowconfigure(0, weight=1)
        self.add_pay_win.columnconfigure(0, weight=1)
        scroll = ctk.CTkScrollableFrame(self.add_pay_win, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        scroll.columnconfigure(0, weight=0)
        scroll.columnconfigure(1, weight=1)

        # Alias para simplificar
        W = scroll
        FONT_LBL  = ctk.CTkFont(size=13, weight="bold")
        FONT_ENTRY = ctk.CTkFont(size=13)
        ENTRY_W, ENTRY_H = 280, 36

        # Título
        ctk.CTkLabel(W, text="Nuevo Pago", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, columnspan=2, pady=(16, 14))

        # CUIT
        ctk.CTkLabel(W, text="Cuit:", font=FONT_LBL).grid(row=1, column=0, padx=(20,8), pady=5, sticky="e")
        ctk.CTkEntry(W, textvariable=self.supplier_cuit_var, width=ENTRY_W, height=ENTRY_H,
                     state='readonly', font=FONT_ENTRY).grid(row=1, column=1, padx=(0,20), pady=5, sticky="w")

        # Monto
        ctk.CTkLabel(W, text="Monto:", font=FONT_LBL).grid(row=2, column=0, padx=(20,8), pady=5, sticky="e")
        ctk.CTkEntry(W, textvariable=self.amount_var, width=ENTRY_W, height=ENTRY_H,
                     font=FONT_ENTRY).grid(row=2, column=1, padx=(0,20), pady=5, sticky="w")

        # Nro recibo
        ctk.CTkLabel(W, text="Numero de recibo:", font=FONT_LBL).grid(row=3, column=0, padx=(20,8), pady=5, sticky="e")
        ctk.CTkEntry(W, textvariable=self.num_receipt_var, width=ENTRY_W, height=ENTRY_H,
                     font=FONT_ENTRY).grid(row=3, column=1, padx=(0,20), pady=5, sticky="w")

        # Observaciones
        ctk.CTkLabel(W, text="Observaciones:", font=FONT_LBL).grid(row=4, column=0, padx=(20,8), pady=5, sticky="e")
        ctk.CTkEntry(W, textvariable=self.observation_var, width=ENTRY_W, height=ENTRY_H,
                     font=FONT_ENTRY).grid(row=4, column=1, padx=(0,20), pady=5, sticky="w")

        # Método
        ctk.CTkLabel(W, text="Metodo de Pago:", font=FONT_LBL).grid(row=5, column=0, padx=(20,8), pady=5, sticky="e")
        method_combo = ctk.CTkComboBox(
            W, values=["EFECTIVO", "TRANSFERENCIA", "CHEQUE"],
            variable=self.method_var, width=ENTRY_W, height=ENTRY_H,
            font=FONT_ENTRY, state="readonly",
            command=lambda value: self.render_dynamic_fields(parent)
        )
        method_combo.set("")
        method_combo.grid(row=5, column=1, padx=(0,20), pady=5, sticky="w")

        # Frame dinámico
        self.dynamic_frame = ctk.CTkFrame(W, fg_color="transparent")
        self.dynamic_frame.grid(row=6, column=0, columnspan=2, pady=(4, 8), sticky="ew")
        self.dynamic_frame.columnconfigure(0, weight=0)
        self.dynamic_frame.columnconfigure(1, weight=1)

        self.create_dynamic_fields()
        self.create_action_buttons(parent)
        
    def create_dynamic_fields(self):
        # TRANSFERENCIA
        self.op_num_lbl = ctk.CTkLabel(self.dynamic_frame, text="Numero de operacion:", font=ctk.CTkFont(size=12, weight="bold"))
        self.op_num_entry = ctk.CTkEntry(self.dynamic_frame, textvariable=self.opt_num_var, width=200, height=35, font=ctk.CTkFont(size=12))
        self.origin_lbl = ctk.CTkLabel(self.dynamic_frame, text="CBU/Alias (Cuenta Emisora):", font=ctk.CTkFont(size=12, weight="bold"))
        self.origin_entry = ctk.CTkEntry(self.dynamic_frame, textvariable=self.origin_var, width=200, height=35, font=ctk.CTkFont(size=12))
        self.destino_lbl = ctk.CTkLabel(self.dynamic_frame, text="CBU/Alias (Cuenta Receptora):", font=ctk.CTkFont(size=12, weight="bold"))
        self.destino_entry = ctk.CTkEntry(self.dynamic_frame, textvariable=self.destinatation_var, width=200, height=35, font=ctk.CTkFont(size=12))

        # CHEQUE — selector de cartera
        self.cartera_lbl = ctk.CTkLabel(
            self.dynamic_frame,
            text="Seleccionar cheque de cartera:",
            font=ctk.CTkFont(size=12, weight="bold")
        )

        # Tabla de cheques en cartera
        cartera_frame = ctk.CTkFrame(self.dynamic_frame, fg_color="transparent")
        self.cartera_frame = cartera_frame

        style = ttk.Style()
        style.configure("Cartera.Treeview", rowheight=20, font=("Segoe UI", 8))
        style.configure("Cartera.Treeview.Heading", font=("Segoe UI", 8, "bold"))

        cols = ("ID", "Nro.", "Banco", "Monto", "Vence")
        self.cartera_table = ttk.Treeview(
            cartera_frame, columns=cols, show="headings",
            height=5, style="Cartera.Treeview"
        )
        widths = {"ID": 0, "Nro.": 120, "Banco": 150, "Monto": 90, "Vence": 90}
        for col in cols:
            w = widths[col]
            self.cartera_table.column(col, width=w, anchor="center",
                                      minwidth=w, stretch=True)
            self.cartera_table.heading(col, text=col)
        # Ocultar columna ID
        self.cartera_table.column("ID", width=0, minwidth=0, stretch=False)

        sy = ttk.Scrollbar(cartera_frame, orient="vertical", command=self.cartera_table.yview)
        self.cartera_table.configure(yscrollcommand=sy.set)
        sy.pack(side="right", fill="y")
        self.cartera_table.pack(fill="x")
        self.cartera_table.bind("<<TreeviewSelect>>", self._on_check_selected)

        # Aviso de excedente
        self.excedente_var = tk.StringVar()
        self.excedente_lbl = ctk.CTkLabel(
            self.dynamic_frame,
            textvariable=self.excedente_var,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#E65100"
        )

        # Campos de cheque (readonly, se completan al seleccionar)
        self.check_bank_lbl   = ctk.CTkLabel(self.dynamic_frame, text="Banco:", font=ctk.CTkFont(size=12, weight="bold"))
        self.check_bank_entry = ctk.CTkEntry(self.dynamic_frame, textvariable=self.bank_var, width=200, height=32,
                                              state="readonly", font=ctk.CTkFont(size=12))
        self.check_num_lbl    = ctk.CTkLabel(self.dynamic_frame, text="Numero de cheque:", font=ctk.CTkFont(size=12, weight="bold"))
        self.check_num_entry  = ctk.CTkEntry(self.dynamic_frame, textvariable=self.check_num_var, width=200, height=32,
                                              state="readonly", font=ctk.CTkFont(size=12))

    ## -- Renderiza distintos campos segun el metodo de pago -- ##
    def render_dynamic_fields(self, parent):
        method = self.method_var.get()

        if method not in ("EFECTIVO", "TRANSFERENCIA", "CHEQUE"):
            return

        self.clear_dynamic_frame()
        self._selected_check = None
        self.excedente_var.set("")

        if method == "TRANSFERENCIA":
            self.op_num_lbl.grid(row=0, column=0, padx=20, pady=5)
            self.op_num_entry.grid(row=0, column=1, padx=(0,40), pady=5)
            self.origin_lbl.grid(row=1, column=0, padx=20, pady=5)
            self.origin_entry.grid(row=1, column=1, padx=(0,40), pady=5)
            self.destino_lbl.grid(row=2, column=0, padx=20, pady=5)
            self.destino_entry.grid(row=2, column=1, padx=(0,40), pady=5)
            self.render_buttons(9)

        elif method == "CHEQUE":
            # Cargar cheques en cartera
            self._load_cartera()

            self.cartera_lbl.grid(row=0, column=0, columnspan=2, padx=20, pady=(8, 2), sticky="w")
            self.cartera_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 4), sticky="ew")
            self.excedente_lbl.grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 2), sticky="w")
            self.check_bank_lbl.grid(row=3, column=0, padx=20, pady=4)
            self.check_bank_entry.grid(row=3, column=1, padx=(0, 40), pady=4)
            self.check_num_lbl.grid(row=4, column=0, padx=20, pady=4)
            self.check_num_entry.grid(row=4, column=1, padx=(0, 40), pady=4)
            self.render_buttons(5)

        elif method == "EFECTIVO":
            self.render_buttons(6)

        self.add_pay_win.update_idletasks()

    def _load_cartera(self):
        """Carga cheques EN_CARTERA en la tabla."""
        for row in self.cartera_table.get_children():
            self.cartera_table.delete(row)

        if not self.checks_model:
            return

        checks = self.checks_model.get_checks_en_cartera()
        for c in checks:
            # c: id, number, bank, type, amount, issue_date, due_date, ...
            try:
                from datetime import datetime as _dt
                due_fmt = _dt.strptime(c[6], "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                due_fmt = c[6]
            self.cartera_table.insert("", "end", values=(
                c[0], c[1], c[2], f"${c[4]}", due_fmt
            ))

    def _on_check_selected(self, event):
        """Al seleccionar un cheque, completa los campos y avisa si hay excedente."""
        sel = self.cartera_table.selection()
        if not sel:
            return

        vals = self.cartera_table.item(sel[0])["values"]
        check_id     = vals[0]
        check_number = vals[1]
        bank         = vals[2]
        check_amount = Decimal(str(vals[3]).replace("$", "").strip())

        # Guardar referencia al cheque seleccionado
        self._selected_check = {
            "id":     check_id,
            "number": check_number,
            "bank":   bank,
            "amount": check_amount,
        }

        # Completar campos
        self.bank_var.set(bank)
        self.check_num_var.set(str(check_number))

        # Verificar excedente respecto al monto del formulario
        self._check_excedente(check_amount)

    def _check_excedente(self, check_amount):
        """Muestra aviso si el cheque supera el monto a pagar."""
        try:
            monto_pago = Decimal(self.amount_var.get().strip() or "0")
        except Exception:
            monto_pago = Decimal("0")

        if check_amount > monto_pago and monto_pago > Decimal("0"):
            excedente = check_amount - monto_pago
            self.excedente_var.set(
                f"⚠️ El cheque supera el monto en ${excedente:.2f}. "
                f"El excedente deberá gestionarse en la veterinaria."
            )
        else:
            self.excedente_var.set("")

    def create_action_buttons(self, parent):
        self.button_frame = ctk.CTkFrame(self.dynamic_frame, fg_color="transparent")

        self.add_button = ctk.CTkButton(
            self.button_frame,
            text="Agregar Pago",
            width=120, height=35,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#4CAF50", hover_color="#45a049",
            command=lambda: self.confirm_payment(parent)
        )
        self.add_button.grid(row=0, column=0, padx=15, pady=10)

        self.cancel_button = ctk.CTkButton(self.button_frame, text="Cancelar", width=120, height=35, font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#757575", hover_color="#616161", command= lambda: close_win(self.add_pay_win, parent))
        self.cancel_button.grid(row=0, column=1, padx=15, pady=10) 

    ## -- Renderiza botones de accion -- ##
    def render_buttons(self, row_num):
        # Botones
        self.button_frame.grid(row=row_num, column=0, columnspan=2)

    ## -- Elimina campos dinamicos -- ##
    def clear_dynamic_frame(self):
        for widget in self.dynamic_frame.winfo_children():
            widget.grid_forget()

    ## -- Confirmación antes de registrar el pago -- ##
    def confirm_payment(self, parent):
        method = self.method_var.get()

        if not method:
            show_warning("Por favor seleccioná un método de pago.")
            return

        amount = self.amount_var.get().strip()
        if not amount or amount == '0':
            show_warning("Por favor ingresá un monto válido.")
            return

        # Armar resumen legible según el método
        resumen = (
            f"Proveedor (CUIT): {self.supplier_cuit_var.get()}\n"
            f"Monto:             $ {amount}\n"
            f"Método de pago:    {method}\n"
            f"N° Recibo:         {self.num_receipt_var.get() or '—'}\n"
        )

        if method == "TRANSFERENCIA":
            resumen += (
                f"N° Operación:      {self.opt_num_var.get() or '—'}\n"
                f"CBU/Alias origen:  {self.origin_var.get() or '—'}\n"
                f"CBU/Alias destino: {self.destinatation_var.get() or '—'}\n"
            )
        elif method == "CHEQUE":
            resumen += (
                f"Banco:             {self.bank_var.get() or '—'}\n"
                f"N° Cheque:         {self.check_num_var.get() or '—'}\n"
            )

        if self.observation_var.get().strip():
            resumen += f"Observaciones:     {self.observation_var.get().strip()}\n"

        if ask_confirmation(resumen, "¿Confirmar registro de pago?"):
            self.controller.register_payment(
                self.supplier_id_var.get(), self.add_pay_win, parent, self.purchase_id
            )

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
            'check_number': self.check_num_var.get().strip(),
            'check_id': self._selected_check['id'] if self._selected_check else None,
        }