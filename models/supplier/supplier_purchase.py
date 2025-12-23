# models/supplier/supplier_purchase.py

from datetime import datetime

class SupplierPurchase():
    def __init__(self, db):
        self.db = db

    def add_new_purchase(self, data, conn=None, commit=True):
        try:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            query = """
            INSERT INTO purchase (supplier_id, document_type, date, expiration_date, state, observations, pending, total) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = [
                data['supplier_id'],
                data['doc_type'],
                date,
                data['expiration_date'],
                data['state'],
                data['observations'],
                data['pending'],
                data['total']
            ]

            return self.db.execute_query(query, params, conn=conn, commit=commit)
        except ValueError as e:
            print(f'Error al cargar la compra: {e}')

    def get_purchase_by_id(self, purchase_id):
        try:
            query= """
            SELECT * FROM purchase WHERE id = ?
            """
            
            return self.db.fetch_one(query, (purchase_id, ))

        except ValueError as e:
            print(f'Error al obtener la compra: {e}')
            return None

    ## -- Devuelve todas las compras asociadas a un cuit -- ##
    def get_all_purchases(self, cuit=None):

        query = """
            SELECT purchase.id, supplier.cuit, purchase.document_type, purchase.invoice_id, purchase.receipt_id , purchase.date, 
            purchase.expiration_date, purchase.state, purchase.observations, purchase.pending, purchase.total
            FROM purchase
            JOIN supplier ON purchase.supplier_id = supplier.id
            WHERE (? IS NULL OR supplier.cuit = ?) 
            ORDER BY 
            CASE 
                WHEN purchase.state = 'PENDIENTE' THEN 0 
                ELSE 1 
            END,
            purchase.expiration_date
        """ 
        params = [
            cuit,
            cuit
        ]
        return self.db.fetch_all(query, params)
    
    ## -- Devuelve todas las compras con deuda pendiente asociadas a un cuit -- ##
    def get_all_purchases_without_paying(self, cuit=None):

        query = """
            SELECT purchase.id, supplier.cuit, purchase.document_type, purchase.invoice_id, purchase.receipt_id , purchase.date, 
            purchase.expiration_date, purchase.state, purchase.observations, purchase.pending, purchase.total
            FROM purchase
            JOIN supplier ON purchase.supplier_id = supplier.id
            WHERE (? IS NULL OR supplier.cuit = ?) AND pending > 0 
            ORDER BY 
            CASE 
                WHEN purchase.state = 'PENDIENTE' THEN 0 
                ELSE 1 
            END,
            purchase.expiration_date
        """

        params = [
            cuit,
            cuit
        ]

        return self.db.fetch_all(query, params)
    
    ## -- Setear compra como pagada -- ##
    def set_new_debt_purchase(self, purchase_id, id, doc_type, new_debt, conn=None, commit=True):

        new_debt = round(new_debt, 2)

        print(f'new_debt: {new_debt}')

        if new_debt <= 0:
            new_debt = 0

        query = """
        UPDATE purchase
        SET
            pending = ?,
            state = CASE
                WHEN ? <= 0 THEN 'PAGADA'
                ELSE 'PENDIENTE'
            END
        WHERE id = ?
        """

        params = (new_debt, new_debt, purchase_id)

        self.db.execute_query(query, params, conn=conn, commit=commit)

        # Si quedó pagada, actualizar comprobante
        if new_debt == 0:
            if doc_type == "REMITO":
                query = """
                UPDATE supplier_receipt
                SET state = 'PAGADA'
                WHERE id = ?
                """
            else:
                query = """
                UPDATE supplier_invoice
                SET state = 'PAGADA'
                WHERE id = ?
                """

            self.db.execute_query(query, (id,), conn=conn, commit=commit)

    
    ## -- Vincular comprobante con compra -- ##
    def set_doc_on_purchase(self, purchase_id, id, doc_type, conn=None, commit=True):
        """Set a doc number on purchase"""

        if doc_type == "REMITO":
            query = """
                UPDATE purchase
                SET receipt_id = ?
                WHERE id = ?
            """
        else:
            query = """
                UPDATE purchase
                SET invoice_id = ?
                WHERE id = ?
            """

        params = [
            id,
            purchase_id
        ]

        return self.db.execute_query(query, params, conn=conn, commit=commit)
    

    ## -- Debt -- ##
    def get_debt_of_supplier(self, cuit):
        query = """
        SELECT SUM(pending) 
        FROM purchase JOIN supplier ON purchase.supplier_id = supplier.id
        WHERE supplier.cuit = ?
        """

        return self.db.fetch_one(query, (cuit, ))
    
    def update_last_debt_update(self, supplier_id, conn=None, commit=True):
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        """Actualizar Saldo deuda a un proveedor"""
        query = """
            UPDATE supplier
            SET last_debt_update = ?
            WHERE id = ?
        """
        params = [
            date,
            supplier_id
        ]

        self.db.execute_query(query, params, conn=conn, commit=commit)
        return date
    
    ## -- -- ##

    ## -- Invoice -- ##
    def add_new_invoice(self, data, conn=None, commit=True):
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
        INSERT INTO supplier_invoice(supplier_id, invoice_id, invoice_type, point_of_sale, date, expiration_date, 
        total, subtotal, iva, discount, state, observations)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params =[
            data['supplier_id'],
            data['invoice_id'],
            data['invoice_type'],
            data['point_of_sale'],
            date,
            data['expiration_date'],
            data['total'],
            data['subtotal'],
            data['iva'],
            data['discount'],
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

    ## -- Receipt -- ##
    def add_new_receipt(self, data, conn=None, commit=True):
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
        INSERT INTO supplier_receipt(supplier_id, receipt_id, date, expiration_date, observations,
        state, total)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            data['supplier_id'],
            data['receipt_id'],
            date,
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

    ## -- Transaccion para agregar venta y recibo -- ##
    def create_receipt_and_purchase(self, receipt_params, purchase_params):
        try:
            conn = self.db.get_connection()

            # Iniciar transacción
            conn.execute("BEGIN")

            receipt_id = self.add_new_receipt(receipt_params, conn, commit=False)
            purchase_id = self.add_new_purchase(purchase_params, conn, commit=False)

            print(f"receipt_id: {receipt_id}")
            print(f"purchase_id: {purchase_id}")

            self.set_doc_on_purchase(purchase_id, receipt_id, "REMITO", conn, commit=False)

            self.update_last_debt_update(purchase_params['supplier_id'], conn, commit=False)

            conn.commit()

        except Exception as e:
            conn.rollback()
            print(f'Hubo un error {e}')
            return False
        
        finally:
            conn.close()
            return True

    ## -- Transaccion para agregar venta y factura -- ##
    def create_invoice_and_purchase(self, invoice_params, purchase_params):
        try:
            conn = self.db.get_connection()

            # Iniciar transacción
            conn.execute("BEGIN")

            invoice_id = self.add_new_invoice(invoice_params, conn, commit=False)
            purchase_id = self.add_new_purchase(purchase_params, conn, commit=False)

            self.set_doc_on_purchase(purchase_id, invoice_id, "FACTURA", conn, commit=False)

            self.update_last_debt_update(purchase_params['supplier_id'], conn, commit=False)

            conn.commit()

        except Exception as e:
            conn.rollback()
            print(f'Hubo un error {e}')
            return False
        
        finally:
            conn.close() 
            return True    