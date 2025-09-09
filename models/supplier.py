from db.database import db

class SupplierModel:
    def __init__(self, db_connection=None):
        self.db = db_connection or db

    def get_all_suppliers(self):
        # Obtener todos los proveedores
        try:
            query = "SELECT * FROM supplier ORDER BY id"
            return  db.fetch_all(query)
        except ValueError as e:
            print(f'Error getting suppliers: {e}')
            return []
    
    def find_supplier_by_id(self, supplier_id):
        # Obtener proveedor a traves de id
        try:
            query = "SELECT * FROM supplier where id_proveedor = ?"
            return db.execute_query(query, (supplier_id, ))
        except ValueError as e:
            print(f'Error getting supplier by ID: {e}')
            return None

    def add_supplier(self, supplier_data):
        # Agregar nuevo proveedor a la base de datos
        query = """
            INSERT INTO supplier (nombre, razon_social)
            VALUES (?, ?)
        """
        params = [
            supplier_data['name'],
            supplier_data['company_name']
        ]

        return self.db.execute_query(query, params)

    def update_supplier_info(self, supplier_id):
        pass


    def delete_supplier(self, supplier_id):
        pass

    def update_balance():
        pass

    def search_supplier(self, search_term):
        # Busco a un proveedor por nombre o ID
        pass
    