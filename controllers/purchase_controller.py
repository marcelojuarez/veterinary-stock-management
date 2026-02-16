from datetime import datetime
from models.stock import StockModel
from views.view_helpers import show_error, show_warning, show_success, close_win
from decimal import Decimal

class PurchaseController():
    def __init__(self, event_bus):
        self.model = None
        self.stock_model = StockModel()
        self.view = None
        self.form_view = None
        self.new_p_form = None # new_product_form
        self.new_p_i_form = None # new_purchase_form
        self.receipt_info_vw = None
        self.invoice_info_vw = None
        self.event_bus = event_bus

        self.event_bus.subscribe(
            'refresh_products_on_p_win',
            self.refresh_products_on_p_win
        )
        
        products = self.stock_model.get_all_products()
        self.products = [(p[0], p[1], p[2], p[10]) for p in products]

    # setters
    def set_model(self, model):
        self.model = model

    def set_view(self, view):
        self.view = view

    def set_receipt_view(self, receipt_view):
        self.receipt_info_vw = receipt_view
    
    def set_invoice_view(self, invoice_view):
        self.invoice_info_vw = invoice_view

    def set_form_view(self, form_view):
        self.form_view = form_view

    def set_new_p_form(self, new_p_form):
        self.new_p_form = new_p_form

    def set_new_p_i_form(self, new_p_i_form):
        self.new_p_i_form = new_p_i_form

    def refresh_products_on_p_win(self):
        products = self.stock_model.get_all_products()
        self.products = [(p[0], p[1], p[2], p[10]) for p in products]

    ## -- Confirmar Compra -- ##
    def confirm_purchase(self, purchase_id):
        # Control si tiene compras asociadas
        try:
            if not self.model.purchase.get_purchase_items(purchase_id):
                show_warning('Advertencia. No puede confirmar una compra sin productos cargados')
                return 

            # Se establece compra como pendiente y deuda proveedor 
            purchase_data = self.model.purchase.get_purchase_by_id(purchase_id)

            doc_type = purchase_data[2]
            if doc_type == "REMITO":
                id = purchase_data[4]
            else:
                id = purchase_data[3]

            result = self.model.purchase.load_products(purchase_id, id, doc_type)

            if result:
                # Refrescar lista con proveedor seleccionado o no
                if self.view.supplier_var.get().strip() == "":
                    self.view.load_purchases(False)
                
                else:
                    self.view.load_purchases(True)

                self.event_bus.publish('refresh_stock_table', None)
                
        except ValueError as e:
            show_error(f'Error al confirmar la compra: {e}')
            return

    ## --  Actualizar la info del documento -- ##
    def update_doc_info(self, purchase_id, doc_type):
        try:
            purchase_data = self.model.purchase.get_purchase_by_id(purchase_id)
            purchase_id = purchase_data[0]

            if doc_type == 'REMITO':
                data = self.receipt_info_vw.get_receipt_data()
                print(f'receipt data: {data}')

                if not self.validate_doc_data(data, doc_type):
                    return False

                receipt_id = purchase_data[4]

                result = self.model.purchase.update_purchase(purchase_id, receipt_id, data, doc_type)

            else:
                data = self.invoice_info_vw.get_invoice_data()
                print(f'invoice data: {data}')

                if not self.validate_doc_data(data, doc_type):
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
            if doc_type == 'REMITO':
                self.receipt_info_vw.recover_previous_values(purchase_id)

            else:
                self.invoice_info_vw.recover_previous_values(purchase_id)
            
            return False

    ## -- Validar datos del documento -- ##
    def validate_doc_data(cls, data, doc_type):
        if doc_type == 'REMITO':
            required_files = {
                'receipt_id': 'Numero de Remito',
                'expiration': 'Fecha de Vencimiento',
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

    ## -- Verifica si una fecha dada esta en el formato valido -- ##
    @staticmethod    
    def is_valid_date(date):
        try:
            datetime.strptime(date, "%d/%m/%Y")
            return True
        except:
            return False

    ## -- Agrega un nuevo producto -- ## 
    def add_new_product(self, window=None):
        """Guardar nuevo producto"""
        try:
            # Obtener datos del formulario
            form_data = self.new_p_form.get_new_product_data()

            print(f'form_data\n: {form_data}')

            # Validaciones
            if not self.validate_new_product_data(form_data) :
                return

            product_data = {
                'Name': (form_data['Name']).upper(),
                'Package': form_data['Package'],
                'Profit': form_data['Profit'],
                'CostPrice': form_data['CostPrice'],
                'Iva': form_data['Iva'],
                'Stock': int(form_data['Stock']),
                'SalePrice': form_data['SalePrice'],
                'PriceWIva': form_data['PriceWIva'],
            }

            # Guardar en DB
            self.model.purchase.add_product(product_data)
            if window:
                window.destroy()
        
            products = self.stock_model.get_all_products()
            self.products = [(p[0], p[1], p[2], p[10]) for p in products]

            # Refrescar tabla
            self.form_view.load_products()
            self.event_bus.publish('refresh_stock_table', None)
            
            show_success("Producto registrado correctamente")
            
        except ValueError as e:
            show_error(f"Error en los datos: {str(e)}")

        except Exception as e:
            show_error(f"{str(e)}")
        
    ## -- Valida los datos del formulario de un nuevo producto -- ##
    def validate_new_product_data(self, form_data):
        
        """Validar datos del formulario"""
        required_fields = {
            'Name': 'Nombre Artículo', 
            'Package': 'Envase', 
            'CostPrice': 'Precio Costo', 
            'Profit': 'Rentabilidad', 
            'Stock': 'Stock'
        }
        
        for field, lbl in required_fields.items():
            if not form_data[field]:
                show_warning(f'Por favor complete el campo "{lbl}"')
                return False
        
        # Validar Tipos Numéricos
        ## Precio de costo
        try:
            Decimal(form_data['CostPrice'])
        except Exception:
            show_warning("Error. Formato incorrecto en precio costo")
            return False
        
        if Decimal(form_data['CostPrice']) <= Decimal('0.00'):
            show_error('Error. El precio de costo no puede ser un valor Negativo o (0)')
            return False
        
        ## Rentabilidad
        try:
            Decimal(form_data['Profit'])
        except Exception:
            show_warning("Error. Formato incorrecto en Rentabilidad")
            return False
        
        if Decimal(form_data['Profit']) < Decimal('0.00'):
            show_error('Error. La rentabilidad no puede ser un valor Negativo')
            return False
            
        return True

    ## -- Agregar un nuevo item de compra -- ##
    def add_purchase_item(self, win, parent):
        try:
            item_data = self.new_p_i_form.get_purchase_item_data()

            if not self.validate_purchase_item_data(item_data):
                return

            # Convertir los valores a los tipos correctos            
            purchase_id = int(item_data['Purchase_id'])
            product_id = int(item_data['Product_id'])

            if self.exists_product_on_purchase(win, parent, purchase_id, product_id):
                return

            data = [
                purchase_id,
                product_id,
                item_data['Product_name'],
                item_data['Pack'],
                item_data['Qty'],
                item_data['Cost'],
                item_data['Iva_rate'],
                item_data['Discount'],
                item_data['Discount_amount'],
                item_data['Subtotal'],
                item_data['Iva_amount'],
                item_data['Total']
            ]

            purchase_data = self.model.purchase.get_purchase_by_id(purchase_id)

            doc_type = purchase_data[2]
            if doc_type == "REMITO":
                doc_id = purchase_data[4]
            else:
                doc_id = purchase_data[3]

            # Se agrega item a la compra
            result = self.model.purchase.handle_add_p_item(data, purchase_id, doc_type, doc_id)

            if result:
                show_success('Item agregado con exito')

                if self.view.supplier_var.get().strip() == "":
                    self.view.load_purchases(False)

                else:
                    self.view.load_purchases(True)

                close_win(win, parent)
                 
            else:
                show_error('Ocurrio un error')
  
        except ValueError as e:
            show_error(f'Error al cargar item de compra: {e}')
            return 

    ## -- Validar el formulario de un item de compra -- ##
    def validate_purchase_item_data(cls, form_data):
        required_fields = {
            'Purchase_id' : 'Id Compra',
            'Product_id': 'Id Producto',
            'Product_name': 'Nombre Producto',
            'Pack': 'Envase',
            'Qty': 'Stock',
            'Cost': 'Precio de Costo',
            'Iva_rate': 'Porcentaje de Iva',
            'Discount': 'Descuento',
            'Discount_amount': 'Monto Descuento',
            'Subtotal': 'SubTotal',
            'Iva_amount': 'Monto Iva',
            'Total': 'Total'
        }

        if not cls.is_int(form_data['Qty']):
            show_error(f'Error. El stock debe ser un valor Entero')
            return False
        
        if int(form_data['Qty']) <= 0:
            show_error(f'Error. El stock debe ser mayor a Cero(0)')
            return False

        for field, lbl in required_fields.items():
            if not form_data[field]:
                show_error(f'Por favor complete el campo "{lbl}"')
                return False
            
        # Validar Tipos Numéricos
        ## Precio de costo
        #- Formato correcto
        try:
            Decimal(form_data['Cost'])
        except Exception:
            show_warning("Error. Formato incorrecto en precio costo")
            return False
        
        #- Valor Positivo
        if Decimal(form_data['Cost']) <= Decimal('0.00'):
            show_error('Error. El precio de costo no puede ser un valor Negativo o (0)')
            return False
        
        ## Descuento
        #- Formato correcto
        try:
            Decimal(form_data['Discount'])
        except Exception:
            show_warning("Error. Formato incorrecto en Descuento")
            return False
        
        #- Valor correcto
        if Decimal(form_data['Discount']) < Decimal('0.00') \
        or Decimal(form_data['Discount']) > Decimal('99.00'):
            show_error('Error. El porcentaje de descuento debe rondar entre 0 y 99 %')
            return False
    
        return True

    ## Verifica si un valor es entero
    @staticmethod    
    def is_int(n):
        try: int(n); return True
        except:
            return False
        
    ## -- Verifica si el producto ya fue incluido en la compra -- ##
    def exists_product_on_purchase(self, win, parent, purchase_id, product_id):
        result = self.model.purchase.get_product_on_purchase(purchase_id, product_id)
        if result is None:
            return False
        
        else:
            show_error('Error. El producto ya esta incluido en la compra. \n' \
                       'Para cualquier modificacion Agregar nuevamente.')
            
            close_win(win, parent)
            return True

    ## -- Eliminar un registro de compra -- ##    
    def delete_purchase(self, purchase_id, doc_type):
        
        purchase_data = self.model.purchase.get_purchase_by_id(purchase_id)
        
        doc_type = purchase_data[2]

        if doc_type == "REMITO":
            doc_id = purchase_data[4]
        else:
            doc_id = purchase_data[3]
        
        result = self.model.purchase.delete_purchase_and_doc(purchase_id, doc_id, doc_type)

        if result:
            if self.view.supplier_var.get().strip() == "":
                self.view.load_purchases(False)

            else:
                self.view.load_purchases(True)

            show_success('Compra eliminada con exito.')

    ## -- Elimina un item de compra -- ##
    def delete_purchase_item(self, purchase_id, product_id):
        try:
            
            purchase_data = self.model.purchase.get_purchase_by_id(purchase_id)

            doc_type = purchase_data[2]
            if doc_type == "REMITO":
                doc_id = purchase_data[4]
            else:
                doc_id = purchase_data[3]

            result = self.model.purchase.handle_delete_purchase_item(purchase_id, product_id, doc_type, doc_id)
            if result:
                show_success('Item eliminado con exito')
                ## actualizar tabla y labels
                if doc_type == "REMITO":
                    self.receipt_info_vw.load_receipt_data(doc_id)
                    self.receipt_info_vw.load_data_into_the_sheet()

                else:
                    self.invoice_info_vw.load_invoice_data(doc_id)
                    self.invoice_info_vw.load_data_into_the_sheet()

                if self.view.supplier_var.get().strip() == "":
                    self.view.load_purchases(False)

                else:
                    self.view.load_purchases(True)

            else:
                show_error('Ocurrio un error')
                

        except ValueError as e:
            show_error(f'Error al eliminar item de compra: {e}')
            return 