from db.database import db
from datetime import datetime

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
            query = "SELECT * FROM proveedores where id = ?"
            return db.fetch_one(query, (supplier_id, ))
        except ValueError as e:
            print(f'Error getting supplier by ID: {e}')
            return None
        
    def find_suppplier_by_cuit(self, supplier_cuit):
        try:
            query = "SELECT * FROM proveedores where cuit = ?"
            return db.fetch_one(query, (supplier_cuit,))
        except ValueError as e:
            print(f'Error getting supplier by CUIT: {e}')
            return None
        
    def get_all_payment_of_supplier(self, supplier_id):
        try:
            query = """
            SELECT * FROM movimientos_proveedor where id_proveedor = ?
            """
            return self.db.fetch_all(query, (supplier_id,))            
        except ValueError as e:
            print(f'Error getting supplier payment by cuit: {e}')
            return None


    def add_supplier(self, supplier_data):
        # Agregar nuevo proveedor a la base de datos
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
            INSERT INTO proveedores (nombre, cuit, domicilio, telefono, email, deuda, ult_act_deuda)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            supplier_data['nombre'],
            supplier_data['cuit'],
            supplier_data['domicilio'],
            supplier_data['telefono'],
            supplier_data['email'],
            supplier_data['deuda'],
            date
        ]

        return self.db.execute_query(query, params)

    def add_new_payment(self, supplier_id, payment_data):
        datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
            INSERT INTO movimientos_proveedor (id_proveedor, monto, metodo, id_recibo, observaciones, saldo_anterior, saldo_posterior, date)
            values(?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = [
            supplier_id,
            payment_data['monto']

        ]

        self.db.execute_query(query, params)
    

    def show_supplier_info(self, supplier_id):
        pass

    def delete_supplier(self, supplier_id):
        try:
            query = "DELETE FROM proveedores where id = ?"
            return db.execute_query(query, (supplier_id, ))
        except Exception as e:
            print(f'Error : {e}')
            return None

    def update_debt(self, supplier_id, new_supplier_debt):
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        """Actualizar Saldo deuda a un proveedor"""
        query = """
            UPDATE proveedores
            SET deuda = ?, ult_act_deuda = ?
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
    