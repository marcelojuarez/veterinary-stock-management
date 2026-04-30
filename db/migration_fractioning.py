"""
migration_fraccionamiento.py
============================
Ejecutar UNA sola vez para agregar el soporte de venta fraccionada.

Crea dos tablas nuevas:
  - stock_fraction_config : configuración de fraccionamiento por producto
  - open_fractions        : bolsas/envases abiertos con saldo restante

NO modifica ninguna tabla existente.

Uso:
    python migration_fraccionamiento.py
"""

import sqlite3
import os
import sys

# ── Ruta a la base de datos ────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'stock.db')


def run_migration(db_path: str = DB_PATH):
    if not os.path.exists(db_path):
        print(f"[ERROR] No se encontró la base de datos en: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    try:
        conn.execute("BEGIN")

        # ── 1. Configuración de fraccionamiento ───────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_fraction_config (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id      INTEGER NOT NULL UNIQUE,
                unit            TEXT    NOT NULL DEFAULT 'KG',   -- KG | GR | LITRO | ML
                qty_per_package REAL    NOT NULL,                 -- cuánto tiene cada unidad cerrada (ej. 15 para bolsa 15kg)
                fraction_price  TEXT    NOT NULL,                 -- precio de venta por unidad fraccionada (sin IVA)
                created_at      TEXT    DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES stock(id) ON DELETE CASCADE
            )
        """)

        # ── 2. Bolsas / envases abiertos ──────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS open_fractions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id  INTEGER NOT NULL,
                remaining   REAL    NOT NULL,   -- cantidad restante en la unidad abierta
                opened_at   TEXT    DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES stock(id) ON DELETE CASCADE
            )
        """)

        # ── 3. Índice para búsquedas rápidas por producto ─────────────────
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_open_fractions_product
            ON open_fractions (product_id)
        """)

        conn.commit()
        print("[OK] Migración de fraccionamiento aplicada correctamente.")
        print("     Tablas creadas: stock_fraction_config, open_fractions")

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] La migración falló: {e}")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    # Permite pasar la ruta como argumento: python migration_fraccionamiento.py ruta/stock.db
    path = sys.argv[1] if len(sys.argv) > 1 else DB_PATH
    run_migration(path)