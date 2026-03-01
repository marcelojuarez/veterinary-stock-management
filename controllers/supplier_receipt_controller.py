from datetime import datetime
from utils.utils import traditional_to_iso
from utils.view_helpers import close_win, show_error

class SupplierReceiptController():
    def __init__(self, supplier_model):
        self.form_view = None 
        self.purchase_view = None 
        self.supplier_model = supplier_model

    def set_form_view(self, form_view):
        self.form_view = form_view

    def set_purchase_view(self, purchase_view):
        self.purchase_view = purchase_view

    ## -- Agrega un nuevo remito de un proveedor -- ##
    def add_new_receipt(self, win, parent):
        try:
            data = self.form_view.get_receipt_form_data()
            supplier_data = self.supplier_model.core.find_supplier_by_cuit(data['supplier_cuit'])

            if not self.validate_receipt_data(data):
                return

            state = 'BORRADOR'

            receipt_params = {
                'supplier_id': supplier_data[0],
                'receipt_id': data['receipt_id'],
                'date': traditional_to_iso(data['date']),
                'expiration_date': traditional_to_iso(data['expiration_date']),
                'observations': data['observations'],
                'state': state,
                'total': data['total']
            }

            purchase_params = {
                'supplier_id': supplier_data[0],
                'doc_type': "REMITO",
                'date': traditional_to_iso(data['date']),
                'expiration_date': traditional_to_iso(data['expiration_date']),
                'state': state,
                'observations': data['observations'],
                'pending' : data['total'], 
                'total': data['total'], 
            }

            self.supplier_model.purchase.create_receipt_and_purchase(receipt_params, purchase_params)
            self.purchase_view.load_purchases(True)
            close_win(win, parent)
            
        except ValueError as e:
            show_error(f'Error en los datos: {e}')
        except Exception as e:
            show_error(f'Error al registrar remito: {e}')

    ## -- Valida los datos del recibo -- ##
    @classmethod
    def validate_receipt_data(cls, data):
        required_files = {
            'supplier_cuit': 'Cuit Proveedor',
            'receipt_id': 'Numero de Recibo',
            'date': 'Fecha',
            'expiration_date': 'Fecha de vencimiento',
            'total': 'Total'
        }
        
        for field, label in required_files.items():
            if not data[field]:
                show_error(f'Por favor complete el campo: "{label}"')
                return False

        if not cls.is_valid_date(data['date']):
            show_error('Por favor coloque la fecha en formato dd/mm/yyyy')
            return False        

        if not cls.is_valid_date(data['expiration_date']):
            show_error('Por favor coloque la fecha en formato dd/mm/yyyy')
            return False
        
        return True

    ## -- Verifica si una fecha dada esta en el formato valido -- ##
    @staticmethod    
    def is_valid_date(date):
        try:
            datetime.strptime(date, "%d/%m/%Y")
            return True
        except:
            return False

