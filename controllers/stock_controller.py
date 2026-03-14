from db.database import db
from decimal import Decimal
from tkinter import messagebox
class StockController:
    def __init__(self, stock_model, supplier_model, payment_model, event_bus):
        self.view = None

        self.stock_model = stock_model
        self.supplier_mdl = supplier_model

        self.all_products = []
        self.payment_model = payment_model
        self.event_bus = event_bus
        self.event_bus.subscribe('refresh_stock_table', self.refresh_stock_table)

        if self.view:
            self.load_products()

    # Setters
    def set_view(self, view):
        self.view = view        

    def load_products(self):
        """Carga inicial (una sola vez)"""
        self.all_products = self.stock_model.get_all_products()
        self.view.refresh_stock_table(self.all_products)

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
            self.stock_model.delete_product(selected_product)
            
            # Refrescar tabla
            self.refresh_stock_table()
            self.event_bus.publish('refresh_products_on_p_win', None)
            
            self.view.show_success("Producto eliminado correctamente")
            
        except Exception as e:
            self.view.show_error(f"Error al eliminar producto: {str(e)}")

    def find_product_live(self, search_text):
        search_text = search_text.strip().lower()

        if not search_text:
            self.view.refresh_stock_table(self.all_products)
            return

        filtered = [
            product for product in self.all_products
            if search_text in str(product[1]).lower()  # name
            or search_text in str(product[0]).lower()  # id
            or search_text in str(product[3]).lower()  # pack
        ]

        self.view.refresh_stock_table(filtered)

    def update_product_field(self, product_id, field, new_value):
        """Actualizar un campo específico de un producto"""
        try:
            # Mapeo de nombres de columnas a nombres de BD
            field_mapping = {
                'Name': 'name',
                'Package': 'pack',
            }
            
            db_field = field_mapping.get(field)
            if not db_field:
                return False
            
            new_value = new_value.upper()
            
            # Actualizar en base de datos
            self.stock_model.update_field(db_field, new_value, product_id)
            
            return True
            
        except Exception as e:
            print(f"Error updating product field: {e}")
            return False
    
    def show_all_products(self):
        self.refresh_stock_table()
        self.view.show_success("Mostrando todos los artículos del inventario")

    def refresh_stock_table(self):
        """Refrescar tabla de stock"""
        try:
            print('Se Refresca la tabla')
            products = self.stock_model.get_all_products()
            self.all_products = products
            self.view.refresh_stock_table(products)
        except Exception as e:
            self.view.show_error(f"Error al refrescar tabla: {str(e)}")