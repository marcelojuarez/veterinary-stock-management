from datetime import datetime
from utils.utils import normalize_decimal, traditional_to_iso
from views.view_helpers import close_win, show_error

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
        # formateo el obj a un string nuevamente
        return date_formated.strftime("%Y-%m-%d")

    def add_new_receipt(self, win, parent):
        try:
            data = self.form_view.get_receipt_form_data()
            supplier_data = self.model.core.find_supplier_by_cuit(data['supplier_cuit'])

            if not self.validate_date(data):
                return
            
            expiration_date = traditional_to_iso(data['expiration_date'])

            receipt_params = {
                'supplier_id': supplier_data[0],
                'receipt_id': data['receipt_id'],
                'expiration_date': expiration_date,
                'observations': data['observations'],
                'state': data['state'],
                'total': data['total']
            }

            purchase_params = {
                'supplier_id': supplier_data[0],
                'doc_type': "REMITO",
                'expiration_date': expiration_date,
                'state': data['state'],
                'observations': data['observations'],
                'pending' : data['total'], 
                'total': data['total'], 
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
            'total': 'Total'
        }
        
        for field, label in required_files.items():
            if not data[field]:
                show_error(f'Por favor complete el campo: "{label}"')
                return False
            
        if not cls.is_valid_date(data['expiration_date']):
            show_error('Por favor coloque la fecha en formato dd/mm/yyyy')
            return False
        
        return True

    @staticmethod    
    def is_valid_date(date):
        try:
            datetime.strptime(date, "%d/%m/%Y")
            return True
        except:
            return False

