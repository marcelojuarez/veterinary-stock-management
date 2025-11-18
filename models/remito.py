from db.database import db
from datetime import datetime

class RemitoModel:

    def __init__(self):
        self.db = db

    def get_next_number(self):
        """Devuelve el próximo número de remito."""
        query = "SELECT MAX(number) FROM delivery_note"
        row = self.db.fetch_one(query)

        if row and row[0]:
            return int(row[0]) + 1
        return 1  # Primer remito

    def create_note(self, number, sale_id, customer_id):
        """
        Inserta un nuevo remito asociado a una venta y cliente.
        """
        query = """
            INSERT INTO delivery_note (number, sale_id, customer_id, date)
            VALUES (?, ?, ?, ?)
        """
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return self.db.execute_query(query, (number, sale_id, customer_id, date))


    def add_item(self, delivery_note_id, product_id, quantity):
        query = """
            INSERT INTO delivery_note_items (delivery_note_id, product_id, quantity)
            VALUES (?, ?, ?)
        """
        return self.db.execute_query(query, (delivery_note_id, product_id, quantity))

    def get_note_by_id(self, note_id):
        query = """
            SELECT id, number, sale_id, customer_id, date
            FROM delivery_note
            WHERE id = ?
        """
        return self.db.fetch_one(query, (note_id,))

    def get_items(self, note_id):
        query = """
            SELECT product_id, quantity
            FROM delivery_note_items
            WHERE delivery_note_id = ?
        """
        rows = self.db.fetch_all(query, (note_id,))
        # convertir a diccionarios
        return [{"product_id": r[0], "quantity": r[1]} for r in rows]

    def get_notes_by_customer(self, customer_id):
        query = """
            SELECT id, number, sale_id, date
            FROM delivery_note
            WHERE customer_id = ?
            ORDER BY date DESC
        """
        rows = self.db.fetch_all(query, (customer_id,))
        return [
            {
                "id": r[0],
                "number": r[1],
                "sale_id": r[2],
                "date": r[3]
            }
            for r in rows
        ]
