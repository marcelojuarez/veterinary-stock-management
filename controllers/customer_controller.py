from models.customer import CustomerModel
from tkinter import messagebox
import re

class CustomerController: 
    def __init__(self, view):
        self.view = view
        self.model = CustomerModel()
        
        self.refresh_customer_table()

    def add_new_customer(self, window=None):
        # Guardar nuevo cliente 
        try: 
            data = self.view.get_customer_data()
            
            if not self.__validate_customer_data(data):
                return 
            
            if not self.__validate_supplier_cuit(data['cuit']):
                print('Entro al chequeo de cuit del proveedor')
                return
            
            if not self.__validate_supplier_phone(data['telefono']):
                return
            
            self.model.add_customer(data)
            self.refresh_customer_table()
            self.clear_form()

            if window: 
                window.destroy()

                self.view.show_success("Cliente registrado correctamente.")
        except ValueError as e:
            self.view.show_error(f"Error en los datos: {str(e)}")
        except Exception as e:
            self.view.show_error(f"Error al registrar el cliente: {str(e)}")

    def update_customer_debt(self, customer_id, monto_deuda):
        # Actualizamos solamente monto_deuda
        try: 
            self.model.update_customer_info(customer_id, monto_deuda)
            self.refresh_customer_table()
            self.view.show_success("Deuda actualizada correctamente")
        except Exception as e: 
            self.view.show_error(f"Error al actualizar la deuda: {str(e)}")
    
    def delete_customer(self, customer_id):
        # Eliminar cliente seleccionado 
        confirm = messagebox.askyesno("Confirmar", "¿Desea eliminar este cliente?")
        if confirm: 
            try: 
                self.model.delete_customer(customer_id)
                self.refresh_customer_table()
                self.view.show_success("Cliente eliminado correctamente")
            except Exception as e:
                self.view.show_error(f'Error al eliminar cliente: {str(e)}')

    def search_customer(self, term):
        # Buscar cliente por nombre o id
        try:
            customers = self.model.search_customer(term)
            self.view.refresh_customer_table(customers)
        except Exception as e:
            self.view.show_error(f"Error al buscar cliente: {str(e)}")

    
    def clear_form(self):
        """Limpiar formulario de la vista"""
        self.view.name_var.set("")
        self.view.cuit_var.set("")
        self.view.home_var.set("")
        self.view.phone_var.set("")
        self.view.debt_amount_var.set(0.0)

    def __validate_customer_data(self, data):
        # Validar campos obligatorios 
        required_fields = ['nombre', 'cuit', 'domicilio', 'telefono']
        for field in required_fields:
            if not data[field]:
                self.view.show_warning(f'Por favor complete el campo {field}.')
                return False 
        return True
    
    def refresh_customer_table(self):
        try:
            customers = self.model.get_all_customers()
            self.view.refresh_customer_table(customers)
        except Exception as e:
            self.view.show_error(f"Error al refrescar la tabla: {e}")

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