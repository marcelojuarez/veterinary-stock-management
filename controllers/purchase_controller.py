from views.view_helpers import show_error
from datetime import datetime

class PurchaseController():
    def __init__(self, model, view, info_view):
        self.model = model
        self.view = view
        self.info_view = info_view

    def confirm_purchase(self, purchase_id):
        # Debo comprobar si tiene al menos un item asociado y calcular su deuda
        
        # Debo setear compra como pendiente
        # suponiendo que la nueva deuda sea 100
        purchase_data = self.model.purchase.get_purchase_by_id(purchase_id)
        print(purchase_data)

        doc_type = purchase_data[2]
        if doc_type == "REMITO":
            id = purchase_data[4]
        else:
            id = purchase_data[3]

        self.model.purchase.set_new_debt_purchase(purchase_id, id, doc_type, 100)

        # Refrescar lista con proveedor seleccionado o no
        if self.view.supplier_var.get().strip() == "":
            self.view.load_purchases(False)
        
        else:
            self.view.load_purchases(True)


    def update_doc_info(self, purchase_id, doc_type):
        try:
            purchase_data = self.model.purchase.get_purchase_by_id(purchase_id)
            purchase_id = purchase_data[0]

            if doc_type == 'REMITO':
                data = self.info_view.get_receipt_data()
                print(f'receipt data: {data}')

                if not self.validate_data(data, doc_type):
                    return False

                receipt_id = purchase_data[4]

                result = self.model.purchase.update_purchase(purchase_id, receipt_id, data, doc_type)

            else:
                data = self.info_view.get_invoice_data()
                print(f'invoice data: {data}')

                if not self.validate_data(data, doc_type):
                    return                

                invoice_id = purchase_data[3]

                result = self.model.purchase.update_purchase(purchase_id, invoice_id, data, doc_type)

            if result:
                if self.view.supplier_var.get().strip() == "":
                    self.view.load_purchases(False)

                else:
                    self.view.load_purchases(True)

            return True

        except ValueError as e:
            show_error(f'Error al actualizar el Documento:{e}')
            self.info_view.recover_previous_values(purchase_id, doc_type)
            return False


    # Validate data
    def validate_data(cls, data, doc_type):
        if doc_type == 'REMITO':
            required_files = {
                'receipt_id': 'Numero de Remito',
                'expiration': 'Fecha de Vencimiento',
                'obs': 'Observaciones'
            }

            for field, label in required_files.items():
                if not data[field]:
                    show_error(f'Por favor complete el campo: "{label}"')
                    return False
            
            if not cls.is_valid_date(data['expiration']):
                show_error('Por favor coloque la fecha en formato dd/mm/yyyy')
                return False
                
        else:
            required_files = {
                'invoice_id': 'Numero de Factura',
                'invoice_type': 'Tipo de Factura',
                'obs': 'Observaciones',
                'expiration': 'Fecha de Vencimiento' 
            }

            for (field,label) in required_files.items():
                if not data[field]:
                    show_error(f'Por favor complete el campo: "{label}"')
                    return False
                
            if not cls.is_valid_date(data['expiration']):
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
