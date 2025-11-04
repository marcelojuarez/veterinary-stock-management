import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from datetime import datetime
from random import choice, randint
from models.user import User
from models.security import gen_password, validate_password

DB_PATH = "db/stock.db"  # ruta a tu base de datos

def seed_stock():
    productos = [
        {"id": "1001", "name": "ALIMENTO CANINO ADULTO", "pack": "BOLSAS 15KG", "profit": 30, "cost_price": 5000, "iva": 21, "quantity": 10},
        {"id": "1002", "name": "ALIMENTO FELINO ADULTO", "pack": "BOLSAS 10KG", "profit": 25, "cost_price": 3500, "iva": 21, "quantity": 8},
        {"id": "1003", "name": "ARENA SANITARIA", "pack": "CAJA 10L", "profit": 20, "cost_price": 800, "iva": 21, "quantity": 15},
        {"id": "1004", "name": "SHAMPOO CANINO", "pack": "BOTELLA 500ML", "profit": 40, "cost_price": 500, "iva": 21, "quantity": 12},
        {"id": "1005", "name": "JUGUETE PELOTA", "pack": "UNIDAD", "profit": 50, "cost_price": 150, "iva": 21, "quantity": 20},
        {"id": "1006", "name": "COLLAR PERRO MEDIANO", "pack": "UNIDAD", "profit": 35, "cost_price": 400, "iva": 21, "quantity": 18},
        {"id": "1007", "name": "CAMA FELINA", "pack": "UNIDAD", "profit": 30, "cost_price": 1200, "iva": 21, "quantity": 5},
        {"id": "1008", "name": "VITAMINAS CANINAS", "pack": "CAJA 30 PASTILLAS", "profit": 25, "cost_price": 600, "iva": 21, "quantity": 10},
        {"id": "1009", "name": "ANTIPULGAS PERRO", "pack": "CAJA 3 UNIDADES", "profit": 20, "cost_price": 900, "iva": 21, "quantity": 7},
        {"id": "1010", "name": "ANTIPULGAS GATO", "pack": "CAJA 3 UNIDADES", "profit": 20, "cost_price": 800, "iva": 21, "quantity": 6},
        {"id": "1011", "name": "CORREA PERRO", "pack": "UNIDAD", "profit": 40, "cost_price": 350, "iva": 21, "quantity": 14},
        {"id": "1012", "name": "COMEDERO ACERO INOX", "pack": "UNIDAD", "profit": 25, "cost_price": 700, "iva": 21, "quantity": 9},
        {"id": "1013", "name": "PLACA IDENTIFICACIÓN", "pack": "UNIDAD", "profit": 50, "cost_price": 200, "iva": 21, "quantity": 25},
        {"id": "1014", "name": "CAMA CANINA PEQUEÑA", "pack": "UNIDAD", "profit": 30, "cost_price": 1000, "iva": 21, "quantity": 5},
        {"id": "1015", "name": "ARENA BIODEGRADABLE", "pack": "CAJA 10L", "profit": 25, "cost_price": 850, "iva": 21, "quantity": 10},
        {"id": "1016", "name": "SNACK GATO", "pack": "BOLSA 500G", "profit": 35, "cost_price": 450, "iva": 21, "quantity": 20},
        {"id": "1017", "name": "SNACK PERRO", "pack": "BOLSA 500G", "profit": 35, "cost_price": 500, "iva": 21, "quantity": 15},
        {"id": "1018", "name": "CEPILLO CANINO", "pack": "UNIDAD", "profit": 40, "cost_price": 300, "iva": 21, "quantity": 12},
        {"id": "1019", "name": "CINTURÓN DE SEGURIDAD PERRO", "pack": "UNIDAD", "profit": 30, "cost_price": 600, "iva": 21, "quantity": 8},
        {"id": "1020", "name": "TRANSPORTADORA GATO", "pack": "UNIDAD", "profit": 25, "cost_price": 1500, "iva": 21, "quantity": 4},
    ]


    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for p in productos:
        sale_price = round(p['cost_price'] * (1 + p['profit']/100), 2)
        price_with_iva = round(sale_price * (1 + p['iva']/100), 2)
        cursor.execute("""
            INSERT OR REPLACE INTO stock 
            (id, name, pack, profit, cost_price, price, iva, price_with_iva, quantity, created_at, last_price_update)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p['id'], p['name'], p['pack'], p['profit'], p['cost_price'], 
            sale_price, p['iva'], price_with_iva, p['quantity'], 
            datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%Y-%m-%d")
        ))

    conn.commit()
    conn.close()
    print("Seed completado: 20 productos insertados")

def seed_client():
    users = [
        {"username": "admin", "password": "admin"},
        {"username": "juan", "password": "juan"}
    ]

    user_model = User()
    for user in users:
        encryp_pwd = gen_password(user['password'])
        user["password"] = encryp_pwd
        user_model.add_new_user(user)

    print("Usuarios cargados.")

def seed_clients():
    clientes = [
        {"nombre": "Veterinaria San Roque", "cuit": "30-71583927-5", "domicilio": "Av. España 945", "telefono": "3584123456", "condicion_iva": "Responsable Inscripto"},
        {"nombre": "AgroVet Río Cuarto", "cuit": "33-50217341-2", "domicilio": "Ruta A005 Km 2", "telefono": "3584234567", "condicion_iva": "Monotributo"},
        {"nombre": "Clínica Mascotera", "cuit": "20-30482956-7", "domicilio": "Buenos Aires 1200", "telefono": "3584345678", "condicion_iva": "Responsable Inscripto"},
        {"nombre": "Pet Shop Luna", "cuit": "27-40918234-3", "domicilio": "Av. Italia 1025", "telefono": "3584456789", "condicion_iva": "Monotributo"},
        {"nombre": "Consumidor Final", "cuit": "", "domicilio": "", "telefono": "", "condicion_iva": "Consumidor Final"},
    ]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for c in clientes:
        cursor.execute("""
            INSERT OR REPLACE INTO clientes (nombre, cuit, domicilio, telefono, condicion_iva)
            VALUES (?, ?, ?, ?, ?)
        """, (c['nombre'], c['cuit'], c['domicilio'], c['telefono'], c['condicion_iva']))

    conn.commit()
    conn.close()
    print("Seed completado: clientes insertados correctamente ✅")

def seed_sales_with_fiados():
    ventas = [
        {"cliente_id": 1, "total": 15000, "estado": "fiada"},
        {"cliente_id": 2, "total": 8200, "estado": "fiada"},
        {"cliente_id": 3, "total": 12500, "estado": "pagada"},
        {"cliente_id": 4, "total": 5600, "estado": "fiada"}
    ]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for v in ventas:
        cursor.execute("""
            INSERT INTO sales (date, total, cliente_id, estado)
            VALUES (datetime('now'), ?, ?, ?)
        """, (v['total'], v['cliente_id'], v['estado']))

    conn.commit()
    conn.close()
    print("💰 Seed completado: ventas con estado 'fiada' y 'pagada'")

def seed_sales_with_products():
    """Crea ventas con productos y deudas (fiadas)"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Obtener clientes y productos
    clientes = cur.execute("SELECT id FROM clientes").fetchall()
    productos = cur.execute("SELECT id, price_with_iva FROM stock").fetchall()
    if not clientes or not productos:
        print("⚠️ Debes ejecutar seed_clients() y seed_stock() primero.")
        return

    ventas = [
        {"cliente_id": clientes[0][0], "estado": "fiada"},
        {"cliente_id": clientes[1][0], "estado": "fiada"},
        {"cliente_id": clientes[2][0], "estado": "pagada"},
        {"cliente_id": clientes[3][0], "estado": "fiada"},
    ]

    for venta in ventas:
        total = 0
        cur.execute("""
            INSERT INTO sales (date, total, cliente_id, estado)
            VALUES (?, 0, ?, ?)
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), venta["cliente_id"], venta["estado"]))
        sale_id = cur.lastrowid

        # Insertar productos aleatorios
        for _ in range(randint(2, 4)):
            prod_id, price = choice(productos)
            cantidad = randint(1, 3)
            subtotal = round(price * cantidad, 2)
            total += subtotal
            cur.execute("""
                INSERT INTO sale_items (sale_id, product_id, quantity, price, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (sale_id, prod_id, cantidad, price, subtotal))

        # Actualizar total de la venta
        cur.execute("UPDATE sales SET total = ? WHERE id = ?", (round(total, 2), sale_id))

    conn.commit()
    conn.close()
    print("✅ Ventas con productos fiadas y pagadas creadas correctamente.")

if __name__ == "__main__":
    seed_stock()
    seed_client()
    seed_clients()
    seed_sales_with_fiados()
    seed_sales_with_products()
