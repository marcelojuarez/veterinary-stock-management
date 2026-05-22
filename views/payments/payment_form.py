import logging
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
from decimal import Decimal
from utils.view_helpers import close_win, show_warning, ask_confirmation
from utils.utils import format_currency, clean_currency_input

logger = logging.getLogger(__name__)


class PaymentForm:

    def __init__(self, pay_win, model, frame, controller=None, checks_model=None, supplier_credit=None):
        self.pay_win        = pay_win
        self.model          = model
        self.frame          = frame
        self.controller     = controller
        self.checks_model   = checks_model
        self.supplier_credit = supplier_credit
        self._selected_check = None
        self._credit_applied = Decimal("0")
        self._credit_amount  = Decimal("0")   # saldo disponible del proveedor
        self._deuda_original = Decimal("0")   # deuda antes de aplicar crédito

    # ──────────────────────────────────────────────────────────────
    # VARIABLES
    # ──────────────────────────────────────────────────────────────
    def setup_payment_variables(self, supplier_id, supplier_cuit, purchase_id, amount):
        self.supplier_id_var  = tk.StringVar(value=supplier_id)
        self.supplier_cuit_var = tk.StringVar(value=supplier_cuit)
        self.amount_var       = tk.StringVar()
        self.method_var       = tk.StringVar()
        self.num_receipt_var  = tk.StringVar()
        self.observation_var  = tk.StringVar()
        self.opt_num_var      = tk.StringVar()
        self.origin_var       = tk.StringVar()
        self.destinatation_var = tk.StringVar()
        self.bank_var         = tk.StringVar()
        self.check_num_var    = tk.StringVar()

        self._credit_applied  = Decimal("0")
        self._credit_amount   = Decimal("0")
        self._selected_check  = None

        if purchase_id is not None and amount is not None:
            self.purchase_id = tk.StringVar(value=purchase_id)
            cleaned = clean_currency_input(amount)
            self.amount_var.set(cleaned)
            self._deuda_original = Decimal(str(cleaned))
        else:
            self.purchase_id = None
            if amount is not None:
                cleaned = clean_currency_input(amount)
                self.amount_var.set(cleaned)
                self._deuda_original = Decimal(str(cleaned))
            else:
                self._deuda_original = Decimal("0")

    def set_controller(self, controller):
        self.controller = controller

    # ──────────────────────────────────────────────────────────────
    # VENTANA PRINCIPAL
    # ──────────────────────────────────────────────────────────────
    def add_payment_win(self, parent, supplier_id, purchase_id=None, amount=None):
        if not supplier_id or str(supplier_id).strip() == '':
            show_warning('Por favor selecciona un Proveedor')
            return

        supplier_data = self.model.core.find_supplier_by_id(supplier_id)

        try:
            debt_total = Decimal(str(self.pay_win.debt_var.get()))
        except Exception:
            debt_total = Decimal("0")

        if debt_total <= Decimal("0"):
            show_warning(
                f'Atención. No se registra Deuda al proveedor: '
                f'{supplier_data[1]} - {supplier_data[2]}'
            )
            return

        self.setup_payment_variables(supplier_id, supplier_data[1], purchase_id, amount)

        # ── Calcular crédito disponible ────────────────────────────
        credit_source = getattr(self.model, 'credit', None) or self.supplier_credit
        if credit_source:
            try:
                self._credit_amount = Decimal(str(
                    credit_source.get_credit_amount_of_supplier(supplier_id) or "0"
                ))
            except Exception as e:
                logger.error("Error leyendo saldo a favor: %s", e)

        # ── Aplicar crédito automáticamente ───────────────────────
        # credit_applied = min(crédito, deuda)  → puede cubrir todo o solo parte
        if self._credit_amount > Decimal("0") and self._deuda_original > Decimal("0"):
            aplicar = min(self._credit_amount, self._deuda_original)
            self._credit_applied = aplicar
            resto = self._deuda_original - aplicar
            self.amount_var.set(str(resto))   # 0 si el crédito cubre todo
        # Si no hay crédito, amount_var ya tiene la deuda original

        # ── Construir ventana ──────────────────────────────────────
        self.add_pay_win = ctk.CTkToplevel(parent if parent else self.frame)
        self.add_pay_win.title("Registrar nuevo pago")
        self.add_pay_win.resizable(False, False)
        self.add_pay_win.protocol("WM_DELETE_WINDOW", lambda: close_win(self.add_pay_win, parent))
        self.add_pay_win.transient(parent)
        self.add_pay_win.grab_set()

        self._screen_w = self.add_pay_win.winfo_screenwidth()
        self._screen_h = self.add_pay_win.winfo_screenheight()
        self._win_w    = 580

        main_container = ctk.CTkFrame(self.add_pay_win, fg_color="#f0f0f0", width=self._win_w)
        main_container.pack(fill="x")
        main_container.pack_propagate(True)

        card = ctk.CTkFrame(main_container, fg_color="white", corner_radius=15, width=self._win_w - 40)
        card.pack(fill="x", padx=20, pady=20)
        card.pack_propagate(True)

        W = card
        W.columnconfigure(0, weight=0)
        W.columnconfigure(1, weight=1)

        FL  = ctk.CTkFont(size=13, weight="bold")
        FE  = ctk.CTkFont(size=13)
        EW, EH = 280, 36
        row = 0

        # Título
        ctk.CTkLabel(W, text="💳 Nuevo Pago", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=row, column=0, columnspan=2, pady=(16, 14)); row += 1

        # CUIT
        ctk.CTkLabel(W, text="CUIT:", font=FL).grid(row=row, column=0, padx=(20,8), pady=5, sticky="e")
        ctk.CTkEntry(W, textvariable=self.supplier_cuit_var, width=EW, height=EH,
                     state='readonly', font=FE).grid(row=row, column=1, padx=(0,20), pady=5, sticky="w"); row += 1

        # ── Banner crédito (antes de monto) ───────────────────────
        if self._credit_applied > Decimal("0"):
            banner = ctk.CTkFrame(W, fg_color="#E8F5E9", corner_radius=8)
            banner.grid(row=row, column=0, columnspan=2, padx=20, pady=(4, 2), sticky="ew"); row += 1
            if self._credit_applied >= self._deuda_original:
                txt = f"✅  Saldo a favor cubre el total: $ {self._credit_applied}"
            else:
                txt = (f"✅  Saldo a favor aplicado: $ {self._credit_applied}"
                       f"  —  Resta pagar: $ {self._deuda_original - self._credit_applied}")
            ctk.CTkLabel(banner, text=txt,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#2E7D32").pack(side="left", padx=10, pady=6)

        # Monto restante a pagar (solo si queda algo)
        resto = Decimal(self.amount_var.get() or "0")
        if resto > Decimal("0"):
            ctk.CTkLabel(W, text="Monto a pagar:", font=FL).grid(
                row=row, column=0, padx=(20,8), pady=5, sticky="e")
            self.amount_entry = ctk.CTkEntry(W, textvariable=self.amount_var, width=EW, height=EH,
                         font=FE)
            self.amount_entry.grid(row=row, column=1, padx=(0,20), pady=5, sticky="w"); row += 1

        # Nro recibo
        ctk.CTkLabel(W, text="Nº de recibo:", font=FL).grid(row=row, column=0, padx=(20,8), pady=5, sticky="e")
        ctk.CTkEntry(W, textvariable=self.num_receipt_var, width=EW, height=EH,
                     font=FE).grid(row=row, column=1, padx=(0,20), pady=5, sticky="w"); row += 1

        # Observaciones
        ctk.CTkLabel(W, text="Observaciones:", font=FL).grid(row=row, column=0, padx=(20,8), pady=5, sticky="e")
        ctk.CTkEntry(W, textvariable=self.observation_var, width=EW, height=EH,
                     font=FE).grid(row=row, column=1, padx=(0,20), pady=5, sticky="w"); row += 1

        # Método de pago — solo si queda resto por pagar
        self._method_row = row
        if resto > Decimal("0"):
            ctk.CTkLabel(W, text="Método de Pago:", font=FL).grid(
                row=row, column=0, padx=(20,8), pady=5, sticky="e")
            self.method_combo = ctk.CTkComboBox(
                W, values=["EFECTIVO", "TRANSFERENCIA", "CHEQUE"],
                variable=self.method_var, width=EW, height=EH,
                font=FE, state="readonly",
                command=lambda value: self.render_dynamic_fields(parent, W)
            )
            self.method_combo.set("")
            self.method_combo.grid(row=row, column=1, padx=(0,20), pady=5, sticky="w"); row += 1

        # Frame dinámico
        self.dynamic_frame = ctk.CTkFrame(W, fg_color="transparent")
        self.dynamic_frame.grid(row=row, column=0, columnspan=2, pady=(4, 4), sticky="ew")
        self.dynamic_frame.columnconfigure(0, weight=0)
        self.dynamic_frame.columnconfigure(1, weight=1)
        self._dynamic_row = row

        self.main_card = W

        self.create_dynamic_fields()
        self.create_action_buttons(parent)

        # Si el crédito cubre todo, mostrar botones directamente
        if resto <= Decimal("0"):
            self.render_buttons(0)

        # Centrar con tamaño natural
        self.add_pay_win.update_idletasks()
        w = self.add_pay_win.winfo_reqwidth()
        h = 400
        self._base_h = h   # guardar altura base para expandir con campos dinámicos
        x = self._screen_w // 2 - w // 2
        y = self._screen_h // 2 - h // 2
        self.add_pay_win.geometry(f"{max(w, self._win_w)}x{h}+{x}+{y}")

    # ──────────────────────────────────────────────────────────────
    # CAMPOS DINÁMICOS
    # ──────────────────────────────────────────────────────────────
    def create_dynamic_fields(self):
        # TRANSFERENCIA
        self.op_num_lbl   = ctk.CTkLabel(self.dynamic_frame, text="Nº de operación:", font=ctk.CTkFont(size=12, weight="bold"))
        self.op_num_entry = ctk.CTkEntry(self.dynamic_frame, textvariable=self.opt_num_var, width=280, height=35, font=ctk.CTkFont(size=12))
        self.origin_lbl   = ctk.CTkLabel(self.dynamic_frame, text="CBU/Alias Emisor:", font=ctk.CTkFont(size=12, weight="bold"))
        self.origin_entry = ctk.CTkEntry(self.dynamic_frame, textvariable=self.origin_var, width=280, height=35, font=ctk.CTkFont(size=12))
        self.destino_lbl  = ctk.CTkLabel(self.dynamic_frame, text="CBU/Alias Receptor:", font=ctk.CTkFont(size=12, weight="bold"))
        self.destino_entry = ctk.CTkEntry(self.dynamic_frame, textvariable=self.destinatation_var, width=280, height=35, font=ctk.CTkFont(size=12))

        # CHEQUE — selector de cartera
        self.cartera_lbl = ctk.CTkLabel(
            self.dynamic_frame, text="Seleccionar cheque de cartera:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        cartera_frame = ctk.CTkFrame(self.dynamic_frame, fg_color="#f9f9f9", corner_radius=8)
        self.cartera_frame = cartera_frame

        style = ttk.Style()
        style.configure("Cartera.Treeview", rowheight=24, font=("Segoe UI", 9))
        style.configure("Cartera.Treeview.Heading", font=("Segoe UI", 9, "bold"))

        cols = ("ID", "Nro.", "Banco", "Monto", "Vence")
        self.cartera_table = ttk.Treeview(
            cartera_frame, columns=cols, show="headings",
            height=4, style="Cartera.Treeview"
        )
        widths = {"ID": 0, "Nro.": 90, "Banco": 120, "Monto": 90, "Vence": 90}
        for col in cols:
            w = widths[col]
            self.cartera_table.column(col, width=w, anchor="center", minwidth=w, stretch=True)
            self.cartera_table.heading(col, text=col)
        self.cartera_table.column("ID", width=0, minwidth=0, stretch=False)

        sy = ttk.Scrollbar(cartera_frame, orient="vertical", command=self.cartera_table.yview)
        self.cartera_table.configure(yscrollcommand=sy.set)
        sy.pack(side="right", fill="y", padx=(0, 4), pady=4)
        self.cartera_table.pack(fill="both", expand=True, padx=4, pady=4)
        self.cartera_table.bind("<<TreeviewSelect>>", self._on_check_selected)

        self.excedente_var = tk.StringVar()
        self.excedente_lbl = ctk.CTkLabel(
            self.dynamic_frame, textvariable=self.excedente_var,
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#E65100"
        )

        self.check_bank_lbl   = ctk.CTkLabel(self.dynamic_frame, text="Banco:", font=ctk.CTkFont(size=12, weight="bold"))
        self.check_bank_entry = ctk.CTkEntry(self.dynamic_frame, textvariable=self.bank_var, width=280, height=32,
                                              state="readonly", font=ctk.CTkFont(size=12))
        self.check_num_lbl    = ctk.CTkLabel(self.dynamic_frame, text="Nº de cheque:", font=ctk.CTkFont(size=12, weight="bold"))
        self.check_num_entry  = ctk.CTkEntry(self.dynamic_frame, textvariable=self.check_num_var, width=280, height=32,
                                              state="readonly", font=ctk.CTkFont(size=12))

    def render_dynamic_fields(self, parent, card_widget):
        method = self.method_var.get()
        if method not in ("EFECTIVO", "TRANSFERENCIA", "CHEQUE"):
            return

        self.clear_dynamic_frame()
        self._selected_check = None
        self.excedente_var.set("")

        if method == "TRANSFERENCIA":
            self.op_num_lbl.grid(row=0, column=0, padx=(20,8), pady=4, sticky="e")
            self.op_num_entry.grid(row=0, column=1, padx=(0,20), pady=4, sticky="w")
            self.origin_lbl.grid(row=1, column=0, padx=(20,8), pady=4, sticky="e")
            self.origin_entry.grid(row=1, column=1, padx=(0,20), pady=4, sticky="w")
            self.destino_lbl.grid(row=2, column=0, padx=(20,8), pady=4, sticky="e")
            self.destino_entry.grid(row=2, column=1, padx=(0,20), pady=4, sticky="w")
            self.render_buttons(3)
            self._resize_window(self._base_h + 150)

        elif method == "CHEQUE":
            self._load_cartera()
            self.cartera_lbl.grid(row=0, column=0, columnspan=2, padx=20, pady=(4, 2), sticky="w")
            self.cartera_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 4), sticky="ew")
            self.excedente_lbl.grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 2), sticky="w")
            self.check_bank_lbl.grid(row=3, column=0, padx=(20,8), pady=4, sticky="e")
            self.check_bank_entry.grid(row=3, column=1, padx=(0,20), pady=4, sticky="w")
            self.check_num_lbl.grid(row=4, column=0, padx=(20,8), pady=4, sticky="e")
            self.check_num_entry.grid(row=4, column=1, padx=(0,20), pady=4, sticky="w")
            self.render_buttons(5)
            self._resize_window(self._base_h + 300)

        elif method == "EFECTIVO":
            self.render_buttons(0)
            self._resize_window(self._base_h)

        self.add_pay_win.update_idletasks()

    def _resize_window(self, new_height):
        self.add_pay_win.update_idletasks()
        req_h = self.add_pay_win.winfo_reqheight()
        h  = max(new_height, req_h)
        sh = getattr(self, '_screen_h', self.add_pay_win.winfo_screenheight())
        h  = min(h, sh - 20)
        w  = getattr(self, '_win_w', 580)
        sw = getattr(self, '_screen_w', self.add_pay_win.winfo_screenwidth())
        x  = sw // 2 - w // 2
        y  = sh // 2 - h // 2
        self.add_pay_win.geometry(f"{w}x{h}+{x}+{y}")

    # ──────────────────────────────────────────────────────────────
    # CARTERA DE CHEQUES
    # ──────────────────────────────────────────────────────────────
    def _load_cartera(self):
        for row in self.cartera_table.get_children():
            self.cartera_table.delete(row)
        if not self.checks_model:
            return
        checks = self.checks_model.get_checks_en_cartera()
        for c in checks:
            try:
                from datetime import datetime as _dt
                due_fmt = _dt.strptime(c[6], "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                due_fmt = c[6]
            self.cartera_table.insert("", "end", values=(c[0], c[1], c[2], f"${c[4]}", due_fmt))

    def _on_check_selected(self, event):
        sel = self.cartera_table.selection()
        if not sel:
            return
        vals = self.cartera_table.item(sel[0])["values"]
        check_id     = vals[0]
        check_number = vals[1]
        bank         = vals[2]
        check_amount = Decimal(str(vals[3]).replace("$", "").strip())
        self._selected_check = {"id": check_id, "number": check_number,
                                "bank": bank, "amount": check_amount}
        self.bank_var.set(bank)
        self.check_num_var.set(str(check_number))
        self.amount_var.set(str(check_amount))
        if hasattr(self, 'amount_entry'):
            self.amount_entry.configure(state='readonly')
        self._check_excedente(check_amount)

    def _check_excedente(self, check_amount):
        try:
            monto_pago = Decimal(self.amount_var.get().strip() or "0")
        except Exception:
            monto_pago = Decimal("0")
        if check_amount > monto_pago and monto_pago > Decimal("0"):
            excedente = check_amount - monto_pago
            self.excedente_var.set(
                f"⚠️ El cheque supera el monto en ${excedente:.2f}. "
                f"El excedente quedará como saldo a favor."
            )
        else:
            self.excedente_var.set("")

    # ──────────────────────────────────────────────────────────────
    # BOTONES
    # ──────────────────────────────────────────────────────────────
    def create_action_buttons(self, parent):
        self.button_frame = ctk.CTkFrame(self.dynamic_frame, fg_color="transparent")
        self.add_button = ctk.CTkButton(
            self.button_frame, text="✓ Agregar Pago",
            width=140, height=38, font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#4CAF50", hover_color="#45a049",
            command=lambda: self.confirm_payment(parent)
        )
        self.add_button.grid(row=0, column=0, padx=10, pady=12)
        self.cancel_button = ctk.CTkButton(
            self.button_frame, text="Cancelar",
            width=140, height=38, font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#757575", hover_color="#616161",
            command=lambda: close_win(self.add_pay_win, parent)
        )
        self.cancel_button.grid(row=0, column=1, padx=10, pady=12)

    def render_buttons(self, row_num):
        self.button_frame.grid(row=row_num, column=0, columnspan=2, pady=(8, 0))

    def clear_dynamic_frame(self):
        for widget in self.dynamic_frame.winfo_children():
            widget.grid_forget()

    # ──────────────────────────────────────────────────────────────
    # CONFIRMACIÓN Y DATOS
    # ──────────────────────────────────────────────────────────────
    def confirm_payment(self, parent):
        amount = self.amount_var.get().strip()
        method = self.method_var.get()
        credito_cubre_todo = self._credit_applied >= self._deuda_original and self._deuda_original > Decimal("0")

        if not credito_cubre_todo:
            if not method:
                show_warning("Por favor seleccioná un método de pago.")
                return
            if not amount or amount == '0':
                show_warning("Por favor ingresá un monto válido.")
                return

        resumen = f"Proveedor (CUIT): {self.supplier_cuit_var.get()}\n"

        if self._credit_applied > Decimal("0"):
            resumen += f"Saldo a favor aplicado: $ {self._credit_applied}\n"

        if not credito_cubre_todo:
            resumen += (
                f"Monto adicional:   $ {amount}\n"
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
        else:
            resumen += "El saldo a favor cubre el total.\n"

        if self.observation_var.get().strip():
            resumen += f"Observaciones:     {self.observation_var.get().strip()}\n"

        if ask_confirmation(resumen, "¿Confirmar registro de pago?"):
            self.controller.register_payment(
                self.supplier_id_var.get(), self.add_pay_win, parent, self.purchase_id
            )

    def get_payment_data(self):
        return {
            'amount':         self.amount_var.get().strip(),
            'method':         self.method_var.get().strip(),
            'receipt_number': self.num_receipt_var.get().strip(),
            'observation':    self.observation_var.get().strip(),
            'operation_num':  self.opt_num_var.get().strip(),
            'origin':         self.origin_var.get().strip(),
            'destination':    self.destinatation_var.get().strip(),
            'bank':           self.bank_var.get().strip(),
            'check_number':   self.check_num_var.get().strip(),
            'check_id':       self._selected_check['id'] if self._selected_check else None,
            'credit_applied': self._credit_applied,
        }