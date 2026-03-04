from db.database import db 
from decimal import Decimal
from datetime import datetime
from utils.utils import norm_to_2_dec

class PaymentModel:
    def __init__(self, sales_model, customer_model=None):
        self.db = db
        self.sale_model = sales_model
        self.customer_model = customer_model

    def create_payment(self, sale_id, client_id, amount, method=None, notes=None, conn=None, commit=True):
        """Registra un pago en la tabla payments."""
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
            INSERT INTO payments (sale_id, client_id, amount, method, notes, date)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.db.execute_query(
            query, 
            (sale_id, client_id, str(amount), method, notes, date),
            conn=conn,
            commit=commit
        )
    
    ## -- Obtiene el monto total de una venta -- ##
    def get_sale_total(self, sale_id, conn=None):

        query = """
        SELECT total FROM sales WHERE id = ?
        """

        return self.db.fetch_one(query, (sale_id, ), conn=conn)
    
    def update_sale_status(self, sale_id, skip_credit_generation=False, conn=None, commit=True):
        row_sale = self.db.fetch_one(
            "SELECT cliente_id, estado, total FROM sales WHERE id = ?",
            (sale_id,),
            conn=conn
        )

        if not row_sale:
            return False
        
        client_id, _, total = row_sale

        total = Decimal(total)
        paid = self.get_total_amount_of_pay_for_a_sale(sale_id, conn=conn)

        if paid <= Decimal('0.00'):
            status = "pending"
        elif Decimal('0.00') < paid < total:
            status = "partial"
        else:
            status = "paid"

        self.db.execute_query(
            "UPDATE sales SET estado = ? WHERE id = ?",
            (status, sale_id),
            conn=conn,
            commit=commit
        )

        # Solo generar crédito si NO viene de aplicación de saldo a favor
        if not skip_credit_generation:
            overpay = Decimal(paid - total)
            if overpay > Decimal('0.00'):
                print(f"DEBUG CREDIT: overpay={overpay}, sale={sale_id}, skip={skip_credit_generation}")
                ## Generacion de saldo a favor debito a una venta
                self.add_customer_credit(
                    client_id=client_id,
                    amount=overpay,
                    reason=f"AJUSTE: Sobrepago en venta #{sale_id}",
                    sale_id=sale_id,
                    conn=conn,
                    commit=commit
                )

                ## Registrar fila informativa en ledger
                self.customer_model.register_credit_balance_in_account(
                    client_id=client_id,
                    sale_id=sale_id,
                    amount=overpay,
                    conn=conn,
                    commit=commit
                )

        return status

    ## -- Devuelve el monto total de pagos asociados a una venta -- ##
    def get_total_amount_of_pay_for_a_sale(self, sale_id, conn=None):
        query = """
        SELECT amount FROM payments WHERE sale_id = ?
        """

        rows = self.db.fetch_all(query, (sale_id, ), conn=conn)

        amount = Decimal('0.00')

        for row in rows:
            amount += Decimal(row[0])

        return norm_to_2_dec(amount)
    

    ## -- Devuelve el monto total de pagos asociados a una venta -- ##
    def get_total_amount_of_pay_for_a_sale(self, sale_id, conn=None):
        query = """
        SELECT amount FROM payments WHERE sale_id = ?
        """

        rows = self.db.fetch_all(query, (sale_id, ), conn=conn)

        amount = Decimal('0.00')

        for row in rows:
            amount += Decimal(row[0])

        return norm_to_2_dec(amount)

    def apply_global_payment(self, customer_id, amount, method="Efectivo"):
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
                    conn=conn,
                    commit=False
                )

                # Actualizar estado de la venta
                sale_status = self.update_sale_status(
                    sale_id, skip_credit_generation=True, conn=conn, commit=False
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
                "credit_added": norm_to_2_dec(remaining) if remaining > Decimal("0.00") else Decimal("0.00"),
            }

        except Exception as e:
            conn.rollback()
            print(f'Hubo un error: {e}')
            return False

        finally:
            conn.close()

    def get_customer_credit(self, client_id) -> Decimal:
        rows = self.db.fetch_all(
            "SELECT amount FROM customer_credit WHERE client_id = ?", 
            (client_id,)
        )

        total = Decimal('0.00')
        for row in rows:
            total += Decimal(row[0])

        return norm_to_2_dec(total)

    def add_customer_credit(self, client_id: int, amount: Decimal, reason: str, sale_id: int, conn=None, commit=True): 
        query = """
            INSERT INTO customer_credit (client_id, amount, reason, sale_id)
            VALUES (?, ?, ?, ?)
        """
        return self.db.execute_query(query, (client_id, str(amount), reason, sale_id), conn=conn, commit=commit)

    def reconcile_sale(self, sale_id, conn=None, commit=True):
        """
        Recalcula una venta con los precios actuales.
        - Si con lo pagado ya alcanza: la pasa a paid (y congela total_cerrado)
        - Si hay sobrepago: crea saldo a favor (customer_credit)
        """
        row_sale = self.db.fetch_one(
            "SELECT cliente_id, estado, total FROM sales WHERE id = ?",
            (sale_id,),
            conn=conn
        )

        if not row_sale:
            return None

        client_id, current_status, total = row_sale

        # Recalcular con precios actuales
        total = Decimal(self.get_sale_total(sale_id, conn=conn))
        paid = self.get_total_amount_of_pay_for_a_sale(sale_id, conn=conn)

        # Determinar nuevo estado
        if paid <= Decimal('0.00'):
            status = "pending"
        elif Decimal('0.00') < paid < total:
            status = "partial"
        else:
            status = "paid"

        # Guardar nuevo estado
        self.db.execute_query(
            "UPDATE sales SET estado = ? WHERE id = ?",
            (status, sale_id),
            conn=conn,
            commit=commit
        )

        overpay = Decimal(paid - total)
        if overpay > Decimal('0.00'):
            # Verificar si ya existe un ajuste de sobrepago para esta venta
            exists = self.db.fetch_one(
                """
                SELECT 1
                FROM customer_credit
                WHERE sale_id = ?
                AND client_id = ?
                AND reason LIKE 'AJUSTE:%'
                LIMIT 1
                """,
                (sale_id, client_id)
            )
            
            if not exists:
                self.add_customer_credit(
                    client_id=client_id,
                    amount=overpay,
                    reason=f"AJUSTE: Diferencia por cambio de precio (venta #{sale_id})",
                    sale_id=sale_id
                )

            else:
                # Se actualiza uno ?
                pass

        return status

