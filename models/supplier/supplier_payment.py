# models/supplier/supplier_payments.py

from datetime import datetime

class SupplierPayment():
    def __init__(self, db):
        self.db = db

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

    def get_payment_by_id(self, payment_id):
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
            SELECT * FROM supplier_movement where id_supplier = ? ORDER BY date
            """
            return self.db.fetch_all(query, (supplier_id,))            
        except ValueError as e:
            print(f'Error getting supplier payment by id: {e}')
            return None    