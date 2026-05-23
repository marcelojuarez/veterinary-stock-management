"""
import_from_csv.py - Importa datos desde CSVs organizados a SQLite

Lee los CSVs generados por xml_to_csv.py y los importa a la base de datos

Uso:
    python import_from_csv.py --db db/stock.db --src carpeta_csvs/
    python import_from_csv.py --db db/stock.db --src carpeta_csvs/ --dry-run
"""

import argparse
import csv
import os
import sqlite3
import sys
from datetime import datetime


def log(msg, indent=0):
    """Helper para logging"""
    print("  " * indent + msg)


def import_proveedores(conn, csv_path, dry_run):
    """Importa proveedores desde CSV"""
    log("\n[1/3] Importando proveedores...")
    
    if not os.path.exists(csv_path):
        log("WARN: proveedores.csv no encontrado", 1)
        return
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        log("WARN: CSV vacío", 1)
        return
    
    # Detectar headers automáticamente
    headers = rows[0].keys()
    log(f"Headers detectados: {', '.join(headers)}", 1)
    
    log(f"Encontrados: {len(rows)} proveedores", 1)
    
    inserted = skipped = 0
    cursor = conn.cursor()
    
    for row in rows:
        # Soportar diferentes nombres de columnas
        nombre = (row.get('nombre') or row.get('name') or '').strip()
        cuit = (row.get('cuit') or '').strip() or None
        direccion = (row.get('direccion') or row.get('address') or '').strip()
        telefono = (row.get('telefono') or row.get('phone') or '').strip()
        email = (row.get('email') or '').strip()
        iva_cond = (row.get('condicion_iva') or row.get('iva_condition') or 'RESP. INSCRIPTO').strip()

        if not nombre:
            skipped += 1
            continue

        if dry_run:
            log(f"[DRY] {nombre} | CUIT: {cuit or '(sin CUIT)'}", 2)
            inserted += 1
            continue
        
        # Evitar duplicados
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
            INSERT INTO supplier (cuit, name, address, phone, email, iva_condition, last_debt_update)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cuit, nombre, direccion, telefono, email, iva_cond, datetime.now().strftime("%Y-%m-%d")))
        inserted += 1
    
    if not dry_run:
        conn.commit()
    
    log(f"✓ Insertados: {inserted} | Salteados: {skipped}", 1)


