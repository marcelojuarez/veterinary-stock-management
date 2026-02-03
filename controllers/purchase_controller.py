from datetime import datetime
from models.stock import StockModel
from views.view_helpers import show_error, show_warning, show_success, close_win
from decimal import Decimal
from utils.utils import normalize_decimal

class PurchaseController():
    def __init__(self, event_bus):
        self.model = None
        self.stock_model = StockModel()
        self.view = None
        self.form_view = None
        self.new_p_form = None # new_product_form
        self.new_p_i_form = None # new_purchase_form
        self.info_view = None
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

    def set_info_view(self, info_view):
        self.info_view = info_view

    def set_form_view(self, form_view):
        self.form_view = form_view

    def set_new_p_form(self, new_p_form):
        self.new_p_form = new_p_form

    def set_new_p_i_form(self, new_p_i_form):
        self.new_p_i_form = new_p_i_form

    def refresh_products_on_p_win(self):
        products = self.stock_model.get_all_products()
        self.products = [(p[0], p[1], p[2], p[10]) for p in products]

    # Confirmar Compra
    def confirm_purchase(self, purchase_id):
        # Control si tiene compras asociadas
        try:
            if not self.model.purchase.get_purchase_items(purchase_id):
                show_warning('Advertencia. No puede confirmar una compra sin productos cargados')
                return 

            # Se establece compra como pendiente y deuda proveedor
            debt = normalize_decimal(self.model.purchase.get_total_of_items(purchase_id)[0])
            purchase_data = self.model.purchase.get_purchase_by_id(purchase_id)

            doc_type = purchase_data[2]
            if doc_type == "REMITO":
                id = purchase_data[4]
            else:
                id = purchase_data[3]

            result = self.model.purchase.load_products_and_set_initial_debt(purchase_id, id, doc_type, debt)

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

    # Actualizar la info del documento
    def update_doc_info(self, purchase_id, doc_type):
        try:
            purchase_data = self.model.purchase.get_purchase_by_id(purchase_id)
            purchase_id = purchase_data[0]

            if doc_type == 'REMITO':
                data = self.info_view.get_receipt_data()
                print(f'receipt data: {data}')

                if not self.validate_doc_data(data, doc_type):
                    return False

                receipt_id = purchase_data[4]

                result = self.model.purchase.update_purchase(purchase_id, receipt_id, data, doc_type)

            else:
                data = self.info_view.get_invoice_data()
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
            self.info_view.recover_previous_values(purchase_id, doc_type)
            return False

    # Validate data
    def validate_doc_data(cls, data, doc_type):
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
        
    def add_new_product(self, window=None):
        """Guardar nuevo producto"""
        try:
            # Obtener datos del formulario
            form_data = self.new_p_form.get_new_product_data()

            print(f'form_data\n: {form_data}')

            # Validaciones
            if not self.validate_new_product_data(form_data):
                return

            profit = normalize_decimal(form_data['Profit'])
            cost_price = normalize_decimal(form_data['CostPrice'])
            sale_price = normalize_decimal(form_data['SalePrice'])
            price_w_iva = normalize_decimal(form_data['PriceWIva'])

            # ciertos campos se setean primeramente con el valor 0(cero)
            product_data = {
                'Name': (form_data['Name']).upper(),
                'Package': form_data['Package'],
                'Profit': profit,
                'CostPrice': cost_price,
                'Iva': form_data['Iva'],
                'Stock': int(form_data['Stock']),
                'SalePrice': sale_price,
                'PriceWIva': price_w_iva,
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
            normalize_decimal(form_data['CostPrice'])
        except Exception:
            show_warning("Error. Formato incorrecto en precio costo")
            return False
        
        if normalize_decimal(form_data['CostPrice']) <= normalize_decimal(0.00):
            show_error('Error. El precio de costo no puede ser un valor Negativo o (0)')
            return False
        
        ## Rentabilidad
        try:
            normalize_decimal(form_data['Profit'])
        except Exception:
            show_warning("Error. Formato incorrecto en Rentabilidad")
            return False
        
        if normalize_decimal(form_data['Profit']) < normalize_decimal(0.00):
            show_error('Error.La rentabilidad no puede ser un valor Negativo')
            return False

        ## Stock
        try:
            int(form_data['Stock'])
        except ValueError:
            show_warning("Error. Formato incorrecto en stock")
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
            product_name = item_data['Product_name']
            pack = item_data['Pack']
            qty = int(item_data['Qty'])
            cost = normalize_decimal(item_data['Cost'])
            iva_rate = normalize_decimal(item_data['Iva_rate'])
            discount = normalize_decimal(item_data['Discount'])
            discount_amount = normalize_decimal(item_data['Discount_amount'])
            subtotal = normalize_decimal(item_data['Subtotal'])
            iva_amount = normalize_decimal(item_data['Iva_amount'])
            total = normalize_decimal(item_data['Total'])
            
            item_data_clean = [
                purchase_id,
                product_id,
                product_name,
                pack,
                qty,
                str(cost),
                str(iva_rate),
                str(discount),
                str(discount_amount),
                str(subtotal),
                str(iva_amount),
                str(total)
            ]

            purchase_data = self.model.purchase.get_purchase_by_id(purchase_id)

            doc_type = purchase_data[2]
            if doc_type == "REMITO":
                doc_id = purchase_data[4]
            else:
                doc_id = purchase_data[3]

            # Se agrega item a la compra
            ok = self.model.purchase.handle_add_p_item(item_data_clean, purchase_id, doc_type, doc_id)
            if ok:
                show_success('Item agregado con exito')
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
        try:
            normalize_decimal(form_data['Cost'])
        except Exception:
            show_warning("Error. Formato incorrecto en precio costo")
            return False
        
        if normalize_decimal(form_data['Cost']) <= normalize_decimal(0.00):
            show_error('Error. El precio de costo no puede ser un valor Negativo o (0)')
            return False
        
        ## Descuento
        try:
            normalize_decimal(form_data['Discount'])
        except Exception:
            show_warning("Error. Formato incorrecto en Descuento")
            return False
        
        if normalize_decimal(form_data['Discount']) < normalize_decimal(0.00) \
        or normalize_decimal(form_data['Discount']) > normalize_decimal(99.00):
            show_error('Error. El porcentaje de descuento debe rondar entre 0 y 99 %')
            return False
    
        return True

    @staticmethod    
    def is_int(n):
        try: int(n); return True
        except:
            return False

    ## -- Eliminar un registro de compra -- ##    
    def delete_purchase(self, purchase_id, doc_type):
        
        purchase_data = self.model.purchase.get_purchase_by_id(purchase_id)

        print(purchase_data)
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
                ## actualizar tabla y labels
                self.info_view.load_data(doc_id)
                self.info_view.load_data_into_the_sheet()
                

        except ValueError as e:
            show_error(f'Error al eliminar item de compra: {e}')
            return 