from db.database import db
from datetime import datetime
from decimal import Decimal
from utils.utils import normalize_to_2_decimals

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
            """, (date, str(total), cliente_id, estado))

            sale_id = cursor.lastrowid

            for item in items:
                if len(item) == 5:
                    product_id, name, quantity, price, observations = item
                else:
                    product_id, name, quantity, price = item
                    observations = None
                
                # OBTENER IVA DEL PRODUCTO
                cursor.execute("SELECT iva FROM stock WHERE id = ?", (product_id,))
                row = cursor.fetchone()
                iva_rate = Decimal(row[0]) if row and row[0] else Decimal*('21.00')
                
                # CALCULAR MONTOS
                subtotal = normalize_to_2_decimals(price * quantity)
                iva_amount = Decimal(subtotal * (iva_rate / Decimal('100')))
                
                # GUARDAR CON IVA
                cursor.execute("""
                    INSERT INTO sale_items (sale_id, product_id, quantity, price, subtotal, iva_rate, iva_amount, observations)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (sale_id, product_id, quantity, str(price), str(subtotal), str(iva_rate), str(iva_amount), observations))

                # Solo descontar stock si NO es honorarios
                cursor.execute("SELECT name FROM stock WHERE id = ?", (product_id,))
                row = cursor.fetchone()
                
                if row and row[0] != 'HONORARIOS PROFESIONALES':
                    cursor.execute("""
                        UPDATE stock SET quantity = quantity - ?
                        WHERE id = ?
                    """, (quantity, product_id))

            conn.commit()
            return sale_id
        
    def get_today_sales(self):
        query = """
            SELECT s.id, s.date, s.total,
                COALESCE(c.nombre, 'Consumidor Final') AS cliente,
                s.estado
            FROM sales s
            LEFT JOIN clientes c ON s.cliente_id = c.id
            WHERE date(s.date) = date('now')
            ORDER BY s.date DESC
        """
        return db.fetch_all(query)
    
    def get_sale_by_id(self, sale_id):
        """Obtener los datos de una venta por su ID"""

        query = """
            SELECT id, date, total, cliente_id, estado
            FROM sales
            WHERE id = ?
        """

        row = db.fetch_one(query, (sale_id,))
        if not row:
            return None

        return {
            "id": row[0],
            "date": row[1],
            "total": row[2],
            "customer_id": row[3],
            "estado": row[4]
        }

    def get_sale_items(self, sale_id):
        query = """
            SELECT 
                si.product_id,
                s.name,
                si.quantity,
                si.price,
                si.subtotal
            FROM sale_items si
            JOIN stock s ON si.product_id = s.id
            WHERE si.sale_id = ?
        """
        
        rows = self.db.fetch_all(query, (sale_id,))
        
        return [
            {
                "product_id": r[0],
                "name": r[1],
                "quantity": r[2],
                "price": r[3],
                "subtotal": r[4]
            }
            for r in rows
        ]




