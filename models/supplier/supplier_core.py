# models/supplier/supplier_core.py

from datetime import datetime

class SupplierCore():
    def __init__(self, db):
        self.db = db

    def get_all_suppliers(self):
        # Obtener todos los proveedores
        try:
            query = "SELECT * FROM supplier ORDER BY name"
            return  self.db.fetch_all(query)
        except ValueError as e:
            print(f'Error getting suppliers: {e}')
            return []
    
    def find_supplier_by_id(self, supplier_id):
        # Obtener proveedor a traves de id
        try:
            query = "SELECT * FROM supplier where id = ?"
            return self.db.fetch_one(query, (supplier_id, ))
        except ValueError as e:
            print(f'Error getting supplier by ID: {e}')
            return None
        
    def find_supplier_by_cuit(self, supplier_cuit):
        try:
            query = "SELECT * FROM supplier where cuit = ?"
            return self.db.fetch_one(query, (supplier_cuit,))
        except ValueError as e:
            print(f'Error getting supplier by CUIT: {e}')
            return None

    def add_supplier(self, supplier_data):
        # Agregar nuevo proveedor a la base de datos
        date = datetime.now().strftime("%Y-%m-%d")
        query = """
            INSERT INTO supplier (name, cuit, home, phone, email, last_debt_update)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = [
            supplier_data['name'],
            supplier_data['cuit'],
            supplier_data['home'],
            supplier_data['phone'],
            supplier_data['email'],
            date
        ]

        return self.db.execute_query(query, params)

    def delete_supplier(self, supplier_id):
        try:
            query = "DELETE FROM supplier where id = ?"
            return self.db.execute_query(query, (supplier_id, ))
        except Exception as e:
            print(f'Error : {e}')
            return None


