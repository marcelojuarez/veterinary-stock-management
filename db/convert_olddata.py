"""
db/convert_olddata.py — Convierte exports del sistema anterior a CSVs estándar
listos para importar con import_from_csv.py

Uso:
    python db/convert_olddata.py --src olddata/ --out olddata/converted/
    python db/import_from_csv.py --db db/stock.db --src olddata/converted/ --dry-run
    python db/import_from_csv.py --db db/stock.db --src olddata/converted/
"""

import argparse
import csv
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET


NS = 'urn:crystal-reports:schemas:report-detail'


def log(msg, indent=0):
    print("  " * indent + msg)


def convert_proveedores(src_dir, out_dir):
    src = os.path.join(src_dir, "proveedores_orig.csv")
    dst = os.path.join(out_dir, "proveedores.csv")
    if not os.path.exists(src):
        log("WARN: proveedores_orig.csv no encontrado — saltando")
        return
    shutil.copy(src, dst)
    with open(src, encoding='utf-8') as f:
        count = sum(1 for _ in f) - 1  # minus header
    log(f"✓ proveedores.csv — {count} registros")


def convert_clientes(src_dir, out_dir):
    src = os.path.join(src_dir, "clientes.csv")
    dst = os.path.join(out_dir, "clientes.csv")
    if not os.path.exists(src):
        log("WARN: clientes.csv no encontrado — saltando")
        return

    rows_out = []
    with open(src, encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 24:
                continue
            # Col 16 = row number — skip non-data rows
            try:
                int(row[16].strip())
            except ValueError:
                continue

            nombre   = row[17].strip()
            doc_type = row[18].strip().upper()
            doc_num  = row[19].strip().replace("-", "").replace(" ", "")
            telefono = row[20].strip() or None
            domicilio = row[23].strip()

            if not nombre:
                continue

            # Formatear CUIT como XX-XXXXXXXX-X si tiene 11 dígitos
            cuit = None
            if doc_type == "CUIT" and doc_num.isdigit() and len(doc_num) == 11:
                cuit = f"{doc_num[:2]}-{doc_num[2:10]}-{doc_num[10]}"
            elif doc_type == "CUIT" and doc_num:
                cuit = doc_num

            rows_out.append({
                "nombre":        nombre,
                "cuit":          cuit or "",
                "domicilio":     domicilio,
                "telefono":      telefono or "",
                "condicion_iva": "R. Inscripto" if cuit else "Consumidor Final",
            })

    with open(dst, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["nombre", "cuit", "domicilio", "telefono", "condicion_iva"])
        writer.writeheader()
        writer.writerows(rows_out)

    log(f"✓ clientes.csv — {len(rows_out)} registros")


def _field_value(element, field_name):
    """Devuelve el texto de <Value> para el FieldName dado dentro de element."""
    for field in element.iter(f'{{{NS}}}Field'):
        if field.get('FieldName') == field_name:
            v = field.find(f'{{{NS}}}Value')
            if v is not None and v.text:
                return v.text.strip()
    return None


def convert_productos(src_dir, out_dir):
    src = os.path.join(src_dir, "articulos_xml.xml")
    dst = os.path.join(out_dir, "productos.csv")
    if not os.path.exists(src):
        log("WARN: articulos_xml.xml no encontrado — saltando")
        return

    tree = ET.parse(src)
    root = tree.getroot()

    # Regex para parsear el texto del GroupHeader
    pattern = re.compile(
        r'Artículo:\s*\d+\s*-\s*(.+?)\s+Iva:\s*([\d,]+)\s+Envase:\s*(.+?)\s+Flia\.',
        re.IGNORECASE
    )

    rows_out = []
    seen = set()

    for group in root.iter(f'{{{NS}}}Group'):
        # Buscar el GroupHeader con el texto del artículo
        header_text = None
        for section in group:
            tag = section.tag.split('}')[-1]
            if tag == 'GroupHeader':
                for text_el in section.iter(f'{{{NS}}}Text'):
                    tv = text_el.find(f'{{{NS}}}TextValue')
                    if tv is not None and tv.text and 'Artículo:' in tv.text:
                        header_text = tv.text.strip()
                        break
            if header_text:
                break

        if not header_text:
            continue

        m = pattern.search(header_text)
        if not m:
            continue

        nombre  = m.group(1).strip()
        iva_str = m.group(2).replace(',', '.')
        envase  = m.group(3).strip()

        # Deduplicar — hay 2 listas de precios por artículo
        key = (nombre, envase)
        if key in seen:
            continue
        seen.add(key)

        try:
            iva = float(iva_str)
        except ValueError:
            iva = 21.0

        costo_raw = _field_value(group, '{@CostoVta}')
        rent_raw  = _field_value(group, '{Datos.VTA_PorcRentabilidad}')

        try:
            costo = float(costo_raw) if costo_raw else 0.0
        except ValueError:
            costo = 0.0

        try:
            rent = float(rent_raw) if rent_raw else 0.0
        except ValueError:
            rent = 0.0

        precio_venta         = round(costo * (1 + rent / 100), 2)
        precio_venta_con_iva = round(precio_venta * (1 + iva / 100), 2)

        rows_out.append({
            "nombre":              nombre,
            "envase":              envase,
            "alicuota_iva":        iva,
            "rentabilidad":        rent,
            "precio_costo":        costo,
            "precio_venta":        precio_venta,
            "precio_venta_con_iva": precio_venta_con_iva,
            "stock":               0,
        })

    fields = ["nombre", "envase", "alicuota_iva", "rentabilidad",
              "precio_costo", "precio_venta", "precio_venta_con_iva", "stock"]
    with open(dst, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows_out)

    log(f"✓ productos.csv — {len(rows_out)} registros (stock=0, actualizar manualmente)")


def main():
    parser = argparse.ArgumentParser(description="Convierte olddata exports a CSVs estándar")
    parser.add_argument("--src", required=True, help="Carpeta con los archivos originales")
    parser.add_argument("--out", required=True, help="Carpeta de salida para los CSVs convertidos")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    print("=" * 60)
    print("  CONVERSIÓN OLDDATA → CSV")
    print(f"  Origen: {args.src}")
    print(f"  Salida: {args.out}")
    print("=" * 60)

    convert_proveedores(args.src, args.out)
    convert_clientes(args.src, args.out)
    convert_productos(args.src, args.out)

    print("=" * 60)
    print("  ✓ Conversión completada")
    print(f"  Siguiente paso:")
    print(f"    python db/import_from_csv.py --db db/stock.db --src {args.out} --dry-run")
    print("=" * 60)


if __name__ == "__main__":
    main()
