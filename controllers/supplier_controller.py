from models.supplier import SupplierModel
from views.supplier_view import SupplierView

class SupplierController():
    def __init__(self, parent):
        self.model = SupplierModel()
        self.view = SupplierView(parent, self)

    def add_new_supplier(self):
        data = self.view.get_supplier_data()

        if not data['name'] or not data['company_name']:
            self.view.show_error('Faltan datos')

        else:
            self.model.add_supplier(supplier_data)

    def show_suppliers(self):
        suppliers_data = self.model.get_all_suppliers()
        return suppliers_data 
    
    def __validates_supplier_data():



