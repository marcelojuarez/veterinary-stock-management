from models.supplier import SupplierModel
from views.supplier_view import SupplierView

class SupplierController():
    def __init__(self, parent):
        self.view = SupplierView(parent, self)
        self.model = SupplierModel()

    def add_new_supplier(self):
        pass
    
    def show_suppliers(self):
        suppliers = self.model.show_suppliers()
        for s in suppliers:
            print(suppliers['nombre'])


