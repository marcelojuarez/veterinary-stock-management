from decimal import Decimal
from db.database import db
from utils.utils import norm_to_2_dec
from models.stock_movement import StockMovementModel

class StockModel:
    def __init__(self, sales_model, payment_model, event_bus, db_conection=None, stock_movement_model=None):
        self.db = db_conection or db
        self.sales_model = sales_model
        self.payment_model = payment_model
        self.event_bus = event_bus
        if self.event_bus is not None:
            self.event_bus.subscribe('clean_price_changes', self.clean_price_changes)
        self.changes = []
        self.movement = stock_movement_model or StockMovementModel()
    
    def clean_price_changes(self):
        self.changes = []

    def get_all_products(self):
        """Obtener todos los productos del stock"""
        query = """
            SELECT id, name, pack, list_price, discount, cost_price, profit, price, iva, 
                   price_with_iva, created_at, last_price_update, quantity
            FROM stock 
            WHERE name != "HONORARIOS"
            ORDER BY name
        """
        return db.fetch_all(query)
    
    def get_all_product_by_name(self, product_name):
        """Obtener un producto por su ID"""
        query = "SELECT id, pack FROM stock WHERE LOWER(name) = LOWER(?)"
        return db.fetch_all(query, (product_name,))
    
    def get_product_by_id(self, product_id):
        """Obtener un producto por su ID"""
        query = """
            SELECT id, name, pack, profit, list_price, discount, cost_price, 
            price, iva, price_with_iva, created_at, last_price_update, quantity
            FROM stock 
            WHERE id = ?
        """
        return db.fetch_one(query, (product_id,))
        
    def update_product_price(self, product_id, product_data, conn=None, commit=True):
        """Actualizar un producto existente"""
        query = """
            UPDATE stock 
            SET profit = ?, cost_price = ?, price = ?, 
                price_with_iva = ?, last_price_update = CURRENT_DATE
            WHERE id = ?
        """
        params = (
            product_data['Profit'],
            product_data['CostPrice'],
            product_data['SalePrice'],
            product_data['PriceWIva'],
            product_id
        )
        self.db.execute_query(query, params, conn=conn, commit=commit)
    
    ## -- Transaccion para actualizar precio de productos -- ##
    # Y montos de ventas relacionadas#
    def update_p_price_and_related_sales_amount(self, product_id, product_data):
        try: 
            conn = self.db.get_connection()
            conn.execute("BEGIN")

            # Guardar estado ANTERIOR antes de actualizar
            prev = self.get_product_by_id(product_id)
            p_name       = prev[1]  if prev else str(product_id)
            cost_before  = prev[6]  if prev else None  # cost_price
            price_before = prev[7]  if prev else None  # price (sin iva)
            qty          = prev[12] if prev else None  # quantity (no cambia)

            # Actualizar precio
            self.update_product_price(product_id, product_data, conn=conn, commit=False)

            # Registrar movimiento de precio
            self.movement.register(
                product_id   = product_id,
                product_name = p_name,
                event_type   = 'PRECIO',
                detail       = 'Actualización manual de precio',
                qty_before   = qty,
                qty_after    = qty,   # el stock no cambia
                cost_before  = cost_before,
                cost_after   = product_data['CostPrice'],
                price_before = price_before,
                price_after  = product_data['SalePrice'],
                conn         = conn,
                commit       = False
            )

            # Actualizar ventas pendientes relacionadas
            query = """
                SELECT DISTINCT s.id, s.cliente_id, c.name
                FROM sales s
                JOIN sale_items si ON si.sale_id = s.id
                LEFT JOIN customer c ON c.id = s.cliente_id
                WHERE si.product_id = ? AND s.estado IN ('pending', 'partial')
            """
            affected_sales = db.fetch_all(query, (product_id,), conn=conn)

            if affected_sales:
                for sale_id, client_id, client in affected_sales:
                    status = db.fetch_one("SELECT estado FROM sales WHERE id = ?", (sale_id,), conn=conn)[0]

                    if status != 'paid':
                        old_total_row = db.fetch_one("SELECT total FROM sales WHERE id = ?", (sale_id,), conn=conn)
                        old_total = Decimal(old_total_row[0]) if old_total_row else Decimal('0.00')

                        self.sales_model.update_sale_item(sale_id, product_id, product_data['PriceWIva'], conn=conn, commit=False)
                        self.sales_model.recalculate_sale_total(sale_id, conn=conn, commit=False)

                        new_total_row = db.fetch_one("SELECT total FROM sales WHERE id = ?", (sale_id,), conn=conn)
                        new_total = Decimal(new_total_row[0]) if new_total_row else Decimal('0.00')

                        if client and old_total != new_total:
                            self.payment_model.customer_model.register_price_adjustment_in_account(
                                sale_id=sale_id,
                                client_id=client_id,
                                old_total=old_total,
                                new_total=new_total,
                                conn=conn,
                                commit=False
                            )

                        # ← sin skip_credit_generation
                        new_status = self.payment_model.update_sale_status(sale_id, conn=conn, commit=False)

                        if new_status == 'paid':
                            payments = self.payment_model.get_payments_for_sale(sale_id, conn=conn)
                            paid = norm_to_2_dec(sum(Decimal(p[1]) for p in payments))

                            # ← genera crédito explícitamente
                            self.payment_model.generate_overpay_credit(
                                sale_id=sale_id,
                                client_id=client_id,
                                total=new_total,
                                payments=payments,
                                conn=conn,
                                commit=False
                            )
                            overpayment = norm_to_2_dec(paid - new_total)
                            if overpayment > Decimal('0.00'):
                                self.changes.append(f"✅ Venta #{sale_id} PAGADA - Saldo a favor: ${overpayment}")
                            else:
                                self.changes.append(f"✅ Venta #{sale_id} quedó PAGADA por cambio de precio")
                        else:
                            self.changes.append(f"✅ Venta #{sale_id} Cambia su monto por cambio de precio")

                    print(f'changes: \n{self.changes}')

            conn.commit()
            if self.changes:
                self.event_bus.publish("price_changes", self.changes)

            return True

        except Exception as e:
            conn.rollback()
            print(f'Hubo un error {e}')
            return False

        finally:
            conn.close()

    def update_field(self, db_field, new_value, product_id):
        query = f"UPDATE stock SET {db_field} = ? WHERE id = ?"
        db.execute_query(query, (new_value, product_id))
        
    def delete_product(self, product_id):
        """Eliminar un producto"""
        query = "DELETE FROM stock WHERE id = ?"
        return db.execute_query(query, (product_id,))

    def update_quantity(self, product_id, quantity, conn=None, commit=True):
        """Actualizar solo la cantidad de un producto"""
        query = "UPDATE stock SET quantity = quantity + ? WHERE id = ?"
        return db.execute_query(query, (quantity, product_id), conn=conn, commit=commit)
        
    def reduce_quantity(self, product_id, quantity_to_reduce):
        """Reducir la cantidad de un producto (para ventas)"""
        current_product = self.get_product_by_id(product_id)
        if not current_product:
            raise ValueError(f"Producto {product_id} no encontrado")
        current_quantity = current_product[-1]  # quantity está en la última posición
        print("Current cantidad: ", current_quantity)
        
        if current_quantity < quantity_to_reduce:
            raise ValueError(
                f"Stock insuficiente. Disponible: {current_quantity}, Solicitado: {quantity_to_reduce}"
            )
        
        new_quantity = current_quantity - quantity_to_reduce
        return self.update_quantity(product_id, new_quantity)
    
    def search_products(self, search_term):
        """Buscar productos por nombre, ID o envase"""
        query = """
            SELECT id, name, pack, profit, cost_price, price, iva, 
                   price_with_iva, created_at, last_price_update, quantity
            FROM stock 
            WHERE name LIKE ? OR id LIKE ? OR pack LIKE ?
            ORDER BY name
        """
        search_pattern = f"%{search_term}%"
        return db.fetch_all(query, (search_pattern, search_pattern, search_pattern))
    
    def get_low_stock_products(self, threshold):
        """Obtener productos con stock bajo (cantidad menor que el umbral)"""
        try: 
            with self.db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, pack, quantity FROM stock WHERE quantity < ? ORDER BY quantity", 
                    (threshold,)
                )
                return cursor.fetchall()
        except Exception as e:
            print(f"Error getting low stock products: {e}")
            return []
    
    def get_available_price_dates(self):
        """Obtener fechas disponibles de última modificación de precios"""
        query = "SELECT DISTINCT last_price_update FROM stock WHERE last_price_update IS NOT NULL ORDER BY last_price_update DESC"
        results = db.fetch_all(query)
        return [str(row[0]) for row in results] if results else []

    def count_products_by_date(self, date):
        """Contar productos por fecha de última modificación"""
        query = "SELECT COUNT(*) FROM stock WHERE last_price_update = ?"
        result = db.fetch_one(query, (date,))
        return result[0] if result else 0

    def bulk_update_prices_by_date(self, date, percent_increase):
        # Guardar estado ANTERIOR de todos los productos afectados
        prev_query = """
            SELECT id, name, cost_price, price, quantity
            FROM stock
            WHERE last_price_update = ?
        """
        prev_products = db.fetch_all(prev_query, (date,))

        multiplier = 1 + (percent_increase / 100)

        query = """
            UPDATE stock 
            SET price = ROUND(CAST(price AS REAL) * ?, 2),
                price_with_iva = CASE 
                    WHEN CAST(iva AS REAL) = 21.0 
                        THEN ROUND(CAST(price AS REAL) * ? * 1.21, 2)
                    WHEN CAST(iva AS REAL) = 10.5 
                        THEN ROUND(CAST(price AS REAL) * ? * 1.105, 2)
                    ELSE ROUND(CAST(price AS REAL) * ?, 2)
                END,
                profit = CASE
                    WHEN CAST(cost_price AS REAL) != 0
                    THEN ROUND(
                        (
                            (CAST(price AS REAL) * ? - CAST(cost_price AS REAL))
                            / CAST(cost_price AS REAL)
                        ) * 100, 2
                    )
                    ELSE '0'
                END,
                last_price_update = CURRENT_DATE
            WHERE last_price_update = ?
        """
        db.execute_query(query, (multiplier, multiplier, multiplier, multiplier, multiplier, date))

        # Registrar un movimiento por cada producto actualizado
        for p in prev_products:
            p_id, p_name, cost_before, price_before, qty = p
            price_after = round(float(price_before) * multiplier, 2) if price_before else None

            self.movement.register(
                product_id   = p_id,
                product_name = p_name,
                event_type   = 'PRECIO_MASIVO',
                detail       = f'Aumento masivo {percent_increase}% — fecha orig. {date}',
                qty_before   = qty,
                qty_after    = qty,
                cost_before  = cost_before,
                cost_after   = cost_before,  # el costo no cambia en aumento masivo
                price_before = price_before,
                price_after  = str(price_after),
            )

        return len(prev_products)
    
    def get_honorarios_id(self):
        """Obtener el ID del producto honorarios"""
        query = "SELECT id FROM stock WHERE name = 'HONORARIOS'"
        row = db.fetch_one(query)
        return row[0] if row else None
    
    def update_product_quantity(self, product_id, new_quantity):
        """
        Actualizar solo la cantidad de stock de un producto
        (usado para ajustes manuales)
        """
        query = """
        UPDATE stock
        SET quantity = ?
        WHERE id = ?
        """
        self.db.execute_query(query, (new_quantity, product_id))
