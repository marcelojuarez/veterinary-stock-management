import tkinter as tk
from models.supplier import SupplierModel
from views.view_helpers import show_warning, show_error, close_win


class PaymentController():
    def __init__(self, view, pay_win):
        self.model = SupplierModel()
        self.view = view
        self.pay_win = pay_win

    def register_payment(self, supplier_var, win, parent):
        try:
            payment_data = self.view.get_payment_data()
            selected = supplier_var.get() # cuit proveedor
            if not selected:
               show_warning("Seleccione un proveedor")
               return
            
            supplier_data = self.model.find_supplier_by_cuit(selected)
            if not self.validate_data(supplier_data[0], payment_data):
                return 
            
            amount = float(payment_data['amount'])
            debt = supplier_data[6]

            if not self.validate_debt(amount, debt):
                return

            new_debt = debt-amount

            data = {
                'Id_supplier' : supplier_data[0],
                'Receipt_number': payment_data['receipt_number'],
                'Amount': amount,
                'Method': payment_data['method'],
                'Observation': payment_data['observation'],
                'Operation_num': payment_data['operation_num'],
                'Origin': payment_data['origin'],
                'Destination': payment_data['destination'],
                'Check_number': payment_data['check_number'],
                'Bank': payment_data['bank'],
                'previous_debt': debt,
                'subsequent_debt': new_debt
            }

            # update debt
            self.model.update_debt(data['Id_supplier'], new_debt)

            self.model.add_new_payment(data['Id_supplier'], data)
            self.view.clear_form_payment()
            self.pay_win.load_payment_movement(data['Id_supplier'], selected)
            close_win(win, parent)


        except Exception as e:
            show_error(f"Error al registrar pago: {e}")

    @classmethod
    def validate_data(cls, supplier_id, data):
        
        if supplier_id == "":
            show_warning("Por favor ingrese el CUIT asociado al proveedor")
            return False

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


    def validate_debt(self, amount, debt):
        if amount > debt:
            msg = f'ERROR:.\n'\
                  f'La deuda actual es: ${debt}\n'\
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