from datetime import datetime
import locale
from views.view_helpers import show_error

class PurchaseFilterController():
    def __init__(self, model):
        self.treeview = None
        self.model = model

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

        print(f'Date from entry: {date}')

        date_db = self.convert_string_to_date_formated(date)

        purchases = self.model.purchase.get_purchase_by_date(date_db)

        for row in self.treeview.get_children():
            self.treeview.delete(row)

        # Cargar compras
        for p in purchases:
            self.treeview.insert(
                parent="", index="end", iid=p[0],
                values=(
                    p[0],
                    p[1],
                    p[2],
                    p[5],
                    p[6],
                    p[7],
                    locale.format_string("%.2f", p[9], grouping=True),
                ),
                tag="orow"
            )    
    
    def convert_string_to_date_formated(self, date):
        # convierto el string a obj tipo date
        date_formated = datetime.strptime(date, "%d/%m/%Y").date()
        # formateo el obj
        return date_formated.strftime("%Y-%m-%d")