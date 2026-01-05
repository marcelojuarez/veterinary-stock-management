from db.database import db 

class PaymentModel:
    def __init__(self):
        self.db = db 

    def create_payment(self, sale_id, client_id, amount, method=None, notes=None):
        """Registra un pago en la tabla payments."""
        query = """
            INSERT INTO payments (sale_id, client_id, amount, method, notes)
            VALUES (?, ?, ?, ?, ?)
        """
        return self.db.execute_query(query, (sale_id, client_id, amount, method, notes))
    
    def get_sale_total_variable(self, sale_id) -> float:
        row = self.db.fetch_one(
            """
            SELECT COALESCE(SUM(si.quantity * st.price_with_iva), 0)
            FROM sale_items si
            JOIN stock st ON st.id = si.product_id
            WHERE si.sale_id = ?
            """,
            (sale_id, )
        )
        return float(row[0]) if row else 0.0
    
    def get_sale_total(self, sale_id) -> float:
        row = self.db.fetch_one(
            "SELECT estado, total_cerrado FROM sales WHERE id = ?",
            (sale_id,)
        )
        if not row:
            return 0.0

        estado, total_cerrado = row
        if estado == 'paid' and total_cerrado is not None:
            return round(float(total_cerrado), 2)

        return round(self.get_sale_total_variable(sale_id), 2)
        
    def get_sale_paid(self, sale_id) -> float:
        row = self.db.fetch_one(
            "SELECT COALESCE(SUM(amount), 0) FROM payments where sale_id = ?", 
            (sale_id, )
            )
        return float(row[0]) if row else 0.0
    
    def get_sale_balance(self, sale_id):
        sale = self.db.fetch_one("SELECT id FROM sales WHERE id = ?", (sale_id,))
        if sale is None: 
            return None
        
        total = self.get_sale_total(sale_id)
        paid = round(self.get_sale_paid(sale_id), 2)
        balance = round(max(0.0, total - paid), 2)

        return {"total" : total, "paid": paid, "balance": balance}
    
    def update_sale_status(self, sale_id, skip_credit_generation=False):
        row_sale = self.db.fetch_one(
            "SELECT cliente_id, estado, total_cerrado FROM sales WHERE id = ?",
            (sale_id,)
        )

        if not row_sale:
            return False
        
        client_id, current_status, total_cerrado = row_sale

        total = round(self.get_sale_total(sale_id), 2)
        paid = round(self.get_sale_paid(sale_id), 2)


        if paid <= 0:
            status = "pending"
        elif paid + 0.009 < total:
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
                    (total, sale_id)
                )

        # 🔹 CAMBIO: Solo generar crédito si NO viene de aplicación de saldo a favor
        overpay = round(paid - total, 2)
        
        if not skip_credit_generation:
            if overpay > 0.01:
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

    def apply_global_payment(self, customer_id, amount):
        """
        Aplica un pago global distribuido entre las deudas pendientes.
        Orden: LIFO (según código original del usuario) -> De la más nueva a la más vieja? 
        Nota: Usualmente es FIFO (ASC), pero respetamos el 'DESC' solicitado.
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
            ORDER BY s.date DESC
        """
        rows = self.db.fetch_all(query, (customer_id,))
        
        remaining = round(float(amount), 2)
        updated_debts = []

        for row in rows:
            if remaining <= 0:
                break

            sale_id, total_variable, paid = row
            balance = float(total_variable) - float(paid)
            # Determinar cuánto pagar de esta venta
            pay_amount = round(min(float(remaining), balance), 2)
            
            if pay_amount > 0.009:
                # Registrar el pago
                self.create_payment(
                    sale_id=sale_id,
                    client_id=customer_id,
                    amount=pay_amount,
                    method="Global",
                    notes="Pago Global Automático"
                )
                
                # Actualizar estado de la venta
                self.update_sale_status(sale_id, skip_credit_generation=True)
                
                remaining = round(float(remaining) - pay_amount, 2)
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
        still_owed = round(sum(
            max(0.0, float(total_variable) - float(paid))
            for _, total_variable, paid in all_sales
        ), 2)


        if remaining > 0.01:
            self.add_customer_credit(
                client_id=customer_id,
                amount=round(remaining, 2),
                reason="SALDO A FAVOR: sobrante de pago global",
                sale_id=None
            )

        return {
            "used": round(float(amount) - float(remaining), 2),
            "remaining": round(float(remaining), 2),
            "updated_debts": updated_debts,
            "still_owed": still_owed,
            "credit_added": round(float(remaining), 2) if remaining > 0.01 else 0.0,
        }

    def get_customer_credit(self, client_id) -> float:
        row = self.db.fetch_one(
            "SELECT COALESCE(SUM(amount), 0) FROM customer_credit WHERE client_id = ?", 
            (client_id,)
        )

        return float(row[0]) if row else 0.0

    def add_customer_credit(self, client_id: int, amount: float, reason: str, sale_id: int | None = None):
        amount = round(float(amount), 2)
        if abs(amount) <= 0.01:
            return None

        query = """
            INSERT INTO customer_credit (client_id, amount, reason, sale_id)
            VALUES (?, ?, ?, ?)
        """
        return self.db.execute_query(query, (client_id, amount, reason, sale_id))

    def use_customer_credit(self, client_id: int, amount: float, reason: str, sale_id: int | None = None):
        """
        Consume crédito guardándolo como movimiento NEGATIVO.
        (customer_credit: amount < 0)
        """
        amount = round(float(amount), 2)
        if amount <= 0.01:
            return 0.0

        available = round(self.get_customer_credit(client_id), 2)
        used = round(min(available, amount), 2)
        if used <= 0.01:
            return 0.0

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

        # 🔹 CAMBIO: Solo respetamos total_cerrado si está PAID y cerrada
        # Si es partial/pending, SIEMPRE recalculamos
        if current_status == "paid" and total_cerrado is not None:
            # Ya está cerrada, no tocar
            return "paid"

        # Recalcular con precios actuales
        total = round(self.get_sale_total_variable(sale_id), 2)
        paid = round(self.get_sale_paid(sale_id), 2)

        # Determinar nuevo estado
        if paid <= 0.01:
            status = "pending"
        elif paid + 0.009 < total:
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
                (total, sale_id)
            )

        overpay = round(paid - total, 2)
        if overpay > 0.01:
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
