from views.view_helpers import show_success, show_error, show_warning, close_win
from datetime import datetime

class SupplierInvoiceController():
    def __init__(self, form_view, purchase_view, supplier_view):
        self.form_view = form_view
        self.purchase_view = purchase_view
        self.supplier_view = supplier_view
        self.model = supplier_view.model

    def add_new_invoice(self, win, parent):

        try:
            data = self.form_view.get_invoice_form_data()
            supplier_data = self.model.core.find_supplier_by_cuit(data['supplier_cuit'])
            print(data)
            if not self.validate_date(data):
                return
            
            invoice_params = {
                'supplier_id': supplier_data[0],
                'invoice_id': data['invoice_id'],
                'invoice_type': data['invoice_type'],
                'point_of_sale': data['point_of_sale'],
                'expiration_date': data['expiration_date'],
                'state': data['state'],
                'observations': data['observations'],
                'subtotal': data['subtotal'],
                'iva': data['iva'],
                'discount': data['discount'],
                'total': float(data['total'])
            }

            if data['state'] == 'PAGADA':
                pending = 0
            else:
                pending = float(data['total'])

            purchase_params = {
                'supplier_id': supplier_data[0],
                'doc_type': "FACTURA",
                'expiration_date': data['expiration_date'],
                'state': data['state'],
                'observations': data['observations'],
                'pending': pending, 
                'total': float(data['total']), 
            }

            result = self.model.purchase.create_invoice_and_purchase(invoice_params, purchase_params)
            self.purchase_view.load_purchases(False)
            close_win(win, parent, self.form_view.clear_invoice_form())
            if result:
                self.supplier_view.controller.refresh_supplier_table()

        except ValueError as e:
            show_error(f'Error en los datos: {e}')
        except Exception as e:
            show_error(f'Error al registrar factura: {e}')

    @classmethod
    def validate_date(cls, data):
        required_files = {
            'invoice_id': 'Numero de Factura',
            'invoice_type': 'Tipo de Factura',
            'point_of_sale': 'Punto de Venta',
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
        
        if not cls._is_float(data['subtotal']):
            show_error('Por favor el monto subtotal debe ser un valor numerico')
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