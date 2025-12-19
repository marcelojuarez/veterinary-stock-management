import tkinter as tk
from views.view_helpers import show_warning, show_error, close_win


class PaymentController():
    def __init__(self, view, pay_win, model):
        self.model = model
        self.view = view
        self.pay_win = pay_win

    """
    Permitir pagar el monto de una compra
    Permitir registrar un monto que afecta a las compras que mas proximo se vencen
    """

    def register_payment(self, supplier_var, win, parent, purchase_id):

        try:

            payment_data = self.view.get_payment_data()
            selected = supplier_var.get() # cuit proveedor

            if not selected:
               show_warning("Seleccione un proveedor")
               return
            
            supplier_data = self.model.core.find_supplier_by_cuit(selected)
            if not self.validate_data(payment_data):
                return 
            
            amount = float(payment_data['amount'])

            if purchase_id is not None:
                # Datos de la compra
                purchase = self.model.purchase.get_purchase_by_id(purchase_id.get())
                
                # Deuda actual de la compra
                debt = purchase[9]
                
                # Chequeo si quiere pagar de mas
                if not self.validate_debt(amount, debt, False):
                    self.view.amount_var.set(debt)
                    return

            else:
                
                purchases = self.model.purchase.get_all_purchases_without_paying(selected)

                for p in purchases:
                    print(p)

                total_debt = self.model.purchase.get_debt_of_supplier(selected)[0]

                # Chequeo si quiere pagar de mas
                if not self.validate_debt(amount, total_debt, True):
                    self.view.amount_var.set(total_debt)
                    return

            data = {
                'Supplier_id' : supplier_data[0],
                'Receipt_number': payment_data['receipt_number'],
                'Amount': amount,
                'Method': payment_data['method'],
                'Observation': payment_data['observation'],
                'Operation_num': payment_data['operation_num'],
                'Origin': payment_data['origin'],
                'Destination': payment_data['destination'],
                'Check_number': payment_data['check_number'],
                'Bank': payment_data['bank'],
            }

            result = self.model.payment.register_payment(data, purchase_id)
            
            if result:
                self.pay_win.load_payment_movement(data['Supplier_id'], selected)
                self.pay_win.load_purchase_history(True)

            close_win(win, parent)

        except Exception as e:
            show_error(f"Error al registrar pago: {e}")

    def purchase_pay_management(self, purchase_id):
        pass
    
    @classmethod
    def validate_data(cls, data):

        required_fields = {
            'amount': 'Monto', 
            'method': 'Metodo', 
            'receipt_number': 'Numero de recibo', 
            'observation': 'Observaciones'
        }

        for field, label in required_fields.items():
             if not data[field]:
                 show_warning(f'Por favor complete el campo "{label}"')
                 return False

        # validacion del monto
        if not cls._is_float(data['amount']):
            show_warning('Monto invalido')
            return False

        # validacion segun el metodo de pago
        if data['method'] == 'TRANSFERENCIA':
            required_fields = {
                'operation_num': 'Numero de operacion',
                'origin': 'CBU/Alias(origen)',  
                'destination': 'CBU/Alias(destino)'
            }

            for field, label in required_fields.items():
                if not data[field]:
                    show_warning(f'Por favor complete el campo "{label}"')
                    return False
                

        elif data['method'] == 'CHEQUE':
            required_fields = {
                'check_number': 'Numero de cheque', 
                'bank': 'Banco'
            }

            for field, label in required_fields.items():
                if not data[field]:
                    show_warning(f'Por favor complete el campo "{label}"')
                    return False
            
            if not cls._is_str(data['bank']):
                show_warning('Nombre de banco invalido')
                return False

        return True


    def validate_debt(self, amount, debt, total_debt):
        if total_debt:
            msg = 'La deuda Total es:'
        else:
            msg = 'La deuda de la compra es: '

        if amount > debt:
            msg = f'ERROR:.\n'\
                  f'{msg} ${debt}\n'\
                  f'El monto que intenta abonar es superior: ${amount}'
            show_warning(msg)
            return False
        
        return True

    @staticmethod
    def _is_float(value):
        try: float(value); return True
        except: return False

    @staticmethod
    def _is_int(value):
        try: int(value); return True
        except: return False 

    @staticmethod
    def _is_str(value):
        try: str(value); return True
        except: return False            