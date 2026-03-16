# models/supplier/supplier_payments.py

from datetime import datetime
from utils.utils import norm_to_2_dec
from decimal import Decimal

class SupplierPayment():
    def __init__(self, db, purchase_model):
        self.db = db
        self.purchase = purchase_model

    ## -- Obtiene un registro de pago a traves de su id -- ##
    def get_payment_by_id(self, payment_id):
        try:
            query = """
            SELECT * 
            FROM supplier_payment 
            WHERE id = ? 
            """
            return self.db.fetch_one(query, (payment_id))
        except ValueError as e:
            print(f'Error getting supplier supplier_payment by cuit: {e}')
            return None

    ## -- Obtiene los datos de un pago hecho por transferencia -- ##
    def get_transfer_data(self, payment_id):
        try:
            query = """
            SELECT operation_num, origin, destination 
            FROM supplier_payment 
            WHERE id = ?
            """
            return self.db.fetch_one(query, (payment_id,))
        except ValueError as e:
            print(f'Error getting transfer data by supplier_payment id: {e}')
            return None

    ## -- Obtiene los datos de un pago hecho por cheque -- ##
    def get_check_data(self, payment_id):
        try:
            query = """
            SELECT check_number, bank 
            FROM supplier_payment 
            WHERE id = ?
            """
            return self.db.fetch_one(query, (payment_id,))
        except ValueError as e:
            print(f'Error getting transfer data by payment id: {e}')
            return None
    
    ## -- Obtiene todos los pagos asociados o no, a un cuit-- ##
    def get_all_payments(self, supplier_id=None):
        try:
            query = """
            SELECT supplier_payment.id, supplier.cuit, supplier_payment.receipt_number, supplier_payment.amount,
            supplier_payment.method, supplier_payment.observation, supplier_payment.operation_num, supplier_payment.origin, 
            supplier_payment.destination, supplier_payment.check_number, supplier_payment.bank, supplier_payment.date
            FROM supplier_payment 
            JOIN supplier ON supplier_payment.supplier_id = supplier.id
            WHERE (? IS NULL OR supplier.id = ?)
            ORDER BY supplier_payment.date DESC, supplier_payment.id DESC
            """
            params = [
               supplier_id,
               supplier_id
            ]

            return self.db.fetch_all(query, params)
        except ValueError as e:
            print(f'Error getting supplier payment by id: {e}')
            return None  

    def add_payment(self, pay_data, check_id=None, conn=None, commit=True):
     
            date = datetime.now().strftime("%Y-%m-%d")
            
            # registra un pago
            query = """
                INSERT INTO supplier_payment (supplier_id, receipt_number, amount, method, observation, operation_num, 
                origin, destination, check_id, check_number, bank, date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ? ,? ,?, ?, ?)
            """

            params = [
                pay_data['Supplier_id'],
                pay_data['Receipt_number'],
                str(pay_data['Amount']),
                pay_data['Method'],
                pay_data['Observation'],
                pay_data['Operation_num'],
                pay_data['Origin'],
                pay_data['Destination'],
                check_id,
                pay_data['Check_number'],
                pay_data['Bank'],
                date
            ]

            return self.db.execute_query(query, params, conn=conn, commit=commit)

    ## -- Agrega una relacion entre un pago y una compra -- ##
    def add_purchase_payment_relation(self, data, conn=None, commit=True):
        date = datetime.now().strftime("%Y-%m-%d")
        query = """
        INSERT INTO purchase_payment (purchase_id, payment_id, amount_applied, applied_at)
        VALUES (?, ?, ?, ?)
        """

        params = [
            data['Purchase_id'],
            data['Payment_id'],
            str(data['Amount_applied']),
            date
        ]

        self.db.execute_query(query, params, conn=conn, commit=commit)

    ## -- Obtiene las compras asociadas a un pago-- ##
    def get_purchase_payment_relation(self, payment_id):
        try:
            query = """
            SELECT purchase_id, amount_applied, applied_at FROM purchase_payment 
            WHERE payment_id = ?
            """

            return self.db.fetch_all(query, (payment_id, ))
        except ValueError as e:
            print(f'Error al obtener las compras asociadas a este pago {e}')
            return None

    ## -- Transaccion que registra un pago -- ##
    def register_payment_and_set_relation(self, pay_data, purchase_id=None):
        try:
            conn = self.db.get_connection()

            # Iniciar transacción
            conn.execute("BEGIN")

            payment_id = self.add_payment(pay_data, conn=conn, commit=False)
            total_amount = pay_data['Amount']

            if purchase_id is not None:
                # El pago aplica a una compra 

                # Datos de la compra
                purchase_data = self.purchase.get_purchase_by_id(purchase_id.get())

                # Nueva Deuda
                debt = Decimal(purchase_data[9])
                new_debt = debt - total_amount

                # Documento asociado
                doc_type = purchase_data[2]

                if doc_type == 'REMITO':
                    id = purchase_data[4]
                
                else:
                    id = purchase_data[3]

                # normalizacion
                new_debt = norm_to_2_dec(new_debt)

                # cambios en la compra
                self.purchase.set_new_debt_purchase(purchase_id.get(), id, doc_type, new_debt, conn=conn, commit=False)
                
                params = {
                    'Purchase_id': purchase_id.get(),
                    'Payment_id': payment_id,
                    'Amount_applied': total_amount
                }
                
                # agrega una relacion entre un pago y una venta
                self.add_purchase_payment_relation(params, conn=conn, commit=False)

            else:
                # El pago aplica a mas de una compra
                purchases = self.purchase.get_all_purchases_without_paying()

                for p in purchases:
                    print(f'Monto: {total_amount}')

                    # Si ya no queda monto para aplicar, cortar el ciclo
                    if total_amount <= Decimal('0.00'):
                        break

                    # Saldo pendiente de la compra actual
                    debt = Decimal(p[10])

                    if debt <= total_amount:
                        # monto restante
                        total_amount = norm_to_2_dec(total_amount - debt)

                        # monto del pago 
                        amount_in_pay = debt

                        # saldo deuda actualizado
                        new_debt = Decimal('0.00')
                    else:
                        # Nuevo saldo pendiente
                        new_debt = debt - total_amount

                        # monto del pago 
                        amount_in_pay = total_amount

                        # monto restante
                        total_amount = Decimal('0.00')

                    # Documento asociado
                    doc_type = p[3]

                    if doc_type == 'REMITO':
                        id = p[5]
                    
                    else:
                        id = p[4]

                    # normalizacion
                    new_debt = norm_to_2_dec(new_debt)

                    #cambios en la compra
                    self.purchase.set_new_debt_purchase(p[0], id, doc_type, new_debt, conn=conn, commit=False)

                    params = {
                        'Purchase_id': p[0],
                        'Payment_id': payment_id,
                        'Amount_applied': amount_in_pay
                    }
                    
                    self.add_purchase_payment_relation(params, conn=conn, commit=False)

            self.purchase.update_last_debt_update(pay_data['Supplier_id'], conn=conn, commit=False)

            conn.commit()

        except Exception as e:
            conn.rollback()
            print(f'Hubo un error {e}')
            return False
        
        finally:
            conn.close() 
            return True    
        
    ## -- Obtiene los pagos a un proveedor vinculados con un cheque -- ##
    def get_supplier_payments_by_check(self, check_id, conn=None):
        query = """
            SELECT id
            FROM supplier_payment
            WHERE check_id = ? AND valid = 1
        """
        return self.db.fetch_all(query, (check_id,), conn=conn)
    
    ## -- Obtiene las compras afectadas por un pago en particular -- ##
    def get_purchases_affected_by_payment(self, supplier_payment_id, conn=None):
        query = """
            SELECT purchase_id, amount_applied
            FROM purchase_payment
            WHERE payment_id = ?
        """
        return self.db.fetch_all(query, (supplier_payment_id,), conn=conn)
    
    def revert_purchase_pending(self, purchase_id, amount_applied, conn=None, commit=True):
        # Obtener pending actual
        row = self.db.fetch_one(
            "SELECT pending, document_type, invoice_id, receipt_id FROM purchase WHERE id = ?",
            (purchase_id,), conn=conn
        )
        if not row:
            return
        
        current_pending, doc_type, invoice_id, receipt_id = row
        
        new_pending = norm_to_2_dec(Decimal(current_pending) + Decimal(amount_applied))
        
        # reutilizar set_new_debt_purchase
        doc_id = receipt_id if doc_type == 'REMITO' else invoice_id
        self.purchase.set_new_debt_purchase(purchase_id, doc_id, doc_type, new_pending, conn=conn, commit=commit)

    ## -- Cancela Registros de pago a un proveedor asociados a un cheque -- ##
    def cancel_check_supplier_payments(self, check_id, conn=None, commit=True):
        # Pagos vinculados al cheque
        payments = self.get_supplier_payments_by_check(check_id, conn=conn)
        print(f'payments: {len(payments)}')

        if not payments:
            return
        
        for pay_id in payments:
            # Por cada pago se obtienen las compras afectadas
            purchases = self.get_purchases_affected_by_payment(pay_id, conn=conn)

            for purchase_id, amount_applied in purchases:
                # Se revierte el pendiente de cada compra
                self.revert_purchase_pending(purchase_id, amount_applied, conn=conn, commit=commit)

            # Se eliminan las relacionas que involucran el pago invalido
            self.db.execute_query(
                "DELETE FROM purchase_payment WHERE payment_id = ?",
                (pay_id,), conn=conn, commit=False
            )

            # Se setea el pago como invalido
            self.db.execute_query(
                "UPDATE supplier_payment SET valid = 0 WHERE id = ?",
                (pay_id,), conn=conn, commit=False
            )