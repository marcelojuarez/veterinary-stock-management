import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from datetime import datetime, timedelta
from random import choice, randint, uniform
from models.company import CompanyModel
from models.user import User
from models.supplier.__init__ import SupplierModel
from models.security import gen_password

DB_PATH = "db/stock.db"

def seed_company_data():
    company_data = {
            "business_name": "EGUIZABAL DIEGO VICENTE",
            "cuit": "20-14221046-1",
            "iva_condition": "Resp. Inscripto",
            "start_date": "", 
            "address": "RUTA 8 KM 681",
            "city": "CHAJAN",
            "province": "CORDOBA",
            "postal_code": "5837",
            "phone1" : "358 - 2412227",
            "phone2" : "03582 492040",
        }

    company_mdl = CompanyModel()
    company_mdl.add_company_data(company_data)

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
    
    # Insertar productos asignando proveedores al azar
    for p in productos_base:
        quantity = randint(5, 50)  # Cantidad aleatoria entre 5 y 50
        sale_price = round(p['cost_price'] * (1 + p['profit']/100), 2)
        price_with_iva = round(sale_price * (1 + p['iva']/100), 2)
        
        cursor.execute("""
            INSERT OR REPLACE INTO stock
            (name, pack, profit, cost_price, price, iva, price_with_iva, quantity, created_at, last_price_update)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p['name'], p['pack'], p['profit'], p['cost_price'], 
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

# Códigos de provincia reales de SENASA para RENSPA y CUIG
CODIGOS_PROVINCIA = {
    "Buenos Aires": "06",
    "Catamarca": "10",
    "Chaco": "22",
    "Chubut": "26",
    "Córdoba": "14",
    "Corrientes": "18",
    "Entre Ríos": "30",
    "Formosa": "34",
    "Jujuy": "38",
    "La Pampa": "42",
    "La Rioja": "46",
    "Mendoza": "50",
    "Misiones": "54",
    "Neuquén": "58",
    "Río Negro": "62",
    "Salta": "66",
    "San Juan": "70",
    "San Luis": "74",
    "Santa Cruz": "78",
    "Santa Fe": "82",
    "Santiago del Estero": "86",
    "Tierra del Fuego": "94",
    "Tucumán": "90"
}

# Códigos de departamento reales de Córdoba (para ejemplo más realista)
DEPARTAMENTOS_CORDOBA = {
    "Capital": "014",
    "Colón": "021",
    "Cruz del Eje": "028",
    "General Roca": "035",
    "General San Martín": "042",
    "Ischilín": "049",
    "Juárez Celman": "056",
    "Marcos Juárez": "063",
    "Minas": "070",
    "Pocho": "077",
    "Punilla": "084",
    "Río Cuarto": "091",
    "Río Primero": "098",
    "Río Seco": "105",
    "Río Segundo": "112",
    "San Alberto": "119",
    "San Javier": "126",
    "San Justo": "133",
    "Santa María": "140",
    "Sobremonte": "147",
    "Tercero Arriba": "154",
    "Totoral": "161",
    "Tulumba": "168",
    "Unión": "175",
    "Calamuchita": "007"
}

# Nombres de establecimientos ganaderos reales/típicos
NOMBRES_ESTABLECIMIENTOS = [
    "La Esperanza", "San José", "Santa Rosa", "El Porvenir", "La Aurora",
    "Los Alamos", "El Trebol", "La Fortuna", "San Antonio", "El Carmen",
    "La Paz", "Los Nogales", "El Paraíso", "Santa María", "San Francisco",
    "La Primavera", "El Progreso", "Los Sauces", "La Victoria", "San Miguel",
    "El Refugio", "Las Margaritas", "San Pedro", "La Cautiva", "El Mangrullo",
    "Los Quebrachos", "La Pampa", "San Martín", "El Rodeo", "Las Acacias",
    "La Constancia", "El Lucero", "Los Talas", "San Carlos", "La Unión",
    "El Diamante", "Las Rosas", "San Ignacio", "La Granja", "El Sauce",
    "Los Cardos", "La Blanqueada", "San Lorenzo", "El Monte", "Las Lomas",
    "La Estación", "El Recreo", "Los Algarrobos", "San Ramón", "La Legua",
    "El Talar", "Las Delicias", "San Felipe", "La Herradura", "El Bagual",
    "Los Molles", "La Querencia", "San Cayetano", "El Chañar", "Las Tunas"
]

# Tipos de actividad ganadera
ACTIVIDADES_GANADERAS = [
    "Cría", "Recría", "Engorde", "Ciclo Completo", "Tambo", "Cabaña",
    "Feedlot", "Invernada", "Cría y Recría"
]


def generar_cuig(provincia="Córdoba"):
    """
    Genera un CUIG (Clave Única de Identificación Ganadera) con formato real.
    Formato: XX-XXX-XXXXX-X (Provincia-Departamento-Número-Dígito verificador)
    Ejemplo real: 14-091-12345-7
    """
    cod_provincia = CODIGOS_PROVINCIA.get(provincia, "14")  # Default Córdoba
    
    if provincia == "Córdoba":
        cod_departamento = choice(list(DEPARTAMENTOS_CORDOBA.values()))
    else:
        cod_departamento = f"{randint(1, 200):03d}"
    
    numero = f"{randint(1, 99999):05d}"
    digito_verificador = randint(0, 9)
    
    return f"{cod_provincia}-{cod_departamento}-{numero}-{digito_verificador}"


def generar_renspa(provincia="Córdoba"):
    """
    Genera un RENSPA (Registro Nacional Sanitario de Productores Agropecuarios) con formato real.
    Formato: XX.XXX.X.XXXXX/XX (Provincia.Departamento.Actividad.Número/Año)
    Ejemplo real: 14.091.0.00123/24
    """
    cod_provincia = CODIGOS_PROVINCIA.get(provincia, "14")
    
    if provincia == "Córdoba":
        cod_departamento = choice(list(DEPARTAMENTOS_CORDOBA.values()))
    else:
        cod_departamento = f"{randint(1, 200):03d}"
    
    # Tipo de actividad (0=Bovinos, 1=Porcinos, 2=Ovinos, 3=Caprinos, 4=Equinos, 5=Avícola)
    tipo_actividad = randint(0, 5)
    
    numero = f"{randint(1, 99999):05d}"
    
    # Año de inscripción (últimos 2 dígitos)
    anio = randint(10, 25)  # Entre 2010 y 2025
    
    return f"{cod_provincia}.{cod_departamento}.{tipo_actividad}.{numero}/{anio:02d}"


def generar_cv():
    """
    Genera una CV (Clave de Vinculación) con formato real.
    La CV es un número de 8 dígitos asignado por SENASA.
    Ejemplo real: 12345678
    """
    return f"{randint(10000000, 99999999)}"


def generar_establecimiento():
    """
    Genera un nombre de establecimiento ganadero realista.
    Puede incluir número de potrero o lote.
    """
    nombre_base = choice(NOMBRES_ESTABLECIMIENTOS)
    
    # 30% de probabilidad de agregar número de lote/potrero
    if randint(1, 100) <= 30:
        return f"{nombre_base} - Lote {randint(1, 20)}"
    
    # 20% de probabilidad de agregar actividad
    if randint(1, 100) <= 20:
        actividad = choice(ACTIVIDADES_GANADERAS)
        return f"{nombre_base} ({actividad})"
    
    return nombre_base

def seed_clients():
    """
    ACTUALIZADO: Genera clientes con datos agropecuarios reales
    (CV, CUIG, RENSPA, Establecimiento)
    """
    
    # Nombres de clientes variados
    nombres_veterinarias = [
        "Veterinaria", "Clínica", "AgroVet", "Pet Shop", "Hospital Veterinario",
        "Centro Veterinario", "Consultorio", "Animal Care", "Mundo Mascota"
    ]
    
    # Nombres específicos para productores agropecuarios
    nombres_agropecuarios = [
        "Estancia", "Cabaña", "Tambo", "Campo", "Agropecuaria", "Ganadera",
        "Hacienda", "Establecimiento", "Granja", "Feedlot"
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
    
    condiciones_iva = ["Consumidor Final", "R. Inscripto", "Exento", "Monotributista"]
    
    # Provincias para variar los códigos RENSPA/CUIG
    provincias = ["Córdoba", "Buenos Aires", "Santa Fe", "La Pampa", "Entre Ríos"]
    
    clientes = [
        {
            "nombre": "Consumidor Final", 
            "cuit": "", 
            "domicilio": "", 
            "telefono": "", 
            "condicion_iva": "Consumidor Final",
            "cv": "",
            "cuig": "",
            "renspa": "",
            "establecimiento": ""
        }
    ]
    
    # =========================================================================
    # TIPO 1: Productores agropecuarios (60 clientes) - TIENEN TODOS LOS DATOS
    # =========================================================================
    print("  📋 Generando productores agropecuarios...")
    for i in range(60):
        provincia = choice(provincias)
        
        # Nombre del establecimiento/productor
        if randint(1, 100) <= 50:
            # Nombre de empresa agropecuaria
            nombre = f"{choice(nombres_agropecuarios)} {choice(complementos)}"
            tipo_cuit = choice(["30", "33"])
        else:
            # Nombre de persona física (productor)
            nombre = f"{choice(nombres_personas)} {choice(apellidos)}"
            tipo_cuit = choice(["20", "23", "27"])
        
        # Generar CUIT
        if tipo_cuit in ["30", "33"]:
            num_cuit = f"{randint(10000000, 99999999)}"
        else:
            num_cuit = f"{randint(20000000, 45000000)}"
        digito = randint(0, 9)
        cuit = f"{tipo_cuit}-{num_cuit}-{digito}"
        
        # Dirección (rutas para productores)
        if randint(1, 100) <= 70:
            calle = choice(["Ruta 36", "Ruta 8", "Ruta 30", "Ruta 158", "Ruta A005", "Ruta Provincial 10"])
            numero = f"Km {randint(1, 150)}"
        else:
            calle = choice(calles)
            numero = str(randint(100, 2500))
        domicilio = f"{calle} {numero}"
        
        telefono = f"358{randint(4000000, 4999999)}"
        condicion = choice(condiciones_iva)
        
        # DATOS AGROPECUARIOS COMPLETOS
        cv = generar_cv()
        cuig = generar_cuig(provincia)
        renspa = generar_renspa(provincia)
        establecimiento = generar_establecimiento()
        
        clientes.append({
            "nombre": nombre,
            "cuit": cuit,
            "domicilio": domicilio,
            "telefono": telefono,
            "condicion_iva": condicion,
            "cv": cv,
            "cuig": cuig,
            "renspa": renspa,
            "establecimiento": establecimiento
        })
    
    # =========================================================================
    # TIPO 2: Veterinarias/Pet Shops (50 clientes) - DATOS PARCIALES
    # =========================================================================
    print("  🏥 Generando veterinarias y pet shops...")
    for i in range(50):
        nombre_negocio = f"{choice(nombres_veterinarias)} {choice(complementos)}"
        
        tipo_cuit = choice(["30", "33"])
        num_cuit = f"{randint(10000000, 99999999)}"
        digito = randint(0, 9)
        cuit = f"{tipo_cuit}-{num_cuit}-{digito}"
        
        calle = choice(calles)
        numero = randint(100, 2500)
        domicilio = f"{calle} {numero}"
        
        telefono = f"358{randint(4000000, 4999999)}"
        condicion = choice(["Responsable Inscripto", "Monotributo"])
        
        # Las veterinarias pueden tener algunos datos agropecuarios (si atienden ganado)
        if randint(1, 100) <= 30:  # 30% tiene datos agropecuarios
            cv = generar_cv()
            cuig = ""  # No suelen tener CUIG
            renspa = generar_renspa("Córdoba") if randint(1, 100) <= 50 else ""
            establecimiento = ""
        else:
            cv = ""
            cuig = ""
            renspa = ""
            establecimiento = ""
        
        clientes.append({
            "nombre": nombre_negocio,
            "cuit": cuit,
            "domicilio": domicilio,
            "telefono": telefono,
            "condicion_iva": condicion,
            "cv": cv,
            "cuig": cuig,
            "renspa": renspa,
            "establecimiento": establecimiento
        })
    
    # =========================================================================
    # TIPO 3: Personas físicas particulares (40 clientes) - SIN DATOS AGROPECUARIOS
    # =========================================================================
    print("  👤 Generando clientes particulares...")
    for i in range(40):
        nombre = f"{choice(nombres_personas)} {choice(apellidos)}"
        
        tipo_cuit = choice(["20", "23", "24", "27"])
        dni = randint(20000000, 45000000)
        digito = randint(0, 9)
        cuit = f"{tipo_cuit}-{dni}-{digito}"
        
        calle = choice(calles)
        numero = randint(100, 2500)
        domicilio = f"{calle} {numero}"
        
        telefono = f"358{randint(4000000, 4999999)}"
        condicion = choice(condiciones_iva)
        
        # Particulares no tienen datos agropecuarios
        clientes.append({
            "nombre": nombre,
            "cuit": cuit,
            "domicilio": domicilio,
            "telefono": telefono,
            "condicion_iva": condicion,
            "cv": "",
            "cuig": "",
            "renspa": "",
            "establecimiento": ""
        })
    
    # =========================================================================
    # INSERTAR EN BASE DE DATOS
    # =========================================================================
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    insertados = 0
    for c in clientes:
        try:
            cursor.execute("""
                INSERT INTO clientes (nombre, cuit, domicilio, telefono, condicion_iva, cv, cuig, renspa, establecimiento)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c['nombre'], 
                c['cuit'], 
                c['domicilio'], 
                c['telefono'], 
                c['condicion_iva'],
                c['cv'],
                c['cuig'],
                c['renspa'],
                c['establecimiento']
            ))
            insertados += 1
        except sqlite3.IntegrityError:
            continue
    
    conn.commit()
    conn.close()


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
    
    seed_company_data()
    seed_suppliers()
    seed_client()
    seed_clients()
    seed_stock()
    # seed_sales_with_fiados()
    # seed_sales_with_products()
    
    print("-" * 50)
    print("✅ ¡Seed completado exitosamente!")