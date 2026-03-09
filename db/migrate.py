"""
migrate.py — Script de migración desde sistema Nemes → SQLite

Fuentes:
  - ExpProveedores.xml          → tabla supplier
  - ExpArticulos.xml            → tabla product (nombre, IVA, envase, rentabilidad)
  - ExpCMP_ArticulosListasPrecio.xml → precio de costo
  - ExpVTA_ArticulosListasPrecio.xml → precio de venta
  - ExpEnvases.xml              → lookup envases
  - ExpPorcIva.xml              → lookup alícuotas IVA
  - ExpResponsabilidadesTributarias.xml → lookup condición IVA proveedores
  - STOCK_1_NOV.xlsx            → stock actual (fuente más fresca)

Uso:
    python migrate.py --db ruta/a/tu.db --src ruta/a/xmls/
    python migrate.py --db ruta/a/tu.db --src ruta/a/xmls/ --dry-run
"""

import argparse
import os
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

try:
    import openpyxl
except ImportError:
    print("ERROR: falta openpyxl. Instalalo con: pip install openpyxl")
    sys.exit(1)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get(element, tag, default=""):
    """Obtiene el texto de un tag XML, limpio, con fallback."""
    node = element.find(tag)
    if node is None or node.text is None:
        return default
    return node.text.strip()


def to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_xml(path):
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as e:
        print(f"  WARN: No se pudo parsear {path}: {e}")
        return []


def map_iva_condition(code):
    """Convierte el código de responsabilidad tributaria al texto de tu app."""
    mapping = {
        "7":  "RESP. INS",       # Responsable Inscripto
        "10": "EXENTO",
        "12": "NO RESPONSABLE",  # Consumidor Final
        "13": "MONOTRIBUTISTA",  # Responsable Monotributo
        "14": "MONOTRIBUTISTA",  # Responsable Monotributo Servicios
        "6":  "RESP. INS",       # IMP/EXP → RI
        "15": "RESP. INS",
    }
    return mapping.get(code, "RESP. INS")


def clean_cuit(raw):
    """Retorna None si el CUIT está vacío o es un placeholder del sistema viejo."""
    if not raw:
        return None
    raw = raw.strip()
    # Cualquier valor con solo ceros o placeholders conocidos → None
    if not raw or re.sub(r'[-\s0]', '', raw) == '':
        return None
    if raw in ("00-00000000-0", "00-00000000-1", "00000000", "0"):
        return None
    return raw


def log(msg, indent=0):
    print("  " * indent + msg)


# ─── Loaders de lookups ───────────────────────────────────────────────────────

def load_lookups(src):
    """Carga todos los diccionarios de referencia."""
    lookups = {}

    # IVA %
    lookups["iva"] = {}
    for item in parse_xml(os.path.join(src, "ExpPorcIva.xml")):
        lookups["iva"][get(item, "IDPorcIva")] = to_float(get(item, "PorIva"))

    # Envases
    lookups["envases"] = {}
    for item in parse_xml(os.path.join(src, "ExpEnvases.xml")):
        if get(item, "Baja") == "N":
            lookups["envases"][get(item, "IDEnvase")] = get(item, "NombreEnvase")

    # Responsabilidades tributarias → condición IVA
    lookups["resp"] = {}
    for item in parse_xml(os.path.join(src, "ExpResponsabilidadesTributarias.xml")):
        id_resp = get(item, "IDRespTributaria")
        lookups["resp"][id_resp] = map_iva_condition(id_resp)

    # Precios de costo (CMP) por IDArticulo
    lookups["cmp"] = {}
    for item in parse_xml(os.path.join(src, "ExpCMP_ArticulosListasPrecio.xml")):
        if get(item, "Baja") == "N":
            id_art = get(item, "IDArticulo")
            lookups["cmp"][id_art] = to_float(get(item, "CMP_PrecioCosto"))

    # Precios de venta (VTA) por IDArticulo
    lookups["vta"] = {}
    for item in parse_xml(os.path.join(src, "ExpVTA_ArticulosListasPrecio.xml")):
        if get(item, "Baja") == "N":
            id_art = get(item, "IDArticulo")
            lookups["vta"][id_art] = to_float(get(item, "VTA_PrecioVenta"))

    log(f"IVA alícuotas: {len(lookups['iva'])} | "
        f"Envases: {len(lookups['envases'])} | "
        f"Precios costo: {len(lookups['cmp'])} | "
        f"Precios venta: {len(lookups['vta'])}")

    return lookups


