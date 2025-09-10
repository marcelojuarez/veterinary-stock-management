from models.stock import StockModel
from tkinter import messagebox

class StockController:
    def __init__(self, view, stock_view=None):
        self.view = view
        self.stock_model = StockModel()
        self.stock_view = stock_view   

    def add_new_product(self, window=None):
        """Guardar nuevo producto"""
        try:
            # Obtener datos del formulario
            form_data = self.view.get_form_data()
            
            # Validaciones
            if not self._validate_form_data(form_data):
                return
            
            if not self._validate_product_id(form_data['id']):
                self.view.show_warning("Código del producto inválido. Debe tener 4 dígitos.")
                return
            
            # Convertir tipos
            product_data = {
                'id': form_data['id'],
                'name': form_data['name'],
                'desc': form_data['desc'],
                'brand': form_data['brand'],
                'price': float(form_data['price']),
                'qnt': int(form_data['qnt']),
            }

            self.stock_model.add_product(product_data)

            if window:
                window.destroy()
            
            # Refrescar tabla
            self.refresh_stock_table()
            
            self.view.show_success("Producto registrado correctamente")
            
        except ValueError as e:
            self.view.show_error(f"Error en los datos: {str(e)}")

        except Exception as e:
            self.view.show_error(f"Error al registar producto: código en uso")

    def delete_product(self):
        """Eliminar producto seleccionado"""
        try:
            selected_product = self.view.get_selected_product()
            
            if not selected_product:
                self.view.show_warning("Por favor seleccione un producto")
                return
            
            if not self.view.ask_confirmation("¿Eliminar el producto seleccionado?"):
                return
            
            # Eliminar de base de datos
            self.stock_model.delete_product(selected_product['id'])
            
            # Refrescar tabla
            self.refresh_stock_table()
            
            self.view.show_success("Producto eliminado correctamente")
            
        except Exception as e:
            self.view.show_error(f"Error al eliminar producto: {str(e)}")

    def find_product(self):
        """Buscar producto por ID o nombre"""
        try:
            form_data = self.view.get_find_data()
            name = form_data['name']
            
            if not (name):
                self.view.show_warning("Ingrese ID o nombre para buscar")
                return
            
            search_term = name
            results = self.stock_model.search_products(search_term)
            
            if results:
                self.view.refresh_stock_table(results)
            
                if len(results) == 1:
                    self.view.show_success("Se encontró 1 producto")
                else:
                    self.view.show_success(f"Se encontraron {len(results)} productos. El más relevante se cargó en el formulario.")
            else:
                self.view.show_warning("No se encontraron productos")
                
        except Exception as e:
            self.view.show_error(f"Error al buscar producto: {str(e)}")

    def refresh_stock_table(self):
        """Refrescar tabla de stock"""
        try:
            products = self.stock_model.get_all_products()
            self.view.refresh_stock_table(products)
        except Exception as e:
            self.view.show_error(f"Error al refrescar tabla: {str(e)}")
    
    def _validate_form_data(self, form_data):
        """Validar datos del formulario"""
        required_fields = ['id', 'name', 'desc', 'brand', 'price', 'qnt']
        
        for field in required_fields:
            if not form_data[field]:
                self.view.show_warning("Por favor complete todos los campos")
                return False
        
        # Validar tipos numéricos
        try:
            float(form_data['price'])
            int(form_data['qnt'])
        except ValueError:
            self.view.show_warning("Los precios y cantidad deben ser números válidos")
            return False
        
        return True
    
    def _validate_product_id(self, product_id):
        """Validar formato del ID del producto"""
        if len(product_id) != 4:
            return False
        
        # Verificar que todos sean dígitos
        return product_id.isdigit()