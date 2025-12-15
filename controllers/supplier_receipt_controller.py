from views.view_helpers import close_win, show_warning, show_error
from datetime import datetime

class SupplierReceiptController():
    def __init__(self, form_view, purchase_view, supplier_view, model):
        self.form_view = form_view 
        self.purchase_view = purchase_view 
        self.supplier_view = supplier_view
        self.model = supplier_view.model

    def add_new_receipt(self, win, parent):
        try:
            data = self.form_view.get_receipt_form_data()
            print(data)

            if not self.validate_date(data):
                return

            supplier_data = self.model.core.find_supplier_by_cuit(data['supplier_cuit'])
            receipt_params = {
                'supplier_id': supplier_data[0],
                'receipt_id': data['receipt_id'],
                'expiration_date': data['expiration_date'],
                'observations': data['observations'],
                'state': data['state'],
                'total': float(data['total']), 
            }

            if data['state'] == 'PAGADA':
                pending = 0
            else:
                pending = float(data['total'])

            purchase_params = {
                'supplier_id': supplier_data[0],
                'doc_type': "REMITO",
                'expiration_date': data['expiration_date'],
                'state': data['state'],
                'observations': data['observations'],
                'pending' : pending, 
                'total': float(data['total']), 
            }

            result = self.model.purchase.create_receipt_and_purchase(receipt_params, purchase_params)
            self.purchase_view.load_purchases(True)
            close_win(win, parent, self.form_view.clear_receipt_form())
            if result:
                self.supplier_view.controller.refresh_supplier_table()
            
        except ValueError as e:
            show_error(f'Error en los datos: {e}')
        except Exception as e:
            show_error(f'Error al registrar remito: {e}')

    @classmethod
    def validate_date(cls, data):
        required_files = {
            'receipt_id': 'Numero de Recibo',
            'expiration_date': 'Fecha de vencimiento',
            'observations': 'Observaciones',
            'total': 'Total'
        }
        
        for field, label in required_files.items():
            if not data[field]:
                show_error(f'Por favor complete el campo: "{label}"')
                return False
            
        if not cls.is_valid_date(data['expiration_date']):
            show_error('Por favor coloque la fecha en formato dd/mm/yyyy')
            return False
        
        if not cls._is_float(data['total']):
            show_error('Por favor el monto total debe ser un valor numerico')
            return False
        
        return True

    @staticmethod    
    def is_valid_date(date):
        try:
            datetime.strptime(date, "%d/%m/%Y")
            return True
        except:
            return False

    @staticmethod
    def _is_float(value):
        try: float(value); return True
        except: return False
