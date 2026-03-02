import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from datetime import datetime, timedelta
from random import choice, randint, uniform
from models.company import CompanyModel
from models.user import User
from models.supplier.__init__ import SupplierModel
from models.sale import SalesModel
from models.payment_model import PaymentModel
from models.stock import StockModel
from models.security import gen_password
from utils.utils import norm_to_2_dec, flex_dec
from decimal import Decimal

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
        #Honorarios
        {"name": "HONORARIOS", "pack": "UNIDAD", "profit": "0.00", "list_price": "0.00", "discount": "0.00", "iva": "0.00"},

        # Alimentos perros
        {"name": "ALIMENTO CANINO CACHORRO", "pack": "BOLSA 3KG", "profit": "30.00", "list_price": "2500.9358", "discount": "0", "iva": "21.00"},
        {"name": "ALIMENTO CANINO CACHORRO", "pack": "BOLSA 15KG", "profit": "28.00", "list_price": "11000.088", "discount": "0", "iva": "10.50"},
        {"name": "ALIMENTO CANINO ADULTO", "pack": "BOLSA 3KG", "profit": "30.00", "list_price": "2200.534", "discount": "0", "iva": "21.00"},
        {"name": "ALIMENTO CANINO ADULTO", "pack": "BOLSA 15KG", "profit": "28.00", "list_price": "9500.750", "discount": "0", "iva": "21.00"},
        {"name": "ALIMENTO CANINO ADULTO", "pack": "BOLSA 20KG", "profit": "25.00", "list_price": "12000.9900", "discount": "0", "iva": "21.00"},
        {"name": "ALIMENTO CANINO SENIOR", "pack": "BOLSA 3KG", "profit": "30.00", "list_price": "2800.400", "discount": "10.00", "iva": "21.00"},
        {"name": "ALIMENTO CANINO SENIOR", "pack": "BOLSA 15KG", "profit": "28.00", "list_price": "12500.800", "discount": "0", "iva": "21.00"},
        {"name": "ALIMENTO PREMIUM PERRO RAZA PEQUEÑA", "pack": "BOLSA 7.5KG", "profit": "35.00", "list_price": "8500.600", "discount": "0", "iva": "21.00"},
        {"name": "ALIMENTO PREMIUM PERRO RAZA MEDIANA", "pack": "BOLSA 15KG", "profit": "35.00", "list_price": "15000.340", "discount": "0", "iva": "21.00"},
        {"name": "ALIMENTO PREMIUM PERRO RAZA GRANDE", "pack": "BOLSA 15KG", "profit": "35.00", "list_price": "14500.200", "discount": "15.00", "iva": "21.00"},
        {"name": "ALIMENTO LIGHT PERRO", "pack": "BOLSA 15KG", "profit": "32.00", "list_price": "13000.7800", "discount": "0", "iva": "21.00"},
        {"name": "ALIMENTO HIPOALERGÉNICO PERRO", "pack": "BOLSA 10KG", "profit": "40.00", "list_price": "18000.990", "discount": "0", "iva": "21.00"},
        
        # # Alimentos gatos
        {"name": "ALIMENTO FELINO CACHORRO", "pack": "BOLSA 1KG", "profit": "30.00", "list_price": "1800.500", "discount": "0", "iva": "21.00"},
        {"name": "ALIMENTO FELINO CACHORRO", "pack": "BOLSA 7.5KG", "profit": "28.00", "list_price": "10000.9956", "discount": "0", "iva": "21.00"},
        {"name": "ALIMENTO FELINO ADULTO", "pack": "BOLSA 1KG", "profit": "30.00", "list_price": "1500.7560", "discount": "0", "iva": "21.00"},
        {"name": "ALIMENTO FELINO ADULTO", "pack": "BOLSA 7.5KG", "profit": "28.00", "list_price": "8500.6090", "discount": "10.00", "iva": "21.00"},
        {"name": "ALIMENTO FELINO ADULTO", "pack": "BOLSA 15KG", "profit": "25.00", "list_price": "15000.3402", "discount": "0", "iva": "21.00"},
        {"name": "ALIMENTO FELINO SENIOR", "pack": "BOLSA 7.5KG", "profit": "30.00", "list_price": "11000.8030", "discount": "0", "iva": "21.00"},
        {"name": "ALIMENTO PREMIUM GATO CASTRADO", "pack": "BOLSA 7.5KG", "profit": "35.00", "list_price": "12500.9900", "discount": "15.00", "iva": "21.00"},
        {"name": "ALIMENTO PREMIUM GATO CONTROL PESO", "pack": "BOLSA 7.5KG", "profit": "35.00", "list_price": "13000.450", "discount": "0", "iva": "21.00"},
        {"name": "ALIMENTO URINARY GATO", "pack": "BOLSA 7.5KG", "profit": "40.00", "list_price": "16000.880", "discount": "0", "iva": "21.00"},
        
        # # Arena sanitaria
        {"name": "ARENA SANITARIA BÁSICA", "pack": "BOLSA 5L", "profit": "25.00", "list_price": "600.567", "discount": "0", "iva": "21.00"},
        {"name": "ARENA SANITARIA BÁSICA", "pack": "BOLSA 10L", "profit": "25.00", "list_price": "1000.750", "discount": "0", "iva": "21.00"},
        {"name": "ARENA AGLOMERANTE", "pack": "BOLSA 5L", "profit": "30.00", "list_price": "1200.600", "discount": "10.00", "iva": "21.00"},
        {"name": "ARENA AGLOMERANTE", "pack": "BOLSA 10L", "profit": "30.00", "list_price": "2000.990", "discount": "0", "iva": "21.00"},
        {"name": "ARENA BIODEGRADABLE", "pack": "BOLSA 10L", "profit": "35.00", "list_price": "2500.340", "discount": "0", "iva": "21.00"},
        {"name": "ARENA SILICA GEL", "pack": "BOLSA 5L", "profit": "40.00", "list_price": "3500.8800", "discount": "15.00", "iva": "21.00"},
        {"name": "PIEDRAS SANITARIAS", "pack": "BOLSA 10KG", "profit": "25.00", "list_price": "800.400", "discount": "0", "iva": "21.00"},

        # # Higiene y cuidado
        {"name": "SHAMPOO PERRO CACHORROS", "pack": "500ML", "profit": "40.00", "list_price": "800.500", "discount": "0", "iva": "21.00"},
        {"name": "SHAMPOO PERRO ADULTO", "pack": "500ML", "profit": "40.00", "list_price": "700.750", "discount": "0", "iva": "21.00"},
        {"name": "SHAMPOO PERRO ANTIPULGAS", "pack": "500ML", "profit": "40.00", "list_price": "1200.990", "discount": "20.00", "iva": "21.00"},
        {"name": "SHAMPOO GATO", "pack": "500ML", "profit": "40.00", "list_price": "900.600", "discount": "0", "iva": "21.00"},
        {"name": "ACONDICIONADOR PERRO", "pack": "500ML", "profit": "40.00", "list_price": "850.340", "discount": "0", "iva": "21.00"},
        {"name": "SHAMPOO SECO PERRO", "pack": "400ML", "profit": "45.00", "list_price": "1100.880", "discount": "0", "iva": "21.00"},
        {"name": "SHAMPOO SECO GATO", "pack": "400ML", "profit": "45.00", "list_price": "1200.450", "discount": "10.00", "iva": "21.00"},
        {"name": "PERFUME MASCOTAS", "pack": "250ML", "profit": "50.00", "list_price": "600.990", "discount": "0", "iva": "21.00"},
        {"name": "CEPILLO DENTAL PERRO", "pack": "UNIDAD", "profit": "45.00", "list_price": "400.500", "discount": "0", "iva": "21.00"},
        {"name": "PASTA DENTAL PERRO", "pack": "100G", "profit": "45.00", "list_price": "800.750", "discount": "0", "iva": "21.00"},
        {"name": "CORTAUÑAS PERRO", "pack": "UNIDAD", "profit": "40.00", "list_price": "600.600", "discount": "0", "iva": "21.00"},
        {"name": "CORTAUÑAS GATO", "pack": "UNIDAD", "profit": "40.00", "list_price": "550.880", "discount": "0", "iva": "21.00"},
        
        # # Antiparasitarios
        {"name": "ANTIPULGAS PERRO 0-10KG", "pack": "PIPETA X3", "profit": "30.00", "list_price": "1500.750", "discount": "0", "iva": "21.00"},
        {"name": "ANTIPULGAS PERRO 10-20KG", "pack": "PIPETA X3", "profit": "30.00", "list_price": "1800.990", "discount": "0", "iva": "21.00"},
        {"name": "ANTIPULGAS PERRO 20-40KG", "pack": "PIPETA X3", "profit": "30.00", "list_price": "2200.625", "discount": "10.00", "iva": "21.00"},
        {"name": "ANTIPULGAS PERRO +40KG", "pack": "PIPETA X3", "profit": "30.00", "list_price": "2500.880", "discount": "0", "iva": "21.00"},
        {"name": "ANTIPULGAS GATO", "pack": "PIPETA X3", "profit": "30.00", "list_price": "1600.450", "discount": "0", "iva": "21.00"},
        {"name": "COLLAR ANTIPULGAS PERRO", "pack": "UNIDAD", "profit": "35.00", "list_price": "2000.340", "discount": "15.00", "iva": "21.00"},
        {"name": "COLLAR ANTIPULGAS GATO", "pack": "UNIDAD", "profit": "35.00", "list_price": "1800.500", "discount": "0", "iva": "21.00"},
        {"name": "DESPARASITARIO INTERNO PERRO", "pack": "COMP X4", "profit": "35.00", "list_price": "1200.750", "discount": "0", "iva": "21.00"},
        {"name": "DESPARASITARIO INTERNO GATO", "pack": "COMP X4", "profit": "35.00", "list_price": "1100.990", "discount": "0", "iva": "21.00"},

        # # Accesorios perros
        {"name": "COLLAR PERRO PEQUEÑO", "pack": "UNIDAD", "profit": "40.00", "list_price": "500.600", "discount": "0", "iva": "21.00"},
        {"name": "COLLAR PERRO MEDIANO", "pack": "UNIDAD", "profit": "40.00", "list_price": "700.450", "discount": "0", "iva": "21.00"},
        {"name": "COLLAR PERRO GRANDE", "pack": "UNIDAD", "profit": "40.00", "list_price": "900.880", "discount": "0", "iva": "21.00"},
        {"name": "CORREA PERRO 1.5M", "pack": "UNIDAD", "profit": "40.00", "list_price": "600.990", "discount": "0", "iva": "21.00"},
        {"name": "CORREA PERRO 3M RETRÁCTIL", "pack": "UNIDAD", "profit": "45.00", "list_price": "2500.7500", "discount": "20.00", "iva": "21.00"},
        {"name": "CORREA PERRO 5M RETRÁCTIL", "pack": "UNIDAD", "profit": "45.00", "list_price": "3200.600", "discount": "0", "iva": "21.00"},
        {"name": "ARNÉS PERRO PEQUEÑO", "pack": "UNIDAD", "profit": "40.00", "list_price": "1200.340", "discount": "0", "iva": "21.00"},
        {"name": "ARNÉS PERRO MEDIANO", "pack": "UNIDAD", "profit": "40.00", "list_price": "1500.880", "discount": "0", "iva": "21.00"},
        {"name": "ARNÉS PERRO GRANDE", "pack": "UNIDAD", "profit": "40.00", "list_price": "1800.500", "discount": "10.00", "iva": "21.00"},
        {"name": "BOZAL PERRO MEDIANO", "pack": "UNIDAD", "profit": "35.00", "list_price": "800.750", "discount": "0", "iva": "21.00"},
        {"name": "BOZAL PERRO GRANDE", "pack": "UNIDAD", "profit": "35.00", "list_price": "1000.990", "discount": "0", "iva": "21.00"},
        {"name": "PRETAL AUTO PERRO", "pack": "UNIDAD", "profit": "40.00", "list_price": "1500.600", "discount": "0", "iva": "21.00"},
        
        # # Accesorios gatos
        {"name": "COLLAR GATO CON CASCABEL", "pack": "UNIDAD", "profit": "45.00", "list_price": "400.750", "discount": "0", "iva": "21.00"},
        {"name": "ARNÉS GATO", "pack": "UNIDAD", "profit": "40.00", "list_price": "900.600", "discount": "0", "iva": "21.00"},
        {"name": "CORREA GATO", "pack": "UNIDAD", "profit": "40.00", "list_price": "500.990", "discount": "10.00", "iva": "21.00"},

        # # Comederos y bebederos
        {"name": "COMEDERO PLÁSTICO PEQUEÑO", "pack": "UNIDAD", "profit": "40.00", "list_price": "300.500", "discount": "0", "iva": "21.00"},
        {"name": "COMEDERO PLÁSTICO MEDIANO", "pack": "UNIDAD", "profit": "40.00", "list_price": "450.880", "discount": "0", "iva": "21.00"},
        {"name": "COMEDERO PLÁSTICO GRANDE", "pack": "UNIDAD", "profit": "40.00", "list_price": "600.750", "discount": "0", "iva": "21.00"},
        {"name": "COMEDERO ACERO INOX PEQUEÑO", "pack": "UNIDAD", "profit": "35.00", "list_price": "800.340", "discount": "0", "iva": "21.00"},
        {"name": "COMEDERO ACERO INOX MEDIANO", "pack": "UNIDAD", "profit": "35.00", "list_price": "1200.990", "discount": "15.00", "iva": "21.00"},
        {"name": "COMEDERO ACERO INOX GRANDE", "pack": "UNIDAD", "profit": "35.00", "list_price": "1500.600", "discount": "0", "iva": "21.00"},
        {"name": "BEBEDERO AUTOMÁTICO 1.5L", "pack": "UNIDAD", "profit": "35.00", "list_price": "1000.750", "discount": "0", "iva": "21.00"},
        {"name": "BEBEDERO AUTOMÁTICO 3L", "pack": "UNIDAD", "profit": "35.00", "list_price": "1500.880", "discount": "0", "iva": "21.00"},
        {"name": "BEBEDERO FUENTE GATO", "pack": "UNIDAD", "profit": "40.00", "list_price": "3500.990", "discount": "20.00", "iva": "21.00"},
        {"name": "COMEDERO DOBLE PERRO", "pack": "UNIDAD", "profit": "40.00", "list_price": "1200.450", "discount": "0", "iva": "21.00"},
        {"name": "COMEDERO ELEVADO PERRO", "pack": "UNIDAD", "profit": "40.00", "list_price": "2500.7800", "discount": "0", "iva": "21.00"},
        
        # # Camas y cuchas
        {"name": "CAMA PERRO PEQUEÑO", "pack": "UNIDAD", "profit": "35.00", "list_price": "2500.750", "discount": "0", "iva": "21.00"},
        {"name": "CAMA PERRO MEDIANO", "pack": "UNIDAD", "profit": "35.00", "list_price": "3500.990", "discount": "10", "iva": "21.00"},
        {"name": "CAMA PERRO GRANDE", "pack": "UNIDAD", "profit": "35.00", "list_price": "5000.600", "discount": "0", "iva": "21.00"},
        {"name": "CAMA GATO", "pack": "UNIDAD", "profit": "35.00", "list_price": "2000.880", "discount": "0", "iva": "21.00"},
        {"name": "CUCHA PLÁSTICO PERRO MEDIANO", "pack": "UNIDAD", "profit": "30.00", "list_price": "4500.340", "discount": "0", "iva": "21.00"},
        {"name": "CUCHA PLÁSTICO PERRO GRANDE", "pack": "UNIDAD", "profit": "30.00", "list_price": "6500.990", "discount": "15.00", "iva": "21.00"},
        {"name": "ALMOHADÓN PERRO", "pack": "UNIDAD", "profit": "40.00", "list_price": "1800.500", "discount": "0", "iva": "21.00"},
        {"name": "MANTA POLAR MASCOTAS", "pack": "UNIDAD", "profit": "40.00", "list_price": "1200.750", "discount": "0", "iva": "21.00"},

        # # Juguetes perros
        {"name": "PELOTA GOMA PERRO 6CM", "pack": "UNIDAD", "profit": "50.00", "list_price": "300.600", "discount": "0", "iva": "21.00"},
        {"name": "PELOTA TENIS PERRO", "pack": "UNIDAD", "profit": "50.00", "list_price": "250.990", "discount": "0", "iva": "21.00"},
        {"name": "HUESO GOMA PERRO", "pack": "UNIDAD", "profit": "50.00", "list_price": "400.750", "discount": "20.00", "iva": "21.00"},
        {"name": "CUERDA PERRO 30CM", "pack": "UNIDAD", "profit": "50.00", "list_price": "350.880", "discount": "0", "iva": "21.00"},
        {"name": "FRISBEE PERRO", "pack": "UNIDAD", "profit": "50.00", "list_price": "500.450", "discount": "0", "iva": "21.00"},
        {"name": "PELUCHE PERRO PEQUEÑO", "pack": "UNIDAD", "profit": "45.00", "list_price": "600.990", "discount": "0", "iva": "21.00"},
        {"name": "PELUCHE PERRO MEDIANO", "pack": "UNIDAD", "profit": "45.00", "list_price": "900.600", "discount": "10.00", "iva": "21.00"},
        {"name": "KONG PERRO PEQUEÑO", "pack": "UNIDAD", "profit": "40.00", "list_price": "1500.7500", "discount": "0", "iva": "21.00"},
        {"name": "KONG PERRO MEDIANO", "pack": "UNIDAD", "profit": "40.00", "list_price": "2000.340", "discount": "0", "iva": "21.00"},
        {"name": "KONG PERRO GRANDE", "pack": "UNIDAD", "profit": "40.00", "list_price": "2500.880", "discount": "15.00", "iva": "21.00"},
        
        # # Juguetes gatos
        {"name": "RATÓN JUGUETE GATO", "pack": "UNIDAD", "profit": "50.00", "list_price": "200.750", "discount": "0", "iva": "21.00"},
        {"name": "VARITA PLUMAS GATO", "pack": "UNIDAD", "profit": "50.00", "list_price": "350.990", "discount": "0", "iva": "21.00"},
        {"name": "PELOTA CASCABEL GATO", "pack": "UNIDAD", "profit": "50.00", "list_price": "180.600", "discount": "10.00", "iva": "21.00"},
        {"name": "RASCADOR VERTICAL GATO", "pack": "UNIDAD", "profit": "35.00", "list_price": "3500.880", "discount": "0", "iva": "21.00"},
        {"name": "RASCADOR HORIZONTAL GATO", "pack": "UNIDAD", "profit": "35.00", "list_price": "1500.340", "discount": "0", "iva": "21.00"},
        {"name": "TÚNEL JUEGO GATO", "pack": "UNIDAD", "profit": "40.00", "list_price": "2000.990", "discount": "15.00", "iva": "21.00"},
        {"name": "LASER GATO", "pack": "UNIDAD", "profit": "45.00", "list_price": "600.500", "discount": "0", "iva": "21.00"},

        # # Transportadoras
        {"name": "TRANSPORTADORA GATO PEQUEÑA", "pack": "UNIDAD", "profit": "30.00", "list_price": "3000.750", "discount": "0", "iva": "21.00"},
        {"name": "TRANSPORTADORA GATO MEDIANA", "pack": "UNIDAD", "profit": "30.00", "list_price": "4000.600", "discount": "0", "iva": "21.00"},
        {"name": "TRANSPORTADORA PERRO PEQUEÑO", "pack": "UNIDAD", "profit": "30.00", "list_price": "3500.880", "discount": "10.00", "iva": "21.00"},
        {"name": "TRANSPORTADORA PERRO MEDIANO", "pack": "UNIDAD", "profit": "30.00", "list_price": "5500.990", "discount": "0", "iva": "21.00"},
        {"name": "MOCHILA TRANSPORTE GATO", "pack": "UNIDAD", "profit": "35.00", "list_price": "4500.340", "discount": "0", "iva": "21.00"},

        # # Sanitarios gatos
        {"name": "BANDEJA SANITARIA SIMPLE", "pack": "UNIDAD", "profit": "35.00", "list_price": "1200.750", "discount": "0", "iva": "21.00"},
        {"name": "BANDEJA SANITARIA CON TAPA", "pack": "UNIDAD", "profit": "35.00", "list_price": "2500.880", "discount": "0", "iva": "21.00"},
        {"name": "BANDEJA SANITARIA AUTOLIMPIANTE", "pack": "UNIDAD", "profit": "30.00", "list_price": "15000.990", "discount": "20.00", "iva": "21.00"},
        {"name": "PALA SANITARIA", "pack": "UNIDAD", "profit": "45.00", "list_price": "300.600", "discount": "0", "iva": "21.00"},
        {"name": "ALFOMBRA SANITARIA", "pack": "UNIDAD", "profit": "40.00", "list_price": "800.450", "discount": "0", "iva": "21.00"},
        
        # # Snacks y premios
        {"name": "SNACK PERRO DENTAL", "pack": "CAJA 200G", "profit": "40.00", "list_price": "800.750", "discount": "0", "iva": "21.00"},
        {"name": "SNACK PERRO HUESOS", "pack": "BOLSA 500G", "profit": "40.00", "list_price": "1200.990", "discount": "10.00", "iva": "21.00"},
        {"name": "SNACK PERRO TIRAS POLLO", "pack": "BOLSA 250G", "profit": "40.00", "list_price": "900.600", "discount": "0", "iva": "21.00"},
        {"name": "SNACK GATO CREMOSO", "pack": "CAJA X12", "profit": "40.00", "list_price": "1500.880", "discount": "0", "iva": "21.00"},
        {"name": "SNACK GATO CRUJIENTE", "pack": "BOLSA 300G", "profit": "40.00", "list_price": "1000.340", "discount": "0", "iva": "21.00"},
        {"name": "HUESO CARNAZA PERRO", "pack": "UNIDAD", "profit": "45.00", "list_price": "600.990", "discount": "15.00", "iva": "21.00"},
        {"name": "OREJA CERDO PERRO", "pack": "UNIDAD", "profit": "45.00", "list_price": "400.500", "discount": "0", "iva": "21.00"},

        # # Vitaminas y suplementos
        {"name": "VITAMINAS PERRO CACHORROS", "pack": "CAJA X30", "profit": "35.00", "list_price": "1500.750", "discount": "0", "iva": "21.00"},
        {"name": "VITAMINAS PERRO ADULTOS", "pack": "CAJA X30", "profit": "35.00", "list_price": "1300.880", "discount": "0", "iva": "21.00"},
        {"name": "VITAMINAS GATO", "pack": "CAJA X30", "profit": "35.00", "list_price": "1400.990", "discount": "10.00", "iva": "21.00"},
        {"name": "SUPLEMENTO ARTICULACIONES", "pack": "FRASCO X60", "profit": "35.00", "list_price": "2500.340", "discount": "0", "iva": "21.00"},
        {"name": "OMEGA 3 MASCOTAS", "pack": "FRASCO X60", "profit": "35.00", "list_price": "2000.880", "discount": "0", "iva": "21.00"},
        {"name": "PROBIÓTICOS MASCOTAS", "pack": "FRASCO X30", "profit": "40.00", "list_price": "2200.7500", "discount": "20.00", "iva": "21.00"},
        
        # # Identificación
        {"name": "PLACA IDENTIFICACIÓN PERRO", "pack": "UNIDAD", "profit": "50.00", "list_price": "350.750", "discount": "0", "iva": "21.00"},
        {"name": "PLACA IDENTIFICACIÓN GATO", "pack": "UNIDAD", "profit": "50.00", "list_price": "300.990", "discount": "10.00", "iva": "21.00"},
        {"name": "CHIP IDENTIFICACIÓN", "pack": "UNIDAD", "profit": "30.00", "list_price": "1200.600", "discount": "0", "iva": "21.00"},

        # Limpieza y hogar
        {"name": "PAÑOS HÚMEDOS MASCOTAS", "pack": "PAQUETE X50", "profit": "45.00", "list_price": "600.880", "discount": "0", "iva": "21.00"},
        {"name": "REPELENTE MASCOTAS", "pack": "SPRAY 250ML", "profit": "40.00", "list_price": "800.340", "discount": "0", "iva": "21.00"},
        {"name": "NEUTRALIZADOR OLORES", "pack": "SPRAY 500ML", "profit": "40.00", "list_price": "1000.990", "discount": "15.00", "iva": "21.00"},
        {"name": "LIMPIADOR PATAS", "pack": "FRASCO 250ML", "profit": "45.00", "list_price": "700.500", "discount": "0", "iva": "21.00"},
        {"name": "BOLSAS RESIDUOS PERRO", "pack": "ROLLO X100", "profit": "50.00", "list_price": "400.750", "discount": "0", "iva": "21.00"},
        {"name": "PAÑALES PERRO M", "pack": "PAQUETE X12", "profit": "40.00", "list_price": "1200.880", "discount": "0", "iva": "21.00"},
        {"name": "PAÑALES PERRO L", "pack": "PAQUETE X12", "profit": "40.00", "list_price": "1500.340", "discount": "20.00", "iva": "21.00"},
        {"name": "EMPAPADORES MASCOTAS", "pack": "PAQUETE X30", "profit": "40.00", "list_price": "2000.7500", "discount": "0", "iva": "21.00"},
    ]
    
    # Obtener proveedores para asignar aleatoriamente
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Insertar productos asignando proveedores al azar
    for p in productos_base:
        if p['name'] == "HONORARIOS":
            quantity = int(1)
        else:
            quantity = randint(5, 50)
            
        list_price = Decimal(p['list_price'])
        discount = Decimal(p['discount'])
        iva = Decimal(p['iva'])
        profit = Decimal(p['profit'])

        # Precio costo
        discount_rate = discount / Decimal('100')
        unit_d_amount = list_price * discount_rate
        cost_price = list_price - unit_d_amount

        # Precio venta
        profit_rate = profit / Decimal('100')
        profit_amount = cost_price * profit_rate
        sale_price = cost_price + profit_amount
        
        # Precio de venta con IVA
        iva_rate = iva / Decimal('100')
        iva_amount = sale_price * iva_rate
        price_with_iva = sale_price + iva_amount        
        
        cost_price = flex_dec(cost_price)
        sale_price = flex_dec(sale_price)
        price_with_iva = flex_dec(price_with_iva)

        cursor.execute("""
            INSERT OR REPLACE INTO stock
            (name, pack, profit, list_price, discount, cost_price, price, iva, price_with_iva, quantity, created_at, last_price_update)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p['name'], p['pack'], str(p['profit']), str(list_price), str(discount), str(cost_price), 
            str(sale_price), str(iva), str(price_with_iva), quantity, 
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

# Códigos oficiales de provincias argentinas (ISO 3166-2 AR)
CODIGOS_PROVINCIA_LETRAS = {
    "Buenos Aires": "BA",
    "Catamarca": "CA",
    "Chaco": "CH",
    "Chubut": "CT",
    "Córdoba": "CB",
    "Corrientes": "CR",
    "Entre Ríos": "ER",
    "Formosa": "FO",
    "Jujuy": "JY",
    "La Pampa": "LP",
    "La Rioja": "LR",
    "Mendoza": "MZ",
    "Misiones": "MI",
    "Neuquén": "NQ",
    "Río Negro": "RN",
    "Salta": "SA",
    "San Juan": "SJ",
    "San Luis": "SL",
    "Santa Cruz": "SC",
    "Santa Fe": "SF",
    "Santiago del Estero": "SE",
    "Tierra del Fuego": "TF",
    "Tucumán": "TU",
    "Ciudad Autónoma de Buenos Aires": "CABA"
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


def generar_cuig(provincia="Córdoba", min_digitos=3, max_digitos=7):
    """
    Genera un CUIG compatible con formato: 2 letras de provincia + 2 a 8 números
    """

    letras = CODIGOS_PROVINCIA_LETRAS.get(provincia, "CB")

    longitud = randint(min_digitos, max_digitos)
    numero = f"{randint(0, 10**longitud - 1):0{longitud}d}"

    return f"{letras}{numero}"

def generar_renspa(provincia="Córdoba"):
    """
    Genera un RENSPA compatible con formato numérico:
    12 a 15 dígitos (sin puntos ni barra)

    """

    cod_provincia = CODIGOS_PROVINCIA.get(provincia, "14")

    if provincia == "Córdoba":
        cod_departamento = choice(list(DEPARTAMENTOS_CORDOBA.values()))
    else:
        cod_departamento = f"{randint(1, 200):03d}"

    tipo_actividad = randint(0, 5)
    numero = f"{randint(1, 99999):05d}"
    anio = f"{randint(10, 25):02d}"

    # Concatenado sin separadores
    renspa = f"{cod_provincia}{cod_departamento}{tipo_actividad}{numero}{anio}"

    return renspa

def generar_cv(min_digitos=3, max_digitos=8):
    """
    Genera una CV numérica entre 3 y 8 dígitos.
    Compatible con regex: ^[0-9]{3,8}$
    """

    longitud = randint(min_digitos, max_digitos)
    return f"{randint(10**(longitud-1), 10**longitud - 1)}"

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
            "name": "Consumidor Final", 
            "cuit": "", 
            "home": "", 
            "phone": "", 
            "iva_condition": "Consumidor Final",
            "cv": "",
            "cuig": "",
            "renspa": "",
            "establishment": ""
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
            "name": nombre,
            "cuit": cuit,
            "home": domicilio,
            "phone": telefono,
            "iva_condition": condicion,
            "cv": cv,
            "cuig": cuig,
            "renspa": renspa,
            "establishment": establecimiento
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
            "name": nombre_negocio,
            "cuit": cuit,
            "home": domicilio,
            "phone": telefono,
            "iva_condition": condicion,
            "cv": cv,
            "cuig": cuig,
            "renspa": renspa,
            "establishment": establecimiento
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
            "name": nombre,
            "cuit": cuit,
            "home": domicilio,
            "phone": telefono,
            "iva_condition": condicion,
            "cv": "",
            "cuig": "",
            "renspa": "",
            "establishment": ""
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
                INSERT INTO customer (name, cuit, home, phone, iva_condition, cv, cuig, renspa, establishment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c['name'], 
                c['cuit'], 
                c['home'], 
                c['phone'], 
                c['iva_condition'],
                c['cv'],
                c['cuig'],
                c['renspa'],
                c['establishment']
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
    clientes = cur.execute("SELECT id FROM customer WHERE id > 1").fetchall()  # Excluir Consumidor Final
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
            VALUES (?, ?, ?, ?)
        """, (fecha_str, "0", venta["cliente_id"], venta["estado"]))
        sale_id = cur.lastrowid

        # Agregar productos aleatorios
        total_venta = Decimal('0.00')
        num_productos = randint(2, 5)
        
        for _ in range(num_productos):
            prod_id, price = choice(productos)
            cantidad = randint(1, 4)
            price_decimal = norm_to_2_dec(price)
            subtotal = norm_to_2_dec(price_decimal * cantidad)
            total_venta += subtotal
            
            cur.execute("""
                INSERT INTO sale_items (sale_id, product_id, quantity, price, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (sale_id, prod_id, cantidad, str(price_decimal), str(subtotal)))

        # Actualizar total de la venta
        total_venta = norm_to_2_dec(total_venta)
        cur.execute("UPDATE sales SET total = ? WHERE id = ?", (str(total_venta), sale_id))

        # 🔹 CREAR PAGOS según el estado
        if venta["estado"] == "paid":
            # Venta pagada: pago completo
            cur.execute("""
                INSERT INTO payments (sale_id, client_id, amount, date, method, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sale_id, venta["cliente_id"], str(total_venta), fecha_str, 
                choice(["Efectivo", "Transferencia", "Tarjeta"]), "Pago completo"))
        
        elif venta["estado"] == "partial":
            # Venta parcial: pago entre 30% y 70% del total
            monto_pagado = norm_to_2_dec(float(total_venta) * uniform(0.3, 0.7))
            fecha_pago = fecha_venta + timedelta(days=randint(1, 3))

            cur.execute("""
                INSERT INTO payments (sale_id, client_id, amount, date, method, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sale_id, venta["cliente_id"], str(monto_pagado), 
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

    paises = ["Argentina"]

    provincias = [
        "Buenos Aires", "Catamarca", "Chaco", "Chubut",
        "Córdoba", "Corrientes", "Entre Ríos", "Formosa", "Jujuy",
        "La Pampa", "La Rioja", "Mendoza", "Misiones", "Neuquén",
        "Río Negro", "Salta", "San Juan", "San Luis", "Santa Cruz",
        "Santa Fe", "Santiago del Estero", "Tierra del Fuego", "Tucumán"
    ]

    ciudades = [
        "Buenos Aires",
        "Córdoba",
        "Rosario",
        "Mendoza",
        "La Plata",
        "San Miguel de Tucumán",
        "Salta",
        "Santa Fe",
        "Mar del Plata",
        "San Juan",
        "Resistencia",
        "Neuquén",
        "Formosa",
        "Corrientes",
        "Posadas",
        "Santiago del Estero",
        "San Salvador de Jujuy",
        "San Luis",
        "La Rioja",
        "Río Gallegos",
        "Ushuaia",
        "Paraná",
        "Viedma",
        "Rawson",
        "Trelew",
        "Villa Carlos Paz",
        "Rafaela",
        "Comodoro Rivadavia",
        "Bahía Blanca",
        "Río Cuarto"
    ]

    condicion_iva = ["RESP. INS", "MONOTRIBUTISTA", "EXENTO", "NO RESPONSABLE"]
    
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

        province = choice(provincias)

        country = choice(paises)

        city = choice(ciudades)
        
        # Teléfono
        phone = f"358{randint(4000000, 4999999)}"
        
        # Email
        nombre_email = nombre.lower().replace(" ", "").replace("&", "")[:15]
        email = f"{nombre_email}@example.com"

        iva_condition = choice(condicion_iva)            
        
        suppliers.append({
            "cuit": cuit,
            "name": nombre,
            "address": home,
            "city": city,
            "province": province,
            "country": country,
            "phone": phone,
            "email": email,
            "iva_condition": iva_condition,
        })
    
    sales_model = SalesModel()
    payment_model = PaymentModel(sales_model)
    stock_model = StockModel(sales_model, payment_model)
    supplier_mdl = SupplierModel(stock_model)
    
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
    #seed_sales_with_products()
    
    print("-" * 50)
    print("✅ ¡Seed completado exitosamente!")