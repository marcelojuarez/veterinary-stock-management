from datetime import datetime
from utils.utils import traditional_to_iso
from decimal import Decimal
from utils.utils import norm_to_2_dec

class SupplierInvoice():
    def __init__(self, db):
        self.db = db

    ## -- Agrega una nueva factura -- ##
    def add_new_invoice(self, data, conn=None, commit=True):
        query = """
        INSERT INTO supplier_invoice(supplier_id, invoice_id, invoice_type, date, expiration_date, 
        supplier_iva_condition, state, observations, pay_condition, pay_period, orig_subtotal, 
        discount, discount_amount, subtotal_w_discount, iva, total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            data['supplier_id'],
            data['invoice_id'],
            data['invoice_type'],
            data['date'],
            data['expiration_date'],
            data['s_iva_c'],
            data['state'],
            data['observations'],
            data['pay_cond'],
            data['pay_period'],
            data['orig_subtotal'],
            data['discount'],
            data['discount_amount'],
            data['subtotal_w_discount'],
            data['iva'],
            data['total'],
        ]

        return self.db.execute_query(query, params, conn=conn, commit=commit)

    ## -- Obtiene los datos de un registro de factura -- ##
    def get_invoice_data(self, invoice_id):
        query = """
        SELECT * FROM supplier_invoice
        WHERE id = ? 
        """

        return self.db.fetch_one(query, (invoice_id, ))
    
    ## -- Obtiene el monto de descuento global de una factura -- ##
    def get_invoice_discount(self, invoice_id):
        query = """
        SELECT discount FROM supplier_invoice
        WHERE id = ? 
        """

        result = self.db.fetch_one(query, (invoice_id, ))[0]
        return Decimal(result)

    ## -- Actualiza el info de una factura -- ##   
    def update_invoice_info(self, invoice_id, data, conn=None, commit=True):
        query = """
        UPDATE supplier_invoice
        SET 
            invoice_id = ?,
            date = ?,
            expiration_date = ?,
            observations = ?,
            pay_condition = ?,
            pay_period = ?            
        WHERE id = ?
        """

        params = [
            data['invoice_id'],
            data['date'],
            data['expiration'],
            data['obs'],
            data['pay_cond'],
            data['pay_period'],
            invoice_id
        ]

        self.db.execute_query(query, params, conn=conn, commit=commit)

    ## -- Agrega las percepciones correspondientes a una factura -- ##
    def add_invoice_perceptions(self, invoice_id, p_parameters, conn=None, commit=True):
        try:
            query = """
            INSERT INTO invoice_perceptions (invoice_id, tax_type, amount)
            VALUES (?, ?, ?)
            """

            params = [
                invoice_id,
                p_parameters['tax_type'],
                p_parameters['amount']
            ]

            self.db.execute_query(query, params, conn=conn, commit=commit)

        except ValueError as e:
            print(f'Error al cargar los datos: {e}')

    ## -- Obtiene el monto total de las percepciones -- ##
    def get_invoice_perceptions_amount(self, invoice_id):
        query = """
        SELECT amount
        FROM invoice_perceptions
        WHERE invoice_id = ?
        """

        rows = self.db.fetch_all(query, (invoice_id, ))

        amount = Decimal('0.00')

        for row in rows:
            amount += Decimal(row[0])

        return norm_to_2_dec(amount)
    
    ## -- Obtiene el monto de las percepciones IIBB -- ##
    def get_iibb_per_amount(self, invoice_id):
        query = """
        SELECT amount
        FROM invoice_perceptions
        WHERE invoice_id = ? AND tax_type = ?
        """

        params = [invoice_id, 'IIBB_PER']

        amount = self.db.fetch_one(query, params)

        if amount is None:
            return Decimal('0.00')
        
        else:
            return norm_to_2_dec(amount[0])

    ## -- Obtiene el monto de las percepciones IVA -- ##
    def get_iva_per_amount(self, invoice_id):
        query = """
        SELECT amount
        FROM invoice_perceptions
        WHERE invoice_id = ? AND tax_type = ?
        """

        params = [invoice_id, 'IVA_PER']

        amount = self.db.fetch_one(query, params)

        if amount is None:
            return Decimal('0.00')
        
        else:
            return norm_to_2_dec(amount[0])

    ## -- Elimina un registro de factura -- ##
    def delete_invoice(self, invoice_id, conn=None, commit=True):
        query = """
        DELETE FROM supplier_invoice WHERE id = ?
        """

        self.db.execute_query(query, (invoice_id, ), conn=conn, commit=commit)
