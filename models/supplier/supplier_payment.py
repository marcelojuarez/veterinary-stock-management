# models/supplier/supplier_payments.py

from datetime import datetime
from .supplier_purchase import SupplierPurchase
from utils.utils import normalize_to_2_decimals
from decimal import Decimal

class SupplierPayment():
    def __init__(self, db):
        self.db = db
        self.purchase = SupplierPurchase(db)

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
    def get_all_payments(self, cuit=None):
        try:
            query = """
            SELECT supplier_payment.id, supplier.cuit, supplier_payment.receipt_number, supplier_payment.amount,
            supplier_payment.method, supplier_payment.observation, supplier_payment.operation_num, supplier_payment.origin, 
            supplier_payment.destination, supplier_payment.check_number, supplier_payment.bank, supplier_payment.date
            FROM supplier_payment 
            JOIN supplier ON supplier_payment.supplier_id = supplier.id
            WHERE (? IS NULL OR supplier.cuit = ?)
            ORDER BY supplier_payment.date DESC
            """
            params = [
               cuit,
               cuit
            ]

            return self.db.fetch_all(query, params)
        except ValueError as e:
            print(f'Error getting supplier payment by id: {e}')
            return None  

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
    def register_payment(self, pay_data, purchase_id=None):
        try:
            conn = self.db.get_connection()

            # Iniciar transacción
            conn.execute("BEGIN")

            date = datetime.now().strftime("%Y-%m-%d")
            
            # registra un pago
            query = """
                INSERT INTO supplier_payment (supplier_id, receipt_number, amount, method, observation, operation_num, 
                origin, destination, check_number, bank, date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ? ,? ,?, ?)
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
                pay_data['Check_number'],
                pay_data['Bank'],
                date
            ]

            payment_id = self.db.execute_query(query, params, conn=conn, commit=False)
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
                new_debt = normalize_to_2_decimals(new_debt)

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
                    debt = Decimal(p[9])

                    if debt <= total_amount:
                        # monto restante
                        total_amount = normalize_to_2_decimals(total_amount - debt)

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
                    doc_type = p[2]

                    if doc_type == 'REMITO':
                        id = p[4]
                    
                    else:
                        id = p[3]

                    # normalizacion
                    new_debt = normalize_to_2_decimals(new_debt)

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
        