# controllers/supplier_controller.py
import re
from utils.view_helpers import show_warning, show_error, show_success, ask_confirmation

class SupplierController():
    def __init__(self, supplier_model, event_bus):
        self.model = supplier_model
        self.view = None
        self.info_view = None

        self.event_bus = event_bus

        self.event_bus.subscribe(
            'refresh_supplier_table',
            self.refresh_supplier_table
        )

    def set_view(self, view):
        self.view = view

    def set_info_view(self, info_view):
        self.info_view = info_view

    def add_new_supplier(self, window=None):
        """Guardar nuevo proveedor"""
        try:
            data = self.view.get_supplier_data()

            if not self.__validates_supplier_data(data):
                return

            if not self.validate_existing_address(None, data['address'], data['city']):
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
            
            if not self.__validate_supplier_address(data['address']):
                print('Entro al chequeo de domicilio del proveedor')
                return

            # convertir tipos
            supplier_data = {
                'name': data['name'].upper(),
                'cuit': data['cuit'],
                'address': data['address'].upper(),
                'city': data['city'].upper(),
                'province': data['province'].upper(),
                'country': data['country'].upper(),
                'phone': data['phone'].upper(),
                'email': data['email'].upper(),
                'iva_condition': data['iva_condition'].upper()
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

    def supplier_info(self, parent):

        try:
            # Obtengo las filas seleccionadas
            selected = self.view.supplier_tree.selection()
            
            if not selected:
                show_warning('Por favor seleccione un proveedor')
                return

            iid = selected[0] # id proveedor
            supplier_data = self.model.core.find_supplier_by_id(iid)
            debt = self.model.purchase.get_debt_of_supplier(iid)
            credit_amount = self.model.credit.get_credit_amount_of_supplier(iid)

            self.info_view.open_info_window(supplier_data, credit_amount, debt, parent)
        except Exception as e:
            print(f'Hubo un error: {e}')
    
    def __validates_supplier_data(self, form_data):
        required_files =  ['name', 'cuit', 'address', 'city', 'province', 'country', 'phone', 'email', 'iva_condition']

        for field in required_files:
            if not form_data[field]:
                show_warning("Por favor complete todos los campos.")
                return False
        
        return True
    
    def validate_existing_address(self, supplier_id, address, city):
        existing = self.model.core.find_supplier_by_address(
            address.strip().upper(), city.strip().upper()
        )

        if existing is None:
            return True

        if supplier_id is not None and str(existing[0]) == str(supplier_id):
            return True

        show_warning(
            f"Ya existe un Proveedor registrada con el domicilio: {address}.\n"
            f"Proveedor: {existing[2]} — CUIT: {existing[1]}"
        )
        return False

    def __validate_supplier_email(self, email_field):
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

        if email_field.strip() == '-':
            return True
        
        if not re.fullmatch(pattern, email_field):
            show_warning("Por favor coloquen el e-mail correctamente.")
            return False
        
        return True
    
    def __validate_supplier_cuit(self, cuit_field):
        pattern = r'^\d{2}-\d{8}-\d$'
        
        if not re.fullmatch(pattern, cuit_field):
            show_warning("Por favor coloque el CUIT correctamente. Formato: XX-XXXXXXXX-X")
            return False
        
        # if self.model.core.find_supplier_by_cuit(cuit_field) is not None:
        #     show_error(f"Error: Ya existe un proveedor con el CUIT: {cuit_field}")
        #     return False
        
        return True
    
    def __validate_supplier_phone(self, phone_field):
        pattern = r'^\+?\d{7,15}$'
        
        if phone_field.strip() == '-':
            return True

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
        if address_field.strip() == '-':
            return True

        if len(address_field) < 5 or len(address_field) > 150:
            show_warning("La dirección del proveedor debe tener entre 5 y 150 caracteres.")
            return False
        
        return True

    def refresh_supplier_table(self):
        """Refrescar la tabla de proveedores"""
        try:    
            print('Se refresca la tabla')
            self.view.suppliers = self.model.core.get_all_suppliers()
            self.view.refresh_supplier_table(self.view.suppliers)
        except Exception as e:
            show_error(f"Error al refrescar la tabla {str(e)}")

    ## -- Actualiza la info de un proveedor -- ##
    def update_supplier_data(self, supplier_id, supplier_data):
        try: 
            if not self.__validates_supplier_data(supplier_data):
                return False
            
            if not self.validate_existing_address(supplier_id, supplier_data['address'], supplier_data['city']):
                return False
            
            if not self.__validate_supplier_email(supplier_data['email']):
                return False
            
            if not self.__validate_supplier_cuit(supplier_data['cuit']):
                print('Entro al chequeo de cuit del proveedor')
                return False
            
            if not self.__validate_supplier_phone(supplier_data['phone']):
                print('Entro al chequeo de telefono del proveedor')
                return False
            
            if not self.__validate_supplier_name(supplier_data['name']):
                print('Entro al chequeo de nombre del proveedor')
                return False
            
            if not self.__validate_supplier_address(supplier_data['address']):
                print('Entro al chequeo de domicilio del proveedor')
                return False

            # convertir tipos
            supplier_data = {
                'name': supplier_data['name'].upper(),
                'cuit': supplier_data['cuit'],
                'address': supplier_data['address'].upper(),
                'city': supplier_data['city'].upper(),
                'province': supplier_data['province'].upper(),
                'country': supplier_data['country'].upper(),
                'phone': supplier_data['phone'].upper(),
                'email': supplier_data['email'].upper(),
                'iva_condition': supplier_data['iva_condition'].upper()
            }

            self.model.core.update_supplier_data(supplier_id, supplier_data)

            self.refresh_supplier_table()
            
            show_success("Proveedor Actualizado Correctamente.")

            return True

        except ValueError as e:
            show_error(f"Error en los datos {str(e)}")
            return False
        except Exception as e:
            show_error(f"Error al actualizar el proveedor: {str(e)}")
            return False

    ## -- Elimina un proveedor -- ##
    def delete_supplier(self):
        selected = self.view.supplier_tree.selection()

        if not selected:
            show_warning('Por favor seleccione un proveedor para eliminar')
            return

        iid = selected[0]
        values = self.view.supplier_tree.item(iid, "values")
        supplier_id = values[0]

        try:
            if self.model.core.has_purchases(supplier_id):
                # Tiene compras → ofrecer borrado lógico
                if not ask_confirmation(
                    'Este proveedor tiene compras asociadas y no puede eliminarse.\n\n'
                    '¿Desea desactivarlo? Dejará de aparecer en las listas '
                    'pero todo su historial se conservará.',
                    'Desactivar Proveedor'
                ):
                    return

                self.model.core.deactivate_supplier(supplier_id)
                self.refresh_supplier_table()

                if self.view.find_var.get() != "":
                    self.view.find_var.set('')

                show_success('El proveedor fue desactivado correctamente.')

            else:
                # Sin compras → eliminación física normal
                if not ask_confirmation(
                    '¿Eliminar el proveedor seleccionado?',
                    'Eliminar Proveedor'
                ):
                    return

                self.model.core.delete_supplier(supplier_id)
                self.refresh_supplier_table()

                if self.view.find_var.get() != "":
                    self.view.find_var.set('')

                show_success('El proveedor fue eliminado correctamente.')

        except Exception as e:
            print(e)
            show_warning('Error al procesar la solicitud')

 
