from views.view_helpers import show_success, show_error, show_warning, close_win
from datetime import datetime
from utils.utils import normalize_string_to_dec, traditional_to_iso
from decimal import Decimal

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

    ## -- Agrega una nueva factura correspondiente a un proveedor -- ##
    def add_new_invoice(self, win, parent):

        try:
            data = self.form_view.get_invoice_form_data()
            supplier_data = self.model.core.find_supplier_by_cuit(data['supplier_cuit'])
            
            if not self.validate_invoice_data(data):
                win.focus_force()
                return
            
            expiration_date = traditional_to_iso(data['expiration_date'])
            discount = normalize_string_to_dec(data['discount'])

            invoice_params = {
                'supplier_id': supplier_data[0],
                'invoice_id': data['invoice_id'],
                'invoice_type': data['invoice_type'],
                'expiration_date': expiration_date,
                'state': data['state'],
                'observations': data['observations'],
                'orig_subtotal': data['subtotal'],
                'discount': discount,
                'discount_amount': '0.00',
                'subtotal_w_discount': data['subtotal'],
                'iva': data['iva'],
                'total': data['total']
            }

            purchase_params = {
                'supplier_id': supplier_data[0],
                'doc_type': "FACTURA",
                'expiration_date': expiration_date,
                'state': data['state'],
                'observations': data['observations'],
                'pending': data['total'], 
                'total': data['total']
            }

            self.model.purchase.create_invoice_and_purchase(invoice_params, purchase_params)
            self.purchase_view.load_purchases(True)
            close_win(win, parent, self.form_view.clear_invoice_form())

        except ValueError as e:
            show_error(f'Error en los datos: {e}')
        except Exception as e:
            show_error(f'Error al registrar factura: {e}')

    ## -- Valida los datos del formulario correspondiente a la factura -- 
    @classmethod
    def validate_invoice_data(cls, data):
        required_files = {
            'invoice_id': 'Numero de Factura',
            'invoice_type': 'Tipo de Factura',
            'expiration_date': 'Fecha de vencimiento',
            'state': 'Estado',
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
        
        if not cls.is_decimal(data['discount']):
            show_error('Error. Formato incorrecto en el descuento.')
            return False

        discount = normalize_string_to_dec(data['discount'])

        if discount < Decimal('0.00') \
        or discount > Decimal('99.00'):
            show_error('Error. El porcentaje de descuento debe rondar entre 0 y 99 %')
            return False

        return True

    ## -- Valida si una fecha esta en el formato correcto -- ##
    @staticmethod    
    def is_valid_date(date):
        try:
            datetime.strptime(date, "%d/%m/%Y")
            return True
        except:
            return False

    ## -- Valida si un dato es un decimal o se puede normalizar -- ##
    @staticmethod
    def is_decimal(value):
        value = normalize_string_to_dec(value)
        if value is None:
            return False
        else:    
            return True
        