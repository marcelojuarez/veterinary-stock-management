from db.database import db 
from datetime import datetime
from utils.utils import normalize_decimal

class PaymentModel:
    def __init__(self):
        self.db = db 

    def create_payment(self, sale_id, client_id, amount, method=None, notes=None):
        """Registra un pago en la tabla payments."""
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        amount = str(normalize_decimal(amount))
        query = """
            INSERT INTO payments (sale_id, client_id, amount, method, notes, date)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.db.execute_query(query, (sale_id, client_id, amount, method, notes, date))
    
    def get_sale_total_variable(self, sale_id):
        row = self.db.fetch_one(
            """
            SELECT COALESCE(SUM(si.quantity * st.price_with_iva), 0)
            FROM sale_items si
            JOIN stock st ON st.id = si.product_id
            WHERE si.sale_id = ?
            """,
            (sale_id, )
        )
        return normalize_decimal(row[0]) if row else normalize_decimal(0.0)
    
    def get_sale_total(self, sale_id):
        row = self.db.fetch_one(
            "SELECT estado, total_cerrado FROM sales WHERE id = ?",
            (sale_id,)
        )
        if not row:
            return normalize_decimal(0.0)

        estado, total_cerrado = row
        if estado == 'paid' and total_cerrado is not None:
            return normalize_decimal(total_cerrado)

        return normalize_decimal(self.get_sale_total_variable(sale_id))
        
    def get_sale_paid(self, sale_id):
        row = self.db.fetch_one(
            "SELECT COALESCE(SUM(amount), 0) FROM payments where sale_id = ?", 
            (sale_id, )
            )
        return normalize_decimal(row[0]) if row else normalize_decimal(0.0)
    
    def get_sale_balance(self, sale_id):
        sale = self.db.fetch_one("SELECT id FROM sales WHERE id = ?", (sale_id,))
        if sale is None: 
            return None
        
        total = normalize_decimal(self.get_sale_total(sale_id))
        paid = normalize_decimal(self.get_sale_paid(sale_id))
        balance = normalize_decimal(max(normalize_decimal(0.0), total - paid))

        return {"total" : total, "paid": paid, "balance": balance}
    
    def update_sale_status(self, sale_id, skip_credit_generation=False):
        row_sale = self.db.fetch_one(
            "SELECT cliente_id, estado, total_cerrado FROM sales WHERE id = ?",
            (sale_id,)
        )

        if not row_sale:
            return False
        
        client_id, current_status, total_cerrado = row_sale

        total = normalize_decimal(self.get_sale_total(sale_id))
        paid = normalize_decimal(self.get_sale_paid(sale_id))


        if paid <= 0:
            status = "pending"
        elif paid + normalize_decimal(0.009) < total:
            status = "partial"
        else:
            status = "paid"

        self.db.execute_query(
            "UPDATE sales SET estado = ? WHERE id = ?",
            (status, sale_id)
        )

        if status == "paid":
            if total_cerrado is None:
                self.db.execute_query(
                    """
                    UPDATE sales
                    SET total_cerrado = ?,
                        fecha_cierre = CURRENT_TIMESTAMP
                    WHERE id = ? AND total_cerrado IS NULL
                    """,
                    (str(total), sale_id)
                )

        # 🔹 CAMBIO: Solo generar crédito si NO viene de aplicación de saldo a favor
        overpay = normalize_decimal(paid - total)
        
        if not skip_credit_generation:
            if overpay > normalize_decimal(0.01):
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
                        reason=f"AJUSTE: Sobrepago en venta #{sale_id}",
                        sale_id=sale_id
                    )

        return status
    
    def get_payments_for_sale(self, sale_id):
        """Devuelve todos los pagos registrados para esta venta."""
        rows = self.db.fetch_all(
            "SELECT id, date, amount, method FROM payments WHERE sale_id = ? ORDER BY date ASC",
            (sale_id,)
        )
        return rows

    def apply_global_payment(self, customer_id, amount, method="Efectivo"):
        """
        Aplica un pago global distribuido entre las deudas pendientes. 
        Nota: Usualmente es FIFO (ASC)
        """
        # 1. Obtener deudas con saldo pendiente
        query = """
            SELECT s.id,
                COALESCE(SUM(si.quantity * st.price_with_iva), 0) AS total_variable,
                COALESCE((SELECT SUM(p.amount) FROM payments p WHERE p.sale_id = s.id), 0) AS paid
            FROM sales s
            JOIN sale_items si ON si.sale_id = s.id
            JOIN stock st ON st.id = si.product_id
            WHERE s.cliente_id = ? AND s.estado IN ('pending', 'partial')
            GROUP BY s.id
            HAVING (total_variable - paid) > 0.01
            ORDER BY s.date ASC
        """
        rows = self.db.fetch_all(query, (customer_id,))
        
        remaining = normalize_decimal(amount)
        updated_debts = []

        for row in rows:
            if remaining <= 0:
                break

            sale_id, total_variable, paid = row
            balance = normalize_decimal(total_variable) - normalize_decimal(paid)
            # Determinar cuánto pagar de esta venta
            pay_amount = normalize_decimal(min(remaining, balance))
            
            if pay_amount > normalize_decimal(0.009):
                # Registrar el pago
                self.create_payment(
                    sale_id=sale_id,
                    client_id=customer_id,
                    amount=pay_amount,
                    method=method,
                    notes="Pago Global Automático"
                )
                
                # Actualizar estado de la venta
                self.update_sale_status(sale_id, skip_credit_generation=True)
                
                remaining = normalize_decimal(remaining - pay_amount)
                updated_debts.append((sale_id, pay_amount))

        # Calcular cuánto queda adeudado en total después del pago global
        total_debt_query = """
            SELECT
                s.id,
                COALESCE(SUM(si.quantity * st.price_with_iva), 0) AS total_variable,
                COALESCE((SELECT SUM(p.amount) FROM payments p WHERE p.sale_id = s.id), 0) AS paid
            FROM sales s
            JOIN sale_items si ON si.sale_id = s.id
            JOIN stock st ON st.id = si.product_id
            WHERE s.cliente_id = ? AND s.estado IN ('pending', 'partial')
            GROUP BY s.id
        """
        all_sales = self.db.fetch_all(total_debt_query, (customer_id,))
        still_owed = normalize_decimal(sum(
            max(normalize_decimal(0.0), normalize_decimal(total_variable) - normalize_decimal(paid))
            for _, total_variable, paid in all_sales
        ))


        if remaining > normalize_decimal(0.01):
            self.add_customer_credit(
                client_id=customer_id,
                amount=normalize_decimal(remaining),
                reason="SALDO A FAVOR: sobrante de pago global",
                sale_id=None
            )

        return {
            "used": normalize_decimal(normalize_decimal(amount) - remaining),
            "remaining": normalize_decimal(remaining),
            "updated_debts": updated_debts,
            "still_owed": still_owed,
            "credit_added": normalize_decimal(remaining) if remaining > normalize_decimal(0.01) else normalize_decimal(0.0),
        }

    def get_customer_credit(self, client_id) -> float:
        row = self.db.fetch_one(
            "SELECT COALESCE(SUM(amount), 0) FROM customer_credit WHERE client_id = ?", 
            (client_id,)
        )

        return normalize_decimal(row[0]) if row else normalize_decimal(0.0)

    def add_customer_credit(self, client_id: int, amount: float, reason: str, sale_id: int | None = None):
        amount = normalize_decimal(amount)
        if abs(amount) <= normalize_decimal(0.01):
            return None

        query = """
            INSERT INTO customer_credit (client_id, amount, reason, sale_id)
            VALUES (?, ?, ?, ?)
        """
        return self.db.execute_query(query, (client_id, str(amount), reason, sale_id))

    def use_customer_credit(self, client_id: int, amount: float, reason: str, sale_id: int | None = None):
        """
        Consume crédito guardándolo como movimiento NEGATIVO.
        (customer_credit: amount < 0)
        """
        amount = normalize_decimal(amount)
        if amount <= normalize_decimal(0.01):
            return normalize_decimal(0.0)

        available = normalize_decimal(self.get_customer_credit(client_id))
        used = normalize_decimal(min(available, amount))
        if used <= normalize_decimal(0.01):
            return normalize_decimal(0.0)

        self.add_customer_credit(
            client_id=client_id,
            amount=-used,
            reason=reason,
            sale_id=sale_id
        )
        return used


    def get_sale_client_id(self, sale_id: int) -> int | None:
        row = self.db.fetch_one("SELECT cliente_id FROM sales WHERE id = ?", (sale_id,))
        return int(row[0]) if row else None

    def reconcile_sale(self, sale_id: int) -> str | None:
        """
        Recalcula una venta con los precios actuales.
        - Si con lo pagado ya alcanza: la pasa a paid (y congela total_cerrado)
        - Si hay sobrepago: crea saldo a favor (customer_credit)
        """
        row_sale = self.db.fetch_one(
            "SELECT cliente_id, estado, total_cerrado FROM sales WHERE id = ?",
            (sale_id,)
        )
        if not row_sale:
            return None

        client_id, current_status, total_cerrado = row_sale

        if current_status == "paid" and total_cerrado is not None:
            # Ya está cerrada, no tocar
            return "paid"

        # Recalcular con precios actuales
        total = normalize_decimal(self.get_sale_total_variable(sale_id))
        paid = normalize_decimal(self.get_sale_paid(sale_id))

        # Determinar nuevo estado
        if paid <= normalize_decimal(0.01):
            status = "pending"
        elif paid + normalize_decimal(0.009) < total:
            status = "partial"
        else:
            status = "paid"

        # Guardar nuevo estado
        self.db.execute_query(
            "UPDATE sales SET estado = ? WHERE id = ?",
            (status, sale_id)
        )

        # Si quedó paid: congelar total
        if status == "paid" and total_cerrado is None:
            self.db.execute_query(
                """
                UPDATE sales
                SET total_cerrado = ?,
                    fecha_cierre = CURRENT_TIMESTAMP
                WHERE id = ? AND total_cerrado IS NULL
                """,
                (str(total), sale_id)
            )

        overpay = normalize_decimal(paid - total)
        if overpay > normalize_decimal(0.01):
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
