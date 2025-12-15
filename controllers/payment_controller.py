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
            if not self.validate_data(supplier_data[0], payment_data):
                return 
            
            amount = float(payment_data['amount'])

            if purchase_id:
                print('Rama purchase id')

                purchase_data = self.model.get_purchase_by_id(purchase_id)
                print(f'Purchase Data: {purchase_data}')
                debt = purchase_data[9]
                
                if not self.validate_debt(amount, debt):
                    self.view.amount_var.set(debt)
                    return

                last_debt = debt - amount

                if last_debt == 0:
                    if purchase_data[2] == 'REMITO':
                    
                        self.model.purchase.set_paid_purchase(
                            purchase_id=purchase_id, 
                            id=purchase_data[4],
                            doc_type=purchase_data[2]
                        )
                        
                    else:

                        self.model.purchase.set_paid_purchase(
                            purchase_id=purchase_id,  
                            id=purchase_data[4],
                            doc_type=purchase_data[2]
                        )

            else:
                print('Debo aplicar ese pago a todas las facturas')
                
                purchases = self.model.purchase.get_all_purchases_without_paying(selected)
                print(purchases)

            # new_debt = debt-amount

            # data = {
            #     'Id_supplier' : supplier_data[0],
            #     'Receipt_number': payment_data['receipt_number'],
            #     'Amount': amount,
            #     'Method': payment_data['method'],
            #     'Observation': payment_data['observation'],
            #     'Operation_num': payment_data['operation_num'],
            #     'Origin': payment_data['origin'],
            #     'Destination': payment_data['destination'],
            #     'Check_number': payment_data['check_number'],
            #     'Bank': payment_data['bank'],
            #     'previous_debt': debt,
            #     'subsequent_debt': new_debt
            # }

            # self.model.update_debt(data['Id_supplier'])
            #self.model.add_new_payment(data['Id_supplier'], data)
            # self.view.clear_form_payment()
            # self.pay_win.load_payment_movement(data['Id_supplier'], selected)

            # if purchase_id:

            # else:
            # # update debt


            # if new_debt == 0:
            #     self.model.mark_purchase_as_paid(purchase_id)


            close_win(win, parent)

        except Exception as e:
            show_error(f"Error al registrar pago: {e}")

    def purchase_pay_management(self, purchase_id):
        pass
    
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