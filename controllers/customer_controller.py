from models.customer import CustomerModel
from models.payment_model import PaymentModel
from tkinter import messagebox
import re
from utils.pdf_generator import generate_payment_receipt
import os

class CustomerController: 
    def __init__(self, view):
        self.view = view
        self.model = CustomerModel()
        self.payment_model = PaymentModel()
        self.refresh_customer_table()

    def add_new_customer_window(self, data, window):
        """Guarda un nuevo cliente desde la ventana modal"""
        try:
            # Validaciones básicas
            if not self.__validate_customer_data(data):
                return False
            if not self.__validate_supplier_cuit(data["cuit"]):
                return False
            if not self.__validate_supplier_phone(data["telefono"]):
                return False

            # Guardar cliente
            self.model.add_customer(data)
            self.refresh_customer_table()
            self.view.show_success("Cliente agregado correctamente.")
            window.destroy()
            return True

        except ValueError as e:
            self.view.show_error(f"Error en los datos: {str(e)}")
            return False
        except Exception as e:
            self.view.show_error(f"Error al registrar el cliente: {str(e)}")
            return False

    def delete_customer(self, customer_id):
        """Elimina un cliente por su ID"""
        confirm = messagebox.askyesno("Confirmar", "¿Desea eliminar este cliente?")
        if not confirm:
            return False

        try:
            self.model.delete_customer(customer_id)
            self.refresh_customer_table()
            self.view.show_success("Cliente eliminado correctamente.")
            return True
        except Exception as e:
            self.view.show_error(f"Error al eliminar el cliente: {str(e)}")
            return False


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
    # --------------------------------------------------------------------
    # 💳 DEUDAS DE CLIENTES
    # --------------------------------------------------------------------
    def show_customer_debts(self, cliente_id, cliente_nombre):
        """Abre ventana con las deudas del cliente"""
        try:
            debts = self.model.get_customer_debts(cliente_id)
            total = self.model.get_total_debt(cliente_id)
            self.view.open_debt_window(cliente_id, cliente_nombre, debts, total)
        except Exception as e:
            self.view.show_error(f"Error al obtener las deudas: {e}")

    def load_sale_items_for_debt(self, sale_id):
        """Carga el detalle de productos de una venta fiada en la vista"""
        try:
            items = self.model.get_sale_items(sale_id)
            self.view.update_debt_items_table(items)
        except Exception as e:
            self.view.show_error(f"Error al obtener los productos de la venta: {e}")

    def customer_has_debts(self, customer_id):
            """Obtengo la cantidad de deudas de un cliente"""
            try: 
                query = "SELECT COUNT(*) FROM sales WHERE cliente_id = ? AND estado = 'fiada';"
                result = self.model.db.fetch_one(query,(customer_id,))
                return result and result[0] > 0
            except Exception as e:
                self.view.show_error(f"Error al obtener las deudas del cliente: {e}")

    def register_payment(self, sale_id, client_id, amount, method, window):
        try:
            self.payment_model.create_payment(
                sale_id=sale_id,
                client_id=client_id,
                amount=amount,
                method=method,
                notes="Payment through UI"
            )

            self.payment_model.update_sale_status(sale_id)

            debts = self.model.get_customer_debts(client_id)
            total = self.model.get_total_debt(client_id)

            self.view.update_debt_window(debts, total)

            window.destroy()
            self.view.show_success("Pago registrado con éxito.")

            # 6) PREGUNTA: ¿Desea generar comprobante?
            generar = messagebox.askyesno(
                "Generar Comprobante",
                "¿Desea generar el comprobante de pago?"
            )

            if generar:
                receipt_path = generate_payment_receipt(
                    client_name=self.model.find_customer_by_id(client_id)[1],
                    sale_id=sale_id,
                    payment_amount=amount,
                    method=method,
                    sale_info=self.payment_model.get_sale_balance(sale_id),
                    payments=self.payment_model.get_payments_for_sale(sale_id)
                )

                self.view.show_success("Comprobante generado con éxito.")
                
                # Abrir el PDF automáticamente (solo Windows)
                try:
                    os.startfile(receipt_path)
                except:
                    pass

        except Exception as e:
            self.view.show_error(f"Error: {e}")
