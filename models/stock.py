from db.database import db

class StockModel: 
    def __init__(self,db_conection=None):
        self.db = db_conection or db
    
    def get_all_products(self):
        # Obtener todos los productos en stock
        try:
            with self.db.cursor() as cursor:
                cursor.execute("SELECT * FROM stock ORDER BY name") 
                return cursor.fetchall() # Obtener todos los productos
        except Exception as e:
            print(f"Error getting products: {e}")
            return []
    
    def get_product_by_id(self, product_id):
        # Obtener un producto por su ID
        try:
            with self.db.cursor() as cursor:
                cursor.execute("SELECT * FROM stock WHERE id = ?", (product_id,))
                return cursor.fetchone() # Obtener un solo producto
        except Exception as e:
            print(f"Error getting product by ID: {e}")
            return None
        
    
    def add_product(self, product_data):
        # Agregar un nuevo producto al stock
        try: 
            with self.db.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO stock (id,name, description, quantity, price, supplier_id)
                    VALUES (?,?, ?, ?, ?, ?)
                """, product_data)
                self.db.commit()
                return cursor.lastrowid # Devuelve el ID del producto agregado 
        except Exception as e:
            print(f"Error adding product: {e}")
            return None
        
    def update_product(self, product_id, product_data):
        # Actualizar un producto existente en el stock
        try: 
            with self.db.cursor() as cursor:
                cursor.execute("""
                    UPDATE stock
                    SET name = ?, description = ?, quantity = ?, price = ?, supplier_id = ?
                    WHERE id = ?
                """, product_data + (product_id,))
                self.db.commit()
                return cursor.rowcount # Devuelve el número de filas afectadas
        except Exception as e:
            self.db.rollback()
            print(f"Error updating product: {e}")
            return None
        
    def delete_product(self, product_id):
        # Eliminar un producto del stock
        try:
            with self.db.cursor() as cursor:
                cursor.execute("DELETE FROM stock WHERE id = ?", (product_id,))
                self.db.commit()
                return cursor.rowcount # Devuelve el número de filas afectadas
        except Exception as e:
            self.db.rollback()
            print(f"Error deleting product: {e}")
            return None

    def update_quantity(self, product_id,new_quantity):
        # Actualizar la cantidad de un producto en stock
        try:
            with self.db.cursor() as cursor:
                cursor.execute("UPDATE stock SET quantity = ? WHERE id = ?", (new_quantity,product_id))
                self.db.commit()
                return cursor.rowcount
        except Exception as e:
            self.db.rollback()
            print(f"Error updating quantity: {e}")
            return 0
        
    def reduce_quantity(self,product_id,quantity_to_reduce):
        # Reducir la cantidad de un producto en stock
        try: 
            with self.db.cursor() as cursor:
                 # Verificar stock suficiente primero
                cursor.execute("SELECT quantity FROM stock WHERE id = ?", (product_id,))
                current_stock = cursor.fetchone()[0]
                
                if current_stock < quantity_to_reduce:
                    raise ValueError("Stock insuficiente")
                
                cursor.execute("UPDATE stock SET quantity = quantity - ? WHERE id = ?", (quantity_to_reduce,product_id))
                self.db.commit()
                return cursor.rowcount
        except Exception as e:
            self.db.rollback()
            print(f"Error reducing quantity: {e}")
            return 0

    def increase_quantity(self,product_id,quantity_to_increase):
        # Aumentar la cantidad de un producto en stock
        try:
            with self.db.cursor() as cursor:
                # Verificar que la cantidad a aumentar sea positiva
                if quantity_to_increase < 0:
                    raise ValueError("La cantidad a aumentar debe ser positiva")
                cursor.execute("UPDATE stock SET quantity = quantity + ? WHERE id = ?", (quantity_to_increase,product_id))
                self.db.commit()
                return cursor.rowcount
        except Exception as e:
            self.db.rollback()
            print(f"Error increasing quantity: {e}")
            return 0
    
    def search_products(self, search_term):
        # Buscar productos por nombre o ID
        try: 
            with self.db.cursor() as cursor:
                cursor.execute(
                            "SELECT * FROM stock WHERE name LIKE ? OR CAST(id AS TEXT) LIKE ? ORDER BY name",
                            ('%'+search_term+'%', '%'+search_term+'%')
                        )
                return cursor.fetchall()
        except Exception as e:
            print(f"Error searching products: {e}")
            return [] 
    
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
            