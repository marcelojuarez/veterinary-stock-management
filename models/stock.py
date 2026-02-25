from db.database import db
from models.sale import SalesModel

class StockModel: 
    def __init__(self, db_conection=None):
        self.db = db_conection or db
        self.sale_model = SalesModel()
    
    def get_all_products(self):
        """Obtener todos los productos del stock"""
        query = """
            SELECT id, name, pack, list_price, discount, cost_price, profit, price, iva, 
                   price_with_iva, created_at, last_price_update, quantity
            FROM stock 
            WHERE name != "HONORARIOS"
            ORDER BY name
        """
        return db.fetch_all(query)
    
    def get_product_by_name(self, product_name):
        """Obtener un producto por su ID"""
        query = "SELECT id, pack FROM stock WHERE LOWER(name) = LOWER(?)"
        return db.fetch_one(query, (product_name,))
    
    def get_product_by_id(self, product_id):
        """Obtener un producto por su ID"""
        query = """
            SELECT id, name, pack, profit, list_price, discount, cost_price, 
            price, iva, price_with_iva, created_at, last_price_update, quantity
            FROM stock 
            WHERE id = ?
        """
        return db.fetch_one(query, (product_id,))
        
    def update_product_price(self, product_id, product_data, conn=None, commit=True):
        """Actualizar un producto existente"""
        query = """
            UPDATE stock 
            SET profit = ?, cost_price = ?, price = ?, 
                price_with_iva = ?, last_price_update = CURRENT_DATE
            WHERE id = ?
        """
        params = (
            product_data['Profit'],
            product_data['CostPrice'],
            product_data['SalePrice'],
            product_data['PriceWIva'],
            product_id
        )
        self.db.execute_query(query, params, conn=conn, commit=commit)
    
    ## -- Transaccion para actualizar precio de productos -- ##
    # Y montos de ventas relacionadas#
    def update_p_price_and_related_sales_amount(self, product_id, product_data):
        try:
            conn = self.db.get_connection()

            conn.execute("BEGIN")
            
            # Se actualiza el precio del producto
            self.update_product_price(product_id, product_data, conn=conn, commit=False)

            # Se obtienen las ventas pendientes o parciales, en donde el producto actualizado, participa
            query = """
                SELECT DISTINCT s.id, s.cliente_id, c.nombre
                FROM sales s
                JOIN sale_items si ON si.sale_id = s.id
                LEFT JOIN clientes c ON c.id = s.cliente_id
                WHERE si.product_id = ? AND s.estado IN ('pending', 'partial')
            """
            # Ventas afectadas por la actualizacion de precio
            affected_sales = db.fetch_all(query, (product_id,), conn=conn)            

            if not affected_sales:
                conn.commit()
                return True

            for sale_id, _, _ in affected_sales:
                # Por cada venta afecta se obtiene su estado actual
                status = db.fetch_one("SELECT estado FROM sales WHERE id = ?", (sale_id,), conn=conn)[0]

                if status != 'paid':

                    self.sale_model.update_sale_item(sale_id, product_id, product_data['SalePrice'], conn=conn, commit=False)
                    self.sale_model.recalculate_sale_total(sale_id, conn=conn, commit=False)
                    ## -- Falta el saldo a favor y demas -- ##
                    #new_status = self.payment_model.reconcile_sale(sale_id)


            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            print(f'Hubo un error {e}')
            return False
        
        finally:
            conn.close() 

    
    def update_field(self, db_field, new_value, product_id):
        query = f"UPDATE stock SET {db_field} = ?, id = ?"
        db.execute_query(query, (new_value, product_id))
        
    def delete_product(self, product_id):
        """Eliminar un producto"""
        query = "DELETE FROM stock WHERE id = ?"
        return db.execute_query(query, (product_id,))

    def update_quantity(self, product_id, quantity, conn=None, commit=True):
        """Actualizar solo la cantidad de un producto"""
        query = "UPDATE stock SET quantity = quantity + ? WHERE id = ?"
        return db.execute_query(query, (quantity, product_id), conn=conn, commit=commit)
        
    def reduce_quantity(self, product_id, quantity_to_reduce):
        """Reducir la cantidad de un producto (para ventas)"""
        current_product = self.get_product_by_id(product_id)
        if not current_product:
            raise ValueError(f"Producto {product_id} no encontrado")
        current_quantity = current_product[-1]  # quantity está en la última posición
        print("Current cantidad: ", current_quantity)
        
        if current_quantity < quantity_to_reduce:
            raise ValueError(
                f"Stock insuficiente. Disponible: {current_quantity}, Solicitado: {quantity_to_reduce}"
            )
        
        new_quantity = current_quantity - quantity_to_reduce
        return self.update_quantity(product_id, new_quantity)
    
    def search_products(self, search_term):
        """Buscar productos por nombre, ID o envase"""
        query = """
            SELECT id, name, pack, profit, cost_price, price, iva, 
                   price_with_iva, created_at, last_price_update, quantity
            FROM stock 
            WHERE name LIKE ? OR id LIKE ? OR pack LIKE ?
            ORDER BY name
        """
        search_pattern = f"%{search_term}%"
        return db.fetch_all(query, (search_pattern, search_pattern, search_pattern))
    
    def get_low_stock_products(self, threshold):
        """Obtener productos con stock bajo (cantidad menor que el umbral)"""
        try: 
            with self.db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, pack, quantity FROM stock WHERE quantity < ? ORDER BY quantity", 
                    (threshold,)
                )
                return cursor.fetchall()
        except Exception as e:
            print(f"Error getting low stock products: {e}")
            return []
    
    def get_available_price_dates(self):
        """Obtener fechas disponibles de última modificación de precios"""
        query = "SELECT DISTINCT last_price_update FROM stock WHERE last_price_update IS NOT NULL ORDER BY last_price_update DESC"
        results = db.fetch_all(query)
        return [str(row[0]) for row in results] if results else []

    def count_products_by_date(self, date):
        """Contar productos por fecha de última modificación"""
        query = "SELECT COUNT(*) FROM stock WHERE last_price_update = ?"
        result = db.fetch_one(query, (date,))
        return result[0] if result else 0

    def bulk_update_prices_by_date(self, date, percent_increase):
        """Actualización masiva de precios por fecha"""
        multiplier = 1 + (percent_increase / 100)
        
        query = """
            UPDATE stock 
            SET price = ROUND(price * ?, 2),
                price_with_iva = CASE 
                    WHEN iva = 21.0 THEN ROUND(price * ? * 1.21, 2)
                    WHEN iva = 10.5 THEN ROUND(price * ? * 1.105, 2)
                    ELSE ROUND(price * ?, 2)
                END,
                profit = ROUND(((price * ? - cost_price) / cost_price) * 100, 2),
                last_price_update = CURRENT_DATE
            WHERE last_price_update = ?
        """
        
        params = (multiplier, multiplier, multiplier, multiplier, multiplier, date)
        
        return db.execute_query(query, params)
    
    def get_honorarios_id(self):
        """Obtener el ID del producto honorarios"""
        query = "SELECT id FROM stock WHERE name = 'HONORARIOS PROFESIONALES'"
        row = db.fetch_one(query)
        return row[0] if row else None
