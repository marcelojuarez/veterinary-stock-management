from datetime import datetime
from utils.utils import traditional_to_iso
from decimal import Decimal

class SupplierInvoice():
    def __init__(self, db):
        self.db = db

## -- Invoice -- ##
    def add_new_invoice(self, data, conn=None, commit=True):
        date = datetime.now().strftime("%Y-%m-%d")
        query = """
        INSERT INTO supplier_invoice(supplier_id, invoice_id, invoice_type, date, expiration_date, 
        state, observations, orig_subtotal, discount, discount_amount, subtotal_w_discount, iva, total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            data['supplier_id'],
            data['invoice_id'],
            data['invoice_type'],
            date,
            data['expiration_date'],
            data['state'],
            data['observations'],
            data['orig_subtotal'],
            str(data['discount']),
            data['discount_amount'],
            data['subtotal_w_discount'],
            data['iva'],
            data['total'],
        ]

        return self.db.execute_query(query, params, conn=conn, commit=commit)

    def get_invoice_data(self, invoice_id):
        query = """
        SELECT * FROM supplier_invoice
        WHERE id = ? 
        """

        return self.db.fetch_one(query, (invoice_id, ))
    
    def get_invoice_discount(self, invoice_id):
        query = """
        SELECT discount FROM supplier_invoice
        WHERE id = ? 
        """

        result = self.db.fetch_one(query, (invoice_id, ))[0]
        return Decimal(result)
        
    def update_invoice_info(self, invoice_id, data, conn=None, commit=True):
        date = datetime.now().strftime("%Y-%m-%d")
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
            traditional_to_iso(data['expiration']),
            invoice_id
        ]

        self.db.execute_query(query, params, conn=conn, commit=commit)

    def delete_invoice(self, invoice_id, conn=None, commit=True):
        query = """
        DELETE FROM supplier_invoice WHERE id = ?
        """

        self.db.execute_query(query, (invoice_id, ), conn=conn, commit=commit)
