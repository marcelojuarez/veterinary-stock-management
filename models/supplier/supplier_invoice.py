from datetime import datetime
from utils.utils import traditional_to_iso


class SupplierInvoice():
    def __init__(self, db):
        self.db = db

## -- Invoice -- ##
    def add_new_invoice(self, data, conn=None, commit=True):
        date = datetime.now().strftime("%Y-%m-%d")
        query = """
        INSERT INTO supplier_invoice(supplier_id, invoice_id, invoice_type, date, expiration_date, 
        total, subtotal, iva, discount, state, observations)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params =[
            data['supplier_id'],
            data['invoice_id'],
            data['invoice_type'],
            date,
            data['expiration_date'],
            str(data['total']),
            str(data['subtotal']),
            str(data['iva']),
            str(data['discount']),
            data['state'],
            data['observations'],
        ]

        return self.db.execute_query(query, params, conn=conn, commit=commit)

    def get_invoice_data(self, invoice_id):
        query = """
        SELECT * FROM supplier_invoice
        WHERE id = ? 
        """

        return self.db.fetch_one(query, (invoice_id, ))
        
    def update_invoice_info(self, invoice_id, data, conn=None, commit=True):
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
        UPDATE supplier_invoice
        SET 
            invoice_id = ?,
            invoice_type = ?,
            observations = ?,
            date = ?,
            expiration_date = ?
        WHERE id = ?
        """

        params = [
            data['invoice_id'],
            data['invoice_type'], 
            data['obs'],
            date,
            data['expiration'],
            invoice_id
        ]

        self.db.execute_query(query, params, conn=conn, commit=commit)

    def delete_invoice(self, invoice_id, conn=None, commit=True):
        query = """
        DELETE FROM supplier_invoice WHERE id = ?
        """

        self.db.execute_query(query, (invoice_id, ), conn=conn, commit=commit)
