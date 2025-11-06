from db.database import db
from datetime import datetime

class SalesModel:
    def __init__(self):
        self.db = db

    def register_sale(self, total, items, cliente_id, estado):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                INSERT INTO sales (date, total, cliente_id, estado)
                VALUES (?, ?, ?, ?)
            """, (date, total, cliente_id, estado))

            sale_id = cursor.lastrowid

            for product_id, quantity, price in items:
                subtotal = round(price * quantity, 2)
                cursor.execute("""
                    INSERT INTO sale_items (sale_id, product_id, quantity, price, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                """, (sale_id, product_id, quantity, price, subtotal))

                # Reducir stock aquí (correcto)
                cursor.execute("""
                    UPDATE stock SET quantity = quantity - ?
                    WHERE id = ?
                """, (quantity, product_id))

            conn.commit()
            return sale_id




    def get_today_sales(self):
        """Obtener todas las ventas del día actual"""
        query = """
            SELECT id, date, total FROM sales
            WHERE DATE(date) = DATE('now')
            ORDER BY date DESC
        """
        return self.db.fetch_all(query)

