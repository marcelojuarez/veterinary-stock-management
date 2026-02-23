from decimal import Decimal
from datetime import datetime
from utils.utils import string_to_flex_dec, traditional_to_iso
from utils.view_helpers import show_success, show_error, show_warning, close_win

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

            iibb_per = string_to_flex_dec(data['iibb_per'])
            iva_per = string_to_flex_dec(data['iva_per'])
            discount = string_to_flex_dec(data['discount'])

            state = 'BORRADOR'

            invoice_params = {
                'supplier_id': supplier_data[0],
                'invoice_id': data['invoice_id'],
                'invoice_type': data['invoice_type'],
                'date': traditional_to_iso(data['date']),
                'expiration_date': traditional_to_iso(data['expiration_date']),
                's_iva_c': data['s_iva_c'],
                'discount': str(discount),
                'state': state,
                'observations': data['observations'],
                'pay_cond': data['pay_cond'],
                'pay_period': data['pay_period'],
                'orig_subtotal': data['subtotal'],
                'discount_amount': '0.00',
                'subtotal_w_discount': data['subtotal'],
                'iva': data['iva'],
                'total': data['total']
            }

            perception_parameters = self.prepare_perceptions_parameters(iibb_per, iva_per)

            purchase_params = {
                'supplier_id': supplier_data[0],
                'doc_type': "FACTURA",
                'date': traditional_to_iso(data['date']),
                'expiration_date': traditional_to_iso(data['expiration_date']),
                'state': state,
                'observations': data['observations'],
                'pending': data['total'], 
                'total': data['total']
            }

            self.model.purchase.create_invoice_and_purchase(invoice_params, perception_parameters, purchase_params)
            self.purchase_view.load_purchases(True)
            close_win(win, parent)

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
            'date': 'Fecha',
            'expiration_date': 'Fecha de vencimiento',
            's_iva_c': 'Cond. IVA Proveedor',
            'subtotal': 'Subtotal',
            'iva': 'Iva',
            'discount': 'Descuento',
            'iibb_per': 'Percepciones IIBB',
            'iva_per': 'Percepciones IVA',
            'total': 'Total',
        }
        
        for field, label in required_files.items():
            if not data[field]:
                show_error(f'Por favor complete el campo: "{label}"')
                return False
        
        ## Fecha de Vencimiento
        if not cls.is_valid_date(data['expiration_date']):
            show_error('Por favor coloque la fecha en formato dd/mm/yyyy')
            return False
        
        ## Percepcion IIBB
        if not cls.is_decimal(data['iibb_per']):
            show_error('Error. Formato incorrecto en la Percepcion IIBB')
            return False
        
        iibb_per = string_to_flex_dec(data['iibb_per'])

        if iibb_per < Decimal('0.00'):
            show_error('Error. El monto de Percepcion IIBB debe ser positivo')
            return False

        ## Percepcion IVA
        if not cls.is_decimal(data['iva_per']):
            show_error('Error. Formato incorrecto en la Percepcion IVA')
            return False

        iva_per = string_to_flex_dec(data['iva_per'])

        if iva_per < Decimal('0.00'):
            show_error('Error. El monto de Percepcion IVA debe ser positivo')
            return False

        ## Descuento
        if not cls.is_decimal(data['discount']):
            show_error('Error. Formato incorrecto en el descuento.')
            return False

        discount = string_to_flex_dec(data['discount'])

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
        value = string_to_flex_dec(value)
        if value is None:
            return False
        else:    
            return True
        
    def prepare_perceptions_parameters(self, iibb_per, iva_per):
        data = []

        if iibb_per > Decimal('0.00'):
            data.append(
                {
                    'tax_type': 'IIBB_PER',
                    'amount': str(iibb_per)
                }
            )

        if iva_per > Decimal('0.00'):
            data.append(
                {
                    'tax_type': 'IVA_PER',
                    'amount': str(iva_per)
                }
            )

        print(data)
        return data