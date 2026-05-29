"""
models/fraction.py
==================
Toda la lógica de negocio para productos fraccionables.

Responsabilidades:
  - Leer / escribir configuración de fraccionamiento (stock_fraction_config)
  - Gestionar envases abiertos (open_fractions)
  - Calcular stock disponible total en unidades fraccionadas
  - Descontar stock al registrar una venta fraccionada
"""

from decimal import Decimal
from db.database import db as default_db


class FractionModel:
    def __init__(self, db_connection=None):
        self.db = db_connection or default_db

    # ─────────────────────────────────────────────────────────────────────
    # CONFIGURACIÓN DE FRACCIONAMIENTO
    # ─────────────────────────────────────────────────────────────────────

    def get_config(self, product_id: int) -> dict | None:
        """
        Devuelve la configuración de fraccionamiento de un producto,
        o None si el producto no es fraccionable.
        """
        row = self.db.fetch_one(
            """
            SELECT product_id, unit, qty_per_package, fraction_price
            FROM stock_fraction_config
            WHERE product_id = ?
            """,
            (product_id,)
        )
        if not row:
            return None
        return {
            "product_id":      row[0],
            "unit":            row[1],
            "qty_per_package": Decimal(str(row[2])),
            "fraction_price":  Decimal(row[3]),
        }

    def is_fractional(self, product_id: int) -> bool:
        """Devuelve True si el producto tiene configuración de fraccionamiento."""
        row = self.db.fetch_one(
            "SELECT 1 FROM stock_fraction_config WHERE product_id = ?",
            (product_id,)
        )
        return row is not None

    def set_config(self, product_id: int, unit: str,
                   qty_per_package: float, fraction_price: str) -> None:
        """
        Crea o actualiza la configuración de fraccionamiento para un producto.
        """
        existing = self.get_config(product_id)
        if existing:
            self.db.execute_query(
                """
                UPDATE stock_fraction_config
                SET unit = ?, qty_per_package = ?, fraction_price = ?
                WHERE product_id = ?
                """,
                (unit, float(qty_per_package), str(fraction_price), product_id)
            )
        else:
            self.db.execute_query(
                """
                INSERT INTO stock_fraction_config (product_id, unit, qty_per_package, fraction_price)
                VALUES (?, ?, ?, ?)
                """,
                (product_id, unit, float(qty_per_package), str(fraction_price))
            )

    def remove_config(self, product_id: int) -> None:
        """Elimina la configuración de fraccionamiento de un producto."""
        self.db.execute_query(
            "DELETE FROM stock_fraction_config WHERE product_id = ?",
            (product_id,)
        )

    # ─────────────────────────────────────────────────────────────────────
    # ENVASES ABIERTOS
    # ─────────────────────────────────────────────────────────────────────

    def get_open_fractions(self, product_id: int, conn=None) -> list[dict]:
        """
        Devuelve todos los envases abiertos de un producto con saldo > 0,
        ordenados del más antiguo al más reciente (FIFO).
        """
        rows = self.db.fetch_all(
            """
            SELECT id, product_id, remaining, opened_at
            FROM open_fractions
            WHERE product_id = ? AND remaining > 0
            ORDER BY opened_at ASC
            """,
            (product_id,),
            conn=conn
        )
        return [
            {"id": r[0], "product_id": r[1], "remaining": Decimal(str(r[2])), "opened_at": r[3]}
            for r in rows
        ]

    def get_all_fractional_stock(self) -> dict:
        """
        Returns {product_id: stock_info} for every fractional product in 2 queries.
        Use this instead of calling is_fractional() + get_available_stock_info() per product.
        """
        rows = self.db.fetch_all("""
            SELECT sfc.product_id, sfc.unit, sfc.qty_per_package, sfc.fraction_price,
                   COALESCE(s.quantity, 0) AS closed_qty
            FROM stock_fraction_config sfc
            JOIN stock s ON s.id = sfc.product_id
        """)
        if not rows:
            return {}

        open_rows = self.db.fetch_all("""
            SELECT product_id, SUM(remaining)
            FROM open_fractions
            WHERE remaining > 0
            GROUP BY product_id
        """)
        open_map = {r[0]: Decimal(str(r[1])) for r in open_rows}

        result = {}
        for pid, unit, qty_per_pkg, frac_price, closed in rows:
            qty_per_pkg    = Decimal(str(qty_per_pkg))
            open_remaining = open_map.get(pid, Decimal("0"))
            total          = Decimal(str(closed)) * qty_per_pkg + open_remaining
            result[pid] = {
                "closed_packages": closed,
                "open_remaining":  open_remaining,
                "total_units":     total,
                "unit":            unit,
                "qty_per_package": qty_per_pkg,
                "fraction_price":  Decimal(str(frac_price)),
            }
        return result

    def total_available_in_open(self, product_id: int, conn=None) -> Decimal:
        """Suma de saldo restante en todos los envases abiertos."""
        row = self.db.fetch_one(
            "SELECT COALESCE(SUM(remaining), 0) FROM open_fractions WHERE product_id = ? AND remaining > 0",
            (product_id,),
            conn=conn
        )
        return Decimal(str(row[0])) if row else Decimal('0')

    def _open_new_package(self, product_id: int, qty_per_package: Decimal,
                          initial_remaining: Decimal, conn, cursor) -> int:
        """
        Abre un envase nuevo:
          1. Descuenta 1 unidad de stock.quantity  (bolsas cerradas)
          2. Inserta en open_fractions con remaining = initial_remaining
             (lo que queda DESPUÉS de descontar lo que se va a vender de esta bolsa)
        Retorna el id del nuevo registro en open_fractions.
        """
        cursor.execute(
            "UPDATE stock SET quantity = quantity - 1 WHERE id = ?",
            (product_id,)
        )
        cursor.execute(
            "INSERT INTO open_fractions (product_id, remaining) VALUES (?, ?)",
            (product_id, float(initial_remaining))
        )
        return cursor.lastrowid

    def _deduct_from_open(self, product_id: int, quantity: Decimal,
                          qty_per_package: Decimal, conn, cursor) -> None:
        """
        Descuenta `quantity` de los envases abiertos usando lógica FIFO.
        Si el saldo en abiertos no alcanza, abre nuevas bolsas cerradas.

        Ejemplo:
            qty_per_package = 25 KG,  quantity = 3 KG
            → No hay bolsa abierta
            → Abre bolsa nueva con remaining = 25 - 3 = 22 KG
            → stock.quantity -= 1
        """
        remaining_to_deduct = quantity

        # 1. Consumir envases ya abiertos (FIFO)
        open_list = self.get_open_fractions(product_id, conn=conn)
        for frac in open_list:
            if remaining_to_deduct <= Decimal('0'):
                break
            deduct        = min(frac["remaining"], remaining_to_deduct)
            new_remaining = frac["remaining"] - deduct
            cursor.execute(
                "UPDATE open_fractions SET remaining = ? WHERE id = ?",
                (float(new_remaining), frac["id"])
            )
            remaining_to_deduct -= deduct

        # 2. Si aún queda por descontar, abrir bolsas cerradas
        while remaining_to_deduct > Decimal('0'):
            # Cuánto se descuenta de esta bolsa
            deduct_from_this = min(qty_per_package, remaining_to_deduct)
            # Lo que queda en la bolsa después del descuento
            left_in_package  = qty_per_package - deduct_from_this

            # Abre la bolsa YA con el saldo correcto (no hace falta UPDATE posterior)
            self._open_new_package(
                product_id       = product_id,
                qty_per_package  = qty_per_package,
                initial_remaining = left_in_package,
                conn             = conn,
                cursor           = cursor
            )
            remaining_to_deduct -= deduct_from_this

    # ─────────────────────────────────────────────────────────────────────
    # STOCK DISPONIBLE (vista consolidada)
    # ─────────────────────────────────────────────────────────────────────

    def get_available_stock_info(self, product_id: int) -> dict:
        """
        Calcula el stock disponible total de un producto fraccionable.

        Retorna:
            {
                "closed_packages": int,          # bolsas/unidades cerradas
                "open_remaining":  Decimal,      # saldo en unidades abiertas
                "total_units":     Decimal,      # total en unidades fraccionadas
                "unit":            str,           # "KG", "GR", etc.
                "qty_per_package": Decimal,
                "display":         str            # texto listo para mostrar en UI
            }
        """
        cfg = self.get_config(product_id)
        if not cfg:
            return {}

        # Unidades cerradas
        row = self.db.fetch_one("SELECT quantity FROM stock WHERE id = ?", (product_id,))
        closed = int(row[0]) if row else 0

        open_remaining = self.total_available_in_open(product_id)
        total = Decimal(str(closed)) * cfg["qty_per_package"] + open_remaining

        display = f"{total} {cfg['unit']} " + f"{closed} u."

        return {
            "closed_packages": closed,
            "open_remaining":  open_remaining,
            "total_units":     total,
            "unit":            cfg["unit"],
            "qty_per_package": cfg["qty_per_package"],
            "display":         display,
        }

    def has_enough_stock(self, product_id: int, quantity: Decimal) -> bool:
        """
        Verifica si hay stock suficiente para una venta fraccionada.
        Considera tanto unidades cerradas como saldo en abiertos.
        """
        info = self.get_available_stock_info(product_id)
        if not info:
            return False
        return info["total_units"] >= quantity

    # ─────────────────────────────────────────────────────────────────────
    # DESCUENTO DE STOCK EN VENTA FRACCIONADA
    # ─────────────────────────────────────────────────────────────────────

    def deduct_fractional_stock(self, product_id: int, quantity: Decimal,
                                conn, commit: bool = False) -> None:
        """
        Punto de entrada principal para descontar stock fraccionado.
        Llamado desde SalesModel.register_sale() dentro de su transacción.

        Parámetros:
            product_id : ID del producto en tabla stock
            quantity   : cantidad a vender en la unidad fraccionada (ej. 2.5 para 2.5 kg)
            conn       : conexión SQLite activa (transacción externa)
            commit     : si True hace commit (normalmente False porque la venta ya lo hace)
        """
        cfg = self.get_config(product_id)
        if not cfg:
            raise ValueError(f"El producto {product_id} no tiene configuración de fraccionamiento.")

        if not self.has_enough_stock(product_id, quantity):
            info = self.get_available_stock_info(product_id)
            raise ValueError(
                f"Stock insuficiente. Disponible: {info.get('total_units', 0)} {cfg['unit']}, "
                f"solicitado: {quantity} {cfg['unit']}"
            )

        cursor = conn.cursor()
        self._deduct_from_open(product_id, quantity, cfg["qty_per_package"], conn, cursor)

        if commit:
            conn.commit()