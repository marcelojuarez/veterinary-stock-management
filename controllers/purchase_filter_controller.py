from datetime import datetime
from utils.view_helpers import show_error
from utils.utils import traditional_to_iso, iso_to_traditional

class PurchaseFilterController():
    def __init__(self, model):
        self.treeview = None
        self.model = model        

    def set_supplier_var(self, supplier_var):
        self.supplier_var = supplier_var

    def set_treeview(self, treeview):
        self.treeview = treeview

    def validate_date(self, date):
        try:
            datetime.strptime(date, "%d/%m/%Y")
            return True
        except:
            return False

    def filter_by_date(self, date):
        if not self.validate_date(date):
            show_error('Por favor introduzca la fecha en formato dd/mm/yyyy')
            return

        date_db = traditional_to_iso(date)

        selected_supplier = self.supplier_var.get()

        if selected_supplier.strip() != "":
            purchases = self.model.purchase.get_purchases_by_date(date_db, selected_supplier)
        else:
            purchases = self.model.purchase.get_purchases_by_date(date_db)

        for row in self.treeview.get_children():
            self.treeview.delete(row)
        # Cargar compras
        for p in purchases:
            estado = p[8]  # índice correcto del estado
            if estado == 'BORRADOR':
                tag = "purchase_draft"
            elif estado == 'PAGADA':
                tag = "purchase_paid"
            else:
                tag = "purchase_pending"  # CONFIRMADA / pendiente de pago
            print(p)
            self.treeview.insert(
                parent="", index="end", iid=p[0],
                values=(
                    p[0], # id
                    p[1], # cuit
                    p[2], # nombre
                    p[3], # tipo doc
                    iso_to_traditional(p[6]), # fecha
                    iso_to_traditional(p[7]), # fecha venc
                    p[8], # estado
                    p[10], # saldo pend
                    p[11] # total
                ),
                tag=(tag,)
            )    
