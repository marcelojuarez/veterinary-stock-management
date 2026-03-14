from decimal import Decimal
from utils.utils import norm_to_2_dec
from db.database import db

class CustomerCredit:
    def __init__(self):
        self.db = db
    
    ## -- Agregar movimiento en tabla de saldos a favor cliente-- ##
    def add_customer_credit(self, data, check_id=None, conn=None, commit=True): 
        query = """
            INSERT INTO customer_credit 
            (client_id, amount, reason, sale_id, check_id, valid)
            VALUES (?, ?, ?, ?, ?, ?)
        """

        params = [
            data['client_id'],
            str(data['amount']),
            data['reason'],
            data['sale_id'],
            check_id,
            1
        ]

        return self.db.execute_query(query, params, conn=conn, commit=commit)
   
   ## -- Obtener saldo a favor de un cliente -- ##
    def get_customer_credit(self, client_id):
        rows = self.db.fetch_all(
            "SELECT amount FROM customer_credit WHERE client_id = ? and valid = ?", 
            (client_id, 1)
        )

        total = Decimal('0.00')
        for row in rows:
            total += Decimal(row[0])

        return norm_to_2_dec(total)


    ## -- Cancela registros de saldos a favor asociados a un cheque -- ##
    def cancel_check_credit(self, check_id, conn=None, commit=True):
        query = """
        UPDATE customer_credit
        SET 
            valid = ?
        WHERE check_id = ?
        """

        self.db.execute_query(query, (0, check_id), conn=conn, commit=commit)