# ─── Stock desde XLSX ─────────────────────────────────────────────────────────

def load_stock_from_xlsx(xlsx_path):
    """
    Parsea STOCK_1_NOV.xlsx que tiene formato de reporte con headers intercalados.
    Retorna dict: nombre_articulo (normalizado) → stock_actual
    """
    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb.active

    skip_prefixes = ("Stock de", "Depósito", "Proveedor", "Familia", "Total", "Subtotal")
    stock_map = {}

    for row in ws.iter_rows(min_row=1, values_only=True):
        col0 = row[0]
        col1 = row[1]  # nombre artículo
        col2 = row[2]  # stock actual

        if col0 is None or col1 is None or col2 is None:
            continue
        if any(str(col0).startswith(p) for p in skip_prefixes):
            continue
        if not isinstance(col2, (int, float)):
            continue

        nombre = str(col1).strip().upper()
        stock_map[nombre] = to_float(col2)

    return stock_map


def match_stock(nombre_articulo, stock_map):
    """
    Intenta matchear el nombre del artículo XML contra el XLSX.
    El XLSX tiene formato 'NOMBRE - ENVASE', el XML solo tiene 'NOMBRE'.
    """
    nombre_upper = nombre_articulo.upper()
    # Búsqueda exacta (nombre del xlsx empieza con el nombre del xml)
    for key, stock in stock_map.items():
        if key.startswith(nombre_upper):
            return stock
    # Fallback: búsqueda parcial
    for key, stock in stock_map.items():
        if nombre_upper in key:
            return stock
    return 0.0


# ─── Migración proveedores ────────────────────────────────────────────────────

