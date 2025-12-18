# controllers/supplier_controller.py

from models.stock import StockModel
from views.view_helpers import show_warning, show_error, show_success
import re

class SupplierController():
    def __init__(self, view, stock_controller):
        self.model = view.model
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
                'email': data['email']
            }

            self.model.core.add_supplier(supplier_data)

            self.refresh_supplier_table()

            self.view.clear_form_supplier()

            if window:
                window.destroy()
            
            show_success("Proveedor registrado correctamente.")

        except ValueError as e:
            show_error(f"Error en los datos {str(e)}")
        except Exception as e:
            show_error(f"Error al registrar el proveedor: {str(e)}")

    def supplier_info(self):

        try:
            # Obtengo las filas seleccionadas
            selected = self.view.supplier_tree.selection()
            
            if not selected:
                show_warning('Por favor seleccione un proveedor')
                return

            iid = selected[0]
            values = self.view.supplier_tree.item(iid, "values")
            print(values)
            debt = self.model.purchase.get_debt_of_supplier(values[2])[0]
            if debt is None:
                debt = 0
            print(debt)
            self.view.open_info_window(values, debt)
        except Exception as e:
            print(f'Hubo un error: {e}')

    def show_suppliers(self):
        suppliers_data = self.model.core.get_all_suppliers()
        return suppliers_data 
    
    def __validates_supplier_data(self, form_data):
        required_files =  ['name', 'cuit', 'home', 'phone', 'email']

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
        
        if self.model.core.find_supplier_by_cuit(cuit_field) is not None:
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
            self.view.suppliers = self.model.core.get_all_suppliers()
            self.view.refresh_supplier_table(self.view.suppliers)
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
            self.model.core.delete_supplier(iid)
            self.refresh_supplier_table()
            if self.view.find_var.get() != "":
                self.view.find_var.set('')
            show_success('El proveedor fue eliminado correctamente')

        except Exception:
            show_warning('Por favor seleccione un proveedor para eliminar')

 
