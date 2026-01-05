import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from datetime import datetime, timedelta
from random import choice, randint, uniform
from models.user import User
from models.supplier.__init__ import SupplierModel
from models.security import gen_password, validate_password

DB_PATH = "db/stock.db"

def seed_stock():
    # Categorías base de productos
    productos_base = [
        # Alimentos perros
        {"name": "ALIMENTO CANINO CACHORRO", "pack": "BOLSA 3KG", "profit": 30, "cost_price": 2500, "iva": 21},
        {"name": "ALIMENTO CANINO CACHORRO", "pack": "BOLSA 15KG", "profit": 28, "cost_price": 11000, "iva": 21},
        {"name": "ALIMENTO CANINO ADULTO", "pack": "BOLSA 3KG", "profit": 30, "cost_price": 2200, "iva": 21},
        {"name": "ALIMENTO CANINO ADULTO", "pack": "BOLSA 15KG", "profit": 28, "cost_price": 9500, "iva": 21},
        {"name": "ALIMENTO CANINO ADULTO", "pack": "BOLSA 20KG", "profit": 25, "cost_price": 12000, "iva": 21},
        {"name": "ALIMENTO CANINO SENIOR", "pack": "BOLSA 3KG", "profit": 30, "cost_price": 2800, "iva": 21},
        {"name": "ALIMENTO CANINO SENIOR", "pack": "BOLSA 15KG", "profit": 28, "cost_price": 12500, "iva": 21},
        {"name": "ALIMENTO PREMIUM PERRO RAZA PEQUEÑA", "pack": "BOLSA 7.5KG", "profit": 35, "cost_price": 8500, "iva": 21},
        {"name": "ALIMENTO PREMIUM PERRO RAZA MEDIANA", "pack": "BOLSA 15KG", "profit": 35, "cost_price": 15000, "iva": 21},
        {"name": "ALIMENTO PREMIUM PERRO RAZA GRANDE", "pack": "BOLSA 15KG", "profit": 35, "cost_price": 14500, "iva": 21},
        {"name": "ALIMENTO LIGHT PERRO", "pack": "BOLSA 15KG", "profit": 32, "cost_price": 13000, "iva": 21},
        {"name": "ALIMENTO HIPOALERGÉNICO PERRO", "pack": "BOLSA 10KG", "profit": 40, "cost_price": 18000, "iva": 21},
        
        # Alimentos gatos
        {"name": "ALIMENTO FELINO CACHORRO", "pack": "BOLSA 1KG", "profit": 30, "cost_price": 1800, "iva": 21},
        {"name": "ALIMENTO FELINO CACHORRO", "pack": "BOLSA 7.5KG", "profit": 28, "cost_price": 10000, "iva": 21},
        {"name": "ALIMENTO FELINO ADULTO", "pack": "BOLSA 1KG", "profit": 30, "cost_price": 1500, "iva": 21},
        {"name": "ALIMENTO FELINO ADULTO", "pack": "BOLSA 7.5KG", "profit": 28, "cost_price": 8500, "iva": 21},
        {"name": "ALIMENTO FELINO ADULTO", "pack": "BOLSA 15KG", "profit": 25, "cost_price": 15000, "iva": 21},
        {"name": "ALIMENTO FELINO SENIOR", "pack": "BOLSA 7.5KG", "profit": 30, "cost_price": 11000, "iva": 21},
        {"name": "ALIMENTO PREMIUM GATO CASTRADO", "pack": "BOLSA 7.5KG", "profit": 35, "cost_price": 12500, "iva": 21},
        {"name": "ALIMENTO PREMIUM GATO CONTROL PESO", "pack": "BOLSA 7.5KG", "profit": 35, "cost_price": 13000, "iva": 21},
        {"name": "ALIMENTO URINARY GATO", "pack": "BOLSA 7.5KG", "profit": 40, "cost_price": 16000, "iva": 21},
        
        # Arena sanitaria
        {"name": "ARENA SANITARIA BÁSICA", "pack": "BOLSA 5L", "profit": 25, "cost_price": 600, "iva": 21},
        {"name": "ARENA SANITARIA BÁSICA", "pack": "BOLSA 10L", "profit": 25, "cost_price": 1000, "iva": 21},
        {"name": "ARENA AGLOMERANTE", "pack": "BOLSA 5L", "profit": 30, "cost_price": 1200, "iva": 21},
        {"name": "ARENA AGLOMERANTE", "pack": "BOLSA 10L", "profit": 30, "cost_price": 2000, "iva": 21},
        {"name": "ARENA BIODEGRADABLE", "pack": "BOLSA 10L", "profit": 35, "cost_price": 2500, "iva": 21},
        {"name": "ARENA SILICA GEL", "pack": "BOLSA 5L", "profit": 40, "cost_price": 3500, "iva": 21},
        {"name": "PIEDRAS SANITARIAS", "pack": "BOLSA 10KG", "profit": 25, "cost_price": 800, "iva": 21},
        
        # Higiene y cuidado
        {"name": "SHAMPOO PERRO CACHORROS", "pack": "500ML", "profit": 40, "cost_price": 800, "iva": 21},
        {"name": "SHAMPOO PERRO ADULTO", "pack": "500ML", "profit": 40, "cost_price": 700, "iva": 21},
        {"name": "SHAMPOO PERRO ANTIPULGAS", "pack": "500ML", "profit": 40, "cost_price": 1200, "iva": 21},
        {"name": "SHAMPOO GATO", "pack": "500ML", "profit": 40, "cost_price": 900, "iva": 21},
        {"name": "ACONDICIONADOR PERRO", "pack": "500ML", "profit": 40, "cost_price": 850, "iva": 21},
        {"name": "SHAMPOO SECO PERRO", "pack": "400ML", "profit": 45, "cost_price": 1100, "iva": 21},
        {"name": "SHAMPOO SECO GATO", "pack": "400ML", "profit": 45, "cost_price": 1200, "iva": 21},
        {"name": "PERFUME MASCOTAS", "pack": "250ML", "profit": 50, "cost_price": 600, "iva": 21},
        {"name": "CEPILLO DENTAL PERRO", "pack": "UNIDAD", "profit": 45, "cost_price": 400, "iva": 21},
        {"name": "PASTA DENTAL PERRO", "pack": "100G", "profit": 45, "cost_price": 800, "iva": 21},
        {"name": "CORTAUÑAS PERRO", "pack": "UNIDAD", "profit": 40, "cost_price": 600, "iva": 21},
        {"name": "CORTAUÑAS GATO", "pack": "UNIDAD", "profit": 40, "cost_price": 550, "iva": 21},
        
        # Antiparasitarios
        {"name": "ANTIPULGAS PERRO 0-10KG", "pack": "PIPETA X3", "profit": 30, "cost_price": 1500, "iva": 21},
        {"name": "ANTIPULGAS PERRO 10-20KG", "pack": "PIPETA X3", "profit": 30, "cost_price": 1800, "iva": 21},
        {"name": "ANTIPULGAS PERRO 20-40KG", "pack": "PIPETA X3", "profit": 30, "cost_price": 2200, "iva": 21},
        {"name": "ANTIPULGAS PERRO +40KG", "pack": "PIPETA X3", "profit": 30, "cost_price": 2500, "iva": 21},
        {"name": "ANTIPULGAS GATO", "pack": "PIPETA X3", "profit": 30, "cost_price": 1600, "iva": 21},
        {"name": "COLLAR ANTIPULGAS PERRO", "pack": "UNIDAD", "profit": 35, "cost_price": 2000, "iva": 21},
        {"name": "COLLAR ANTIPULGAS GATO", "pack": "UNIDAD", "profit": 35, "cost_price": 1800, "iva": 21},
        {"name": "DESPARASITARIO INTERNO PERRO", "pack": "COMP X4", "profit": 35, "cost_price": 1200, "iva": 21},
        {"name": "DESPARASITARIO INTERNO GATO", "pack": "COMP X4", "profit": 35, "cost_price": 1100, "iva": 21},
        
        # Accesorios perros
        {"name": "COLLAR PERRO PEQUEÑO", "pack": "UNIDAD", "profit": 40, "cost_price": 500, "iva": 21},
        {"name": "COLLAR PERRO MEDIANO", "pack": "UNIDAD", "profit": 40, "cost_price": 700, "iva": 21},
        {"name": "COLLAR PERRO GRANDE", "pack": "UNIDAD", "profit": 40, "cost_price": 900, "iva": 21},
        {"name": "CORREA PERRO 1.5M", "pack": "UNIDAD", "profit": 40, "cost_price": 600, "iva": 21},
        {"name": "CORREA PERRO 3M RETRÁCTIL", "pack": "UNIDAD", "profit": 45, "cost_price": 2500, "iva": 21},
        {"name": "CORREA PERRO 5M RETRÁCTIL", "pack": "UNIDAD", "profit": 45, "cost_price": 3200, "iva": 21},
        {"name": "ARNÉS PERRO PEQUEÑO", "pack": "UNIDAD", "profit": 40, "cost_price": 1200, "iva": 21},
        {"name": "ARNÉS PERRO MEDIANO", "pack": "UNIDAD", "profit": 40, "cost_price": 1500, "iva": 21},
        {"name": "ARNÉS PERRO GRANDE", "pack": "UNIDAD", "profit": 40, "cost_price": 1800, "iva": 21},
        {"name": "BOZAL PERRO MEDIANO", "pack": "UNIDAD", "profit": 35, "cost_price": 800, "iva": 21},
        {"name": "BOZAL PERRO GRANDE", "pack": "UNIDAD", "profit": 35, "cost_price": 1000, "iva": 21},
        {"name": "PRETAL AUTO PERRO", "pack": "UNIDAD", "profit": 40, "cost_price": 1500, "iva": 21},
        
        # Accesorios gatos
        {"name": "COLLAR GATO CON CASCABEL", "pack": "UNIDAD", "profit": 45, "cost_price": 400, "iva": 21},
        {"name": "ARNÉS GATO", "pack": "UNIDAD", "profit": 40, "cost_price": 900, "iva": 21},
        {"name": "CORREA GATO", "pack": "UNIDAD", "profit": 40, "cost_price": 500, "iva": 21},
        
        # Comederos y bebederos
        {"name": "COMEDERO PLÁSTICO PEQUEÑO", "pack": "UNIDAD", "profit": 40, "cost_price": 300, "iva": 21},
        {"name": "COMEDERO PLÁSTICO MEDIANO", "pack": "UNIDAD", "profit": 40, "cost_price": 450, "iva": 21},
        {"name": "COMEDERO PLÁSTICO GRANDE", "pack": "UNIDAD", "profit": 40, "cost_price": 600, "iva": 21},
        {"name": "COMEDERO ACERO INOX PEQUEÑO", "pack": "UNIDAD", "profit": 35, "cost_price": 800, "iva": 21},
        {"name": "COMEDERO ACERO INOX MEDIANO", "pack": "UNIDAD", "profit": 35, "cost_price": 1200, "iva": 21},
        {"name": "COMEDERO ACERO INOX GRANDE", "pack": "UNIDAD", "profit": 35, "cost_price": 1500, "iva": 21},
        {"name": "BEBEDERO AUTOMÁTICO 1.5L", "pack": "UNIDAD", "profit": 35, "cost_price": 1000, "iva": 21},
        {"name": "BEBEDERO AUTOMÁTICO 3L", "pack": "UNIDAD", "profit": 35, "cost_price": 1500, "iva": 21},
        {"name": "BEBEDERO FUENTE GATO", "pack": "UNIDAD", "profit": 40, "cost_price": 3500, "iva": 21},
        {"name": "COMEDERO DOBLE PERRO", "pack": "UNIDAD", "profit": 40, "cost_price": 1200, "iva": 21},
        {"name": "COMEDERO ELEVADO PERRO", "pack": "UNIDAD", "profit": 40, "cost_price": 2500, "iva": 21},
        
        # Camas y cuchas
        {"name": "CAMA PERRO PEQUEÑO", "pack": "UNIDAD", "profit": 35, "cost_price": 2500, "iva": 21},
        {"name": "CAMA PERRO MEDIANO", "pack": "UNIDAD", "profit": 35, "cost_price": 3500, "iva": 21},
        {"name": "CAMA PERRO GRANDE", "pack": "UNIDAD", "profit": 35, "cost_price": 5000, "iva": 21},
        {"name": "CAMA GATO", "pack": "UNIDAD", "profit": 35, "cost_price": 2000, "iva": 21},
        {"name": "CUCHA PLÁSTICO PERRO MEDIANO", "pack": "UNIDAD", "profit": 30, "cost_price": 4500, "iva": 21},
        {"name": "CUCHA PLÁSTICO PERRO GRANDE", "pack": "UNIDAD", "profit": 30, "cost_price": 6500, "iva": 21},
        {"name": "ALMOHADÓN PERRO", "pack": "UNIDAD", "profit": 40, "cost_price": 1800, "iva": 21},
        {"name": "MANTA POLAR MASCOTAS", "pack": "UNIDAD", "profit": 40, "cost_price": 1200, "iva": 21},
        
        # Juguetes perros
        {"name": "PELOTA GOMA PERRO 6CM", "pack": "UNIDAD", "profit": 50, "cost_price": 300, "iva": 21},
        {"name": "PELOTA TENIS PERRO", "pack": "UNIDAD", "profit": 50, "cost_price": 250, "iva": 21},
        {"name": "HUESO GOMA PERRO", "pack": "UNIDAD", "profit": 50, "cost_price": 400, "iva": 21},
        {"name": "CUERDA PERRO 30CM", "pack": "UNIDAD", "profit": 50, "cost_price": 350, "iva": 21},
        {"name": "FRISBEE PERRO", "pack": "UNIDAD", "profit": 50, "cost_price": 500, "iva": 21},
        {"name": "PELUCHE PERRO PEQUEÑO", "pack": "UNIDAD", "profit": 45, "cost_price": 600, "iva": 21},
        {"name": "PELUCHE PERRO MEDIANO", "pack": "UNIDAD", "profit": 45, "cost_price": 900, "iva": 21},
        {"name": "KONG PERRO PEQUEÑO", "pack": "UNIDAD", "profit": 40, "cost_price": 1500, "iva": 21},
        {"name": "KONG PERRO MEDIANO", "pack": "UNIDAD", "profit": 40, "cost_price": 2000, "iva": 21},
        {"name": "KONG PERRO GRANDE", "pack": "UNIDAD", "profit": 40, "cost_price": 2500, "iva": 21},
        
        # Juguetes gatos
        {"name": "RATÓN JUGUETE GATO", "pack": "UNIDAD", "profit": 50, "cost_price": 200, "iva": 21},
        {"name": "VARITA PLUMAS GATO", "pack": "UNIDAD", "profit": 50, "cost_price": 350, "iva": 21},
        {"name": "PELOTA CASCABEL GATO", "pack": "UNIDAD", "profit": 50, "cost_price": 180, "iva": 21},
        {"name": "RASCADOR VERTICAL GATO", "pack": "UNIDAD", "profit": 35, "cost_price": 3500, "iva": 21},
        {"name": "RASCADOR HORIZONTAL GATO", "pack": "UNIDAD", "profit": 35, "cost_price": 1500, "iva": 21},
        {"name": "TÚNEL JUEGO GATO", "pack": "UNIDAD", "profit": 40, "cost_price": 2000, "iva": 21},
        {"name": "LASER GATO", "pack": "UNIDAD", "profit": 45, "cost_price": 600, "iva": 21},
        
        # Transportadoras
        {"name": "TRANSPORTADORA GATO PEQUEÑA", "pack": "UNIDAD", "profit": 30, "cost_price": 3000, "iva": 21},
        {"name": "TRANSPORTADORA GATO MEDIANA", "pack": "UNIDAD", "profit": 30, "cost_price": 4000, "iva": 21},
        {"name": "TRANSPORTADORA PERRO PEQUEÑO", "pack": "UNIDAD", "profit": 30, "cost_price": 3500, "iva": 21},
        {"name": "TRANSPORTADORA PERRO MEDIANO", "pack": "UNIDAD", "profit": 30, "cost_price": 5500, "iva": 21},
        {"name": "MOCHILA TRANSPORTE GATO", "pack": "UNIDAD", "profit": 35, "cost_price": 4500, "iva": 21},
        
        # Sanitarios gatos
        {"name": "BANDEJA SANITARIA SIMPLE", "pack": "UNIDAD", "profit": 35, "cost_price": 1200, "iva": 21},
        {"name": "BANDEJA SANITARIA CON TAPA", "pack": "UNIDAD", "profit": 35, "cost_price": 2500, "iva": 21},
        {"name": "BANDEJA SANITARIA AUTOLIMPIANTE", "pack": "UNIDAD", "profit": 30, "cost_price": 15000, "iva": 21},
        {"name": "PALA SANITARIA", "pack": "UNIDAD", "profit": 45, "cost_price": 300, "iva": 21},
        {"name": "ALFOMBRA SANITARIA", "pack": "UNIDAD", "profit": 40, "cost_price": 800, "iva": 21},
        
        # Snacks y premios
        {"name": "SNACK PERRO DENTAL", "pack": "CAJA 200G", "profit": 40, "cost_price": 800, "iva": 21},
        {"name": "SNACK PERRO HUESOS", "pack": "BOLSA 500G", "profit": 40, "cost_price": 1200, "iva": 21},
        {"name": "SNACK PERRO TIRAS POLLO", "pack": "BOLSA 250G", "profit": 40, "cost_price": 900, "iva": 21},
        {"name": "SNACK GATO CREMOSO", "pack": "CAJA X12", "profit": 40, "cost_price": 1500, "iva": 21},
        {"name": "SNACK GATO CRUJIENTE", "pack": "BOLSA 300G", "profit": 40, "cost_price": 1000, "iva": 21},
        {"name": "HUESO CARNAZA PERRO", "pack": "UNIDAD", "profit": 45, "cost_price": 600, "iva": 21},
        {"name": "OREJA CERDO PERRO", "pack": "UNIDAD", "profit": 45, "cost_price": 400, "iva": 21},
        
        # Vitaminas y suplementos
        {"name": "VITAMINAS PERRO CACHORROS", "pack": "CAJA X30", "profit": 35, "cost_price": 1500, "iva": 21},
        {"name": "VITAMINAS PERRO ADULTOS", "pack": "CAJA X30", "profit": 35, "cost_price": 1300, "iva": 21},
        {"name": "VITAMINAS GATO", "pack": "CAJA X30", "profit": 35, "cost_price": 1400, "iva": 21},
        {"name": "SUPLEMENTO ARTICULACIONES", "pack": "FRASCO X60", "profit": 35, "cost_price": 2500, "iva": 21},
        {"name": "OMEGA 3 MASCOTAS", "pack": "FRASCO X60", "profit": 35, "cost_price": 2000, "iva": 21},
        {"name": "PROBIÓTICOS MASCOTAS", "pack": "FRASCO X30", "profit": 40, "cost_price": 2200, "iva": 21},
        
        # Identificación
        {"name": "PLACA IDENTIFICACIÓN PERRO", "pack": "UNIDAD", "profit": 50, "cost_price": 350, "iva": 21},
        {"name": "PLACA IDENTIFICACIÓN GATO", "pack": "UNIDAD", "profit": 50, "cost_price": 300, "iva": 21},
        {"name": "CHIP IDENTIFICACIÓN", "pack": "UNIDAD", "profit": 30, "cost_price": 1200, "iva": 21},
        
        # Limpieza y hogar
        {"name": "PAÑOS HÚMEDOS MASCOTAS", "pack": "PAQUETE X50", "profit": 45, "cost_price": 600, "iva": 21},
        {"name": "REPELENTE MASCOTAS", "pack": "SPRAY 250ML", "profit": 40, "cost_price": 800, "iva": 21},
        {"name": "NEUTRALIZADOR OLORES", "pack": "SPRAY 500ML", "profit": 40, "cost_price": 1000, "iva": 21},
        {"name": "LIMPIADOR PATAS", "pack": "FRASCO 250ML", "profit": 45, "cost_price": 700, "iva": 21},
        {"name": "BOLSAS RESIDUOS PERRO", "pack": "ROLLO X100", "profit": 50, "cost_price": 400, "iva": 21},
        {"name": "PAÑALES PERRO M", "pack": "PAQUETE X12", "profit": 40, "cost_price": 1200, "iva": 21},
        {"name": "PAÑALES PERRO L", "pack": "PAQUETE X12", "profit": 40, "cost_price": 1500, "iva": 21},
        {"name": "EMPAPADORES MASCOTAS", "pack": "PAQUETE X30", "profit": 40, "cost_price": 2000, "iva": 21},
    ]
    
    # Obtener proveedores para asignar aleatoriamente
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    proveedores = cursor.execute("SELECT cuit FROM supplier").fetchall()
    
    if not proveedores:
        print("⚠️ No hay proveedores. Ejecuta seed_suppliers() primero.")
        conn.close()
        return
    
    cuits_proveedores = [p[0] for p in proveedores]
    
    # Insertar productos asignando proveedores al azar
    for p in productos_base:
        cuit_supplier = choice(cuits_proveedores)
        quantity = randint(5, 50)  # Cantidad aleatoria entre 5 y 50
        sale_price = round(p['cost_price'] * (1 + p['profit']/100), 2)
        price_with_iva = round(sale_price * (1 + p['iva']/100), 2)
        
        cursor.execute("""
            INSERT OR REPLACE INTO stock 
            (cuit_supplier, name, pack, profit, cost_price, price, iva, price_with_iva, quantity, created_at, last_price_update)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cuit_supplier, p['name'], p['pack'], p['profit'], p['cost_price'], 
            sale_price, p['iva'], price_with_iva, quantity, 
            datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%Y-%m-%d")
        ))
    
    conn.commit()
    conn.close()
    print(f"✅ Seed completado: {len(productos_base)} productos insertados")

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
    # Nombres de clientes variados
    nombres_veterinarias = [
        "Veterinaria", "Clínica", "AgroVet", "Pet Shop", "Hospital Veterinario",
        "Centro Veterinario", "Consultorio", "Animal Care", "Mundo Mascota"
    ]
    
    complementos = [
        "San Roque", "Los Pinos", "Del Sur", "Norte", "Centro", "Las Flores",
        "El Trébol", "La Esperanza", "Don Bosco", "Santa Rita", "Los Andes",
        "La Pampa", "El Campo", "Las Acacias", "Del Valle", "La Colina",
        "San Juan", "Santa Rosa", "El Parque", "La Villa", "Los Sauces"
    ]
    
    nombres_personas = [
        "Juan", "María", "Carlos", "Laura", "Roberto", "Ana", "José",
        "Patricia", "Luis", "Gabriela", "Pedro", "Claudia", "Miguel",
        "Silvia", "Fernando", "Mónica", "Diego", "Alejandra", "Ricardo",
        "Mariana", "Gustavo", "Valeria", "Sergio", "Carolina", "Pablo"
    ]
    
    apellidos = [
        "González", "Rodríguez", "Pérez", "García", "Martínez", "López",
        "Fernández", "Sánchez", "Romero", "Torres", "Díaz", "Ruiz",
        "Álvarez", "Giménez", "Castro", "Morales", "Ortiz", "Silva"
    ]
    
    calles = [
        "Av. España", "Buenos Aires", "San Martín", "Belgrano", "Mitre",
        "Rivadavia", "Av. Italia", "Colón", "Sarmiento", "Alvear",
        "Dean Funes", "Entre Ríos", "Libertad", "Independencia", "9 de Julio",
        "Roca", "Sobremonte", "Baigorria", "Mendoza", "Santa Rosa",
        "Ruta 36", "Ruta A005", "Ruta 8", "Ruta 30", "Ruta 158"
    ]
    
    condiciones_iva = ["Responsable Inscripto", "Monotributo", "Consumidor Final"]
    
    clientes = [
        {"nombre": "Consumidor Final", "cuit": "", "domicilio": "", "telefono": "", "condicion_iva": "Consumidor Final"}
    ]
    
    # Generar 100 clientes empresas (veterinarias, pet shops, etc.)
    for i in range(100):
        nombre_negocio = f"{choice(nombres_veterinarias)} {choice(complementos)}"
        
        # Generar CUIT (30 o 33 para empresas)
        tipo_cuit = choice(["30", "33"])
        num_cuit = f"{randint(10000000, 99999999)}"
        digito = randint(0, 9)
        cuit = f"{tipo_cuit}-{num_cuit}-{digito}"
        
        # Generar dirección
        calle = choice(calles)
        numero = randint(100, 2500)
        domicilio = f"{calle} {numero}"
        
        # Generar teléfono
        telefono = f"358{randint(4000000, 4999999)}"
        
        # Condición IVA (sin Consumidor Final para empresas)
        condicion = choice(["Responsable Inscripto", "Monotributo"])
        
        clientes.append({
            "nombre": nombre_negocio,
            "cuit": cuit,
            "domicilio": domicilio,
            "telefono": telefono,
            "condicion_iva": condicion
        })
    
    # Generar 50 clientes personas físicas
    for i in range(50):
        nombre = f"{choice(nombres_personas)} {choice(apellidos)}"
        
        # Generar CUIT persona física (20, 23, 24, 27)
        tipo_cuit = choice(["20", "23", "24", "27"])
        dni = randint(20000000, 45000000)
        digito = randint(0, 9)
        cuit = f"{tipo_cuit}-{dni}-{digito}"
        
        # Dirección
        calle = choice(calles)
        numero = randint(100, 2500)
        domicilio = f"{calle} {numero}"
        
        # Teléfono
        telefono = f"358{randint(4000000, 4999999)}"
        
        # Condición IVA
        condicion = choice(condiciones_iva)
        
        clientes.append({
            "nombre": nombre,
            "cuit": cuit,
            "domicilio": domicilio,
            "telefono": telefono,
            "condicion_iva": condicion
        })
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for c in clientes:
        try:
            cursor.execute("""
                INSERT INTO clientes (nombre, cuit, domicilio, telefono, condicion_iva)
                VALUES (?, ?, ?, ?, ?)
            """, (c['nombre'], c['cuit'], c['domicilio'], c['telefono'], c['condicion_iva']))
        except sqlite3.IntegrityError:
            # Si hay duplicado de CUIT, saltear
            continue
    
    conn.commit()
    conn.close()
    print(f"✅ Seed completado: {len(clientes)} clientes insertados correctamente")


def seed_sales_with_products():
    """
    MEJORADO: Crea ventas con productos usando estados correctos
    Estados: 'paid', 'pending', 'partial'
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Obtener clientes y productos
    clientes = cur.execute("SELECT id FROM clientes WHERE id > 1").fetchall()  # Excluir Consumidor Final
    productos = cur.execute("SELECT id, price_with_iva FROM stock").fetchall()
    
    if not clientes or not productos:
        print("⚠️ Debes ejecutar seed_clients() y seed_stock() primero.")
        conn.close()
        return

    # Generar ventas variadas con diferentes estados
    ventas_config = [
        # Ventas PAGADAS (50% de las ventas)
        *[{"cliente_id": choice(clientes)[0], "estado": "paid", "fecha_dias_atras": randint(1, 30)} for _ in range(20)],
        
        # Ventas PENDIENTES sin pagos (30% de las ventas)
        *[{"cliente_id": choice(clientes)[0], "estado": "pending", "fecha_dias_atras": randint(5, 20)} for _ in range(12)],
        
        # Ventas con PAGO PARCIAL (20% de las ventas)
        *[{"cliente_id": choice(clientes)[0], "estado": "partial", "fecha_dias_atras": randint(3, 15)} for _ in range(8)],
    ]

    print(f"📦 Creando {len(ventas_config)} ventas con productos...")

    for idx, venta in enumerate(ventas_config, 1):
        # Calcular fecha de la venta
        fecha_venta = datetime.now() - timedelta(days=venta["fecha_dias_atras"])
        fecha_str = fecha_venta.strftime("%Y-%m-%d %H:%M:%S")
        
        # Insertar venta inicial con total 0
        cur.execute("""
            INSERT INTO sales (date, total, cliente_id, estado)
            VALUES (?, 0, ?, ?)
        """, (fecha_str, venta["cliente_id"], venta["estado"]))
        sale_id = cur.lastrowid

        # Agregar productos aleatorios
        total_venta = 0
        num_productos = randint(2, 5)
        
        for _ in range(num_productos):
            prod_id, price = choice(productos)
            cantidad = randint(1, 4)
            subtotal = round(price * cantidad, 2)
            total_venta += subtotal
            
            cur.execute("""
                INSERT INTO sale_items (sale_id, product_id, quantity, price, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (sale_id, prod_id, cantidad, price, subtotal))

        # Actualizar total de la venta
        total_venta = round(total_venta, 2)
        cur.execute("UPDATE sales SET total = ? WHERE id = ?", (total_venta, sale_id))

        # 🔹 CREAR PAGOS según el estado
        if venta["estado"] == "paid":
            # Venta pagada: pago completo
            cur.execute("""
                INSERT INTO payments (sale_id, client_id, amount, date, method, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sale_id, venta["cliente_id"], total_venta, fecha_str, 
                  choice(["Efectivo", "Transferencia", "Tarjeta"]), "Pago completo"))
        
        elif venta["estado"] == "partial":
            # Venta parcial: pago entre 30% y 70% del total
            monto_pagado = round(total_venta * uniform(0.3, 0.7), 2)
            fecha_pago = fecha_venta + timedelta(days=randint(1, 3))
            
            cur.execute("""
                INSERT INTO payments (sale_id, client_id, amount, date, method, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sale_id, venta["cliente_id"], monto_pagado, 
                  fecha_pago.strftime("%Y-%m-%d %H:%M:%S"),
                  choice(["Efectivo", "Transferencia"]), "Pago parcial"))

        # Para 'pending' no creamos pagos
        
        if idx % 10 == 0:
            print(f"  ✓ {idx}/{len(ventas_config)} ventas creadas...")

    conn.commit()
    conn.close()
    
    print("✅ Ventas con productos creadas correctamente.")
    print(f"   📊 Estados: paid (50%), pending (30%), partial (20%)")

def seed_suppliers():
    # Nombres base para proveedores
    tipos_negocio = [
        "Veterinaria", "AgroVet", "Distribuidora", "Comercial", "Pet Shop",
        "Hospital Veterinario", "Clínica", "Centro Veterinario", "Depósito",
        "Mayorista", "Servicios Veterinarios", "Productos Veterinarios"
    ]
    
    complementos = [
        "San Marcos", "Los Robles", "Animal Plus", "El Arca", "La Unión",
        "Central", "Del Sur", "Norte Grande", "PetLife", "VetCare",
        "Los Pinos", "Las Flores", "Don Bosco", "Santa Rita", "El Trébol",
        "La Esperanza", "Del Valle", "Los Andes", "La Pampa", "San Juan",
        "Del Centro", "La Villa", "Los Sauces", "Campo Total", "ProCampo"
    ]
    
    sufijos = ["SRL", "SA", "& Cía", "Hnos", "e Hijos"]
    
    calles = [
        "Av. Belgrano", "Ruta 36", "Mitre", "Alvear", "Dean Funes",
        "San Martín", "Marcelo T. de Alvear", "Ruta 30", "Colón",
        "Av. Italia", "Santa Rosa", "Pueyrredón", "Almafuerte",
        "Lavalle", "Av. Buenos Aires", "Roca", "Mendoza", "Baigorria",
        "Libertad", "Sarmiento", "España", "Alberdi", "Bolívar",
        "Avenida Sabattini", "Entre Ríos", "9 de Julio", "Sobremonte",
        "Rivadavia", "Ruta 8", "Ruta 158", "Ruta A005"
    ]
    
    suppliers = []
    
    # Generar 200 proveedores
    for i in range(200):
        # Nombre del proveedor
        tipo = choice(tipos_negocio)
        complemento = choice(complementos)
        
        # 30% de probabilidad de agregar sufijo (SRL, SA, etc.)
        if randint(1, 100) <= 30:
            nombre = f"{tipo} {complemento} {choice(sufijos)}"
        else:
            nombre = f"{tipo} {complemento}"
        
        # Generar CUIT (30 o 33 para empresas)
        tipo_cuit = choice(["30", "33"])
        num_cuit = f"{randint(10000000, 99999999)}"
        digito = randint(0, 9)
        cuit = f"{tipo_cuit}-{num_cuit}-{digito}"
        
        # Dirección
        calle = choice(calles)
        if "Ruta" in calle:
            numero = f"Km {randint(1, 30)}"
        else:
            numero = str(randint(100, 2500))
        home = f"{calle} {numero}"
        
        # Teléfono
        phone = f"358{randint(4000000, 4999999)}"
        
        # Email
        nombre_email = nombre.lower().replace(" ", "").replace("&", "")[:15]
        email = f"{nombre_email}@example.com"
        
        # Deuda aleatoria (70% sin deuda, 30% con deuda)
        if randint(1, 100) <= 70:
            debt = 0
        else:
            debt = randint(5000, 150000)
        
        suppliers.append({
            "cuit": cuit,
            "name": nombre,
            "home": home,
            "phone": phone,
            "email": email,
            "debt": debt
        })
    
    supplier_mdl = SupplierModel()
    
    for supplier in suppliers:
        supplier_mdl.core.add_supplier(supplier)

    print("✅ Carga de proveedores correcta")

if __name__ == "__main__":
    print("🌱 Iniciando seed de la base de datos...")
    print("-" * 50)
    
    seed_suppliers()
    seed_client()
    seed_clients()
    seed_stock()
    seed_sales_with_products()
    
    print("-" * 50)
    print("✅ ¡Seed completado exitosamente!")