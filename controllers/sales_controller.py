"""
controllers/sales_controller.py
"""

from decimal import Decimal
from tkinter import messagebox
from services.remito_pdf import RemitoPDF
from utils.utils import norm_to_2_dec


class SalesController:
    def __init__(
            self,
            customer_model,
            remito_model,
            sales_model,
            stock_model,
            invoice_controller,
            event_bus,
            fraction_model=None
        ):
        self.sales_view         = None
        self.customer_model     = customer_model
        self.remito_model       = remito_model
        self.sales_model        = sales_model
        self.stock_model        = stock_model
        self.invoice_controller = invoice_controller
        self.event_bus          = event_bus
        self.fraction_model     = fraction_model

    def set_view(self, view):
        self.sales_view = view
        self.event_bus.subscribe('refresh_stock_in_sale_view', self.sales_view.load_available_products)

    # ─────────────────────────────────────────────────────────────────────
    # AGREGAR PRODUCTO A LA VENTA
    # ─────────────────────────────────────────────────────────────────────

    def add_product_to_sale(self, product_id, name, pack, price, stock,
                            qty_input,
                            is_fractional=False,
                            unit='UNIDAD',
                            fraction_price=None):
        """
        Formatos de tupla que se agregan a items_in_sale:
          Normal      : (pid, name, pack, qty, price)              — len 5
          Honorarios  : (pid, name, pack, qty, price, obs)         — len 6
          Fraccionado : (pid, name, pack, qty, price, label, True) — len 7
                         label = "3 KG" (para mostrar en tabla)
        """
        try:
            if is_fractional:
                quantity = Decimal(str(qty_input).replace(',', '.'))
            else:
                quantity = int(qty_input)

            if quantity <= 0:
                self.sales_view.show_warning("La cantidad debe ser mayor a 0.")
                return False

            # Validar disponibilidad
            if is_fractional:
                if self.fraction_model and not self.fraction_model.has_enough_stock(product_id, quantity):
                    info = self.fraction_model.get_available_stock_info(product_id)
                    self.sales_view.show_warning(
                        f"Stock insuficiente.\nDisponible: {info.get('total_units', 0)} {unit}"
                    )
                    return False
            else:
                if quantity > stock:
                    self.sales_view.show_warning(f"Solo hay {stock} unidades disponibles.")
                    return False

            # Para productos normales: acumular si ya está en la venta
            # IMPORTANTE: solo acumular si el ítem existente también es normal (len 5)
            # Un ítem fraccionado (len 7) del mismo producto es una línea independiente
            if not is_fractional:
                for i, item in enumerate(self.sales_view.items_in_sale):
                    if item[0] == product_id and len(item) == 5:
                        current_qty = item[3]
                        new_qty     = current_qty + quantity
                        if new_qty > stock:
                            self.sales_view.show_warning("Stock insuficiente.")
                            return False
                        self.sales_view.items_in_sale[i] = (
                            product_id, name, pack, new_qty, price
                        )
                        return True

            # Agregar nuevo item
            if is_fractional:
                unit_label = f"{quantity} {unit}"
                self.sales_view.items_in_sale.append(
                    (product_id, name, pack, quantity, price, unit_label, True)
                )
            else:
                self.sales_view.items_in_sale.append(
                    (product_id, name, pack, quantity, price)
                )

            return True

        except ValueError:
            self.sales_view.show_error("Ingrese una cantidad válida.")
            return False

    # ─────────────────────────────────────────────────────────────────────
    # HELPER CENTRALIZADO — qty y price de cualquier formato de item
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def _unpack_qty_price(item):
        """
        qty y price siempre están en posiciones 3 y 4, sin importar el len.
          len 5 : (pid, name, pack, qty, price)
          len 6 : (pid, name, pack, qty, price, obs)
          len 7 : (pid, name, pack, qty, price, unit_label, True)
        """
        return item[3], item[4]

    # ─────────────────────────────────────────────────────────────────────
    # BÚSQUEDA EN VIVO
    # ─────────────────────────────────────────────────────────────────────

    def search_products_live(self, search_text=''):
        search_text = search_text.strip().lower()
        if not search_text:
            self.sales_view.refresh_product_tree(self.sales_view.all_products)
            return

        filtered = [
            p for p in self.sales_view.all_products
            if search_text in str(p[0]).lower() or search_text in str(p[1]).lower()
        ]
        self.sales_view.refresh_product_tree(filtered)

    # ─────────────────────────────────────────────────────────────────────
    # CONFIRMAR VENTA
    # ─────────────────────────────────────────────────────────────────────

    def confirm_sale(self):
        try:
            items = self.sales_view.items_in_sale
            if not items:
                self.sales_view.show_warning("No hay productos en la venta.")
                return

            total = Decimal('0.00')
            for item in items:
                qty, price = self._unpack_qty_price(item)
                total += Decimal(str(qty)) * Decimal(str(price))

            total          = norm_to_2_dec(total)
            cliente_nombre = self.sales_view.client_var.get()
            cliente_id     = self.customer_model.get_client_id_by_name(cliente_nombre)
            estado         = "paid" if self.sales_view.payment_type_var.get() == "PAID" else "pending"
            retenciones    = self.sales_view.get_retenciones()

            sale_id = self.sales_model.register_sale(total, items, cliente_id, estado, retenciones)

            pdf = self.invoice_controller.generate_invoice(cliente_id, items)
            self.sales_view.show_success(f"Venta registrada.\nFactura creada: {pdf}")

            self.sales_view.last_sale_id = sale_id
            debt = self.customer_model.get_total_debt(cliente_id)

            if estado == "pending":
                data = {
                    "client_id":    cliente_id,
                    "type":         "VENTA",
                    "description":  f"Venta #{sale_id} · PENDIENTE",
                    "amount":       total,
                    "payment":      Decimal('0.00'),
                    "debt":         debt,
                    "reference_id": sale_id,
                    "reference":    ''
                }
                self.customer_model.add_row_in_customer_ledger(data)
                self.sales_view.generate_delivery_note()

            self.sales_view.clear_sale()
            self.event_bus.publish('refresh_stock_table', None)
            self.sales_view.load_available_products()

        except Exception as e:
            self.sales_view.show_error(f"Error al procesar venta: {e}")

    # ─────────────────────────────────────────────────────────────────────
    # RESTO DE MÉTODOS (sin cambios)
    # ─────────────────────────────────────────────────────────────────────

    def show_today_sales(self):
        try:
            rows = self.sales_model.get_today_sales()
            if not rows:
                self.sales_view.show_warning("No hay ventas registradas hoy.")
                return
            self.sales_view.open_sales_query_window()
        except Exception as e:
            self.sales_view.show_error(f"Error al listar ventas: {e}")

    def create_delivery_note(self, sale_id):
        sale     = self.sales_model.get_sale_by_id(sale_id)
        items    = self.sales_model.get_sale_items(sale_id)
        customer = self.customer_model.find_customer_by_id(sale['customer_id'])
        number   = self.remito_model.get_next_number()

        delivery_note_id = self.remito_model.create_note(number, sale_id, customer[0])
        for it in items:
            self.remito_model.add_item(delivery_note_id, it['product_id'], it['quantity'])

        pdf_path = RemitoPDF().generate_remito(number, customer, items)
        self.sales_view.last_sale_id = None
        return pdf_path

    def ask_remito(self, message):
        if messagebox.askquestion("Confirmación", message) == "yes":
            self.sales_view.generate_delivery_note()

    def get_sales_by_date_range(self, fecha_desde, fecha_hasta, estado=None):
        try:
            return self.sales_model.get_sales_by_date_range(fecha_desde, fecha_hasta, estado=estado)
        except Exception as e:
            print(f"Error al obtener ventas por rango de fechas: {e}")
            return []