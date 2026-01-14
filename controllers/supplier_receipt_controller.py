from views.view_helpers import close_win, show_warning, show_error
from datetime import datetime

class SupplierReceiptController():
    def __init__(self):
        self.form_view = None 
        self.purchase_view = None 
        self.model = None

    def set_form_view(self, form_view):
        self.form_view = form_view

    def set_purchase_view(self, purchase_view):
        self.purchase_view = purchase_view

    def set_model(self, model):
        self.model = model

    def convert_string_to_date_formated(self, date):
        # convierto el string a obj tipo date
        date_formated = datetime.strptime(date, "%d/%m/%Y").date()
        # formateo el obj
        return date_formated.strftime("%Y-%m-%d")

    def add_new_receipt(self, win, parent):
        try:
            data = self.form_view.get_receipt_form_data()
            supplier_data = self.model.core.find_supplier_by_cuit(data['supplier_cuit'])
            print(data)

            if not self.validate_date(data):
                return
            
            expiration_date = self.convert_string_to_date_formated(data['expiration_date'])

            receipt_params = {
                'supplier_id': supplier_data[0],
                'receipt_id': data['receipt_id'],
                'expiration_date': expiration_date,
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
                'expiration_date': expiration_date,
                'state': data['state'],
                'observations': data['observations'],
                'pending' : pending, 
                'total': float(data['total']), 
            }

            self.model.purchase.create_receipt_and_purchase(receipt_params, purchase_params)
            self.purchase_view.load_purchases(True)
            close_win(win, parent, self.form_view.clear_receipt_form())
            
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
