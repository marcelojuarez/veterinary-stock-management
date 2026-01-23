from views.view_helpers import show_success, show_error, show_warning, close_win
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

class SupplierInvoiceController():
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

    def add_new_invoice(self, win, parent):

        try:
            data = self.form_view.get_invoice_form_data()
            supplier_data = self.model.core.find_supplier_by_cuit(data['supplier_cuit'])
            print(data)
            
            if not self.validate_date(data):
                return
            
            expiration_date = self.convert_string_to_date_formated(data['expiration_date'])
            total = Decimal(data['total']).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            invoice_params = {
                'supplier_id': supplier_data[0],
                'invoice_id': data['invoice_id'],
                'invoice_type': data['invoice_type'],
                'expiration_date': expiration_date,
                'state': data['state'],
                'observations': data['observations'],
                'subtotal': data['subtotal'],
                'iva': data['iva'],
                'discount': data['discount'],
                'total': total
            }

            if data['state'] == 'PAGADA':
                pending = 0
            else:
                pending = Decimal(data['total']).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            purchase_params = {
                'supplier_id': supplier_data[0],
                'doc_type': "FACTURA",
                'expiration_date': expiration_date,
                'state': data['state'],
                'observations': data['observations'],
                'pending': pending, 
                'total': total
            }

            self.model.purchase.create_invoice_and_purchase(invoice_params, purchase_params)
            self.purchase_view.load_purchases(True)
            close_win(win, parent, self.form_view.clear_invoice_form())

        except ValueError as e:
            show_error(f'Error en los datos: {e}')
        except Exception as e:
            show_error(f'Error al registrar factura: {e}')

    @classmethod
    def validate_date(cls, data):
        required_files = {
            'invoice_id': 'Numero de Factura',
            'invoice_type': 'Tipo de Factura',
            'expiration_date': 'Fecha de vencimiento',
            'state': 'Estado',
            'observations': 'Observaciones',
            'subtotal': 'Subtotal',
            'iva': 'Iva',
            'discount': 'Descuento',
            'total': 'Total'
        }
        
        for field, label in required_files.items():
            if not data[field]:
                show_error(f'Por favor complete el campo: "{label}"')
                return False
            
        if not cls.is_valid_date(data['expiration_date']):
            show_error('Por favor coloque la fecha en formato dd/mm/yyyy')
            return False
        
        if not cls._is_decimal(data['subtotal']):
            show_error('Por favor el monto subtotal debe ser un valor numerico')
            return False
        
        if not cls._is_decimal(data['total']):
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
    def _is_decimal(value):
        try: Decimal(value); return True
        except: return False