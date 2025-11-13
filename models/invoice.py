from db.database import db
from datetime import datetime

class InvoiceModel:
    def __init__(self):
        self.db = db

    def create_invoice(self, customer_id, subtotal, iva, total):
        query = """
            INSERT INTO invoice (number, date, customer_id, subtotal, iva, total)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        number = datetime.now().strftime("F-%Y%m%d-%H%M%S")
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        invoice_id = self.db.execute_query(
            query,
            (number, date, customer_id, subtotal, iva, total)
        )

        return invoice_id, number

    def add_invoice_item(self, invoice_id, product_id, quantity, price, subtotal):
        query = """
            INSERT INTO invoice_items (invoice_id, product_id, quantity, price, subtotal)
            VALUES (?, ?, ?, ?, ?)
        """

        self.db.execute_query(query, (invoice_id, product_id, quantity, price, subtotal))

    def get_invoice(self, invoice_id):
        return self.db.fetch_one(
            "SELECT * FROM invoice WHERE id = ?",
            (invoice_id,)
        )

    def get_invoice_items(self, invoice_id):
        return self.db.fetch_all(
            "SELECT product_id, quantity, price, subtotal FROM invoice_items WHERE invoice_id = ?",
            (invoice_id,)
        )
