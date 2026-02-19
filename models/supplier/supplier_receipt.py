from datetime import datetime
from utils.utils import traditional_to_iso

class SupplierReceipt():
    def __init__(self, db):
        self.db = db

    def add_new_receipt(self, data, conn=None, commit=True):
        query = """
        INSERT INTO supplier_receipt(supplier_id, receipt_id, date, expiration_date, observations,
        state, total)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            data['supplier_id'],
            data['receipt_id'],
            data['date'],
            data['expiration_date'],
            data['observations'],
            data['state'],
            data['total'], 
        ]

        return self.db.execute_query(query, params, conn=conn, commit=commit)
    
    def get_receipt_data(self, receipt_id):
        query = """
        SELECT * FROM supplier_receipt
        WHERE id = ? 
        """

        return self.db.fetch_one(query, (receipt_id, ))

    def update_receipt_info(self, receipt_id, data, conn=None, commit=True):
        date = datetime.now().strftime("%Y-%m-%d")
        query = """
        UPDATE supplier_receipt
        SET 
            receipt_id = ?,
            date = ?,
            expiration_date = ?,
            observations = ?
        WHERE id = ?
        """

        params = [
            data['receipt_id'],            
            date,
            traditional_to_iso(data['expiration']),
            data['obs'],
            receipt_id
        ]

        self.db.execute_query(query, params, conn=conn, commit=False)

    def delete_receipt(self, receipt_id, conn=None, commit=True):
        query = """
        DELETE FROM supplier_receipt WHERE id = ?
        """

        self.db.execute_query(query, (receipt_id, ), conn=conn, commit=commit)