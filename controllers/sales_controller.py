from models.stock import StockModel
from models.sale import SalesModel
from tkinter import messagebox

class SalesController:
    def __init__(self, sales_view):
        self.sales_view = sales_view
        self.stock_model = StockModel()
        self.sales_model = SalesModel()


    def search_product_for_sale(self, search_term: str):
        """Buscar productos para la SalesView y llenar la tabla de disponibles"""
        try:
            term = (search_term or "").strip()
            if not term:
                self.sales_view.show_warning("Ingrese nombre o código para buscar")
                return

            rows = self.stock_model.search_products(term)
            # llenar tabla de disponibles (solo productos con stock > 0)
            self.sales_view.product_tree.delete(*self.sales_view.product_tree.get_children())

            count = 0
            for (pid, name, pack, profit, cost, price, iva, price_w_iva,
                created_at, last_update, qty) in rows:
                if qty and int(qty) > 0:
                    self.sales_view.product_tree.insert(
                        "", "end",
                        values=(pid, name, f"{price_w_iva:.2f}", int(qty))
                    )
                    count += 1

            if count == 0:
                self.sales_view.show_warning("No se encontraron productos disponibles")
            else:
                self.sales_view.show_success(f"Se encontraron {count} productos")

        except Exception as e:
            self.sales_view.show_error(f"Error al buscar producto: {e}")

    def add_product_to_sale(self, product_id, name, price, stock, qty_input):
        """Validar y agregar producto a la venta"""
        try:
            quantity = int(qty_input)
            stock = int(stock)
            price = float(price)

            if quantity <= 0:
                self.sales_view.show_warning("La cantidad debe ser mayor a 0.")
                return False
            if quantity > stock:
                self.sales_view.show_warning(f"Solo hay {stock} unidades disponibles.")
                return False

            # Buscar si ya existe en la venta
            existing_item = None
            for i, (pid, qty, p) in enumerate(self.sales_view.items_in_sale):
                if pid == product_id:
                    existing_item = i
                    break

            if existing_item is not None:
                # Ya existe: sumar cantidad
                current_qty = self.sales_view.items_in_sale[existing_item][1]
                new_qty = current_qty + quantity
                if new_qty > stock:
                    self.sales_view.show_warning("Stock insuficiente.")
                    return False

                self.sales_view.items_in_sale[existing_item] = (product_id, new_qty, price)
            else:
                # Nuevo producto
                self.sales_view.items_in_sale.append((product_id, quantity, price))

            return True

        except ValueError:
            self.sales_view.show_error("Ingrese una cantidad válida.")
            return False

    def delete_item(self):
        """Eliminar item seleccionado de la venta"""
        if not self.sales_view.ask_confirmation("¿Eliminar artículo?"):
            return

        if self.sales_view.delete_selected_product():
            self.sales_view.show_success("Artículo eliminado correctamente.")
        else:
            self.sales_view.show_warning("Seleccione el artículo que desea eliminar.")


    def confirm_sale(self, p):
        """Procesar venta y actualizar stock"""
        try:
            items = self.sales_view.items_in_sale
            if not items:
                self.sales_view.show_warning("No hay productos en la venta.")
                return

            total = sum(q * p for _, q, p in items)

            # Registrar la venta
            sale_id = self.sales_model.register_sale(total, items)

            # Descontar stock
            '''
            print(items)
            for product_id, quantity, _ in items:
                print(product_id)
                self.stock_model.reduce_quantity(product_id, quantity)
            '''

            # Actualizar vista
            self.sales_view.show_success(f"Venta registrada correctamente (ID: {sale_id})")
            self.sales_view.clear_sale()
            self.sales_view.load_available_products()

        except Exception as e:
            self.sales_view.show_error(f"Error al procesar venta: {e}")


    def show_today_sales(self):
        """Mostrar un resumen de las ventas del día"""
        try:
            rows = self.sales_model.get_today_sales()
            if not rows:
                self.sales_view.show_warning("No hay ventas registradas hoy.")
                return

            msg = "🧾 Ventas de hoy:\n\n"
            total_dia = 0
            for sale_id, date, total in rows:
                msg += f"• Venta #{sale_id} - {date} - Total ${total:.2f}\n"
                total_dia += total

            msg += f"\nTOTAL DEL DÍA: ${total_dia:.2f}"
            self.sales_view.show_success(msg)

        except Exception as e:
            self.sales_view.show_error(f"Error al listar ventas: {e}")
