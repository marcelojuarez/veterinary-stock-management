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
            event_bus
        ):
        self.sales_view = None
        self.customer_model = customer_model
        self.remito_model = remito_model
        self.sales_model = sales_model
        self.stock_model = stock_model
        self.invoice_controller = invoice_controller
        self.event_bus = event_bus

    def set_view(self, view):
        self.sales_view = view
        self.event_bus.subscribe('refresh_stock_in_sale_view', self.sales_view.load_available_products)

    def add_product_to_sale(self, product_id, name, pack, price, stock, qty_input):
        """Validar y agregar producto a la venta"""
        try:
            quantity = int(qty_input)

            if quantity <= 0:
                self.sales_view.show_warning("La cantidad debe ser mayor a 0.")
                return False
            
            if quantity > stock:
                self.sales_view.show_warning(f"Solo hay {stock} unidades disponibles.")
                return False

            # Buscar si ya existe en la venta - FIX: Manejar items con 4 o 5 elementos
            existing_item = None
            for i, item in enumerate(self.sales_view.items_in_sale):
                # El ID siempre está en la posición 0
                if item[0] == product_id:
                    existing_item = i
                    break

            if existing_item is not None:
                # Ya existe: sumar cantidad
                current_item = self.sales_view.items_in_sale[existing_item]
                current_qty = current_item[3]  # La cantidad siempre está en posición 2
                new_qty = current_qty + quantity
                
                if new_qty > stock:
                    self.sales_view.show_warning("Stock insuficiente.")
                    return False

                self.sales_view.items_in_sale[existing_item] = (
                        product_id, name, pack, new_qty, price
                )
            else:
                # Nuevo producto (siempre 4 elementos, sin observaciones)
                self.sales_view.items_in_sale.append((product_id, name, pack, quantity, price))

            return True

        except ValueError:
            self.sales_view.show_error("Ingrese una cantidad válida.")
            return False

    def search_products_live(self, search_text):
        """Buscar productos en tiempo real mientras se escribe"""
        search_text = search_text.strip().lower()
        
        # Si no hay texto de búsqueda, mostrar todos los productos
        if not search_text:
            self.sales_view.refresh_product_tree(self.sales_view.all_products)
            return
        
        # Filtrar productos que coincidan con la búsqueda
        filtered_products = []
        
        for product in self.sales_view.all_products:
            pid, name, _, _, _, _, _, _, _, _, _, _, _, = product

            # Buscar en: ID, nombre 
            if (search_text in str(pid).lower() or 
                search_text in str(name).lower()):
                filtered_products.append(product)
        
        # Actualizar tabla con resultados filtrados
        self.sales_view.refresh_product_tree(filtered_products)
        
    ## -- Confirmar compra -- ##
    def confirm_sale(self):
        """Procesar venta y actualizar stock"""
        try:
            items = self.sales_view.items_in_sale
            if not items:
                self.sales_view.show_warning("No hay productos en la venta.")
                return

            total = Decimal('0.00')
            for item in self.sales_view.items_in_sale:
                if len(item) == 6:  # Tiene observaciones (honorarios)
                    _, _, _, qty, price, _ = item
                else:  # Producto normal
                    _, _, _, qty, price = item
                total += qty * price

            # total normalizado
            total = norm_to_2_dec(total)
            cliente_nombre = self.sales_view.client_var.get()
            cliente_id = self.customer_model.get_client_id_by_name(cliente_nombre)

            if cliente_id is None:
                cliente_id = None

            estado = "paid" if self.sales_view.payment_type_var.get() == "PAID" else "pending"

            retenciones = self.sales_view.get_retenciones()

            sale_id = self.sales_model.register_sale(total, items, cliente_id, estado, retenciones)

            pdf = self.invoice_controller.generate_invoice(cliente_id, items)
            self.sales_view.show_success(f"Venta registrada.\nFactura creada: {pdf}")

            self.sales_view.last_sale_id = sale_id
            debt = self.customer_model.get_total_debt(cliente_id)

            if estado == "pending":
                # Se genera el remito en compras por cuenta corriente 
                data = {
                    "client_id": cliente_id,
                    "type": "VENTA",
                    "description": f"Venta #{sale_id} · {qty} producto(s) · PENDIENTE",
                    "amount": total,
                    "payment": Decimal('0.00'),
                    "debt": debt,
                    "reference_id" : sale_id,
                    "reference": ''
                }
                self.customer_model.add_row_in_customer_ledger(data)
                self.sales_view.generate_delivery_note()
            self.sales_view.clear_sale()
            self.event_bus.publish('refresh_stock_table', None)
            self.sales_view.load_available_products()

        except Exception as e:
            self.sales_view.show_error(f"Error al procesar venta: {e}")

    ## -- Permite renderizar la ventana de ventas del dia-- ##
    def show_today_sales(self):
        """Mostrar ventas del día en una vista con tabla"""
        try:
            rows = self.sales_model.get_today_sales()
            if not rows:
                self.sales_view.show_warning("No hay ventas registradas hoy.")
                return

            self.sales_view.open_sales_query_window()

        except Exception as e:
            self.sales_view.show_error(f"Error al listar ventas: {e}")

    ## -- Crea el remito asociado a una venta -- ##
    def create_delivery_note(self, sale_id):
        sale = self.sales_model.get_sale_by_id(sale_id)
        items = self.sales_model.get_sale_items(sale_id)
        customer = self.customer_model.find_customer_by_id(sale['customer_id'])
        number = self.remito_model.get_next_number()

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
        """
        Obtener ventas por rango de fechas y opcionalmente filtradas por estado
        
        Args:
            fecha_desde (str): Fecha inicial en formato YYYY-MM-DD
            fecha_hasta (str): Fecha final en formato YYYY-MM-DD  
            estado (str, optional): Estado de la venta ('paid', 'pending', 'partial', None para todos)
        
        Returns:
            list: Lista de tuplas (sale_id, fecha, total, cliente, estado, pagado)
        """
        try:
            
            # Ejecutar query
            rows = self.sales_model.get_sales_by_date_range(fecha_desde, fecha_hasta, estado=estado)            
            return rows
            
        except Exception as e:
            print(f"Error al obtener ventas por rango de fechas: {e}")
            return []
