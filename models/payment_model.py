from db.database import db 
from decimal import Decimal
from datetime import datetime
from utils.utils import norm_to_2_dec

class PaymentModel:
    def __init__(self, sales_model, customer_credit, checks_model, customer_model=None):
        self.db = db
        self.sale_model = sales_model
        self.customer_credit = customer_credit
        self.checks_model = checks_model
        self.customer_model = customer_model

    def create_payment(self, sale_id, client_id, amount, method=None, notes=None,
                       check_id=None, conn=None, commit=True):
        """Registra un pago en la tabla payments."""
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
            INSERT INTO payments (sale_id, client_id, amount, method, notes, date, check_id, valid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.db.execute_query(
            query,
            (sale_id, client_id, str(amount), method, notes, date, check_id, 1),
            conn=conn,
            commit=commit
        )
    
    #def get

    ## -- Obtiene el monto total de una venta -- ##
    def get_sale_total(self, sale_id, conn=None):

        query = """
        SELECT total FROM sales WHERE id = ?
        """

        return self.db.fetch_one(query, (sale_id, ), conn=conn)
    
    ##
    def update_sale_status(self, sale_id, conn=None, commit=True):
        row_sale = self.db.fetch_one(
            "SELECT cliente_id, estado, total FROM sales WHERE id = ?",
            (sale_id,), conn=conn
        )
        if not row_sale:
            return False

        _, _, total = row_sale
        total = Decimal(total)
        paid = self.get_total_amount_of_pay_for_a_sale(sale_id, conn=conn)

        if paid <= Decimal('0.00'):
            status = "pending"
        elif paid < total:
            status = "partial"
        else:
            status = "paid"

        self.db.execute_query(
            "UPDATE sales SET estado = ? WHERE id = ?",
            (status, sale_id), conn=conn, commit=commit
        )
        return status

    def generate_overpay_credit(self, sale_id, client_id, total, payments, conn=None, commit=True):
        self.db.execute_query(
            "UPDATE customer_credit SET valid = 0 WHERE sale_id = ? AND valid = 1",
            (sale_id,), conn=conn, commit=False
        )
        remaining_total = Decimal(total)

        for _, amount, check_id in payments:
            amount = Decimal(amount)

            if remaining_total <= Decimal('0.00'):
                overpay = amount 

            elif amount <= remaining_total:
                # cubre deuda, no hay overpay
                remaining_total -= amount
                continue
            else:
                # parte cubre deuda, parte es overpay
                overpay = norm_to_2_dec(amount - remaining_total)
                remaining_total = Decimal('0.00')

            if overpay > Decimal('0.00'):
                self.customer_credit.add_customer_credit(
                    {
                        'client_id': client_id,
                        'amount': overpay,
                        'reason': f"AJUSTE: Sobrepago en venta #{sale_id}",
                        'sale_id': sale_id
                    },
                    check_id=check_id,
                    conn=conn,
                    commit=commit
                )
                self.customer_model.register_credit_balance_in_account(
                    client_id=client_id,
                    reference_id=sale_id,
                    description=f"Saldo a favor · Ajuste Vta #{sale_id} · ${overpay}",
                    conn=conn,
                    commit=commit
                )

    ## -- Devuelve el monto total de pagos asociados a una venta -- ##
    def get_total_amount_of_pay_for_a_sale(self, sale_id, conn=None):
        query = """
        SELECT amount FROM payments WHERE sale_id = ? and valid = ?
        """

        rows = self.db.fetch_all(query, (sale_id, 1), conn=conn)

        amount = Decimal('0.00')

        for row in rows:
            amount += Decimal(row[0])

        return norm_to_2_dec(amount)
    
    ## -- Devuelve el monto total de pagos asociados a un cliente -- ##
    def get_total_paid_by_client(self, client_id, conn=None):
        check_amount = self.checks_model.get_cartera_total_from_client(client_id)

        query = """
            SELECT amount 
            FROM payments 
            WHERE client_id = ? 
            AND valid = ?
            AND check_id IS NULL
            AND method != 'Saldo a Favor'
        """

        rows = self.db.fetch_all(query, (client_id, 1), conn=conn)

        amount = Decimal(check_amount)

        for amount_row, in rows:
            amount += Decimal(amount_row)

        return norm_to_2_dec(amount)


    def get_payments_for_sale(self, sale_id, conn=None):
        query = """
            SELECT id, amount, check_id
            FROM payments
            WHERE sale_id = ? AND valid = 1
            ORDER BY id ASC
        """
        return self.db.fetch_all(query, (sale_id,), conn=conn)

    def apply_global_payment(self, customer_id, amount, method="Efectivo", check_id=None, check_data=None):
        """
        Aplica un pago global distribuido entre las deudas pendientes. 
        Nota: Usualmente es FIFO (ASC)
        """
        try:
            conn = self.db.get_connection()

            conn.execute("BEGIN")

            # 1. Obtener deudas con saldo pendiente
            query = """
                SELECT 
                    s.id,
                    s.total
                FROM sales s
                WHERE s.cliente_id = ? AND s.estado IN ('pending', 'partial')
                GROUP BY s.id
                ORDER BY s.date ASC
            """
            rows = self.db.fetch_all(query, (customer_id,), conn=conn)
            
            remaining = amount
            updated_debts = []

            for row in rows:
                if remaining <= Decimal('0.00'):
                    break

                sale_id, total = row
                paid = self.get_total_amount_of_pay_for_a_sale(sale_id, conn=conn)
                balance = Decimal(total) - paid
                # Determinar cuánto pagar de esta venta
                pay_amount = min(remaining, balance)

                # Registrar el pago
                self.create_payment(
                    sale_id=sale_id,
                    client_id=customer_id,
                    amount=pay_amount,
                    method=method,
                    notes="Pago Global Automático",
                    check_id=check_id,
                    conn=conn,
                    commit=False
                )

                # Actualizar estado de la venta
                sale_status = self.update_sale_status(
                    sale_id, conn=conn, commit=False
                )
                
                # Se registra el movimiento en la cuenta del cliente
                self.customer_model.register_payment_in_account(
                    sale_id,
                    customer_id,
                    pay_amount,
                    method,
                    "PAGO",
                    sale_status,
                    conn=conn,
                    commit=False
                )

                remaining = remaining - pay_amount
                updated_debts.append((sale_id, pay_amount))

            print(f'remaining: {remaining}')
            surplus = Decimal('0.00')

            # Verifica si se genera saldo a favor al pagar con cheque
            if remaining > Decimal('0.00') and check_id is not None:
                self.customer_credit.add_customer_credit(
                    {
                        'client_id': customer_id,
                        'amount': remaining,
                        'reason': f"Excedente cheque {check_data['number']} · {check_data['bank']}",
                        'sale_id': None
                    },
                    check_id=check_id,
                    conn=conn,
                    commit=False
                )
                self.customer_model.register_credit_balance_in_account(
                    client_id=customer_id,
                    reference_id=check_id,
                    description=f"Saldo a favor · Cheque cargado. ${remaining}",
                    conn=conn,
                    commit=False
                )

                surplus = remaining

            # Obtener el total de todas las ventas
            all_sales = self.sale_model.get_total_of_all_sales(customer_id, conn=conn)
            still_owed = Decimal('0.00')

            for sale_id, total in all_sales:
                payment_amount = self.get_total_amount_of_pay_for_a_sale(sale_id, conn=conn)
                still_owed += Decimal(total) - payment_amount

            conn.commit()

            return {
                "used": norm_to_2_dec(amount - remaining),
                "remaining": norm_to_2_dec(remaining),
                "updated_debts": updated_debts,
                "still_owed": still_owed,
                "surplus": surplus,
                "credit_added": norm_to_2_dec(remaining) if remaining > Decimal("0.00") else Decimal("0.00"),
            }

        except Exception as e:
            conn.rollback()
            print(f'Hubo un error: {e}')
            return False

        finally:
            conn.close()

    ## -- Cancela pagos asociados a un cheque o echeq -- ##
    def cancel_check_payments(self, check_id, conn=None, commit=True):
        try:
            query = """
            UPDATE payments
            SET 
                valid = ?
            WHERE check_id = ?
            """

            self.db.execute_query(query, (0, check_id), conn=conn, commit=commit)
        
        except Exception as e:
            raise RuntimeError(f'Error al cancelar pagos asociados a un cheque: {e}') from e
