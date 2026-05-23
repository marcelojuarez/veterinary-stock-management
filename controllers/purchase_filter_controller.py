from datetime import datetime
from utils.view_helpers import show_error, show_warning
from utils.utils import traditional_to_iso, iso_to_traditional, format_currency

class PurchaseFilterController():
    def __init__(self, model):
        self.treeview = None
        self.model = model        

    # var supplier_id from purchase window
    def set_supplier_id_var(self, supplier_id_var):
        self.supplier_id_var = supplier_id_var

    # var search from purchase window
    def set_search_var(self, search_var):
        self.search_var = search_var

    def set_treeview(self, treeview):
        self.treeview = treeview

    ## Validate date
    def validate_date(self, date):
        try:
            datetime.strptime(date, "%d/%m/%Y")
            return True
        except:
            return False

    ## Filter by date
    def filter_by_date(self, date, invoice_num_var):
        if not self.validate_date(date):
            show_error('Por favor introduzca la fecha en formato dd/mm/yyyy')
            return
        
        invoice_num_var.set('')

        date_db = traditional_to_iso(date)

        selected_supplier = self.supplier_id_var.get()

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
                    format_currency(p[10]), # saldo pend
                    format_currency(p[11]) # total
                ),
                tag=(tag,)
            )    

    # Validate invoice number
    def validate_invoice_number(self, invoice_number):
            if not invoice_number.isdigit():
                show_error(
                    'Error. El valor ingresado contiene caracteres no permitidos.\n'
                    '\n'
                    'Ingrese el número utilizando únicamente dígitos (0-9).\n'
                    'Ejemplo: 1234 56789121'
                )
                return False
            return True

    # Filter by invoice number
    def filter_by_invoice_number(self, invoice_number):
        inv_num = ''.join(invoice_number.split())

        if (inv_num == ''):
            show_warning('Por favor ingrese un numero de factura.\n')
            return

        if not self.validate_invoice_number(inv_num):
            return
        
        # buscar y obtener la compra
        selected_p = self.model.purchase.get_purchase_by_invoice_number(inv_num)

        if selected_p is None:
            show_warning(
                'Error.\n '
                f'No se encontró una factura con N°: {invoice_number}\n'
            )
            return

        self.search_var.set(selected_p[2])

        # Limpiar tabla
        for row in self.treeview.get_children():
            self.treeview.delete(row)

        # insertar en la tabla
        state = selected_p[6]  # índice correcto del estado
        if state == 'BORRADOR':
            tag = "purchase_draft"
        elif state == 'PAGADA':
            tag = "purchase_paid"
        else:
            tag = "purchase_pending"  # CONFIRMADA / pendiente de pago

        self.treeview.insert(
            parent="", index="end", iid=selected_p[0],
            values=(
                selected_p[0], # id
                selected_p[1], # cuit
                selected_p[2], # nombre
                selected_p[3], # tipo doc
                iso_to_traditional(selected_p[4]), # fecha
                iso_to_traditional(selected_p[5]), # fecha venc
                state, # estado
                format_currency(selected_p[7]), # saldo pend
                format_currency(selected_p[8]) # total
            ),
            tag=(tag,)
        ) 

        

        

        

