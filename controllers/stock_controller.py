import logging
from db.database import db
from decimal import Decimal
from tkinter import messagebox

logger = logging.getLogger(__name__)
class StockController:
    def __init__(self, stock_model, supplier_model, payment_model, event_bus):
        self.view = None

        self.stock_model = stock_model
        self.supplier_mdl = supplier_model

        self.all_products = []
        self.payment_model = payment_model
        self.event_bus = event_bus
        self.event_bus.subscribe('stock_change', self.refresh_stock_table)

        if self.view:
            self.load_products()

    # Setters
    def set_view(self, view):
        self.view = view        

    def reload_products(self):
        """Carga todos los productos desde la DB, en memoria"""
        self.all_products = self.stock_model.get_all_products()
        
    def load_products(self):
        """Carga inicial de productos"""
        self.reload_products()
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

            # Eliminar de base de datos (soft delete si tiene historial asociado)
            result = self.stock_model.delete_product(selected_product)

            # Refrescar tablas de stock
            self.event_bus.publish('stock_change', None)

            if result == "deactivated":
                self.view.show_info(
                    "El producto tiene ventas, compras o movimientos asociados, así que "
                    "no se puede borrar sin perder ese historial.\n\n"
                    "Se marcó como DESCONTINUADO: ya no aparece en ventas, compras ni "
                    "inventario, pero su historial queda intacto."
                )
            else:
                self.view.show_success("Producto eliminado correctamente")

        except Exception as e:
            self.view.show_error(f"Error al eliminar producto: {str(e)}")

    def find_product_live(self, search_text):
        """Muestra la lista de productos que corresponde a la busqueda"""
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
            logger.error("Error updating product field: %s", e)
            return False
    
    def add_product(self, data: dict):
        """Agregar un producto nuevo directamente al stock."""
        try:
            self.stock_model.add_product(data)
            self.event_bus.publish('stock_change', None)
            self.view.show_success("Producto agregado correctamente")
        except Exception as e:
            logger.error("Error al agregar producto: %s", e)
            self.view.show_error(f"Error al agregar producto: {str(e)}")

    def refresh_stock_table(self):
        """Refresca tabla de stock"""
        try:
            self.reload_products()
            self._apply_current_search()
        except Exception as e:
            self.view.show_error(f"Error al refrescar tabla: {str(e)}")

    def _apply_current_search(self):
        """Aplica el filtro activo o muestra todo si no hay busqueda"""
        search_text = self.view.find_entry.get().strip()

        if search_text:
            self.find_product_live(search_text)
        else:
            self.view.refresh_stock_table(self.all_products)