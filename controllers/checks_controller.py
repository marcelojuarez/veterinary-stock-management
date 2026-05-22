"""
Controlador de cartera de cheques.
"""
from decimal import Decimal
from datetime import datetime
from tkinter import messagebox
from utils.view_helpers import show_error
from db.database import db

class ChecksController:
    def __init__(self, checks_model, payment_model, customer_credit, customer_model, sales_model, 
                 supplier_model, event_bus=None):
        self.model = checks_model
        self.db = db
        self.payment_model = payment_model
        self.customer_credit = customer_credit
        self.customer_model = customer_model
        self.sales_model = sales_model
        self.supplier_model = supplier_model
        self.view = None
        if event_bus:
            event_bus.subscribe('refresh_checks', lambda _: self.load_checks(
                self.view.filter_var.get() if self.view else "EN_CARTERA"
            ))

    def set_view(self, view):
        self.view = view
        self.load_checks("EN_CARTERA")

    def load_checks(self, filter_status="EN_CARTERA"):
        try:
            status = None if filter_status == "TODOS" else filter_status
            checks = self.model.get_all_checks(status=status)
            self.view.refresh_table(checks)
            all_checks = self.model.get_all_checks()
            self.view.update_stats(all_checks)
        except Exception as e:
            self.view.show_error(f"Error al cargar cheques: {e}")

    ## -- Marcar cheque como cobrado -- ##
    def mark_cobrado(self, check_id):
        try:
            self.model.mark_cobrado(check_id)
            self.view.show_success("Cheque marcado como COBRADO.")
            self.load_checks(self.view.filter_var.get())
        except Exception as e:
            self.view.show_error(f"Error: {e}")
    
    ## -- Marcar cheque como rechazado -- ##
    def manage_check_rechazado(self, check_id, check_state):
        result = self.mark_rechazado(check_id, check_state)

        if not result:
            return False, 'Ocurrió un error.'

        check_data = self.model.get_check_by_id(check_id)
        client_id = check_data[9]
        new_debt = self.customer_model.get_total_debt(client_id)
        client_data = self.customer_model.find_customer_by_id(client_id)
        ## Se genera fila en customer_ledger
        self.customer_model.register_bounced_check_in_account(
            client_id, 
            check_amount=check_data[4], 
            debt_amount=new_debt
        )

        client_name = client_data[1]

        check_amount = check_data[4]
        if check_state == 'ENDOSADO':
            supplier_id = self.supplier_model.payment.get_supplier_id_by_check(check_id)
            if supplier_id:
                supplier_data = self.supplier_model.core.find_supplier_by_id(supplier_id)
                supplier_name = supplier_data[1]
            else:
                supplier_name = 'proveedor desconocido'
            self.view.show_warning(
                f"Cheque rechazado correctamente.\n\n"
                f"• Monto del cheque: ${check_amount}\n"
                f"• Se revirtieron los pagos del cliente {client_name}.\n"
                f"• Se revirtieron los pagos al proveedor {supplier_name}.\n"
                f"• Deuda actual del cliente: ${new_debt}"
            )
        else:
            self.view.show_warning(
                f"Cheque rechazado correctamente.\n\n"
                f"• Monto del cheque: ${check_amount}\n"
                f"• Se revirtieron los pagos del cliente {client_name}.\n"
                f"• Deuda actual del cliente: ${new_debt}"
            )

        return True, 'Operación completada.'


    def mark_rechazado(self, check_id, check_state):
        try:
            conn = self.db.get_connection()

            # Iniciar transacción
            conn.execute("BEGIN")

            if check_state == 'EN_CARTERA':
                # Cancelar pagos de cliente asociados a un cheque
                self.payment_model.cancel_check_payments(check_id, conn=conn, commit=False)

                # Cancelar saldo a favor de cliente generado por cheque
                self.customer_credit.cancel_check_credit(check_id, conn=conn, commit=False)

                # Recalcular deuda de cliente luego de rechazo de cheque
                self._recalculate_credits_after_bounce(check_id, conn=conn, commit=False)

            elif check_state == 'ENDOSADO':
                # Cancelar pagos y salgo a favor de un proveedor asociados a un cheque
                self.supplier_model.payment.cancel_check_supplier_payments(check_id, conn=conn, commit=False)

                # Cancelar cheque asociado al cliente
                self.payment_model.cancel_check_payments(check_id, conn=conn, commit=False)
                self.customer_credit.cancel_check_credit(check_id, conn=conn, commit=False)
                self._recalculate_credits_after_bounce(check_id, conn=conn, commit=False)

            else:
                raise ValueError(f"Estado de cheque desconocido: {check_state}")


            # Marcar cheque como cancelado
            self.model.mark_rechazado(check_id, conn=conn, commit=False)
            self.view.show_success("Cheque marcado como RECHAZADO.")
            self.load_checks(self.view.filter_var.get())


            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            show_error(f"Error al marcar un cheque como rechazado: {e}")
            return False
        
        finally:
            conn.close()

    def endorse_check(self, check_id, purchase_id):
        """
        Endosa el cheque a una compra de proveedor:
        1. Registra el pago en supplier_payment
        2. Actualiza purchase.pending y purchase.state
        3. Marca el cheque como ENDOSADO
        Si el cheque supera el pendiente, el excedente queda como saldo a favor del proveedor.
        """
        try:
            # Obtener datos del cheque
            check = self.model.get_check_by_id(check_id)
            if not check:
                self.view.show_error("Cheque no encontrado.")
                return
            # check: id, number, bank, type, amount, issue_date, due_date, status, ...
            check_amount = Decimal(check[4])
            check_number = check[1]
            bank         = check[2]
            check_type   = check[3]

            # Obtener datos de la compra
            purchase = self.db.fetch_one(
                "SELECT id, supplier_id, total, pending, state FROM purchase WHERE id = ?",
                (purchase_id,)
            )
            if not purchase:
                self.view.show_error("Compra no encontrada.")
                return

            p_id, supplier_id, total, pending, state = purchase
            pending_dec = Decimal(str(pending))

            # Calcular cuánto aplica
            aplicado      = min(check_amount, pending_dec)
            excedente     = check_amount - aplicado
            nuevo_pending = pending_dec - aplicado

            if nuevo_pending <= Decimal('0.00'):
                nuevo_state   = "PAGADA"
                nuevo_pending = Decimal('0.00')
            else:
                nuevo_state = "PENDIENTE"

            # Confirmación
            msg = (
                f"Cheque Nro. {check_number} — ${check_amount}\n"
                f"Pendiente de la compra: ${pending_dec}\n\n"
                f"Se aplicará: ${aplicado}\n"
            )
            if excedente > Decimal('0.00'):
                msg += f"⚠️ Excedente de ${excedente} — quedará sin aplicar.\n"
            msg += f"\nNuevo estado de la compra: {nuevo_state}\n\n¿Confirmar?"

            if not messagebox.askyesno("Confirmar endoso", msg):
                return

            conn = self.db.get_connection()
            conn.execute("BEGIN")
            try:
                date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 1. Registrar en supplier_payment
                obs = f"Endoso {check_type} Nro.{check_number} — Banco: {bank}"
                self.db.execute_query(
                    """
                    INSERT INTO supplier_payment
                        (supplier_id, amount, method, bank,
                         check_number, date, observation)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (supplier_id, str(aplicado),
                     check_type, bank, check_number, date_now, obs),
                    conn=conn, commit=False
                )

                # 2. Actualizar purchase.pending y purchase.state
                self.db.execute_query(
                    "UPDATE purchase SET pending = ?, state = ? WHERE id = ?",
                    (str(nuevo_pending), nuevo_state, purchase_id),
                    conn=conn, commit=False
                )

                # 3. Marcar cheque como ENDOSADO
                self.db.execute_query(
                    "UPDATE checks SET status = 'ENDOSADO', purchase_id = ? WHERE id = ?",
                    (purchase_id, check_id),
                    conn=conn, commit=False
                )

                conn.commit()

            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()

            msg_ok = f"Cheque endosado correctamente.\nCompra #{purchase_id} → {nuevo_state}"
            if excedente > Decimal('0.00'):
                msg_ok += f"\n\n⚠️ ${excedente} del cheque quedaron sin aplicar."
            self.view.show_success(msg_ok)
            self.load_checks(self.view.filter_var.get())

        except Exception as e:
            self.view.show_error(f"Error al endosar: {e}")
            import traceback; traceback.print_exc()

    def get_open_purchases(self):
        """Retorna compras de proveedores con saldo pendiente."""
        try:
            rows = self.db.fetch_all("""
                SELECT
                    p.id,
                    s.name,
                    p.date,
                    p.total,
                    p.pending
                FROM purchase p
                JOIN supplier s ON s.id = p.supplier_id
                WHERE p.state IN ('PENDIENTE', 'BORRADOR')
                ORDER BY p.date DESC
            """)
            return rows or []
        except Exception as e:
            print(f"[ChecksController] get_open_purchases: {e}")
            return []
    
    # Reestablece ventas pagas
    def _recalculate_credits_after_bounce(self, check_id, conn=None, commit=True):
        affected_sales = self.model.get_sales_affected_by_check(check_id, conn=conn)

        for sale_id, client_id in affected_sales:
            # actualizar monto venta con precio actual
            self.sales_model.update_sale_amount(sale_id, conn=conn, commit=False)

            # actualiza el estado de venta
            new_status = self.payment_model.update_sale_status(sale_id, conn=conn, commit=False)
            print(f'new_status: {new_status}')

