"""
models/sale.py  (con soporte de fraccionamiento)
=================================================
Cambios respecto a la versión original:
  - register_sale() detecta si un ítem es fraccionado (len == 7 o flag is_fractional)
  - Para ítems fraccionados llama a FractionModel.deduct_fractional_stock()
    en lugar de hacer UPDATE stock directamente
  - Todo lo demás permanece idéntico
"""

import logging
from db.database import db
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)
from utils.utils import norm_to_2_dec
from models.stock_movement import StockMovementModel
from models.fraction import FractionModel


class SalesModel:
    def __init__(self, stock_movement_model=None, fraction_model=None):
        self.db = db
        self.movement = stock_movement_model or StockMovementModel()
        self.fraction = fraction_model or FractionModel()

    def register_sale(self, total, items, cliente_id, estado, retenciones=None):
        """
        Registra una venta completa.

        Formato de cada item en `items`:
          Normal       : (product_id, name, pack, quantity, price_with_iva)
          Con obs.     : (product_id, name, pack, quantity, price_with_iva, observations)
          Fraccionado  : (product_id, name, pack, quantity, price_with_iva, observations, True)
                         ← el séptimo elemento True indica fraccionado
        """
        conn = self.db.get_connection()
        try:
            conn.execute("BEGIN")
            cursor = conn.cursor()
            read_cursor = conn.cursor()
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
                # ── Desempaquetar ítem (soporta 5, 6 o 7 campos) ─────────
                is_fractional = False
                observations = None

                if len(item) == 7:
                    product_id, _, _, quantity, price_with_iva, observations, is_fractional = item
                elif len(item) == 6:
                    product_id, _, _, quantity, price_with_iva, observations = item
                else:
                    product_id, _, _, quantity, price_with_iva = item

                # quantity puede ser int o Decimal (fraccionado)
                quantity = Decimal(str(quantity))

                # ── Datos del producto ────────────────────────────────────
                read_cursor.execute(
                    "SELECT iva, name, price, cost_price, quantity FROM stock WHERE id = ?",
                    (product_id,)
                )
                row = read_cursor.fetchone()
                iva_rate     = Decimal(row[0]) if row and row[0] else Decimal('21.00')
                p_name       = row[1] if row else str(product_id)
                price_before = row[2] if row else None
                cost_before  = row[3] if row else None
                qty_before   = row[4] if row else None

                # ── Cálculo de precios ────────────────────────────────────
                divisor              = Decimal('1') + (iva_rate / Decimal('100'))
                price_without_iva    = norm_to_2_dec(price_with_iva / divisor)
                subtotal_with_iva    = norm_to_2_dec(price_with_iva * quantity)
                subtotal_without_iva = norm_to_2_dec(price_without_iva * quantity)
                iva_amount           = norm_to_2_dec(subtotal_without_iva * (iva_rate / Decimal('100')))

                cursor.execute("""
                    INSERT INTO sale_items
                        (sale_id, product_id, quantity, price, subtotal, iva_rate, iva_amount, observations)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sale_id, product_id,
                    str(quantity),          # guardar como TEXT para soportar decimales
                    str(price_with_iva),
                    str(subtotal_with_iva),
                    str(iva_rate),
                    str(iva_amount),
                    observations
                ))

                # ── Descuento de stock ────────────────────────────────────
                is_honorarios = (p_name == 'HONORARIOS')

                if not is_honorarios:
                    if is_fractional:
                        # Delegar al modelo de fraccionamiento (FIFO sobre bolsas abiertas)
                        self.fraction.deduct_fractional_stock(
                            product_id=product_id,
                            quantity=quantity,
                            conn=conn,
                            commit=False
                        )
                        qty_after = None   # el stock.quantity solo varía si se abre una bolsa nueva
                    else:
                        # Venta normal: descontar unidades enteras
                        cursor.execute(
                            "UPDATE stock SET quantity = quantity - ? WHERE id = ?",
                            (str(quantity), product_id)
                        )
                        qty_after = (qty_before or 0) - int(quantity)

                    self.movement.register(
                        product_id   = product_id,
                        product_name = p_name,
                        event_type   = 'VENTA_FRACCION' if is_fractional else 'VENTA',
                        detail       = f"Venta ID {sale_id}" + (f" — {quantity} {self.fraction.get_config(product_id)['unit']}" if is_fractional else ""),
                        qty_before   = qty_before,
                        qty_after    = qty_after,
                        cost_before  = cost_before,
                        cost_after   = cost_before,
                        price_before = price_before,
                        price_after  = price_before,
                        conn         = conn,
                        commit       = False
                    )

            conn.commit()
            return sale_id

        except Exception as e:
            conn.rollback()
            logger.error("Error al registrar venta: %s", e)
            raise

        finally:
            conn.close()

    # ── El resto de métodos es idéntico al original ───────────────────────

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
        row = db.fetch_one(
            "SELECT id, date, total, cliente_id, estado FROM sales WHERE id = ?",
            (sale_id,)
        )
        if not row:
            return None
        return {"id": row[0], "date": row[1], "total": row[2], "customer_id": row[3], "estado": row[4]}

    def get_sale_total(self, sale_id, conn=None):
        return self.db.fetch_one("SELECT total FROM sales WHERE id = ?", (sale_id,), conn=conn)

    def get_sales_by_date_range(self, fecha_desde, fecha_hasta, estado=None):
        query = """
            SELECT s.id, s.date, s.total,
                COALESCE(c.name, '') as cliente, s.estado
            FROM sales s
            LEFT JOIN customer c ON c.id = s.cliente_id
            WHERE DATE(s.date) BETWEEN ? AND ?
        """
        params = [fecha_desde, fecha_hasta]
        if estado:
            query += " AND s.estado = ?"
            params.append(estado)
        query += " ORDER BY s.date DESC"

        sales = self.db.fetch_all(query, tuple(params))
        for i, s in enumerate(sales):
            payments = self.db.fetch_all("SELECT amount FROM payments WHERE sale_id = ?", (s[0],))
            amount = sum(Decimal(p[0]) for p in payments)
            sales[i] = s + (str(norm_to_2_dec(amount)),)
        return sales

    def get_total_of_all_sales(self, client_id, conn=None):
        return self.db.fetch_all(
            "SELECT id, total FROM sales WHERE cliente_id = ? AND estado IN ('pending', 'partial') GROUP BY id",
            (client_id,), conn=conn
        )

    def get_sale_items(self, sale_id):
        rows = self.db.fetch_all("""
            SELECT si.product_id, s.name, s.pack, si.quantity, si.price, si.subtotal,
                   si.observations
            FROM sale_items si
            JOIN stock s ON si.product_id = s.id
            WHERE si.sale_id = ?
        """, (sale_id,))
        return [
            {
                "product_id":   r[0],
                "name":         r[1],
                "pack":         r[2],
                "quantity":     r[3],
                "price":        r[4],
                "subtotal":     r[5],
                "observations": r[6],
            }
            for r in rows
        ]

    def get_total_of_sale_items(self, sale_id, conn=None):
        rows = self.db.fetch_all("SELECT subtotal FROM sale_items WHERE sale_id = ?", (sale_id,), conn=conn)
        total = sum(Decimal(r[0]) for r in rows)
        return norm_to_2_dec(total)

    def get_sale_item(self, sale_id, p_id, conn=None):
        return self.db.fetch_one(
            "SELECT * FROM sale_items WHERE sale_id = ? AND product_id = ?",
            (sale_id, p_id), conn=conn
        )

    def update_sale_item(self, sale_id, p_id, new_price_w_iva, conn=None, commit=True):
        sale_item_data = self.get_sale_item(sale_id, p_id)
        qty       = Decimal(str(sale_item_data[3]))
        iva_rate  = Decimal(sale_item_data[6])
        new_price = norm_to_2_dec(new_price_w_iva)

        divisor              = Decimal('1') + (iva_rate / Decimal('100'))
        price_without_iva    = norm_to_2_dec(new_price / divisor)
        subtotal_with_iva    = norm_to_2_dec(new_price * qty)
        subtotal_without_iva = norm_to_2_dec(price_without_iva * qty)
        new_iva_amount       = norm_to_2_dec(subtotal_without_iva * (iva_rate / Decimal('100')))

        self.db.execute_query("""
            UPDATE sale_items SET price = ?, subtotal = ?, iva_amount = ?
            WHERE sale_id = ? AND product_id = ?
        """, [str(new_price), str(subtotal_with_iva), str(new_iva_amount), sale_id, p_id],
            conn=conn, commit=commit)

    def recalculate_sale_total(self, sale_id, conn=None, commit=True):
        new_total = self.get_total_of_sale_items(sale_id, conn=conn)
        self.db.execute_query(
            "UPDATE sales SET total = ? WHERE id = ?",
            (str(new_total), sale_id), conn=conn, commit=commit
        )