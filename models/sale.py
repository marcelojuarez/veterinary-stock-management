from db.database import db
from datetime import datetime
from decimal import Decimal
from utils.utils import norm_to_2_dec

class SalesModel:
    def __init__(self):
        self.db = db

    def register_sale(self, total, items, cliente_id, estado, retenciones=None):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                INSERT INTO sales (date, total, cliente_id, estado)
                VALUES (?, ?, ?, ?)
            """, (date, str(total), cliente_id, estado))

            sale_id = cursor.lastrowid
    
            # Guardar retenciones SI EXISTEN
            if retenciones:
                for tipo, monto in retenciones.items():
                    if tipo != 'certificado' and monto > 0:
                        cursor.execute("""
                            INSERT INTO sale_retentions (sale_id, tax_type, amount, certificate_number)
                            VALUES (?, ?, ?, ?)
                        """, (sale_id, tipo, str(monto), retenciones.get('certificado', '')))

            for item in items:
                if len(item) == 5:
                    product_id, name, quantity, price_with_iva, observations = item
                else:
                    product_id, name, quantity, price_with_iva = item
                    observations = None
                
                # OBTENER IVA DEL PRODUCTO
                cursor.execute("SELECT iva FROM stock WHERE id = ?", (product_id,))
                row = cursor.fetchone()
                iva_rate = Decimal(row[0]) if row and row[0] else Decimal('21.00')
                
                # DESCOMPONER EL PRECIO (price_with_iva → price sin IVA)
                price_with_iva_decimal = Decimal(str(price_with_iva))
                divisor = Decimal('1') + (iva_rate / Decimal('100'))
                price_without_iva = norm_to_2_dec(price_with_iva_decimal / divisor)
                
                # CALCULAR MONTOS
                subtotal = norm_to_2_dec(price_without_iva * quantity)  # Sin IVA
                iva_amount = norm_to_2_dec(subtotal * (iva_rate / Decimal('100')))  # IVA
                
                # GUARDAR
                cursor.execute("""
                    INSERT INTO sale_items (sale_id, product_id, quantity, price, subtotal, iva_rate, iva_amount, observations)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (sale_id, product_id, quantity, str(price_without_iva), str(subtotal), str(iva_rate), str(iva_amount), observations))

                # Solo descontar stock si NO es honorarios
                cursor.execute("SELECT name FROM stock WHERE id = ?", (product_id,))
                row = cursor.fetchone()
                
                if row and row[0] != 'HONORARIOS':
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
            WHERE date(s.date) = date('now','localtime')
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




