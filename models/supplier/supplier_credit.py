# models/supplier/supplier_credit.py

import logging
from decimal import Decimal
from datetime import datetime
from utils.utils import norm_to_2_dec

logger = logging.getLogger(__name__)

class SupplierCredit:
    def __init__(self, db):
        self.db = db

    """
    Agrega un nuevo movimiento de crédito.
    amount puede ser positivo (genera crédito) o negativo (usa crédito).
    """
    def add_movement(self, data, conn=None, commit=True):

        date = datetime.now().strftime("%Y-%m-%d")

        query = """
            INSERT INTO supplier_credit_movements
            (supplier_id, date, amount, type, purchase_id, check_id, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        params = [
            data['supplier_id'],
            date,
            data['amount'],
            data['type'],
            data['purchase_id'],
            data['check_id'],
            data['notes'],
        ]
        return self.db.execute_query(query, params, conn=conn, commit=commit)

    def get_last_movement(self, supplier_id):
        """
        Obtiene el último movimiento del proveedor.
        """

        query = """
            SELECT id, supplier_id, date, amount, type, purchase_id, check_id, notes
            FROM supplier_credit_movements
            WHERE supplier_id = ?
            ORDER BY id DESC
            LIMIT 1
        """

        row = self.db.fetch_one(query, (supplier_id, ))

        if not row:
            return None

        return {
            "id": row[0],
            "supplier_id": row[1],
            "date": row[2],
            "amount": Decimal(row[3]),
            "type": row[4],
            "purchase_id": row[5],
            "check_id": row[6],
            "notes": row[7]
        }

    ## -- Devuelve el saldo a favor actual del proveedor  -- ##
    def get_credit_amount_of_supplier(self, supplier_id):

        query = """
        SELECT amount
        FROM supplier_credit_movements
        WHERE supplier_id = ? AND valid = ? 
        """

        rows = self.db.fetch_all(query, (supplier_id, 1))

        total = Decimal("0.00")

        for r in rows:
            total += Decimal(r[0])

        return norm_to_2_dec(total)