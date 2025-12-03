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
    
    def get_sale_balance(self, sale_id):
        """Devuelve total, pagado y saldo de una venta."""
        sale = self.db.fetch_one(
            "SELECT total FROM sales WHERE id = ?", (sale_id,)
        )
        if sale is None:
            return None
        
        sale_total = float(sale[0])

        pagos = self.db.fetch_one(
            "SELECT IFNULL(SUM(amount), 0) FROM payments WHERE sale_id = ?",
            (sale_id,)
        )
        total_paid = float(pagos[0]) if pagos else 0.0

        balance = sale_total - total_paid
        
        return {
            "total": sale_total,
            "paid": total_paid,
            "balance": balance
        }
    
    def update_sale_status(self, sale_id):
        """Actualiza el estado de la venta según sus pagos."""
        info = self.get_sale_balance(sale_id)
        if info is None:
            return False

        total = info["total"]
        paid = info["paid"]

        if paid == 0:
            status = "pending"
        elif paid < total:
            status = "partial"
        else:
            status = "paid"

        # IMPORTANTE: columna correcta = estado
        self.db.execute_query(
            "UPDATE sales SET estado = ? WHERE id = ?",
            (status, sale_id)
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
            SELECT s.id, s.total, IFNULL(SUM(p.amount), 0) as paid
            FROM sales s
            LEFT JOIN payments p ON s.id = p.sale_id
            WHERE s.cliente_id = ?
            GROUP BY s.id
            HAVING (s.total - paid) > 0.01
            ORDER BY s.date DESC
        """
        rows = self.db.fetch_all(query, (customer_id,))
        
        remaining = amount
        updated_debts = []

        for row in rows:
            if remaining <= 0:
                break

            sale_id, total, paid = row
            balance = total - paid
            
            # Determinar cuánto pagar de esta venta
            pay_amount = min(remaining, balance)
            
            if pay_amount > 0:
                # Registrar el pago
                self.create_payment(
                    sale_id=sale_id,
                    client_id=customer_id,
                    amount=pay_amount,
                    method="Global",
                    notes="Pago Global Automático"
                )
                
                # Actualizar estado de la venta
                self.update_sale_status(sale_id)
                
                remaining -= pay_amount
                updated_debts.append((sale_id, pay_amount))

        # Calcular deuda total restante
        # Reutilizamos la query de CustomerModel logic o una simple suma
        total_debt_query = """
            SELECT s.total, IFNULL(SUM(p.amount), 0)
            FROM sales s
            LEFT JOIN payments p ON s.id = p.sale_id
            WHERE s.cliente_id = ?
            GROUP BY s.id
        """
        all_sales = self.db.fetch_all(total_debt_query, (customer_id,))
        still_owed = sum(s[0] - s[1] for s in all_sales if (s[0] - s[1]) > 0.01)

        return {
            "used": amount - remaining,
            "remaining": remaining,
            "updated_debts": updated_debts,
            "still_owed": still_owed
        }

