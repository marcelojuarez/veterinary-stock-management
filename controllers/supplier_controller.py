from models.supplier import SupplierModel
from models.stock import StockModel
from views.view_helpers import show_warning, show_error, show_success
import re

class SupplierController():
    def __init__(self, view, stock_controller):
        self.model = SupplierModel()
        self.view = view
        self.stock_model = StockModel()
        self.stock_controller = stock_controller
        self.stock_view = self.view.stock_view

    def add_new_supplier(self, window=None):
        """Guardar nuevo proveedor"""
        try:
            data = self.view.get_supplier_data()

            if not self.__validates_supplier_data(data):
                print('Entro al chequeo de datos del proveedor')
                return

            if not self.__validate_supplier_email(data['email']):
                print('Entro al chequeo de email del proveedor')
                return
            
            if not self.__validate_supplier_cuit(data['cuit']):
                print('Entro al chequeo de cuit del proveedor')
                return
            
            if not self.__validate_supplier_phone(data['phone']):
                print('Entro al chequeo de telefono del proveedor')
                return
            
            if not self.__validate_supplier_name(data['name']):
                print('Entro al chequeo de nombre del proveedor')
                return
            
            if not self.__validate_supplier_address(data['home']):
                print('Entro al chequeo de domicilio del proveedor')
                return

            # convertir tipos
            supplier_data = {
                'name': data['name'],
                'cuit': data['cuit'],
                'home': data['home'],
                'phone': data['phone'],
                'email': data['email'],
                'debt': data['debt']
            }

            self.model.add_supplier(supplier_data)

            self.refresh_supplier_table()

            self.view.clear_form_supplier()

            if window:
                window.destroy()
            
            show_success("Proveedor registrado correctamente.")

        except ValueError as e:
            show_error(f"Error en los datos {str(e)}")
        except Exception as e:
            show_error(f"Error al registrar el proveedor: {str(e)}")

    def open_win_add_supplier_product(self, supplier_cuit):
        try:
            self.view.open_add_product_window(supplier_cuit)

        except Exception as e:
            print({e})


    def add_supplier_product(self):
        data = self.stock_view.get_form_data()
        print(f'Datos: {data}')
        self.stock_controller.add_new_product()
        self.stock_view.clear_form_fields()


    def supplier_info(self):
        # Obtengo las filas seleccionadas
        selected = self.view.supplier_tree.selection()

        try:
            iid = selected[0]
            values = self.view.supplier_tree.item(iid, "values")
            print(f'Valores: {values}')
            self.view.open_info_window(values)
        except Exception:
            show_warning('Por favor seleccione un proveedor')

    def show_suppliers(self):
        suppliers_data = self.model.get_all_suppliers()
        return suppliers_data 
    
    def __validates_supplier_data(self, form_data):
        required_files =  ['name', 'cuit', 'home', 'phone', 'email', 'debt']

        print(f'Formulario de datos {form_data}')

        for field in required_files:
            if not form_data[field]:
                show_warning("Por favor complete todos los campos.")
                return False
        
        return True

    def __validate_supplier_email(self, email_field):
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        if not re.fullmatch(pattern, email_field):
            show_warning("Por favor coloquen el e-mail correctamente.")
            return False
        
        return True
    
    def __validate_supplier_cuit(self, cuit_field):
        pattern = r'^\d{2}-\d{8}-\d$'
        
        if not re.fullmatch(pattern, cuit_field):
            show_warning("Por favor coloque el CUIT correctamente. Formato: XX-XXXXXXXX-X")
            return False
        
        if self.model.find_suppplier_by_cuit(cuit_field) is not None:
            show_error(f"Error: Ya existe un proveedor con el CUIT: {cuit_field}")
            return False
        
        return True
    
    def __validate_supplier_phone(self, phone_field):
        pattern = r'^\+?\d{7,15}$'
        
        if not re.fullmatch(pattern, phone_field):
            show_warning("Por favor coloque el teléfono correctamente. Debe contener entre 7 y 15 dígitos, puede incluir un '+' al inicio.")
            return False
        
        return True
    
    def __validate_supplier_name(self, name_field):
        if len(name_field) < 2 or len(name_field) > 100:
            show_warning("El nombre del proveedor debe tener entre 2 y 100 caracteres.")
            return False
        
        return True
    
    def __validate_supplier_address(self, address_field):
        if len(address_field) < 5 or len(address_field) > 150:
            show_warning("La dirección del proveedor debe tener entre 5 y 150 caracteres.")
            return False
        
        return True

    def refresh_supplier_table(self):
        """Refrescar la tabla de proveedores"""
        try:    
            suppliers = self.model.get_all_suppliers()
            self.view.refresh_supplier_table(suppliers)
        except Exception as e:
            show_error(f"Error al refrescar la tabla {str(e)}")

    def delete_supplier(self):
        # Obtengo las filas seleccionadas
        selected = self.view.supplier_tree.selection()

        try:
            # Selecciona la primer fila
            iid = selected[0]
            values = self.view.supplier_tree.item(iid, "values")
            print(values)
            self.model.delete_supplier(iid)
            self.refresh_supplier_table()
            show_success('El proveedor fue eliminado correctamente')

        except Exception:
            show_warning('Por favor seleccione un proveedor para eliminar')

    def update_debt(self, supplier_data, new_debt, win=None):
        self.view.lbl_debt.configure(text=f"${new_debt}")
        # Se actualiza la deuda
        self.model.update_debt(supplier_data[0] ,new_debt)
        data = self.model.find_supplier_by_id(supplier_data[0])
        # Se actualiza el momento de actualizacion
        self.view.last_update_debt.set(value=f'Ultima actualizacion deuda: \n {data[7]}') 
        self.refresh_supplier_table()
        if win:
            win.destroy()
        
    
    def register_purchase(self, product_tree, qty_var, window):
        try:
            selected = product_tree.selection()
            if not selected:
                show_warning("Seleccione un producto")
                return
            product_id = product_tree.item(selected[0])["values"][0]
            quantity = int(qty_var.get())

            if quantity <= 0:
                show_warning("Cantidad inválida")
                return

            product_data = self.stock_model.get_product_by_id(product_id)

            message = f"¿Desea actualizar el stock del producto '{product_data[2]}' con {qty_var.get()} unidades?"

            confirmation = self.view.ask_confirmation(message, "Actualizar stock")
            print(f'product_data: {product_data[11]}')
            quantity += int(product_data[11])
            
            if confirmation:
                self.stock_model.update_quantity(product_id, quantity)

                show_success("Compra registrada y stock actualizado.")
                window.destroy()
                self.view.stock_view.controller.refresh_stock_table()

            else:
                print('no hay actualizacion')

        except Exception as e:
            show_error(f"Error al registrar compra: {e}")

