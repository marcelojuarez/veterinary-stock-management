from datetime import datetime
from db.database import db as default_db


class StockMovementModel:
    def __init__(self, db_connection=None):
        self.db = db_connection or default_db

    # ------------------------------------------------------------------ #
    # REGISTRO DE MOVIMIENTOS                                             #
    # ------------------------------------------------------------------ #

    def register(
        self,
        product_id,
        product_name,
        event_type,
        detail=None,
        qty_before=None,
        qty_after=None,
        cost_before=None,
        cost_after=None,
        price_before=None,
        price_after=None,
        conn=None,
        commit=True
    ):
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        query = """
        INSERT INTO stock_movement 
            (product_id, product_name, date, event_type, detail,
             qty_before, qty_after, cost_before, cost_after, price_before, price_after)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = [
            product_id,
            product_name,
            date,
            event_type,
            detail,
            qty_before,
            qty_after,
            str(cost_before) if cost_before is not None else None,
            str(cost_after)  if cost_after  is not None else None,
            str(price_before) if price_before is not None else None,
            str(price_after)  if price_after  is not None else None,
        ]

        self.db.execute_query(query, params, conn=conn, commit=commit)

    # ------------------------------------------------------------------ #
    # CONSULTAS                                                           #
    # ------------------------------------------------------------------ #

    def get_all(self, limit=200):
        """Todos los movimientos, más recientes primero."""
        query = """
        SELECT id, product_id, product_name, date, event_type,
               detail, qty_before, qty_after,
               cost_before, cost_after, price_before, price_after
        FROM stock_movement
        ORDER BY date DESC
        LIMIT ?
        """
        return self.db.fetch_all(query, (limit,))

    def get_by_product(self, product_id, limit=200):
        """Movimientos de un producto específico."""
        query = """
        SELECT id, product_id, product_name, date, event_type,
               detail, qty_before, qty_after,
               cost_before, cost_after, price_before, price_after
        FROM stock_movement
        WHERE product_id = ?
        ORDER BY date DESC
        LIMIT ?
        """
        return self.db.fetch_all(query, (product_id, limit))

    def get_by_event_type(self, event_type, limit=200):
        """Movimientos filtrados por tipo de evento."""
        query = """
        SELECT id, product_id, product_name, date, event_type,
               detail, qty_before, qty_after,
               cost_before, cost_after, price_before, price_after
        FROM stock_movement
        WHERE event_type = ?
        ORDER BY date DESC
        LIMIT ?
        """
        return self.db.fetch_all(query, (event_type, limit))

    def get_by_date_range(self, date_from, date_to, product_id=None):
        """
        Movimientos entre dos fechas (ISO: yyyy-mm-dd).
        Si se pasa product_id, filtra por producto.
        """
        if product_id:
            query = """
            SELECT id, product_id, product_name, date, event_type,
                   detail, qty_before, qty_after,
                   cost_before, cost_after, price_before, price_after
            FROM stock_movement
            WHERE DATE(date) BETWEEN ? AND ?
              AND product_id = ?
            ORDER BY date DESC
            """
            return self.db.fetch_all(query, (date_from, date_to, product_id))
        else:
            query = """
            SELECT id, product_id, product_name, date, event_type,
                   detail, qty_before, qty_after,
                   cost_before, cost_after, price_before, price_after
            FROM stock_movement
            WHERE DATE(date) BETWEEN ? AND ?
            ORDER BY date DESC
            """
            return self.db.fetch_all(query, (date_from, date_to))