def import_clientes(conn, csv_path, dry_run):
    """Importa clientes desde CSV"""
    log("\n[2/3] Importando clientes...")
    
    if not os.path.exists(csv_path):
        log("WARN: clientes.csv no encontrado", 1)
        return
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        log("WARN: CSV vacío", 1)
        return
    
    # Detectar headers automáticamente
    headers = rows[0].keys()
    log(f"Headers detectados: {', '.join(headers)}", 1)
    
    log(f"Encontrados: {len(rows)} clientes", 1)
    
    inserted = skipped = 0
    cursor = conn.cursor()
    
    for row in rows:
        # Soportar diferentes nombres de columnas
        nombre = (row.get('nombre') or row.get('name') or '').strip()
        cuit = (row.get('cuit') or '').strip() or None
        domicilio = (row.get('domicilio') or row.get('home') or '').strip()
        telefono = (row.get('telefono') or row.get('phone') or '').strip() or None
        iva_cond = (row.get('condicion_iva') or row.get('iva_condition') or 'Consumidor Final').strip()

        if not nombre:
            skipped += 1
            continue

        if dry_run:
            log(f"[DRY] {nombre}", 2)
            inserted += 1
            continue
        
        # Evitar duplicados
        cursor.execute("SELECT id FROM customer WHERE name = ?", (nombre,))
        if cursor.fetchone():
            skipped += 1
            continue
        
        if cuit:
            cursor.execute("SELECT id FROM customer WHERE cuit = ?", (cuit,))
            if cursor.fetchone():
                skipped += 1
                continue
        
        if telefono:
            cursor.execute("SELECT id FROM customer WHERE phone = ?", (telefono,))
            if cursor.fetchone():
                skipped += 1
                continue
        
        cursor.execute("""
            INSERT INTO customer (name, cuit, home, phone, iva_condition)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, cuit, domicilio, telefono, iva_cond))
        inserted += 1
    
    if not dry_run:
        conn.commit()
    
    log(f"✓ Insertados: {inserted} | Salteados: {skipped}", 1)


def import_productos(conn, csv_path, dry_run):
    """Importa productos desde CSV"""
    log("\n[3/3] Importando productos...")
    
    if not os.path.exists(csv_path):
        log("ERROR: productos.csv no encontrado", 1)
        return
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    log(f"Encontrados: {len(rows)} productos", 1)
    
    inserted = skipped = with_stock = no_price = 0
    cursor = conn.cursor()
    
    for row in rows:
        nombre = row['nombre'].strip()
        envase = row['envase'].strip()
        iva = float(row['alicuota_iva'])
        rentabilidad = float(row['rentabilidad'])
        costo = float(row['precio_costo'])
        venta = float(row['precio_venta'])
        venta_con_iva = float(row['precio_venta_con_iva'])
        stock = int(float(row['stock']))
        
        if not nombre:
            skipped += 1
            continue
        
        if costo == 0 and venta == 0:
            no_price += 1
        
        if stock > 0:
            with_stock += 1
        
        if dry_run:
            stock_info = f"Stock:{stock}" if stock > 0 else "Sin stock"
            log(f"[DRY] {nombre} | {envase} | IVA:{iva}% | "
                f"Costo:${costo} Venta:${venta} | {stock_info}", 2)
            inserted += 1
            continue
        
        # Evitar duplicados
        cursor.execute("SELECT id FROM stock WHERE name = ? AND pack = ?", (nombre, envase))
        if cursor.fetchone():
            skipped += 1
            continue
        
        cursor.execute("""
            INSERT INTO stock (name, pack, list_price, discount, cost_price,
                               profit, price, iva, price_with_iva, quantity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nombre,
            envase,
            str(costo),           # list_price
            "0",                  # discount
            str(costo),           # cost_price
            str(rentabilidad),    # profit
            str(venta),           # price (sin IVA)
            str(iva),             # iva
            str(venta_con_iva),   # price_with_iva
            stock                 # quantity
        ))
        inserted += 1
    
    if not dry_run:
        conn.commit()
    
    log(f"✓ Insertados: {inserted} | Salteados: {skipped}", 1)
    log(f"ℹ  Sin precio: {no_price} | Con stock > 0: {with_stock}", 1)


def main():
    parser = argparse.ArgumentParser(description="Importa CSVs a SQLite")
    parser.add_argument("--db", required=True, help="Ruta al archivo .db")
    parser.add_argument("--src", required=True, help="Carpeta con archivos CSV")
    parser.add_argument("--dry-run", action="store_true", help="Solo muestra qué haría")
    args = parser.parse_args()
    
    if not os.path.exists(args.db):
        print(f"ERROR: Base de datos no encontrada: {args.db}")
        sys.exit(1)
    
    print("=" * 70)
    print("  IMPORTACIÓN CSV → SQLite")
    print(f"  DB:     {args.db}")
    print(f"  Origen: {args.src}")
    print(f"  Modo:   {'DRY RUN' if args.dry_run else 'REAL'}")
    print("=" * 70)
    
    conn = sqlite3.connect(args.db)
    
    # Importar en orden
    import_proveedores(conn, os.path.join(args.src, "proveedores.csv"), args.dry_run)
    import_clientes(conn, os.path.join(args.src, "clientes.csv"), args.dry_run)
    import_productos(conn, os.path.join(args.src, "productos.csv"), args.dry_run)
    
    conn.close()
    
    print("\n" + "=" * 70)
    if args.dry_run:
        print("  DRY RUN completado - ningún dato modificado")
        print("  Para ejecutar de verdad, quitá --dry-run")
    else:
        print("  ✓ Importación completada exitosamente")
    print("=" * 70)


if __name__ == "__main__":
    main()