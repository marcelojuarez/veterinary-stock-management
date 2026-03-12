import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
from decimal import Decimal
from utils.view_helpers import close_win, show_warning, ask_confirmation


# ══════════════════════════════════════════════════════════════
#  CONSTANTES DE ESTILO — único lugar para cambiar apariencia
# ══════════════════════════════════════════════════════════════
class _S:
    # Ventana
    WIN_W, WIN_H  = 600, 650

    # Padding exterior
    PAD_X         = 28
    PAD_Y         = 18

    # Grilla de campos
    ROW_PAD_Y     = (5, 5)    # (arriba, abajo) por fila
    LABEL_PAD_X   = (0, 14)   # separación etiqueta → campo
    LABEL_MIN_W   = 140     # ancho mínimo col-0 (etiquetas)

    # Campos — tamaño ÚNICO para toda la ventana
    FIELD_W       = 290
    FIELD_H       = 34

    # Zona dinámica: altura fija reservada
    DYN_H         = 220

    # Tabla cartera
    TABLE_ROWS    = 4
    TABLE_H       = 108

    # Botones
    BTN_W         = 155
    BTN_H         = 36

    # Colores
    COLOR_OK      = "#4CAF50"
    COLOR_OK_HV   = "#43A047"
    COLOR_CNL     = "#757575"
    COLOR_CNL_HV  = "#616161"
    COLOR_WARN    = "#E65100"

    # Columnas tabla
    TABLE_COLS    = ("ID", "Nro.", "Banco", "Monto", "Vence")
    TABLE_WIDTHS  = {"ID": 0, "Nro.": 95, "Banco": 150, "Monto": 82, "Vence": 82}

    @staticmethod
    def fonts():
        return {
            "title":   ctk.CTkFont(size=17, weight="bold"),
            "label":   ctk.CTkFont(size=13, weight="bold"),
            "field":   ctk.CTkFont(size=13),
            "btn":     ctk.CTkFont(size=13, weight="bold"),
            "warn":    ctk.CTkFont(size=11, weight="bold"),
            "table":   ("Segoe UI", 9),
            "table_h": ("Segoe UI", 9, "bold"),
        }


