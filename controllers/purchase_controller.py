from views.view_helpers import show_error, show_warning, show_success, close_win
from datetime import datetime
from models.stock import StockModel

class PurchaseController():
    def __init__(self):
        self.model = None
        self.view = None
        self.form_view = None
        self.info_view = None
        self.event_bus = None
        self.stock_model = StockModel()

    # setters
    def set_model(self, model):
        self.model = model

    def set_view(self, view):
        self.view = view

    def set_info_view(self, info_view):
        self.info_view = info_view

    def set_form_view(self, form_view):
        self.form_view = form_view

    def set_event_bus(self, event_bus):
        self.event_bus = event_bus

    # Confirmar Compra
    def confirm_purchase(self, purchase_id):
        # Control si tiene compras asociadas
        try:
            if not self.model.purchase.get_purchase_items(purchase_id):
                show_warning('Advertencia. No puede confirmar una compra sin productos cargados')
                return 

            # Se establece compra como pendiente y deuda proveedor
            debt = self.model.purchase.get_sum_of_items(purchase_id)[0]
            print(f'Suma de totales: {debt}')
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

                self.event_bus.publish('refresh_table', None)
                
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
            form_data = self.form_view.get_new_product_data()

            # Validaciones
            if not self.validate_new_product_data(form_data):
                return

            profit = float(form_data['Profit'])
            cost_price = float(form_data['CostPrice'])
            sale_price = float(form_data['SalePrice'])
            price_w_iva = float(form_data['PriceWIva'])

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
            
            # Refrescar tabla
            self.event_bus.publish('refresh_table', None)

            products = self.stock_model.get_all_products()
            self.form_view.products = [(p[0], p[1], p[2], p[10]) for p in products]

            self.form_view.load_products()
            
            show_success("Producto registrado correctamente")
            
        except ValueError as e:
            show_error(f"Error en los datos: {str(e)}")

        except Exception as e:
            show_error(f"Error al registrar producto: {str(e)}")
        
    def validate_new_product_data(self, form_data):
        """Validar datos del formulario"""
        required_fields = ['Name', 'Package', 'Profit', 'CostPrice', 'Stock']
        
        for field in required_fields:
            if not form_data[field]:
                self.view.show_warning("Por favor complete todos los campos")
                return False
        
        # Validar tipos numéricos
        try:
            float(form_data['CostPrice'])
            int(form_data['Stock'])
        except ValueError:
            self.view.show_warning("Los precios y cantidad deben ser números válidos")
            return False
    
        return True

    ## -- Agregar un nuevo item de compra -- ##

    def add_purchase_item(self, win, parent):
        try:
            item_data = self.form_view.get_purchase_item_data()

            if not self.validate_purchase_item_data(item_data):
                return

            # Convertir los valores a los tipos correctos
            item_data = [
                int(item_data['purchase_id']),
                int(item_data['product_id']),
                item_data['product_name'],
                item_data['pack'],
                int(item_data['qty']),
                float(item_data['cost']),
                float(item_data['iva_rate']),
                float(item_data['discount']),
                float(item_data['discount_amount']),
                float(item_data['subtotal']),
                float(item_data['iva_amount']),
                float(item_data['total']),
            ]

            # Se agrega item a la compra
            self.model.purchase.add_purchase_item(item_data)
            show_success('Item agregado con exito')
            close_win(win, parent)   

        except ValueError as e:
            show_error(f'Error al cargar item de compra: {e}')
            return 
    
    ## -- -- ##

    ## -- Validar el formulario de un item de compra -- ##
    def validate_purchase_item_data(cls, data):
        required_fields = {
            'purchase_id' : 'Id Compra',
            'product_id': 'Id Producto',
            'product_name': 'Nombre Producto',
            'pack': 'Envase',
            'qty': 'Stock',
            'cost': 'Precio de Costo',
            'iva_rate': 'Porcentaje de Iva',
            'discount': 'Descuento',
            'discount_amount': 'Monto Descuento',
            'subtotal': 'SubTotal',
            'iva_amount': 'Monto Iva',
            'total': 'Total'
        }

        for field, lbl in required_fields.items():
            if not data[field]:
                show_error(f'Campo Incompleto: "{lbl}"')
                return False

        if not cls.is_int(data['qty']):
            show_error(f'Error. El stock debe ser un valor Entero')
            return False
    
        return True

    ## -- -- ##

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