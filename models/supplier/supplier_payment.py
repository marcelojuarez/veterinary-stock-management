# models/supplier/supplier_payments.py

import logging
from datetime import datetime
from utils.utils import norm_to_2_dec
from decimal import Decimal

logger = logging.getLogger(__name__)

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
            return self.db.fetch_one(query, (payment_id,))
        except ValueError as e:
            logger.error("Error getting supplier payment by cuit: %s", e)
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
            logger.error("Error getting transfer data by supplier_payment id: %s", e)
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
            logger.error("Error getting transfer data by payment id: %s", e)
            return None
    
    ## -- Obtiene todos los pagos asociados o no, a un cuit-- ##
    def get_all_payments(self, supplier_id=None):
        try:
            query = """
            SELECT supplier_payment.id, supplier.name, supplier.cuit, supplier_payment.receipt_number, supplier_payment.amount,
            supplier_payment.method, supplier_payment.observation, supplier_payment.operation_num, supplier_payment.origin,
            supplier_payment.destination, supplier_payment.check_number, supplier_payment.bank, supplier_payment.date,
            supplier_payment.created_at
            FROM supplier_payment
            JOIN supplier ON supplier_payment.supplier_id = supplier.id
            WHERE (? IS NULL OR supplier.id = ?) AND valid = ?
            ORDER BY supplier_payment.created_at DESC, supplier_payment.id DESC
            """
            params = [
               supplier_id,
               supplier_id,
               1
            ]

            return self.db.fetch_all(query, params)
        except ValueError as e:
            logger.error("Error getting supplier payment by id: %s", e)
            return None  

    def add_payment(self, pay_data, check_id=None, conn=None, commit=True):
     
            date = datetime.now().strftime("%Y-%m-%d")
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # ← NUEVO: Hora exacta
            
            # registra un pago
            query = """
                INSERT INTO supplier_payment (supplier_id, receipt_number, amount, method, observation, operation_num, 
                origin, destination, check_id, check_number, bank, date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                date,
                created_at  # ← NUEVO
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
            logger.error("Error al obtener compras asociadas al pago: %s", e)
            return None

    ## -- Transaccion que registra un pago -- ##
    def register_payment_and_set_relation(self, pay_data, check_id=None, conn=None, purchase_id=None):
            payment_id = self.add_payment(pay_data, check_id=check_id, conn=conn, commit=False)
            total_amount = pay_data['Amount']

            if purchase_id is not None:
                # El pago aplica a una compra 

                # Datos de la compra
                purchase_data = self.purchase.get_purchase_by_id(purchase_id)

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
                self.purchase.set_new_debt_purchase(purchase_id, id, doc_type, new_debt, conn=conn, commit=False)

                params = {
                    'Purchase_id': purchase_id,
                    'Payment_id': payment_id,
                    'Amount_applied': total_amount
                }
                
                # agrega una relacion entre un pago y una venta
                self.add_purchase_payment_relation(params, conn=conn, commit=False)

            else:
                # El pago aplica a mas de una compra
                purchases = self.purchase.get_all_purchases_without_paying(pay_data['Supplier_id'])

                for p in purchases:

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
        
    def get_supplier_id_by_check(self, check_id):
        query = """
            SELECT supplier_id FROM supplier_payment 
            WHERE check_id = ? AND valid = 0
        """
        result = self.db.fetch_one(query, (check_id,))
        return result[0] if result else None

    ## -- Cancela Cheques endosados a un proveedor -- ##
    ## -- Cancela Saldo a favor por cheques -- ##
    ## -- Restablece estados y pendiente de las compras -- ##
    def cancel_check_supplier_payments(self, check_id, conn=None, commit=True):
        try:
            # Obtener el payment_id antes de invalidar
            query = """
            SELECT id FROM supplier_payment
            WHERE check_id = ? AND valid = ?
            """
            id = self.db.fetch_one(query, ( check_id, 1), conn=conn)

            if not id:
                return

            payment_id = id[0]
            print(f'payment_id of cancel payment: {payment_id}')

            # Reestablecer pendiente y estado de las compras asociadas al pago 
            ## Obtener compras afectadas por el pago 
            query = """
            SELECT purchase_id, amount_applied FROM purchase_payment 
            WHERE valid = ? AND payment_id = ?
            """

            for purchase_id, amount_applied in self.db.fetch_all(query, (1, payment_id), conn=conn):
                purchase_pending = self.db.fetch_one("SELECT pending FROM purchase WHERE id = ?",
                                                     (purchase_id, ), conn=conn)
                old_pending = Decimal(purchase_pending[0])
                new_pending = old_pending + Decimal(amount_applied)

                ## Se actualiza la compra
                query = """
                UPDATE purchase
                SET
                    pending = ?,
                    state = 'PENDIENTE'
                WHERE id = ?
                """
                self.db.execute_query(query, (str(new_pending), purchase_id), conn=conn, commit=commit)

            # Invalidar filas en purchase_payment(relacion de pago y compra)
            query = """ 
            UPDATE purchase_payment 
            SET 
                valid = 0
            WHERE payment_id = ?
            """                
            self.db.execute_query(query, (payment_id,), conn=conn, commit=commit)

            # Cancelar pago asociado a cheque
            query = """
            UPDATE supplier_payment
            SET
                valid = ?
            WHERE id = ?
            """
            self.db.execute_query(query, (0, payment_id), conn=conn, commit=commit)

            # Cancelar saldo a favor asociado al cheque
            query = """
            UPDATE supplier_credit_movements
            SET
                valid = ?
            WHERE check_id = ?
            """
            self.db.execute_query(query, (0, check_id), conn=conn, commit=commit)

        except Exception as e:
            raise RuntimeError(f'Error al cancelar pagos asociados a un cheque: {e}') from e