# ══════════════════════════════════════════════════════════════
class PaymentForm:

    def __init__(self, pay_win, model, frame, controller=None, checks_model=None):
        self.pay_win         = pay_win
        self.model           = model
        self.frame           = frame
        self.controller      = controller
        self.checks_model    = checks_model
        self._selected_check = None

    # ──────────────────────────────────────────────────────────
    #  Variables de formulario
    # ──────────────────────────────────────────────────────────
    def setup_payment_variables(self, supplier_id, supplier_cuit, purchase_id, amount):
        self.supplier_id_var    = tk.StringVar(value=supplier_id)
        self.supplier_cuit_var  = tk.StringVar(value=supplier_cuit)
        self.amount_var         = tk.StringVar()

        if purchase_id is not None and amount is not None:
            self.purchase_id = tk.StringVar(value=purchase_id)
            self.amount_var.set(amount)
        else:
            self.purchase_id = None

        self.method_var         = tk.StringVar()
        self.num_receipt_var    = tk.StringVar()
        self.observation_var    = tk.StringVar()
        self.opt_num_var        = tk.StringVar()
        self.origin_var         = tk.StringVar()
        self.destinatation_var  = tk.StringVar()
        self.bank_var           = tk.StringVar()
        self.check_num_var      = tk.StringVar()
        self.excedente_var      = tk.StringVar()

    def set_controller(self, controller):
        self.controller = controller

    # ──────────────────────────────────────────────────────────
    #  Ventana principal
    # ──────────────────────────────────────────────────────────
    def add_payment_win(self, parent, supplier_id, purchase_id=None, amount=None):
        if supplier_id.strip() == "":
            show_warning("Por favor seleccioná un Proveedor")
            return

        supplier_data = self.model.core.find_supplier_by_id(supplier_id)

        if Decimal(self.pay_win.debt_var.get()) <= Decimal("0.00"):
            show_warning(
                f"Atención. No se registra Deuda al proveedor: "
                f"{supplier_data[1]} - {supplier_data[2]}"
            )
            return

        self.setup_payment_variables(supplier_id, supplier_data[1], purchase_id, amount)
        self.F = _S.fonts()

        self.add_pay_win = ctk.CTkToplevel(parent or self.frame)
        self.add_pay_win.title("Registrar nuevo pago")
        self.add_pay_win.resizable(False, False)

        sw = self.add_pay_win.winfo_screenwidth()
        sh = self.add_pay_win.winfo_screenheight()
        self.add_pay_win.geometry(
            f"{_S.WIN_W}x{_S.WIN_H}"
            f"+{sw // 2 - _S.WIN_W // 2}+{sh // 2 - _S.WIN_H // 2}"
        )
        self.add_pay_win.protocol(
            "WM_DELETE_WINDOW", lambda: close_win(self.add_pay_win, parent)
        )
        self.add_pay_win.transient(parent)
        self.add_pay_win.grab_set()

        # ── Clave: botones se declaran PRIMERO con side="bottom" ──
        # Tkinter reserva su espacio antes de repartir el resto,
        # así nunca quedan cortados aunque crezca la zona dinámica.
        btn_frame = ctk.CTkFrame(self.add_pay_win, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x",
                       padx=_S.PAD_X, pady=(4, _S.PAD_Y))

        main = ctk.CTkFrame(self.add_pay_win, fg_color="transparent")
        main.pack(side="top", fill="both", expand=True,
                  padx=_S.PAD_X, pady=(_S.PAD_Y, 0))

        # col-0 = etiquetas (ancho fijo) | col-1 = campos (flexible)
        main.columnconfigure(0, minsize=_S.LABEL_MIN_W, weight=0)
        main.columnconfigure(1, weight=1)

        self._build_static_fields(main, parent)
        self._build_dynamic_section(main)
        self._build_buttons(btn_frame, parent)

    # ──────────────────────────────────────────────────────────
    #  Campos estáticos (siempre visibles)
    # ──────────────────────────────────────────────────────────
    def _build_static_fields(self, main, parent):
        F, S = self.F, _S

        ctk.CTkLabel(main, text="Registrar Nuevo Pago", font=F["title"]) \
            .grid(row=0, column=0, columnspan=2, pady=(0, 14))

        static_rows = [
            (1, "CUIT:",             self.supplier_cuit_var, "readonly"),
            (2, "Monto:",            self.amount_var,        "normal"),
            (3, "Número de recibo:", self.num_receipt_var,   "normal"),
            (4, "Observaciones:",    self.observation_var,   "normal"),
        ]
        for row, text, var, state in static_rows:
            ctk.CTkLabel(main, text=text, font=F["label"]) \
                .grid(row=row, column=0, sticky="e",
                      pady=S.ROW_PAD_Y, padx=S.LABEL_PAD_X)
            ctk.CTkEntry(
                main, textvariable=var,
                width=S.FIELD_W, height=S.FIELD_H,
                font=F["field"], state=state,
            ).grid(row=row, column=1, sticky="w", pady=S.ROW_PAD_Y)

        ctk.CTkLabel(main, text="Método de pago:", font=F["label"]) \
            .grid(row=5, column=0, sticky="e",
                  pady=S.ROW_PAD_Y, padx=S.LABEL_PAD_X)
        ctk.CTkComboBox(
            main,
            values=["EFECTIVO", "TRANSFERENCIA", "CHEQUE"],
            variable=self.method_var,
            width=S.FIELD_W, height=S.FIELD_H,
            font=F["field"], state="readonly",
            command=lambda v: self.render_dynamic_fields(parent),
        ).grid(row=5, column=1, sticky="w", pady=S.ROW_PAD_Y)

    # ──────────────────────────────────────────────────────────
    #  Zona dinámica con altura fija reservada
    # ──────────────────────────────────────────────────────────
    def _build_dynamic_section(self, main):
        # grid_propagate(False) mantiene DYN_H fijo sin importar
        # cuántos widgets se muestren adentro.
        container = ctk.CTkFrame(main, fg_color="transparent",
                                 height=_S.DYN_H)
        container.grid(row=6, column=0, columnspan=2,
                       sticky="ew", pady=(8, 0))
        container.grid_propagate(False)

        self.dynamic_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.dynamic_frame.place(x=0, y=0, relwidth=1.0)

        # Mismas proporciones de columna que main → alineación perfecta
        self.dynamic_frame.columnconfigure(0, minsize=_S.LABEL_MIN_W, weight=0)
        self.dynamic_frame.columnconfigure(1, weight=1)

        self._create_dynamic_widgets()

    def _create_dynamic_widgets(self):
        """Instancia todos los widgets dinámicos una sola vez."""
        F, S = self.F, _S
        df = self.dynamic_frame

        # ── Transferencia ──
        self.op_num_lbl    = ctk.CTkLabel(df, text="Número de operación:",    font=F["label"])
        self.op_num_entry  = ctk.CTkEntry(df, textvariable=self.opt_num_var,  width=S.FIELD_W, height=S.FIELD_H, font=F["field"])
        self.origin_lbl    = ctk.CTkLabel(df, text="CBU / Alias (emisor):",   font=F["label"])
        self.origin_entry  = ctk.CTkEntry(df, textvariable=self.origin_var,   width=S.FIELD_W, height=S.FIELD_H, font=F["field"])
        self.destino_lbl   = ctk.CTkLabel(df, text="CBU / Alias (receptor):", font=F["label"])
        self.destino_entry = ctk.CTkEntry(df, textvariable=self.destinatation_var, width=S.FIELD_W, height=S.FIELD_H, font=F["field"])

        # ── Cheque ──
        self.cartera_lbl = ctk.CTkLabel(df, text="Seleccionar cheque de cartera:",
                                        font=F["label"])

        self.cartera_frame = ctk.CTkFrame(df, fg_color="transparent",
                                          height=S.TABLE_H)
        self.cartera_frame.pack_propagate(False)

        style = ttk.Style()
        style.configure("Cartera.Treeview", rowheight=22, font=F["table"])
        style.configure("Cartera.Treeview.Heading", font=F["table_h"])

        self.cartera_table = ttk.Treeview(
            self.cartera_frame,
            columns=S.TABLE_COLS,
            show="headings",
            height=S.TABLE_ROWS,
            style="Cartera.Treeview",
        )
        for col in S.TABLE_COLS:
            w = S.TABLE_WIDTHS[col]
            self.cartera_table.column(col, width=w, minwidth=w,
                                      anchor="center", stretch=(col != "ID"))
            self.cartera_table.heading(col, text=col)
        self.cartera_table.column("ID", width=0, minwidth=0, stretch=False)

        sy = ttk.Scrollbar(self.cartera_frame, orient="vertical",
                           command=self.cartera_table.yview)
        self.cartera_table.configure(yscrollcommand=sy.set)
        sy.pack(side="right", fill="y")
        self.cartera_table.pack(fill="both", expand=True)
        self.cartera_table.bind("<<TreeviewSelect>>", self._on_check_selected)

        self.excedente_lbl = ctk.CTkLabel(
            df, textvariable=self.excedente_var,
            font=F["warn"], text_color=_S.COLOR_WARN,
            anchor="w", justify="left",
        )

        # Campos readonly — mismo tamaño que el resto
        self.check_bank_lbl   = ctk.CTkLabel(df, text="Banco:",            font=F["label"])
        self.check_bank_entry = ctk.CTkEntry(df, textvariable=self.bank_var,
                                             width=S.FIELD_W, height=S.FIELD_H,
                                             state="readonly", font=F["field"])
        self.check_num_lbl    = ctk.CTkLabel(df, text="Número de cheque:", font=F["label"])
        self.check_num_entry  = ctk.CTkEntry(df, textvariable=self.check_num_var,
                                             width=S.FIELD_W, height=S.FIELD_H,
                                             state="readonly", font=F["field"])

    # ──────────────────────────────────────────────────────────
    #  Botones
    # ──────────────────────────────────────────────────────────
    def _build_buttons(self, btn_frame, parent):
        F, S = self.F, _S
        btn_frame.columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_frame, text="Registrar Pago",
            width=S.BTN_W, height=S.BTN_H, font=F["btn"],
            fg_color=S.COLOR_OK, hover_color=S.COLOR_OK_HV,
            command=lambda: self.confirm_payment(parent),
        ).grid(row=0, column=0, padx=10, pady=6)

        ctk.CTkButton(
            btn_frame, text="Cancelar",
            width=S.BTN_W, height=S.BTN_H, font=F["btn"],
            fg_color=S.COLOR_CNL, hover_color=S.COLOR_CNL_HV,
            command=lambda: close_win(self.add_pay_win, parent),
        ).grid(row=0, column=1, padx=10, pady=6)

    # ──────────────────────────────────────────────────────────
    #  Renderizado dinámico
    # ──────────────────────────────────────────────────────────
    def render_dynamic_fields(self, parent):
        method = self.method_var.get()
        if method not in ("EFECTIVO", "TRANSFERENCIA", "CHEQUE"):
            return

        self._clear_dynamic_frame()
        self._selected_check = None
        self.excedente_var.set("")

        S  = _S
        py = S.ROW_PAD_Y
        px = S.LABEL_PAD_X

        if method == "TRANSFERENCIA":
            pairs = [
                (self.op_num_lbl,  self.op_num_entry),
                (self.origin_lbl,  self.origin_entry),
                (self.destino_lbl, self.destino_entry),
            ]
            for i, (lbl, ent) in enumerate(pairs):
                lbl.grid(row=i, column=0, sticky="e", padx=px, pady=py)
                ent.grid(row=i, column=1, sticky="w",           pady=py)

        elif method == "CHEQUE":
            self._load_cartera()
            self.cartera_lbl.grid(     row=0, column=0, columnspan=2,
                                       sticky="w", padx=(2, 0), pady=(4, 2))
            self.cartera_frame.grid(   row=1, column=0, columnspan=2,
                                       sticky="ew", pady=(0, 4))
            self.excedente_lbl.grid(   row=2, column=0, columnspan=2,
                                       sticky="w", padx=(2, 0), pady=(0, 2))
            self.check_bank_lbl.grid(  row=3, column=0, sticky="e", padx=px, pady=py)
            self.check_bank_entry.grid(row=3, column=1, sticky="w",           pady=py)
            self.check_num_lbl.grid(   row=4, column=0, sticky="e", padx=px, pady=py)
            self.check_num_entry.grid( row=4, column=1, sticky="w",           pady=py)

        # EFECTIVO: sin campos extra
        self.add_pay_win.update_idletasks()

    def _clear_dynamic_frame(self):
        for w in self.dynamic_frame.winfo_children():
            w.grid_forget()

    # ──────────────────────────────────────────────────────────
    #  Cartera de cheques
    # ──────────────────────────────────────────────────────────
    def _load_cartera(self):
        for row in self.cartera_table.get_children():
            self.cartera_table.delete(row)
        if not self.checks_model:
            return
        from datetime import datetime as _dt
        for c in self.checks_model.get_checks_en_cartera():
            try:
                due_fmt = _dt.strptime(c[6], "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                due_fmt = c[6]
            self.cartera_table.insert("", "end",
                                      values=(c[0], c[1], c[2], f"${c[4]}", due_fmt))

    def _on_check_selected(self, event):
        sel = self.cartera_table.selection()
        if not sel:
            return
        vals         = self.cartera_table.item(sel[0])["values"]
        check_amount = Decimal(str(vals[3]).replace("$", "").strip())

        self._selected_check = {
            "id":     vals[0],
            "number": vals[1],
            "bank":   vals[2],
            "amount": check_amount,
        }
        self.bank_var.set(vals[2])
        self.check_num_var.set(str(vals[1]))
        self._check_excedente(check_amount)

    def _check_excedente(self, check_amount):
        try:
            monto_pago = Decimal(self.amount_var.get().strip() or "0")
        except Exception:
            monto_pago = Decimal("0")

        if check_amount > monto_pago > Decimal("0"):
            excedente = check_amount - monto_pago
            self.excedente_var.set(
                f"⚠️  El cheque supera el monto en ${excedente:.2f}. "
                f"El excedente deberá gestionarse en la veterinaria."
            )
        else:
            self.excedente_var.set("")

    # ──────────────────────────────────────────────────────────
    #  Confirmación y registro
    # ──────────────────────────────────────────────────────────
    def confirm_payment(self, parent):
        method = self.method_var.get()
        if not method:
            show_warning("Por favor seleccioná un método de pago.")
            return

        amount = self.amount_var.get().strip()
        if not amount or amount == "0":
            show_warning("Por favor ingresá un monto válido.")
            return

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

    # ──────────────────────────────────────────────────────────
    #  Datos del formulario
    # ──────────────────────────────────────────────────────────
    def get_payment_data(self):
        return {
            "amount":         self.amount_var.get().strip(),
            "method":         self.method_var.get().strip(),
            "receipt_number": self.num_receipt_var.get().strip(),
            "observation":    self.observation_var.get().strip(),
            "operation_num":  self.opt_num_var.get().strip(),
            "origin":         self.origin_var.get().strip(),
            "destination":    self.destinatation_var.get().strip(),
            "bank":           self.bank_var.get().strip(),
            "check_number":   self.check_num_var.get().strip(),
            "check_id":       self._selected_check["id"] if self._selected_check else None,
        }