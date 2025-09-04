from db.database import db

class SupplierModel:
    def __init__(self):
        pass

    def show_suppliers(self):
        # Show all suppliers of the database
        query = "SELECT * FROM supplier ORDER BY id"
        return  db.fetch_all(query)

    def add_supplier(self, supplier_data):
        # Add supplier 
        query = """
            INSERT INTO supplier (id, razon_social, nombre, activo)
            VALUES (?, ?, ?, ?)
        """
        params = [
            supplier_data['id'],
            supplier_data['razon_social'],
            supplier_data['nombre'],
            supplier_data['activo']
        ]

        return db.execute_query(query, params)


    def find_supplier_by_id(self, supplier_id):
        # supplier wanted by ID
        query = "SELECT * FROM supplier where id_proveedor = ?"
        return db.execute_query(query, (supplier_id, ))

    def delete_supplier(self, supplier_id):
        pass

    def update_supplier_info(self, supplier_id):
        pass

    def update_balance():
        pass
