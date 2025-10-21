from db.database import db

class StockModel: 
    def __init__(self, db_conection=None):
        self.db = db_conection or db
    
    def get_all_products(self):
        """Obtener todos los productos del stock"""
        query = """
            SELECT id, name, pack, profit, cost_price, price, iva, 
                   price_with_iva, created_at, last_price_update, quantity
            FROM stock 
            ORDER BY name
        """
        return db.fetch_all(query)
    
    def get_product_by_id(self, product_id):
        """Obtener un producto por su ID"""
        query = """
            SELECT id, name, pack, profit, cost_price, price, iva, 
                   price_with_iva, created_at, last_price_update, quantity
            FROM stock 
            WHERE id = ?
        """
        return db.fetch_one(query, (product_id,))
        
    def add_product(self, product_data):
        """Agregar un nuevo producto"""
        query = """
            INSERT INTO stock 
            (id, name, pack, profit, cost_price, price, iva, price_with_iva, quantity) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            product_data['Id'],
            product_data['Name'],
            product_data['Package'],
            product_data['Profit'],
            product_data['CostPrice'],
            product_data['SalePrice'],
            product_data['Iva'],
            product_data['PriceWIva'],
            product_data['Stock'],
        )
        return db.execute_query(query, params)
        
    def update_product(self, product_id, product_data):
        """Actualizar un producto existente"""
        query = """
            UPDATE stock 
            SET name = ?, pack = ?, profit = ?, cost_price = ?, price = ?, 
                iva = ?, price_with_iva = ?, quantity = ?, last_price_update = CURRENT_DATE
            WHERE id = ?
        """
        params = (
            product_data['Name'],
            product_data['Package'],
            product_data['Profit'],
            product_data['CostPrice'],
            product_data['SalePrice'],
            product_data['Iva'],
            product_data['PriceWIva'],
            product_data['Stock'],
            product_id
        )
        return db.execute_query(query, params)
    
    def update_field(self, db_field, new_value, product_id):
        query = f"UPDATE stock SET {db_field} = ?, last_price_update = CURRENT_DATE WHERE id = ?"
        db.execute_query(query, (new_value, product_id))
        
    def delete_product(self, product_id):
        """Eliminar un producto"""
        query = "DELETE FROM stock WHERE id = ?"
        return db.execute_query(query, (product_id,))

    def update_quantity(self, product_id, new_quantity):
        """Actualizar solo la cantidad de un producto"""
        query = "UPDATE stock SET quantity = ? WHERE id = ?"
        return db.execute_query(query, (new_quantity, product_id))
        
    def reduce_quantity(self, product_id, quantity_to_reduce):
        """Reducir la cantidad de un producto (para ventas)"""
        current_product = self.get_product_by_id(product_id)
        if not current_product:
            raise ValueError(f"Producto {product_id} no encontrado")
        
        current_quantity = current_product[-1]  # quantity está en la última posición
        
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
                    WHEN iva = '21%' THEN ROUND(price * ? * 1.21, 2)
                    WHEN iva = '10.5%' THEN ROUND(price * ? * 1.105, 2)
                    ELSE ROUND(price * ?, 2)
                END,
                profit = ROUND(((price * ? - cost_price) / cost_price) * 100, 2),
                last_price_update = CURRENT_DATE
            WHERE last_price_update = ?
        """
        
        params = (multiplier, multiplier, multiplier, multiplier, multiplier, date)
        
        return db.execute_query(query, params)
