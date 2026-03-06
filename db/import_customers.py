"""
Script para importar clientes desde el XML exportado de Crystal Reports
a la base de datos SQLite del proyecto.

USO:
    python import_customers.py

Asegurate de tener el archivo clientesxml.xml en la misma carpeta,
o cambiá XML_PATH a la ruta correcta.
También ajustá DB_PATH si tu base de datos está en otra ubicación.
"""

import xml.etree.ElementTree as ET
import sqlite3
import os

# ── Configuración ──────────────────────────────────────────────
XML_PATH = "db/clientesxml.xml"  # ruta al XML exportado
DB_PATH  = "db/stock.db"       # ruta a tu base de datos
# ───────────────────────────────────────────────────────────────

NS = {"cr": "urn:crystal-reports:schemas:report-detail"}

def get_field(section, field_name):
    """Obtener el valor de un campo por su atributo Name."""
    field = section.find(f".//cr:Field[@Name='{field_name}']", NS)
    if field is not None:
        value = field.findtext("cr:Value", default="", namespaces=NS)
        return value.strip() if value else None
    return None

def parse_customers(xml_path):
    """Parsear el XML y devolver lista de clientes."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    customers = []

    for group in root.findall("cr:Group[@Level='1']", NS):
        header  = group.find(".//cr:GroupHeader/cr:Section", NS)
        details = group.find(".//cr:Details/cr:Section", NS)

        if header is None:
            continue

        name      = get_field(header, "ApellidoRSocial1")
        doc_type  = get_field(header, "Abreviatura1")     # DNI o CUIT
        doc_num   = get_field(header, "NroDocumento1")
        phone     = get_field(header, "Telefonos1")
        home      = get_field(details, "Direccion1") if details is not None else None

        # Si el tipo de documento es CUIT lo guardamos en cuit,
        # si es DNI no lo guardamos como cuit (para evitar conflictos UNIQUE)
        cuit = doc_num if doc_type == "CUIT" else None

        # Limpiar teléfono vacío
        if phone == "":
            phone = None

        # Limpiar home
        if home:
            home = home.strip()

        if name:
            customers.append({
                "name":  name,
                "cuit":  cuit,
                "home":  home,
                "phone": phone,
            })

    return customers

def import_to_db(customers, db_path):
    """Insertar clientes en la base de datos."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    inserted = 0
    skipped  = 0

    for c in customers:
        try:
            cursor.execute("""
                INSERT INTO customer (name, cuit, home, phone)
                VALUES (?, ?, ?, ?)
            """, (c["name"], c["cuit"], c["home"], c["phone"]))
            inserted += 1
        except sqlite3.IntegrityError:
            # CUIT o phone duplicado → saltear
            print(f"  [SKIP] {c['name']} - ya existe o CUIT/teléfono duplicado")
            skipped += 1

    conn.commit()
    conn.close()

    return inserted, skipped

def main():
    if not os.path.exists(XML_PATH):
        print(f"ERROR: No se encontró el archivo XML en '{XML_PATH}'")
        return

    if not os.path.exists(DB_PATH):
        print(f"ERROR: No se encontró la base de datos en '{DB_PATH}'")
        return

    print(f"Leyendo clientes de '{XML_PATH}'...")
    customers = parse_customers(XML_PATH)
    print(f"  → {len(customers)} clientes encontrados en el XML")

    print(f"\nImportando a '{DB_PATH}'...")
    inserted, skipped = import_to_db(customers, DB_PATH)

    print(f"\n✓ Importación completada:")
    print(f"  - Insertados: {inserted}")
    print(f"  - Salteados:  {skipped}")

if __name__ == "__main__":
    main()