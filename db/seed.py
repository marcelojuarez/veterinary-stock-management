import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from datetime import datetime
from random import choice, randint
from models.user import User
from models.supplier import SupplierModel
from models.security import gen_password, validate_password

DB_PATH = "db/stock.db"  # ruta a tu base de datos

def seed_stock():
    productos = [
        {"cuit_supplier": "20-45418222-0", "name": "ALIMENTO CANINO ADULTO", "pack": "BOLSAS 15KG", "profit": 30, "cost_price": 5000, "iva": 21, "quantity": 10},
        {"cuit_supplier": "20-45418222-0", "name": "ALIMENTO FELINO ADULTO", "pack": "BOLSAS 10KG", "profit": 25, "cost_price": 3500, "iva": 21, "quantity": 8},
        {"cuit_supplier": "20-45418222-0", "name": "ARENA SANITARIA", "pack": "CAJA 10L", "profit": 20, "cost_price": 800, "iva": 21, "quantity": 15},
        {"cuit_supplier": "20-45418222-0", "name": "SHAMPOO CANINO", "pack": "BOTELLA 500ML", "profit": 40, "cost_price": 500, "iva": 21, "quantity": 12},
        {"cuit_supplier": "20-45418222-0", "name": "JUGUETE PELOTA", "pack": "UNIDAD", "profit": 50, "cost_price": 150, "iva": 21, "quantity": 20},
        {"cuit_supplier": "20-45418222-0", "name": "COLLAR PERRO MEDIANO", "pack": "UNIDAD", "profit": 35, "cost_price": 400, "iva": 21, "quantity": 18},
        {"cuit_supplier": "20-45418222-0", "name": "CAMA FELINA", "pack": "UNIDAD", "profit": 30, "cost_price": 1200, "iva": 21, "quantity": 5},
        {"cuit_supplier": "20-45418222-0", "name": "VITAMINAS CANINAS", "pack": "CAJA 30 PASTILLAS", "profit": 25, "cost_price": 600, "iva": 21, "quantity": 10},
        {"cuit_supplier": "20-45418222-0", "name": "ANTIPULGAS PERRO", "pack": "CAJA 3 UNIDADES", "profit": 20, "cost_price": 900, "iva": 21, "quantity": 7},
        {"cuit_supplier": "20-45418222-0", "name": "ANTIPULGAS GATO", "pack": "CAJA 3 UNIDADES", "profit": 20, "cost_price": 800, "iva": 21, "quantity": 6},
        {"cuit_supplier": "20-45418222-0", "name": "CORREA PERRO", "pack": "UNIDAD", "profit": 40, "cost_price": 350, "iva": 21, "quantity": 14},
        {"cuit_supplier": "20-45418222-0", "name": "COMEDERO ACERO INOX", "pack": "UNIDAD", "profit": 25, "cost_price": 700, "iva": 21, "quantity": 9},
        {"cuit_supplier": "20-45418222-0", "name": "PLACA IDENTIFICACIÓN", "pack": "UNIDAD", "profit": 50, "cost_price": 200, "iva": 21, "quantity": 25},
        {"cuit_supplier": "20-45418222-0", "name": "CAMA CANINA PEQUEÑA", "pack": "UNIDAD", "profit": 30, "cost_price": 1000, "iva": 21, "quantity": 5},
        {"cuit_supplier": "20-45418222-0", "name": "ARENA BIODEGRADABLE", "pack": "CAJA 10L", "profit": 25, "cost_price": 850, "iva": 21, "quantity": 10},
        {"cuit_supplier": "20-45418222-0", "name": "SNACK GATO", "pack": "BOLSA 500G", "profit": 35, "cost_price": 450, "iva": 21, "quantity": 20},
        {"cuit_supplier": "20-45418222-0", "name": "SNACK PERRO", "pack": "BOLSA 500G", "profit": 35, "cost_price": 500, "iva": 21, "quantity": 15},
        {"cuit_supplier": "20-45418222-0", "name": "CEPILLO CANINO", "pack": "UNIDAD", "profit": 40, "cost_price": 300, "iva": 21, "quantity": 12},
        {"cuit_supplier": "20-45418222-0", "name": "CINTURÓN DE SEGURIDAD PERRO", "pack": "UNIDAD", "profit": 30, "cost_price": 600, "iva": 21, "quantity": 8},
        {"cuit_supplier": "20-45418222-0", "name": "TRANSPORTADORA GATO", "pack": "UNIDAD", "profit": 25, "cost_price": 1500, "iva": 21, "quantity": 4},
    ]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for p in productos:
        sale_price = round(p['cost_price'] * (1 + p['profit']/100), 2)
        price_with_iva = round(sale_price * (1 + p['iva']/100), 2)
        cursor.execute("""
            INSERT OR REPLACE INTO stock 
            (cuit_supplier, name, pack, profit, cost_price, price, iva, price_with_iva, quantity, created_at, last_price_update)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p['cuit_supplier'], p['name'], p['pack'], p['profit'], p['cost_price'], 
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

def seed_suppliers():

    suppliers = [
        {"cuit": "30-71234567-1", "name": "Veterinaria San Marcos", "home": "Av. Belgrano 450", "phone": "3584111111", "email": "sanmarcos@example.com", "debt": 0},
        {"cuit": "33-80123456-2", "name": "AgroVet Los Robles", "home": "Ruta 36 Km 5", "phone": "3584222222", "email": "losrobles@example.com", "debt": 0},
        {"cuit": "20-76543210-3", "name": "Clínica Animal Plus", "home": "Mitre 1230", "phone": "3584333333", "email": "animalplus@example.com", "debt": 0},
        {"cuit": "27-65432109-4", "name": "Pet Shop El Arca", "home": "Hipólito Yrigoyen 950", "phone": "3584444444", "email": "elarca@example.com", "debt": 0},
        {"cuit": "23-55667788-5", "name": "VetFarm Río Cuarto", "home": "Dean Funes 780", "phone": "3584555555", "email": "vetfarm@example.com", "debt": 0},
        {"cuit": "30-99887766-6", "name": "Proveedores Caninos SRL", "home": "Alvear 120", "phone": "3584666666", "email": "caninos_srl@example.com", "debt": 0},
        {"cuit": "33-11223344-7", "name": "Mascotas Felices", "home": "Marcelo T. de Alvear 500", "phone": "3584777777", "email": "felices@example.com", "debt": 0},
        {"cuit": "20-22113344-8", "name": "Agro Servicios La Unión", "home": "Ruta 30 Km 10", "phone": "3584888888", "email": "launion@example.com", "debt": 0},
        {"cuit": "27-33445566-9", "name": "Pet House Central", "home": "San Martín 855", "phone": "3584999999", "email": "pethouse@example.com", "debt": 0},
        {"cuit": "23-44556677-0", "name": "Clínica Animalia", "home": "Colón 220", "phone": "3584000001", "email": "animalia@example.com", "debt": 0},

        {"cuit": "30-55443322-1", "name": "Veterinaria El Trébol", "home": "Av. Italia 430", "phone": "3584000002", "email": "eltrebol@example.com", "debt": 0},
        {"cuit": "33-66778899-2", "name": "AgroVet Sur", "home": "Ruta 8 Km 1", "phone": "3584000003", "email": "agrovetsur@example.com", "debt": 0},
        {"cuit": "20-77889900-3", "name": "Pet Shop La Mascota", "home": "Santa Rosa 320", "phone": "3584000004", "email": "lamascota@example.com", "debt": 0},
        {"cuit": "27-88990011-4", "name": "Veterinaria Los Amigos", "home": "Pueyrredón 1240", "phone": "3584000005", "email": "losamigos@example.com", "debt": 0},
        {"cuit": "23-99001122-5", "name": "Clínica PetLife", "home": "Almafuerte 1900", "phone": "3584000006", "email": "petlife@example.com", "debt": 0},
        {"cuit": "30-12349876-6", "name": "Comercial Veterinaria Norte", "home": "Lavalle 980", "phone": "3584000007", "email": "vetnorte@example.com", "debt": 0},
        {"cuit": "33-23456789-7", "name": "Distribuidora AnimalPro", "home": "Av. Buenos Aires 2200", "phone": "3584000008", "email": "animalpro@example.com", "debt": 0},
        {"cuit": "20-34567890-8", "name": "AgroPet Servicios", "home": "Roca 1120", "phone": "3584000009", "email": "agropet@example.com", "debt": 0},
        {"cuit": "27-45678901-9", "name": "Pet Market", "home": "Mendoza 300", "phone": "3584000010", "email": "petmarket@example.com", "debt": 0},
        {"cuit": "23-56789012-0", "name": "Clínica VetCare", "home": "Baigorria 420", "phone": "3584000011", "email": "vetcare@example.com", "debt": 0},

        {"cuit": "30-67890123-1", "name": "Veterinaria Los Pinos", "home": "Libertad 670", "phone": "3584000012", "email": "lospinos@example.com", "debt": 0},
        {"cuit": "33-78901234-2", "name": "AgroVet Centro", "home": "Sarmiento 1450", "phone": "3584000013", "email": "agrovetcentro@example.com", "debt": 0},
        {"cuit": "20-89012345-3", "name": "MascotaShop", "home": "España 700", "phone": "3584000014", "email": "mascotashop@example.com", "debt": 0},
        {"cuit": "27-90123456-4", "name": "Clínica Buen Pastor", "home": "Alberdi 1205", "phone": "3584000015", "email": "buenpastor@example.com", "debt": 0},
        {"cuit": "23-01234567-5", "name": "Petworld RC", "home": "Bolívar 1010", "phone": "3584000016", "email": "petworld@example.com", "debt": 0},
        {"cuit": "30-11224455-6", "name": "VetMax Distribuciones", "home": "Avenida Sabattini 2400", "phone": "3584000017", "email": "vetmax@example.com", "debt": 0},
        {"cuit": "33-22335566-7", "name": "Agro Campo Total", "home": "Ruta 30 Km 6", "phone": "3584000018", "email": "campototal@example.com", "debt": 0},
        {"cuit": "20-33446677-8", "name": "Pet City", "home": "Entre Ríos 430", "phone": "3584000019", "email": "petcity@example.com", "debt": 0},
        {"cuit": "27-44557788-9", "name": "Veterinaria Don Bosco", "home": "Dean Funes 899", "phone": "3584000020", "email": "donbosco@example.com", "debt": 0},
        {"cuit": "23-55668899-0", "name": "Clínica VetSalud", "home": "Sobremonte 1220", "phone": "3584000021", "email": "vetsalud@example.com", "debt": 0},

        {"cuit": "30-66779900-1", "name": "ZooMarket", "home": "Mitre 780", "phone": "3584000022", "email": "zoomarket@example.com", "debt": 0},
        {"cuit": "33-77880011-2", "name": "Distribuidora Animal Center", "home": "Rivadavia 150", "phone": "3584000023", "email": "animalcenter@example.com", "debt": 0},
        {"cuit": "20-88991122-3", "name": "PetLine", "home": "Avenida Italia 2400", "phone": "3584000024", "email": "petline@example.com", "debt": 0},
        {"cuit": "27-99002233-4", "name": "Veterinaria Norte Grande", "home": "Bv. Roca 980", "phone": "3584000025", "email": "nortegrande@example.com", "debt": 0},
        {"cuit": "23-10111213-5", "name": "VetPoint", "home": "Avenida Sabattini 800", "phone": "3584000026", "email": "vetpoint@example.com", "debt": 0},
        {"cuit": "30-12131415-6", "name": "Mascotas & Cía", "home": "9 de Julio 300", "phone": "3584000027", "email": "mascotaycia@example.com", "debt": 0},
        {"cuit": "33-14151617-7", "name": "Distribuidora ProCampo", "home": "Ruta 158 Km 4", "phone": "3584000028", "email": "procampo@example.com", "debt": 0},
        {"cuit": "20-16171819-8", "name": "PetCo Regional", "home": "San Juan 1120", "phone": "3584000029", "email": "petcoregional@example.com", "debt": 0},
        {"cuit": "27-18192021-9", "name": "Clínica AnimalHome", "home": "Buenos Aires 1450", "phone": "3584000030", "email": "animalhome@example.com", "debt": 0},
        {"cuit": "23-20212223-0", "name": "Veterinaria Los Sauces", "home": "Rioja 800", "phone": "3584000031", "email": "lossauces@example.com", "debt": 0},

        {"cuit": "30-21222324-1", "name": "Pet Store Real", "home": "Alvear 670", "phone": "3584000032", "email": "petreal@example.com", "debt": 0},
        {"cuit": "33-23242526-2", "name": "Distribuidora VetLine", "home": "Río Negro 250", "phone": "3584000033", "email": "vetline@example.com", "debt": 0},
        {"cuit": "20-25262728-3", "name": "AgroVet CampoSur", "home": "Ruta 36 Km 12", "phone": "3584000034", "email": "camposur@example.com", "debt": 0},
        {"cuit": "27-27282930-4", "name": "Clínica Mascotín", "home": "Belgrano 990", "phone": "3584000035", "email": "mascotin@example.com", "debt": 0},
        {"cuit": "23-30313233-5", "name": "PetGo Tienda Animal", "home": "Roca 560", "phone": "3584000036", "email": "petgo@example.com", "debt": 0},
        {"cuit": "30-33343536-6", "name": "Veterinaria Vida Animal", "home": "Avenida España 450", "phone": "3584000037", "email": "vidanimal@example.com", "debt": 0},
        {"cuit": "33-35363738-7", "name": "Agro Servicios Patagónicos", "home": "Ruta A005 Km 3", "phone": "3584000038", "email": "patagonicos@example.com", "debt": 0},
        {"cuit": "20-37383940-8", "name": "Petland RC", "home": "Sobremonte 1340", "phone": "3584000039", "email": "petland@example.com", "debt": 0},
        {"cuit": "20-45418222-0", "name": "Marcelo Juarez", "home": "Zona Rural", "phone": "3385444490", "email": "marcelo@gmail.com", "debt": 0},
    ]             

    supplier_mdl = SupplierModel() 

    for supplier in suppliers:
        supplier_mdl.add_supplier(supplier)

    print("✅ Carga de proveedores correcta")

if __name__ == "__main__":
    seed_stock()
    seed_client()
    seed_clients()
    seed_suppliers()
    seed_sales_with_fiados()
    seed_sales_with_products()
