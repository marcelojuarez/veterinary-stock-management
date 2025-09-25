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
            
            if not self._validate_product_id(form_data['Id']):
                self.view.show_warning("Código del producto inválido. Debe tener 4 dígitos.")
                return
            
            cost_price = float(form_data['CostPrice'])
            profit = float(form_data['Profit'])
            
            sale_price = cost_price * (1 + profit / 100)

            product_data = {
                'Id': form_data['Id'],
                'Name': form_data['Name'],
                'Package': form_data['Package'],
                'Profit': profit,
                'CostPrice': cost_price,
                'SalePrice': round(sale_price, 2),
                'Iva': form_data['Iva'],
                'Stock': int(form_data['Stock']),
            }

            if form_data['Iva'] == "21%":
                product_data['PriceWIva'] = round(product_data['SalePrice'] * 1.21, 2)
            elif form_data['Iva'] == "10.5%":
                product_data['PriceWIva'] = round(product_data['SalePrice'] * 1.105, 2)
            else:
                product_data['PriceWIva'] = product_data['SalePrice']

            # Guardar en DB
            self.stock_model.add_product(product_data)

            if window:
                window.destroy()
            
            # Refrescar tabla
            self.refresh_stock_table()
            
            self.view.show_success("Producto registrado correctamente")
            
        except ValueError as e:
            self.view.show_error(f"Error en los datos: {str(e)}")

        except Exception as e:
            self.view.show_error(f"Error al registrar producto: {str(e)}")


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
            self.stock_model.delete_product(selected_product['Id'])
            
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
            
                if len(results) >= 1:
                    self.view.show_success(f"Se encontraron {len(results)} productos")
            else:
                self.view.show_warning("No se encontraron productos")
                
        except Exception as e:
            self.view.show_error(f"Error al buscar producto: {str(e)}")

    def update_product_field(self, product_id, field, new_value):
        """Actualizar un campo específico de un producto"""
        try:
            # Mapeo de nombres de columnas a nombres de BD
            field_mapping = {
                'Name': 'name',
                'Package': 'pack',
                'Profit': 'profit', 
                'Price': 'price',
                'Stock': 'quantity'
            }
            
            db_field = field_mapping.get(field)
            if not db_field:
                return False
            
            # Convertir tipos si es necesario
            if field == 'CostPrice':
                new_value = float(new_value)
            elif field == 'Stock':
                new_value = int(new_value)
            
            # Actualizar en base de datos
            self.stock_model.update_field(db_field, new_value, product_id)
            
            return True
            
        except Exception as e:
            print(f"Error updating product field: {e}")
            return False

    def refresh_stock_table(self):
        """Refrescar tabla de stock"""
        try:
            products = self.stock_model.get_all_products()
            self.view.refresh_stock_table(products)
        except Exception as e:
            self.view.show_error(f"Error al refrescar tabla: {str(e)}")
    
    def _validate_form_data(self, form_data):
        """Validar datos del formulario"""
        required_fields = ['Id', 'Name', 'Package', 'Profit', 'CostPrice', 'Stock']
        
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
    
    def _validate_product_id(self, product_id):
        """Validar formato del ID del producto"""
        if len(product_id) != 4:
            return False
        
        # Verificar que todos sean dígitos
        return product_id.isdigit()