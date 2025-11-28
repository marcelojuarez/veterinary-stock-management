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
