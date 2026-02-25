from db.database import db 
from decimal import Decimal
from datetime import datetime
from utils.utils import norm_to_2_dec
from models.sale import SalesModel

class PaymentModel:
    def __init__(self):
        self.db = db
        self.sale_model = SalesModel()

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

        # 🔹 CAMBIO: Solo generar crédito si NO viene de aplicación de saldo a favor
        overpay = paid - total
        
        if not skip_credit_generation:
            if overpay > Decimal('0.01'):
                exists = self.db.fetch_one(
                    """
                    SELECT 1
                    FROM customer_credit
                    WHERE sale_id = ?
                    AND client_id = ?
                    AND reason LIKE 'AJUSTE:%'
                    LIMIT 1
                    """,
                    (sale_id, client_id),
                    conn=conn
                )
                print(f"DEBUG CREDIT: overpay={overpay}, sale={sale_id}, skip={skip_credit_generation}")
                print(f"DEBUG CREDIT: exists={exists}")
                if not exists:
                    self.add_customer_credit(
                        client_id=client_id,
                        amount=overpay,
                        reason=f"AJUSTE: Sobrepago en venta #{sale_id}",
                        sale_id=sale_id,
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
                self.update_sale_status(
                    sale_id, skip_credit_generation=True, conn=conn, commit=False
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
                "credit_added": norm_to_2_dec(remaining) if remaining > norm_to_2_dec(0.01) else norm_to_2_dec(0.0),
            }

        except Exception as e:
            conn.rollback()
            print(f'Hubo un error: {e}')
            return False

        finally:
            conn.close()

    def get_customer_credit(self, client_id) -> float:
        row = self.db.fetch_one(
            "SELECT COALESCE(SUM(amount), 0) FROM customer_credit WHERE client_id = ?", 
            (client_id,)
        )

        return norm_to_2_dec(row[0]) if row else norm_to_2_dec(0.0)

    def add_customer_credit(self, client_id: int, amount: Decimal, reason: str, sale_id: int, conn=None, commit=True): 
        query = """
            INSERT INTO customer_credit (client_id, amount, reason, sale_id)
            VALUES (?, ?, ?, ?)
        """
        return self.db.execute_query(query, (client_id, str(amount), reason, sale_id), conn=conn, commit=commit)

    def use_customer_credit(self, client_id: int, amount: float, reason: str, sale_id: int | None = None):
        """
        Consume crédito guardándolo como movimiento NEGATIVO.
        (customer_credit: amount < 0)
        """
        amount = norm_to_2_dec(amount)
        if amount <= norm_to_2_dec(0.01):
            return norm_to_2_dec(0.0)

        available = norm_to_2_dec(self.get_customer_credit(client_id))
        used = norm_to_2_dec(min(available, amount))
        if used <= norm_to_2_dec(0.01):
            return norm_to_2_dec(0.0)

        self.add_customer_credit(
            client_id=client_id,
            amount=-used,
            reason=reason,
            sale_id=sale_id
        )
        return used

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

    def reconcile_customer_sales(self, client_id: int):
        """
        Recalcula todas las ventas abiertas del cliente.
        Útil después de cambios masivos de precios.
        """
        rows = self.db.fetch_all(
            "SELECT id FROM sales WHERE cliente_id = ? AND estado IN ('pending','partial')",
            (client_id,)
        )
        
        reconciled = 0
        for (sale_id,) in rows:
            self.reconcile_sale(int(sale_id))
            reconciled += 1
        
        return reconciled
