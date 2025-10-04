from db.database import db

class SupplierModel:
    def __init__(self, db_connection=None):
        self.db = db_connection or db

    def get_all_suppliers(self):
        # Obtener todos los proveedores
        try:
            query = "SELECT * FROM proveedores ORDER BY id"
            return  db.fetch_all(query)
        except ValueError as e:
            print(f'Error getting suppliers: {e}')
            return []
    
    def find_supplier_by_id(self, supplier_id):
        # Obtener proveedor a traves de id
        try:
            query = "SELECT * FROM proveedores where id_proveedor = ?"
            return db.execute_query(query, (supplier_id, ))
        except ValueError as e:
            print(f'Error getting supplier by ID: {e}')
            return None

    def add_supplier(self, supplier_data):
        # Agregar nuevo proveedor a la base de datos
        query = """
            INSERT INTO proveedores (nombre, cuit, domicilio, telefono, email )
            VALUES (?, ?, ?, ?, ?)
        """
        params = [
            supplier_data['nombre'],
            supplier_data['cuit'],
            supplier_data['domicilio'],
            supplier_data['telefono'],
            supplier_data['email']
        ]

        print(params)

        return self.db.execute_query(query, params)
    
    def add_supplier_product(self, supplier_id, product_data):
        query = """
            INSERT INTO stock_proveedor (id, name, description, brand, price, quantity)
            VALUES (?, ?, ?, ?, ?, ?)
        """

        params = [
            supplier_id,
            product_data['name'],
            product_data['description'],
            product_data['brand'],
            product_data['price'],
            product_data['quantity']
        ]

        print(params)

        return self.db.execute_query(query, params)

    def show_supplier_info(self, supplier_id):
        pass

    def delete_supplier(self, supplier_id):
        try:
            query = "DELETE FROM proveedores where id = ?"
            return db.execute_query(query, (supplier_id, ))
        except Exception as e:
            print(f'Error : {e}')
            return None

    def update_balance():
        pass

    def search_supplier(self, search_term):
        # Busco a un proveedor por nombre o ID
        pass
    