def migrate_suppliers(conn, src, lookups, dry_run):
    log("\n[1/2] PROVEEDORES")

    proveedores = parse_xml(os.path.join(src, "ExpProveedores.xml"))
    activos = [p for p in proveedores if get(p, "Baja") == "N"]
    log(f"  Encontrados: {len(activos)} activos")

    inserted = skipped = 0
    cursor = conn.cursor()

    for p in activos:
        nombre = get(p, "NombreProveedor")
        cuit   = clean_cuit(get(p, "NroDoc"))
        calle  = get(p, "Dom_Calle")
        nro    = get(p, "Dom_Nro")
        address = f"{calle} {nro}".strip() if calle else ""
        phone   = get(p, "Telefono")
        email   = get(p, "Email")
        id_resp = get(p, "IDRespTributaria")
        iva_cond = lookups["resp"].get(id_resp, "RESP. INS")

        if not nombre:
            skipped += 1
            continue

        if dry_run:
            log(f"    [DRY] {nombre} | CUIT: {cuit or '(sin CUIT)'} | IVA: {iva_cond}", 1)
            inserted += 1
            continue

        # Evitar duplicados por nombre o por CUIT real (idempotente)
        cursor.execute("SELECT id FROM supplier WHERE name = ?", (nombre,))
        if cursor.fetchone():
            skipped += 1
            continue
        if cuit:
            cursor.execute("SELECT id FROM supplier WHERE cuit = ?", (cuit,))
            if cursor.fetchone():
                skipped += 1
                continue

        cursor.execute("""
            INSERT INTO supplier (cuit, name, address, city, province, country,
                                  phone, email, iva_condition, last_debt_update)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cuit,   # None → NULL en SQLite, permite múltiples sin violar UNIQUE
            nombre, address,
            "",   # ciudad: no está disponible sin ExpLocalidades (archivo roto)
            "",   # provincia
            "Argentina",
            phone, email, iva_cond,
            datetime.now().strftime("%Y-%m-%d")
        ))
        inserted += 1

    if not dry_run:
        conn.commit()
    log(f"  ✓ Insertados: {inserted} | Salteados/duplicados: {skipped}")


# ─── Migración productos ──────────────────────────────────────────────────────

def migrate_products(conn, src, lookups, stock_map, dry_run):
    log("\n[2/2] PRODUCTOS / STOCK")

    articulos = parse_xml(os.path.join(src, "ExpArticulos.xml"))
    activos   = [a for a in articulos
                 if get(a, "Baja") == "N" and get(a, "EsGasto") == "false"]
    log(f"  Encontrados: {len(activos)} activos (excluye gastos y dados de baja)")

    inserted = skipped = no_price = 0
    cursor = conn.cursor()

    for a in activos:
        id_art      = get(a, "IDArticulo")
        nombre      = get(a, "NombreArticulo")
        id_envase   = get(a, "IDEnvase")
        id_iva      = get(a, "IDPorcIva")
        rentabilidad = to_float(get(a, "PorcRentabilidad"))

        envase     = lookups["envases"].get(id_envase, "UNIDAD")
        iva_rate   = lookups["iva"].get(id_iva, 21.0)
        price_cost = lookups["cmp"].get(id_art, 0.0)
        price_sale = lookups["vta"].get(id_art, 0.0)
        stock      = match_stock(nombre, stock_map)

        if not nombre:
            skipped += 1
            continue

        if price_cost == 0.0 and price_sale == 0.0:
            no_price += 1

        if dry_run:
            log(f"    [DRY] {nombre} | {envase} | IVA:{iva_rate}% | "
                f"Costo:${price_cost} Venta:${price_sale} | Stock:{stock}", 1)
            inserted += 1
            continue

        # Evitar duplicados por nombre+envase (UNIQUE constraint de la tabla)
        cursor.execute("SELECT id FROM stock WHERE name = ? AND pack = ?", (nombre, envase))
        if cursor.fetchone():
            skipped += 1
            continue

        # Calcular price_with_iva
        price_with_iva = round(price_sale * (1 + iva_rate / 100), 2)

        cursor.execute("""
            INSERT INTO stock (name, pack, list_price, discount, cost_price,
                               profit, price, iva, price_with_iva, quantity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nombre,
            envase,
            str(price_cost),       # list_price  = precio lista del proveedor
            "0",                   # discount    = sin descuento inicial
            str(price_cost),       # cost_price  = precio costo
            str(rentabilidad),     # profit      = % rentabilidad
            str(price_sale),       # price       = precio venta sin IVA
            str(iva_rate),         # iva         = alícuota %
            str(price_with_iva),   # price_with_iva
            stock,                 # quantity    = stock actual del XLSX
        ))
        inserted += 1

    if not dry_run:
        conn.commit()

    log(f"  ✓ Insertados: {inserted} | Salteados/duplicados: {skipped} | "
        f"Sin precio (se insertan igual): {no_price}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Migración Nemes → SQLite")
    parser.add_argument("--db",      required=True, help="Ruta al archivo .db de la app")
    parser.add_argument("--src",     required=True, help="Carpeta con los archivos XML y XLSX")
    parser.add_argument("--dry-run", action="store_true",
                        help="Muestra qué se migraría sin escribir nada")
    args = parser.parse_args()

    if not os.path.exists(args.db):
        print(f"ERROR: No se encuentra la base de datos: {args.db}")
        sys.exit(1)

    xlsx_path = os.path.join(args.src, "STOCK_1_NOV.xlsx")
    if not os.path.exists(xlsx_path):
        print(f"WARN: No se encuentra {xlsx_path} — el stock se importará en 0")

    print("=" * 60)
    print(f"  MIGRACIÓN NEMES → SQLite")
    print(f"  DB:      {args.db}")
    print(f"  Fuentes: {args.src}")
    print(f"  Modo:    {'DRY RUN (sin cambios)' if args.dry_run else 'REAL'}")
    print("=" * 60)

    conn = sqlite3.connect(args.db)

    log("\nCargando lookups...")
    lookups = load_lookups(args.src)

    log("\nCargando stock desde XLSX...")
    if os.path.exists(xlsx_path):
        stock_map = load_stock_from_xlsx(xlsx_path)
        log(f"  {len(stock_map)} artículos con stock encontrados en XLSX")
    else:
        stock_map = {}
        log("  WARN: STOCK_1_NOV.xlsx no encontrado — stock se importará en 0")

    migrate_suppliers(conn, args.src, lookups, args.dry_run)
    migrate_products(conn, args.src, lookups, stock_map, args.dry_run)

    conn.close()

    print("\n" + "=" * 60)
    if args.dry_run:
        print("  DRY RUN completado — ningún dato fue modificado.")
        print("  Para ejecutar de verdad, quitá --dry-run")
    else:
        print("  ✓ Migración completada exitosamente.")
    print("=" * 60)


if __name__ == "__main__":
    main()