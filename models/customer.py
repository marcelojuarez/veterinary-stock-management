import sqlite3
from db.database import db

class CustomerModel:
    def __init__(self, db_connection=None):
        self.db = db_connection or db 

    def get_all_customers(self): 
        # Obtener todos los clientes
        try: 
            query = "SELECT * FROM clientes ORDER BY id"
            return db.fetch_all(query)
        except ValueError as e: 
            print(f'Error getting customers: {e}')
            return []

    def find_customer_by_id(self, customer_id):
        # Obtener cliente a traves de id
        try:
            query = "SELECT * FROM clientes where id = ?"
            return db.execute_query(query, (customer_id,))
        except ValueError as e:
            print(f'Error getting customer by ID: {e}')
            return None

    def add_customer(self, customer_data):
        # Agregar nuevo cliente a la base de datos
        query = """
            INSERT INTO clientes (nombre, cuit, domicilio, telefono)
            VALUES(?, ?, ?, ?)
        """
        params = [
            customer_data['nombre'].upper(),
            customer_data['cuit'],
            customer_data['domicilio'].upper(),
            customer_data['telefono']
        ]
        try:
            return db.execute_query(query, params)
        except sqlite3.IntegrityError as e: 
            raise ValueError("ya existe un cliente con alguno de esos datos.")
    
    def update_customer_info(self, customer_id, monto_deuda):
        # Actualizar la informacion del cliente 
        query = "UPDATE clientes SET monto_deuda = ? where id = ?"
        params = (monto_deuda, customer_id)
        try: 
            return db.execute_query(query, params)
        except Exception as e:
            print(f'Error updating customer debt info: {e}')
            return None
        

    def delete_customer(self, customer_id):
        # Eliminar la informacion del cliente
        try:
            query = "DELETE FROM clientes where id = ?"
            return db.execute_query(query, (customer_id,))
        except Exception as e: 
            print(f'Error : {e}')
            return None 
    
    def search_customer(self, search_term):
        # Busco a un cliente por nombre o id 
        try:
            if search_term.isdigit():
                query = "SELECT * FROM clientes WHERE id = ?"
                return self.db.fetch_all(query, (int(search_term),))
            else:
                query = "SELECT * FROM clientes WHERE nombre LIKE ?"
                return self.db.fetch_all(query, (f"%{search_term.upper()}%",))
        except Exception as e:
            print(f"Error searching customer: {e}")
            return []
            