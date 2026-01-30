from models.stock import StockModel
from models.sale import SalesModel
from models.customer import CustomerModel
from models.remito import RemitoModel
from tkinter import messagebox
from controllers.invoice_controller import InvoiceController
from services.remito_pdf import RemitoPDF

class SalesController:
    def __init__(self):
        self.sales_view = None
        self.stock_model = StockModel()
        self.sales_model = SalesModel()
        self.customer_model = CustomerModel()
        self.remito_model = RemitoModel()

    def set_view(self, view):
        self.sales_view = view

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
            for row in rows:
                pid = row[0]
                name = row[2]
                price_w_iva = row[8]
                qty = row[11]

                if qty and int(qty) > 0:
                    count += 1
                    self.sales_view.product_tree.insert(
                        "",
                        "end",
                        values=(pid, name, f"{price_w_iva:.2f}", int(qty))
                    )

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
                current_qty = current_item[2]  # La cantidad siempre está en posición 2
                new_qty = current_qty + quantity
                
                if new_qty > stock:
                    self.sales_view.show_warning("Stock insuficiente.")
                    return False

                # Actualizar manteniendo la estructura original (4 o 5 elementos)
                if len(current_item) == 5:  # Tiene observaciones (honorario)
                    self.sales_view.items_in_sale[existing_item] = (
                        product_id, name, new_qty, price, current_item[4]
                    )
                else:  # Producto normal
                    self.sales_view.items_in_sale[existing_item] = (
                        product_id, name, new_qty, price
                    )
            else:
                # Nuevo producto (siempre 4 elementos, sin observaciones)
                self.sales_view.items_in_sale.append((product_id, name, quantity, price))

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

    def search_products_live(self):
        """Buscar productos en tiempo real mientras se escribe"""
        search_text = self.sales_view.search_var.get().strip().lower()
        
        # Si no hay texto de búsqueda, mostrar todos los productos
        if not search_text:
            self.sales_view.refresh_product_tree(self.sales_view.all_products)
            return
        
        # Filtrar productos que coincidan con la búsqueda
        filtered_products = []
        
        for product in self.sales_view.all_products:
            (pid, name, pack, profit, cost, price, 
            iva, price_with_iva, created_at, last_update, qty) = product
            
            # Buscar en: ID, nombre y envase
            if (search_text in str(pid).lower() or 
                search_text in str(name).lower() or 
                search_text in str(pack).lower()):
                filtered_products.append(product)
        
        # Actualizar tabla con resultados filtrados
        self.sales_view.refresh_product_tree(filtered_products)
        

    def confirm_sale(self):
        """Procesar venta y actualizar stock"""
        try:
            items = self.sales_view.items_in_sale
            if not items:
                self.sales_view.show_warning("No hay productos en la venta.")
                return

            total = 0
            for item in self.sales_view.items_in_sale:
                if len(item) == 5:  # Tiene observaciones (honorarios)
                    _, _, qty, price, _ = item
                else:  # Producto normal
                    _, _, qty, price = item
                total += qty * price

            cliente_nombre = self.sales_view.client_var.get()
            cliente_id = self.customer_model.get_client_id_by_name(cliente_nombre)

            if cliente_id is None:
                cliente_id = None

            estado = "paid" if self.sales_view.payment_type_var.get() == "PAID" else "pending"

            sale_id = self.sales_model.register_sale(total, items, cliente_id, estado)

            invoice = InvoiceController()

            pdf = invoice.generate_invoice(cliente_id, items)

            self.sales_view.show_success(f"Venta registrada.\nFactura creada: {pdf}")
            self.sales_view.last_sale_id = sale_id
            # self.ask_remito(f"¿Desea generar remito?")
            self.sales_view.clear_sale()
            self.sales_view.load_available_products()

        except Exception as e:
            self.sales_view.show_error(f"Error al procesar venta: {e}")

    def show_today_sales(self):
        """Mostrar ventas del día en una vista con tabla"""
        try:
            rows = self.sales_model.get_today_sales()
            if not rows:
                self.sales_view.show_warning("No hay ventas registradas hoy.")
                return

            self.sales_view.open_today_sales_window(rows)

        except Exception as e:
            self.sales_view.show_error(f"Error al listar ventas: {e}")

    def get_all_clients_with_data(self):
        """Retorna lista completa de clientes con todos sus datos"""
        # Ejemplo de implementación:
        clients = self.customer_model.get_all_clients()
        return [
            {
                "nombre": client[1],
                "cuit": client[2],
                "domicilio": client[3]
            }
            for client in clients
        ]

    def get_client_names(self):
        """Obtener nombres de clientes para el combo de ventas"""
        try:
            clients = self.customer_model.get_all_clients()
            return [c[1] for c in clients] if clients else ["Consumidor Final"]
        except Exception:
            return ["Consumidor Final"]
        
    def get_client_data(self, client_name):
        """Obtener datos completos del cliente por nombre"""
        try:
            client = self.customer_model.get_client_by_name(client_name)
            if client:
                return {
                    "id": client[0],
                    "nombre": client[1],
                    "cuit": client[2],
                    "domicilio": client[3]
                }
            return None
        except Exception as e:
            print(f"Error obteniendo cliente: {e}")
            return None
        
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



