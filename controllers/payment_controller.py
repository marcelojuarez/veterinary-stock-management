from decimal import Decimal
from utils.utils import string_to_2_dec
from utils.view_helpers import show_warning, show_error, close_win
from utils.receipts.manager import generate_orden_pago_proveedor
from tkinter import messagebox
from db.database import db


def _get_val(var):
    """Extrae el valor de un StringVar, str o int."""
    if var is None:
        return None
    return var.get() if hasattr(var, 'get') else var


class PaymentController():
    def __init__(self, supplier_model, event_bus, checks_model=None, supplier_credit=None):
        self.supplier_model   = supplier_model
        self.form_view        = None
        self.pay_view         = None
        self.event_bus        = event_bus
        self.checks_model     = checks_model
        self.supplier_credit  = supplier_credit   # instancia de SupplierCredit

    def set_form_view(self, view):
        self.form_view = view

    def set_pay_view(self, pay_view):
        self.pay_view = pay_view

    def register_payment(self, supplier_var, win, parent, purchase_id):
        conn = None
        purchase_id_int = None
        payment_data = None
        supplier_data = None
        credit_applied = Decimal("0")
        amount = Decimal("0")

        try:
            conn = db.get_connection()

            conn.execute("BEGIN")

            # -- Datos y Validaciones -- #
            # Datos de pago
            payment_data = self.form_view.get_payment_data()
            selected = _get_val(supplier_var)

            if not selected:
                show_warning("Seleccione un proveedor")
                return

            # Datos del proveedor
            supplier_data = self.supplier_model.core.find_supplier_by_id(int(selected), conn=conn)

            credit_applied = payment_data.get('credit_applied', Decimal("0"))
            amount_str     = payment_data['amount'].strip()
            # Si el crédito cubre todo, amount puede ser "0" o ""
            amount = string_to_2_dec(amount_str) if amount_str and amount_str != "0" else Decimal("0")
            total_pagado = amount + credit_applied

            # Validar datos solo si hay un pago adicional al crédito
            if amount > Decimal("0"):
                if not self.validate_data(payment_data):
                    return

            purchase_id_val = _get_val(purchase_id)
            purchase_id_int = int(purchase_id_val) if purchase_id_val else None

            if purchase_id_int is not None:
                # Se paga una sola compra
                purchase = self.supplier_model.purchase.get_purchase_by_id(purchase_id_int, conn=conn)
                debt = Decimal(purchase[9])
                if total_pagado > debt:
                    show_warning(f'El total a abonar (${total_pagado}) supera la deuda (${debt})')
                    return
            else:
                # El pago aplica a multiples compras
                total_debt = self.supplier_model.purchase.get_debt_of_supplier(selected, conn=conn)
                if total_pagado > Decimal(str(total_debt)):
                    show_warning(f'El total a abonar (${total_pagado}) supera la deuda total (${total_debt})')
                    return

            data = {
                'Supplier_id':    supplier_data[0],
                'Receipt_number': payment_data['receipt_number'],
                'Amount':         total_pagado,        # total real abonado
                'Method':         payment_data['method'] or 'SALDO_A_FAVOR',
                'Observation':    payment_data['observation'],
                'Operation_num':  payment_data['operation_num'],
                'Origin':         payment_data['origin'],
                'Destination':    payment_data['destination'],
                'Check_number':   payment_data['check_number'],
                'Bank':           payment_data['bank'],
            }

            check_id = payment_data.get('check_id')

            # Vincula 
            self.supplier_model.payment.register_payment_and_set_relation(data, check_id, conn, purchase_id)

            # ── Usar saldo a favor ────────────────────────────────
            if credit_applied > Decimal("0") and self.supplier_credit:
                self._usar_saldo_favor(
                    supplier_id  = supplier_data[0],
                    amount       = credit_applied,
                    purchase_id  = purchase_id_int,
                    conn=conn,
                    commit=False
                )

            # ── Endosar cheque + excedente ────────────────────────

            if check_id and self.checks_model:
                check = self.checks_model.get_check_by_id(check_id, conn=conn)
                if check:
                    check_amount = Decimal(str(check[4]))
                    excedente    = check_amount - amount

                    self.checks_model.update_status(
                        check_id, "ENDOSADO", purchase_id=purchase_id_int, conn=conn, commit=False
                    )

                    if excedente > Decimal("0") and self.supplier_credit:
                        self._registrar_saldo_favor(
                            supplier_id  = supplier_data[0],
                            excedente    = excedente,
                            check_id     = check_id,
                            check_number = payment_data.get('check_number', ''),
                            check_bank   = payment_data.get('bank', ''),
                            conn=conn,
                            commit=False
                        )

            conn.commit()

            self.event_bus.publish('refresh_checks', None)
            self.pay_view.load_payment_movement(selected)
            self.pay_view.load_purchase_history(True)
            self.event_bus.publish('refresh_supplier_table', None)

        except Exception as e:
            if conn:
                conn.rollback()
            show_error(f"Error al registrar pago: {e}")
            return  # salimos, no generamos orden de pago

        finally:
            if conn:
                conn.close()

        # ── Orden de pago ─────────────────────────────────────
        try:
            purchase_total   = ""
            purchase_pending = ""
            if purchase_id_int:
                p = self.supplier_model.purchase.get_purchase_by_id(purchase_id_int)
                if p:
                    purchase_total   = str(p[10])
                    purchase_pending = str(p[9])

            # Armar lista de medios para la OP
            payments_list = []
            if credit_applied > Decimal("0"):
                payments_list.append({
                    "method": "SALDO_A_FAVOR",
                    "amount": credit_applied,
                })
            if amount > Decimal("0"):
                met = payment_data['method'].upper()
                pago_entry = {"method": met, "amount": amount}
                if met in ("CHEQUE", "ECHEQ"):
                    pago_entry.update(
                        check_number = payment_data.get('check_number', ''),
                        check_bank   = payment_data.get('bank', ''),
                    )
                elif met == "TRANSFERENCIA":
                    pago_entry.update(
                        operation_num = payment_data.get('operation_num', ''),
                        origin        = payment_data.get('origin', ''),
                        destination   = payment_data.get('destination', ''),
                    )
                payments_list.append(pago_entry)

            parent_win = win if hasattr(win, 'winfo_exists') else None
            imprimir = messagebox.askyesno(
                "Orden de pago",
                "¿Desea imprimir la orden de pago?",
                parent=parent_win
            )
            generate_orden_pago_proveedor(
                supplier_name      = supplier_data[2],
                supplier_cuit      = supplier_data[1] or "",
                payments           = payments_list,
                receipt_number     = payment_data['receipt_number'],
                observation        = payment_data['observation'],
                purchase_id        = purchase_id_int,
                purchase_total     = purchase_total,
                purchase_remaining = purchase_pending,
                auto_print         = imprimir,
            )

            close_win(win, parent)

        except Exception as e:
                show_warning(f"El pago se registró correctamente pero no se pudo generar la orden de pago: {e}")

    def _usar_saldo_favor(self, supplier_id, amount, purchase_id, conn=None, commit=True):
        """
        Registra el uso del saldo a favor como movimiento negativo
        en supplier_credit_movements.
        """
        nota = f"Aplicado a compra #{purchase_id}" if purchase_id else "Aplicado a pago de deuda"
        self.supplier_credit.add_movement({
            "supplier_id":  supplier_id,
            "amount":       str(-amount),   # negativo = se consume saldo
            "type":         "USO_SALDO",
            "purchase_id": purchase_id,
            "check_id": None,
            "notes":        nota,
        }, conn=conn, commit=commit)
        print(f"[PaymentController] Saldo a favor usado: ${amount} para supplier {supplier_id}")

    def _registrar_saldo_favor(self, supplier_id, excedente, check_id, check_number, check_bank,
                               conn=None, commit=True):
        """
        Registra el excedente del cheque como saldo a favor del proveedor
        en supplier_credit_movements.
        amount positivo = crédito a favor de la veterinaria
        (el proveedor nos "debe" ese excedente).
        """

        nota = f"Excedente cheque N°{check_number} ({check_bank})" if check_number else "Excedente de cheque"
        self.supplier_credit.add_movement({
            "supplier_id":  supplier_id,
            "amount":       str(excedente),
            "type":         "EXCEDENTE_CHEQUE",
            "purchase_id": None,
            "check_id": check_id,
            "notes":        nota,
        }, conn=conn, commit=commit)
        print(f"[PaymentController] Saldo a favor registrado: ${excedente} para supplier {supplier_id}")

    @classmethod
    def validate_data(cls, data):

        required_fields = {
            'amount':         'Monto',
            'method':         'Metodo',
            'receipt_number': 'Numero de recibo',
        }

        for field, label in required_fields.items():
            if not data[field]:
                show_warning(f'Por favor complete el campo "{label}"')
                return False

        if not cls._is_decimal(data['amount']):
            show_error('Error. Monto invalido')
            return False

        amount = string_to_2_dec(data['amount'])
        if amount <= Decimal('0.00'):
            show_error('Error. El monto debe ser un valor positivo')
            return False

        if data['method'] == 'TRANSFERENCIA':
            for field, label in {
                'operation_num': 'Numero de operacion',
                'origin':        'CBU/Alias(origen)',
                'destination':   'CBU/Alias(destino)'
            }.items():
                if not data[field]:
                    show_warning(f'Por favor complete el campo "{label}"')
                    return False

        elif data['method'] == 'CHEQUE':
            for field, label in {
                'check_number': 'Numero de cheque',
                'bank':         'Banco'
            }.items():
                if not data[field]:
                    show_warning(f'Por favor complete el campo "{label}"')
                    return False
            if not cls._is_str(data['bank']):
                show_warning('Nombre de banco invalido')
                return False

        return True

    def validate_debt(self, amount, debt, total_debt):
        if amount > debt:
            prefix = 'La deuda Total es:' if total_debt else 'La deuda de la compra es: '
            show_warning(f'ERROR:\n{prefix} ${debt}\nEl monto que intenta abonar es superior: ${amount}')
            return False
        return True

    @staticmethod
    def _is_decimal(value):
        return string_to_2_dec(value) is not None

    @staticmethod
    def _is_int(value):
        try: int(value); return True
        except: return False

    @staticmethod
    def _is_str(value):
        try: str(value); return True
        except: return False