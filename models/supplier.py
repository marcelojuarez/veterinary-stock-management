from db.database import db
from datetime import datetime

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
            query = "SELECT * FROM supplier where id = ?"
            return db.fetch_one(query, (supplier_id, ))
        except ValueError as e:
            print(f'Error getting supplier by ID: {e}')
            return None
        
    def find_suppplier_by_cuit(self, supplier_cuit):
        try:
            query = "SELECT * FROM supplier where cuit = ?"
            return db.fetch_one(query, (supplier_cuit,))
        except ValueError as e:
            print(f'Error getting supplier by CUIT: {e}')
            return None

    def add_supplier(self, supplier_data):
        # Agregar nuevo proveedor a la base de datos
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
            INSERT INTO supplier (name, cuit, home, phone, email, debt, last_debt_update)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            supplier_data['name'],
            supplier_data['cuit'],
            supplier_data['home'],
            supplier_data['phone'],
            supplier_data['email'],
            supplier_data['debt'],
            date
        ]

        return self.db.execute_query(query, params)

    def delete_supplier(self, supplier_id):
        try:
            query = "DELETE FROM supplier where id = ?"
            return db.execute_query(query, (supplier_id, ))
        except Exception as e:
            print(f'Error : {e}')
            return None

    def update_debt(self, supplier_id, new_supplier_debt):
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        """Actualizar Saldo deuda a un proveedor"""
        query = """
            UPDATE supplier
            SET debt = ?, last_debt_update = ?
            WHERE id = ?
        """
        params = [
            new_supplier_debt,
            date,
            supplier_id
        ]

        return db.execute_query(query, params)
    
    def search_supplier(self, search_term):
        # Busco a un proveedor por nombre o ID
        pass
    

    def add_new_payment(self, supplier_id, data):
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
            INSERT INTO supplier_movement (id_supplier, receipt_number, amount, method, observation, operation_num, 
            origin, destination, check_number, bank, previous_debt, subsequent_debt, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ? ,? ,?, ?, ?, ?)
        """

        params = [
            data['Id_supplier'],
            data['Receipt_number'],
            data['Amount'],
            data['Method'],
            data['Observation'],
            data['Operation_num'],
            data['Origin'],
            data['Destination'],
            data['Check_number'],
            data['Bank'],
            data['previous_debt'],
            data['subsequent_debt'],
            date
        ]

        print(f'data: {params}')
        self.db.execute_query(query, params)

    def get_payment_by_id_and_method(self, payment_id):
        try:
            query="""
            SELECT * FROM supplier_movement where id = ? 
            """
            return self.db.fetch_one(query, (payment_id))
        except ValueError as e:
            print(f'Error getting supplier payment by cuit: {e}')
            return None

    def get_transfer_data(self, payment_id):
        try:
            query = """
            SELECT operation_num, origin, destination FROM supplier_movement where id = ?
            """
            return self.db.fetch_one(query, (payment_id,))
        except ValueError as e:
            print(f'Error getting transfer data by payment id: {e}')
            return None

    def get_check_data(self, payment_id):
        try:
            query = """
            SELECT check_number, bank FROM supplier_movement where id = ?
            """
            return self.db.fetch_one(query, (payment_id,))
        except ValueError as e:
            print(f'Error getting transfer data by payment id: {e}')
            return None
        
    def get_all_payment_of_supplier(self, supplier_id):
        try:
            query = """
            SELECT * FROM supplier_movement where id_supplier = ?
            """
            return self.db.fetch_all(query, (supplier_id,))            
        except ValueError as e:
            print(f'Error getting supplier payment by cuit: {e}')
            return None
