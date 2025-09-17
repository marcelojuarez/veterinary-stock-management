from models.supplier import SupplierModel
import re

class SupplierController():
    def __init__(self, view):
        self.model = SupplierModel()
        self.view = view

    def add_new_supplier(self):
        """Guardar nuevo proveedor"""
        try:
            data = self.view.get_supplier_data()

            if not self.__validates_supplier_data(data):
                print('Entro al chequeo de datos del proveedor')
                return

            if not self.__validate_supplier_email(data['email']):
                print('Entro al chequeo de email del proveedor')
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

            print('despues de agregar a la tabla')

            self.refresh_supplier_table()
            
            self.view.show_success("Producto registrado correctamente")

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
                self.view.show_warning("Por favor complete todos los campos")
                return False
        
        return True

    def __validate_supplier_email(self, email_field):
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        if not re.fullmatch(pattern, email_field):
            self.view.show_warning("Por favor coloquen correctamente")
            return False
        
        return True
    

    def refresh_supplier_table(self):
        """Refrescar la tabla de proveedores"""
        try:    
            suppliers = self.model.get_all_suppliers()
            self.view.refresh_supplier_table(suppliers)
        except Exception as e:
            self.view.show_error(f"Error al refrescar la tabla {str(e)}")

