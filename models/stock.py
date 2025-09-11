from db.database import db

class StockModel: 
    def __init__(self,db_conection=None):
        self.db = db_conection or db
    
    def get_all_products(self):
        """Obtener todos los productos del stock"""
        query = "SELECT id, name, description, brand, price, quantity FROM stock ORDER BY name"
        return db.fetch_all(query)
    
    def get_product_by_id(self, product_id):
        """Obtener un producto por su ID"""
        query = "SELECT id, name, description, brand, price, quantity FROM stock WHERE id = ?"
        return db.fetch_one(query, (product_id,))
        
    
    def add_product(self, product_data):
        """Agregar un nuevo producto"""
        query = """
            INSERT INTO stock (id, name, description, brand, price, quantity)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            product_data['id'],
            product_data['name'],
            product_data['desc'],
            product_data['brand'],
            product_data['price'],
            product_data['qnt'],
        )
        return db.execute_query(query, params)
        
    def update_product(self, product_id, product_data):
        """Actualizar un producto existente"""
        query = """
            UPDATE stock 
            SET name = ?, brand = ?, description = ?, price = ?, quantity = ?
            WHERE id = ?
        """
        params = (
            product_data['name'],
            product_data['desc'],
            product_data['brand'],
            product_data['price'],
            product_data['qnt'],
            product_id
        )
        return db.execute_query(query, params)
    
    def update_field(self, db_field, new_value, product_id):
        query = f"UPDATE stock SET {db_field} = ? WHERE id = ?"
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
        # Primero obtener la cantidad actual
        current_product = self.get_product_by_id(product_id)
        if not current_product:
            raise ValueError(f"Producto {product_id} no encontrado")
        
        current_quantity = current_product[4]  # quantity está en el índice 4
        
        if current_quantity < quantity_to_reduce:
            raise ValueError(f"Stock insuficiente. Disponible: {current_quantity}, Solicitado: {quantity_to_reduce}")
        
        new_quantity = current_quantity - quantity_to_reduce
        return self.update_quantity(product_id, new_quantity)

    def update_quantity(self, product_id, new_quantity):
        """Actualizar solo la cantidad de un producto"""
        query = "UPDATE stock SET quantity = ? WHERE id = ?"
        return db.execute_query(query, (new_quantity, product_id))
    
    def search_products(self, search_term):
        """Buscar productos por nombre o ID"""
        query = """
            SELECT id, name, description, brand, price, quantity 
            FROM stock 
            WHERE name LIKE ? OR id LIKE ? OR description LIKE ? OR brand LIKE ?
            ORDER BY name
        """
        search_pattern = f"%{search_term}%"
        return db.fetch_all(query, (search_pattern, search_pattern, search_pattern, search_pattern))
    
    def get_products_by_category(self, category):
        #  Obtener productos por categoría (asumiendo que hay una columna 'category' en la tabla stock)
        try:
            with self.db.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM stock WHERE category = ? ORDER BY name",
                    (category,)
                )                         
                return cursor.fetchall()
        except Exception as e:
            print(f"Error getting products by category: {e}")
            return []
                

    def get_categories(self):
        # Obtener todas las categorías únicas de productos
        try:
            with self.db.cursor() as cursor:
                cursor.execute("SELECT DISTINCT category FROM stock")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting categories: {e}")
            return []
    
    def get_low_stock_products(self, threshold):
        # Obtener productos con stock bajo (cantidad menor que el umbral)
        try: 
            with self.db.cursor() as cursor:
                cursor.execute("SELECT * FROM stock WHERE quantity < ? ORDER BY quantity", (threshold,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error getting low stock products: {e}")
            return []
            