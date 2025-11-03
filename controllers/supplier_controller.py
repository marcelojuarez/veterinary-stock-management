from models.supplier import SupplierModel
import re

class SupplierController():
    def __init__(self, view):
        self.model = SupplierModel()
        self.view = view

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
            
            if not self.__validate_supplier_phone(data['telefono']):
                print('Entro al chequeo de telefono del proveedor')
                return
            
            if not self.__validate_supplier_name(data['nombre']):
                print('Entro al chequeo de nombre del proveedor')
                return
            
            if not self.__validate_supplier_address(data['domicilio']):
                print('Entro al chequeo de domicilio del proveedor')
                return

            # convertir tipos
            supplier_data = {
                'nombre': data['nombre'],
                'cuit': data['cuit'],
                'domicilio': data['domicilio'],
                'telefono': data['telefono'],
                'email': data['email']
            }

            self.model.add_supplier(supplier_data)

            self.refresh_supplier_table()

            self.clear_form()

            if window:
                window.destroy()
            
            self.view.show_success("Proveedor registrado correctamente.")

        except ValueError as e:
            self.view.show_error(f"Error en los datos {str(e)}")
        except Exception as e:
            self.view.show_error(f"Error al registrar el proveedor: {str(e)}")

    def show_suppliers(self):
        suppliers_data = self.model.get_all_suppliers()
        return suppliers_data 
    
    def __validates_supplier_data(self, form_data):
        required_files =  ['nombre', 'cuit', 'domicilio', 'telefono', 'email']

        print(f'Formulario de datos {form_data}')

        for field in required_files:
            if not form_data[field]:
                self.view.show_warning("Por favor complete todos los campos.")
                return False
        
        return True

    def __validate_supplier_email(self, email_field):
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        if not re.fullmatch(pattern, email_field):
            self.view.show_warning("Por favor coloquen el e-mail correctamente.")
            return False
        
        return True
    
    def __validate_supplier_cuit(self, cuit_field):
        pattern = r'^\d{2}-\d{8}-\d$'
        
        if not re.fullmatch(pattern, cuit_field):
            self.view.show_warning("Por favor coloque el CUIT correctamente. Formato: XX-XXXXXXXX-X")
            return False
        
        return True
    
    def __validate_supplier_phone(self, phone_field):
        pattern = r'^\+?\d{7,15}$'
        
        if not re.fullmatch(pattern, phone_field):
            self.view.show_warning("Por favor coloque el teléfono correctamente. Debe contener entre 7 y 15 dígitos, puede incluir un '+' al inicio.")
            return False
        
        return True
    
    def __validate_supplier_name(self, name_field):
        if len(name_field) < 2 or len(name_field) > 100:
            self.view.show_warning("El nombre del proveedor debe tener entre 2 y 100 caracteres.")
            return False
        
        return True
    
    def __validate_supplier_address(self, address_field):
        if len(address_field) < 5 or len(address_field) > 150:
            self.view.show_warning("La dirección del proveedor debe tener entre 5 y 150 caracteres.")
            return False
        
        return True

    def refresh_supplier_table(self):
        """Refrescar la tabla de proveedores"""
        try:    
            suppliers = self.model.get_all_suppliers()
            self.view.refresh_supplier_table(suppliers)
        except Exception as e:
            self.view.show_error(f"Error al refrescar la tabla {str(e)}")

    def clear_form(self):
        """Limpiar formulario"""
        self.view.email_var.set('')
        self.view.name_var.set('')
        self.view.cuit_var.set('')
        self.view.home_var.set('')
        self.view.phone_var.set('')


    def delete_supplier(self):
        # Obtengo las filas selecionadas
        selected = self.view.supplier_tree.selection()

        try:
            # Selecciona la primer fila
            iid = selected[0]
            values = self.view.supplier_tree.item(iid, "values")
            print(values)
            self.model.delete_supplier(iid)
            self.refresh_supplier_table()
            self.view.show_success('El proveedor fue eliminado correctamente')
            

        except Exception:
            self.view.show_warning('Por favor seleccione un proveedor para eliminar')
