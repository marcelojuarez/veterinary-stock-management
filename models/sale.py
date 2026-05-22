from db.database import db
from datetime import datetime
from decimal import Decimal
from utils.utils import norm_to_2_dec
from models.stock_movement import StockMovementModel

class SalesModel:
    def __init__(self, stock_movement_model=None):
        self.db = db
        self.movement = stock_movement_model or StockMovementModel()

    def register_sale(self, total, items, cliente_id, estado, retenciones=None):
        conn = self.db.get_connection()
        try:
            conn.execute("BEGIN")
            cursor = conn.cursor()
            read_cursor = conn.cursor()  # cursor separado para lecturas dentro del loop
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                INSERT INTO sales (date, total, cliente_id, estado)
                VALUES (?, ?, ?, ?)
            """, (date, str(total), cliente_id, estado))

            sale_id = cursor.lastrowid

            # Guardar retenciones si existen
            if retenciones:
                for tipo, monto in retenciones.items():
                    if tipo != 'certificado' and monto > 0:
                        cursor.execute("""
                            INSERT INTO sale_retentions (sale_id, tax_type, amount, certificate_number)
                            VALUES (?, ?, ?, ?)
                        """, (sale_id, tipo, str(monto), retenciones.get('certificado', '')))

            for item in items:
                if len(item) == 6:
                    product_id, _, _, quantity, price_with_iva, observations = item
                else:
                    product_id, _, _, quantity, price_with_iva = item
                    observations = None

                # IVA del producto
                read_cursor.execute("SELECT iva, name, price, cost_price, quantity FROM stock WHERE id = ?", (product_id,))
                row = read_cursor.fetchone()
                iva_rate    = Decimal(row[0]) if row and row[0] else Decimal('21.00')
                p_name      = row[1] if row else str(product_id)
                price_before = row[2] if row else None   # precio de venta sin iva
                cost_before  = row[3] if row else None   # costo
                qty_before   = row[4] if row else None   # stock actual

                # Descomponer precio
                divisor             = Decimal('1') + (iva_rate / Decimal('100'))
                price_without_iva   = norm_to_2_dec(price_with_iva / divisor)
                subtotal_with_iva   = norm_to_2_dec(price_with_iva * quantity)
                subtotal_without_iva = norm_to_2_dec(price_without_iva * quantity)
                iva_amount          = norm_to_2_dec(subtotal_without_iva * (iva_rate / Decimal('100')))

                cursor.execute("""
                    INSERT INTO sale_items 
                        (sale_id, product_id, quantity, price, subtotal, iva_rate, iva_amount, observations)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (sale_id, product_id, quantity, str(price_with_iva),
                    str(subtotal_with_iva), str(iva_rate), str(iva_amount), observations))

                # Descontar stock y registrar movimiento (solo si no es honorarios)
                is_honorarios = p_name == 'HONORARIOS'

                if not is_honorarios:
                    cursor.execute("""
                        UPDATE stock SET quantity = quantity - ? WHERE id = ?
                    """, (quantity, product_id))

                    qty_after = (qty_before or 0) - quantity

                    self.movement.register(
                        product_id   = product_id,
                        product_name = p_name,
                        event_type   = 'VENTA',
                        detail       = f"Venta ID {sale_id}",
                        qty_before   = qty_before,
                        qty_after    = qty_after,
                        cost_before  = cost_before,
                        cost_after   = cost_before,
                        price_before = price_before,
                        price_after  = price_before,
                        conn         = conn,   # <- pasar la conexión activa
                        commit       = False
                    )

            conn.commit()
            return sale_id

        except Exception as e:
            conn.rollback()
            print(f'Error al registrar venta: {e}')
            raise

        finally:
            conn.close()
        
    def get_today_sales(self):
        query = """
            SELECT s.id, s.date, s.total,
                COALESCE(c.name, 'Consumidor Final') AS cliente,
                s.estado
            FROM sales s
            LEFT JOIN customer c ON s.cliente_id = c.id
            WHERE date(s.date) = date('now','localtime')
            ORDER BY s.date DESC
        """
        return db.fetch_all(query)
    
    def get_sale_by_id(self, sale_id):
        """Obtener los datos de una venta por su ID"""

        query = """
            SELECT id, date, total, cliente_id, estado
            FROM sales
            WHERE id = ?
        """

        row = db.fetch_one(query, (sale_id,))
        if not row:
            return None

        return {
            "id": row[0],
            "date": row[1],
            "total": row[2],
            "customer_id": row[3],
            "estado": row[4]
        }

    ## -- Obtiene el monto total de una venta -- ##
    def get_sale_total(self, sale_id, conn=None):

        query = """
        SELECT total FROM sales WHERE id = ?
        """

        return self.db.fetch_one(query, (sale_id, ), conn=conn)

    
    def get_sales_by_date_range(self, fecha_desde, fecha_hasta, estado=None):
        # Query base
            query = """
                SELECT 
                    s.id,
                    s.date,
                    s.total,
                    COALESCE(c.name, '') as cliente,
                    s.estado
                FROM sales s
                LEFT JOIN customer c ON c.id = s.cliente_id
                WHERE DATE(s.date) BETWEEN ? AND ?
            """
            
            params = [fecha_desde, fecha_hasta]
            
            # Filtro por estado si se especifica
            if estado:
                query += " AND s.estado = ?"
                params.append(estado)
            
            query += " ORDER BY s.date DESC"
            
            # Ejecutar query
            sales = self.db.fetch_all(query, tuple(params))

            for i, s in enumerate(sales):
                # Se obtiene el monto total de pagos
                query = """
                SELECT amount FROM payments WHERE sale_id = ? AND valid = 1
                """

                payments = self.db.fetch_all(query, (s[0], ))

                amount = Decimal('0.00')

                for p in payments:
                    amount += Decimal(p[0])

                amount = norm_to_2_dec(amount)

                sales[i] = s + (str(amount),)
            
            return sales
    
    ## -- Obtiene el monto total de todas las ventas asociadas a un cliente -- ##
    def get_total_of_all_sales(self, client_id, conn=None):

        query = """
        SELECT
            id,
            total
        FROM sales
        WHERE cliente_id = ?
        GROUP BY id
        """

        return self.db.fetch_all(query, (client_id, ), conn=conn)
    
    def get_sale_items(self, sale_id, conn=None):
        query = """
            SELECT 
                si.product_id,
                s.name,
                s.pack,
                si.quantity,
                si.price,
                si.subtotal
            FROM sale_items si
            JOIN stock s ON si.product_id = s.id
            WHERE si.sale_id = ?
        """
        
        rows = self.db.fetch_all(query, (sale_id,))
        
        return [
            {
                "product_id": r[0],
                "name": r[1],
                "pack": r[2],
                "quantity": r[3],
                "price": r[4],
                "subtotal": r[5]
            }
            for r in rows
        ]
    
    def get_total_of_sale_items(self, sale_id, conn=None):
        query = """
        SELECT subtotal FROM sale_items WHERE sale_id = ?
        """

        rows = self.db.fetch_all(query, (sale_id, ), conn=conn)

        print(rows)

        total = Decimal('0.00')

        for subtotal in rows:
            total += Decimal(subtotal[0])

        return norm_to_2_dec(total)

    ## -- Obtiene todos los datos de un item de venta -- ##
    def get_sale_item(self, sale_id, p_id, conn=None):
        query = """
        SELECT * FROM sale_items WHERE sale_id = ? AND product_id = ?
        """

        return self.db.fetch_one(query, (sale_id, p_id), conn=conn)

    ## -- Actualiza los valores de un item de compra al aumentar el precio de un producto -- ##
    def update_sale_item(self, sale_id, p_id, new_price_w_iva, conn=None, commit=True):
        sale_item_data = self.get_sale_item(sale_id, p_id)
        qty = sale_item_data[3]
        iva_rate = Decimal(sale_item_data[6])
        new_price_w_iva = norm_to_2_dec(new_price_w_iva)

        divisor = Decimal('1') + (iva_rate / Decimal('100'))
        price_without_iva = norm_to_2_dec(new_price_w_iva / divisor)

        # Subtotales
        subtotal_with_iva = norm_to_2_dec(new_price_w_iva * qty) # con IVA
        subtotal_without_iva = norm_to_2_dec(price_without_iva * qty)  # Sin IVA

        new_iva_amount = norm_to_2_dec(subtotal_without_iva * (iva_rate / Decimal('100'))) # Total IVA


        query = """
        UPDATE sale_items
        SET
            price = ?,
            subtotal = ?,
            iva_amount = ?
        WHERE sale_id = ? AND product_id = ?
        """

        params = [
            str(new_price_w_iva),
            str(subtotal_with_iva),
            str(new_iva_amount),
            sale_id,
            p_id
        ]

        self.db.execute_query(query, params, conn=conn, commit=commit)

    def update_sale_amount(self, sale_id, conn=None, commit=True):
        data_tuples = self.update_sales_items_and_get_new_sales_amount(sale_id, conn=conn, commit=commit)

        new_amount = sum(Decimal(row[0]) for row in data_tuples)

        query = """
        UPDATE sales SET
            total = ?
        WHERE id = ?
        """
        self.db.execute_query(query, (str(new_amount), sale_id), conn=conn, commit=commit)

    def update_sales_items_and_get_new_sales_amount(self, sale_id, conn=None, commit=True):
        try:
            # obtiene los items de venta de una compra
            query = """
            SELECT * FROM sale_items WHERE sale_id = ?
            """
            sale_items = self.db.fetch_all(query, (sale_id, ), conn=conn)

            # se actualiza cada item de venta
            for item in sale_items:
                s_item_id = item[0]
                p_id = item[2]
                quantity = item[3]

                # obtiene info del producto en stock
                query ="""
                SELECT iva, price_with_iva FROM stock WHERE id = ?
                """
                product_data = self.db.fetch_one(query, (p_id, ), conn=conn)
                iva_rate = Decimal(product_data[0])
                price_with_iva = Decimal(product_data[1])

                # Descomponer precio
                divisor = Decimal('1') + (iva_rate / Decimal('100'))
                price_without_iva   = norm_to_2_dec(price_with_iva / divisor)
                subtotal_with_iva   = norm_to_2_dec(price_with_iva * quantity)
                subtotal_without_iva = norm_to_2_dec(price_without_iva * quantity)
                iva_amount          = norm_to_2_dec(subtotal_without_iva * (iva_rate / Decimal('100')))
                query = """
                UPDATE sale_items SET
                    price = ?,
                    subtotal = ?,
                    iva_rate = ?,
                    iva_amount = ?
                WHERE id = ?
                """
                params = [str(price_with_iva), str(subtotal_with_iva), str(iva_rate), str(iva_amount), s_item_id]
                self.db.execute_query(query, params, conn=conn, commit=commit)


            query = """
            SELECT subtotal FROM sale_items WHERE sale_id = ?
            """

            return self.db.fetch_all(query, (sale_id, ), conn=conn)

        except ValueError as e:
            print(f'Ocurrio un error: {e}')
            return


    ## -- Recalcula el monto total de una venta -- ##
    def recalculate_sale_total(self, sale_id, conn=None, commit=True):
        new_total = self.get_total_of_sale_items(sale_id, conn=conn)

        query = """
        UPDATE sales SET total = ? WHERE id = ?
        """

        self.db.execute_query(query, (str(new_total), sale_id), conn=conn, commit=commit)