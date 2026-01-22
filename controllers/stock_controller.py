from models.stock import StockModel
from models.supplier import SupplierModel
from tkinter import messagebox
from db.database import db
from models.payment_model import PaymentModel
class StockController:
    def __init__(self, view, stock_view=None):
        self.view = view
        self.stock_model = StockModel()
        self.stock_view = stock_view   
        self.supplier_mdl = SupplierModel()
        self.all_products = []
        self.payment_model = PaymentModel()
        if self.stock_view:
            self.load_products()

    def load_products(self):
        """Carga inicial (una sola vez)"""
        self.all_products = self.stock_model.get_all_products()
        self.stock_view.refresh_stock_table(self.all_products)

    def add_new_product(self, window=None):
        """Guardar nuevo producto"""
        try:
            # Obtener datos del formulario
            form_data = self.view.get_form_data()

            print(form_data)

            print(f'Supplier cuit tiene {form_data['Cuit_supplier']}')

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
                'Cuit_supplier': form_data['Cuit_supplier'],
                'Name': (form_data['Name']).upper(),
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
            self.stock_model.delete_product(selected_product)
            
            # Refrescar tabla
            self.refresh_stock_table()
            
            self.view.show_success("Producto eliminado correctamente")
            
        except Exception as e:
            self.view.show_error(f"Error al eliminar producto: {str(e)}")

    def find_product(self, find_entry=None):
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
                find_entry.set("")
                self.view.refresh_stock_table(results)
            
                if len(results) >= 1:
                    self.view.show_success(f"Se encontraron {len(results)} productos")
            else:
                self.view.show_warning("No se encontraron productos")
                
        except Exception as e:
            self.view.show_error(f"Error al buscar producto: {str(e)}")

    def find_product_live(self, search_text):
        search_text = search_text.strip().lower()

        if not search_text:
            self.view.refresh_stock_table(self.all_products)
            return

        filtered = [
            product for product in self.all_products
            if search_text in str(product[2]).lower()  # name
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
                'Cuit_supplier': 'cuit_supplier',
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
            elif field == 'Name':
                new_value = new_value.upper()
            
            # Actualizar en base de datos
            self.stock_model.update_field(db_field, new_value, product_id)
            
            return True
            
        except Exception as e:
            print(f"Error updating product field: {e}")
            return False
    
    def update_product_price(self, product_id, product_data):
        """Actualizar un producto existente (manejo híbrido de rentabilidad/precio)"""
        
        current_product = self.stock_model.get_product_by_id(product_id)
        if not current_product:
            raise ValueError(f"Producto {product_id} no encontrado")

        (
            _,
            _,
            _,
            old_profit,
            old_cost,
            old_sale_price,
            iva,
            _,
            _,
            created_at,
            quantity
        ) = current_product

        # Nuevos valores
        new_cost = float(product_data['CostPrice'])
        new_sale_price = float(product_data['SalePrice'])
        new_profit = float(product_data['Profit']) if product_data.get('Profit') else old_profit

        # Lógica híbrida
        if new_cost != old_cost and new_sale_price == old_sale_price:
            new_sale_price = round(new_cost * (1 + old_profit / 100), 2)
        elif new_sale_price != old_sale_price:
            new_profit = round(((new_sale_price - new_cost) / new_cost) * 100, 2)

        # Recalcular Precio con IVA
        if iva == "21%":
            price_with_iva = round(new_sale_price * 1.21, 2)
        elif iva == "10.5%":
            price_with_iva = round(new_sale_price * 1.105, 2)
        else:
            price_with_iva = new_sale_price

        complete_product_data = {
            'Name': product_data['Name'],
            'Cuit_supplier': product_data['Cuit_supplier'],
            'Package': product_data['Package'],
            'Profit': new_profit,
            'CostPrice': new_cost,
            'SalePrice': new_sale_price,
            'Iva': iva,
            'PriceWIva': price_with_iva,
            'Stock': quantity,
        }
    
        self.stock_model.update_product(product_id, complete_product_data)
        self._reconcile_sales_with_product(product_id, old_sale_price, new_sale_price)
        self.refresh_stock_table()


    def _reconcile_sales_with_product(self, product_id, old_price, new_price):
        """Actualizar precios en ventas que contengan el producto modificado"""
        if abs(old_price - new_price) < 0.01:
            return
        
        try: 
            query = """
                SELECT DISTINCT s.id, s.cliente_id, c.nombre
                FROM sales s
                JOIN sale_items si ON si.sale_id = s.id
                LEFT JOIN clientes c ON c.id = s.cliente_id
                WHERE si.product_id = ? AND s.estado IN ('pending', 'partial')
            """
            affected_sales = db.fetch_all(query, (product_id,))

            if not affected_sales:
                return
            
            reconciled_count = 0
            credits_generate = 0

            for sale_id, cliente_id, cliente_nombre in affected_sales:
                old_status = db.fetch_one("SELECT estado FROM sales WHERE id = ?", (sale_id,))[0]
                new_status = self.payment_model.reconcile_sale(sale_id)
                reconciled_count += 1

                if old_status != 'paid' and new_status == 'paid':
                    credits_generate += 1

            if reconciled_count > 0:
                msg = f"✅ Se recalcularon {reconciled_count} venta(s) afectada(s) por el cambio de precio."
                
                if credits_generate > 0:
                    msg += f"\n{credits_generate} venta(s) quedaron pagadas y se generó saldo a favor."
                
                if new_price < old_price:
                    msg += f"\nPrecio bajó: ${old_price:.2f} → ${new_price:.2f}"
                else:
                    msg += f"\nPrecio subió: ${old_price:.2f} → ${new_price:.2f}"
                
                messagebox.showinfo("Ventas Reconciliadas", msg)
            
        except Exception as e:
            print(f"⚠️ Error al reconciliar ventas: {e}")
            # No bloqueamos la actualización de precio si falla la reconciliación



    def show_all_products(self):
        self.refresh_stock_table()
        self.view.show_success("Mostrando todos los artículos del inventario")

    def refresh_stock_table(self):
        """Refrescar tabla de stock"""
        try:
            products = self.stock_model.get_all_products()
            self.all_products = products
            self.view.refresh_stock_table(products)
        except Exception as e:
            self.view.show_error(f"Error al refrescar tabla: {str(e)}")
    
    def _validate_form_data(self, form_data):
        """Validar datos del formulario"""
        required_fields = ['Id', 'Cuit_supplier', 'Name', 'Package', 'Profit', 'CostPrice', 'Stock']
        
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
        product = self.stock_model.get_product_by_id(product_id)
        if product:
            self.view.show_error("Error al registrar el producto: Código en uso")        
        if len(product_id) != 4:
            return False
        
        # Verificar que todos sean dígitos
        return product_id.isdigit()