from decimal import Decimal
from utils.utils import string_to_2_dec
from utils.view_helpers import show_warning, show_error, close_win

class PaymentController():
    def __init__(self, supplier_model, event_bus, checks_model=None):
        self.supplier_model = supplier_model
        self.form_view = None
        self.pay_view = None
        self.event_bus = event_bus
        self.checks_model = checks_model

    def set_form_view(self, view):
        self.form_view = view

    def set_pay_view(self, pay_view):
        self.pay_view = pay_view        

    # Permitir pagar el monto de una compra
    # Permitir registrar un monto que afecta a las compras que mas proximo se vencen
    def register_payment(self, supplier_id, win, parent, purchase_id):

        try:

            payment_data = self.form_view.get_payment_data()

            if not supplier_id:
               show_warning("Seleccione un proveedor")
               return
            
            # se validan los datos de pago
            if not self.validate_data(payment_data):
                return 
            
            amount = string_to_2_dec(payment_data['amount'])

            if purchase_id is not None:
                ## Se paga una compra en concreto

                # Datos de la compra
                purchase = self.supplier_model.purchase.get_purchase_by_id(purchase_id.get())
                # Deuda actual de la compra
                debt = Decimal(purchase[9])
                
                # Chequeo si quiere pagar de mas
                if not self.validate_debt(amount, debt, False):
                    self.form_view.amount_var.set(debt)
                    return

            else:
                # Se pagan multiples compras 
                
                purchases = self.supplier_model.purchase.get_all_purchases_without_paying(supplier_id)

                for p in purchases:
                    print(p)

                total_debt = self.supplier_model.purchase.get_debt_of_supplier(supplier_id)

                # Se chequea si el monto es superior a la deuda
                if not self.validate_debt(amount, total_debt, True):
                    self.form_view.amount_var.set(str(total_debt))
                    return

            data = {
                'Supplier_id' : supplier_id,
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

            result = self.supplier_model.payment.register_payment(data, purchase_id)
            
            if result:
                # Si se pagó con un cheque de cartera, marcarlo como ENDOSADO
                check_id = payment_data.get('check_id')
                if check_id and self.checks_model:
                    try:
                        purchase_id_val = int(purchase_id.get()) if purchase_id else None
                        self.checks_model.update_status(
                            check_id, "ENDOSADO", purchase_id=purchase_id_val
                        )
                        self.event_bus.publish('refresh_checks', None)
                    except Exception as e:
                        print(f"[PaymentController] No se pudo endosar el cheque: {e}")

                self.pay_view.load_payment_movement(supplier_id)
                self.pay_view.load_purchase_history(True)
                self.event_bus.publish('refresh_supplier_table', None)

            close_win(win, parent)

        except Exception as e:
            show_error(f"Error al registrar pago: {e}")
    
    @classmethod
    def validate_data(cls, data):

        required_fields = {
            'amount': 'Monto', 
            'method': 'Metodo', 
            'receipt_number': 'Numero de recibo', 
        }

        for field, label in required_fields.items():
             if not data[field]:
                 show_warning(f'Por favor complete el campo "{label}"')
                 return False

        # validacion del monto
        if not cls._is_decimal(data['amount']):
            show_error('Error. Monto invalido')
            return False
        
        amount = string_to_2_dec(data['amount'])

        if amount <= Decimal('0.00'):
            show_error('Error. El monto debe ser un valor positivo')
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

    ## -- Valida el monto de pago -- ##
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

    ## -- Valida si un dato es un decimal o se puede normalizar -- ##
    @staticmethod
    def _is_decimal(value):
        value = string_to_2_dec(value)
        if value is None:
            return False
        else:    
            return True

    @staticmethod
    def _is_int(value):
        try: int(value); return True
        except: return False 

    @staticmethod
    def _is_str(value):
        try: str(value); return True
        except: return False