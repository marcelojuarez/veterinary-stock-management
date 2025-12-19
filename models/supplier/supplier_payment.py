# models/supplier/supplier_payments.py

from datetime import datetime
from .supplier_purchase import SupplierPurchase

class SupplierPayment():
    def __init__(self, db):
        self.db = db
        self.purchase = SupplierPurchase(db)

    def get_payment_by_id(self, payment_id):
        try:
            query="""
            SELECT * 
            FROM supplier_payment 
            WHERE id = ? 
            """
            return self.db.fetch_one(query, (payment_id))
        except ValueError as e:
            print(f'Error getting supplier supplier_payment by cuit: {e}')
            return None

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
        
    def get_all_payment_of_supplier(self, supplier_id):
        try:
            query = """
            SELECT * FROM supplier_payment 
            WHERE supplier_id = ? ORDER BY date DESC
            """
            return self.db.fetch_all(query, (supplier_id,))            
        except ValueError as e:
            print(f'Error getting supplier payment by id: {e}')
            return None    

    def add_purchase_payment_relation(self, data, conn=None, commit=True):
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
        INSERT INTO purchase_payment (purchase_id, payment_id, amount_applied, applied_at)
        VALUES (?, ?, ?, ?)
        """

        params = [
            data['Purchase_id'],
            data['Payment_id'],
            data['Amount_applied'],
            date
        ]

        self.db.execute_query(query, params, conn=conn, commit=commit)

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

    def register_payment(self, pay_data, purchase_id=None):
        try:
            conn = self.db.get_connection()

            # Iniciar transacción
            conn.execute("BEGIN")

            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            query = """
                INSERT INTO supplier_payment (supplier_id, receipt_number, amount, method, observation, operation_num, 
                origin, destination, check_number, bank, date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ? ,? ,?, ?)
            """

            params = [
                pay_data['Supplier_id'],
                pay_data['Receipt_number'],
                pay_data['Amount'],
                pay_data['Method'],
                pay_data['Observation'],
                pay_data['Operation_num'],
                pay_data['Origin'],
                pay_data['Destination'],
                pay_data['Check_number'],
                pay_data['Bank'],
                date
            ]

            payment_id = self.db.execute_query(query, params, conn=conn, commit=False)
            rest_amount = pay_data['Amount']

            if purchase_id is not None:
                # El pago aplica a una compra 

                # Datos de la compra
                purchase_data = self.purchase.get_purchase_by_id(purchase_id.get())

                # Nueva Deuda
                debt = purchase_data[9]
                new_debt = debt - rest_amount

                # Documento asociado
                doc_type = purchase_data[2]

                if doc_type == 'REMITO':
                    id = purchase_data[4]
                
                else:
                    id = purchase_data[3]

                # cambios en la compra
                self.purchase.set_new_debt_purchase(purchase_id.get(), id, doc_type, new_debt, conn=conn, commit=False)
                
                params = {
                    'Purchase_id': purchase_id.get(),
                    'Payment_id': payment_id,
                    'Amount_applied': rest_amount
                }
                
                self.add_purchase_payment_relation(params, conn=conn, commit=False)

            else:
                print('Mas de una compra')
                purchases = self.purchase.get_all_purchases_without_paying()

                for p in purchases:
                    print(f'Monto: {rest_amount}')

                    # Si ya no queda monto para aplicar, cortar el ciclo
                    if rest_amount <= 0:
                        break

                    # Saldo pendiente de la compra actual
                    debt = p[9]

                    if debt - rest_amount <= 0.0:
                        # monto restante
                        rest_amount = rest_amount - debt

                        # monto del pago 
                        amount = debt

                        # saldo deuda actualizado
                        new_debt = 0
                    else:
                        # Nuevo saldo pendiente
                        new_debt = debt - rest_amount
                        amount = rest_amount
                        rest_amount = 0

                    # Documento asociado
                    doc_type = p[2]

                    if doc_type == 'REMITO':
                        id = p[4]
                    
                    else:
                        id = p[3]

                    #cambios en la compra
                    self.purchase.set_new_debt_purchase(p[0], id, doc_type, new_debt, conn=conn, commit=False)

                    params = {
                        'Purchase_id': p[0],
                        'Payment_id': payment_id,
                        'Amount_applied': amount
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
        