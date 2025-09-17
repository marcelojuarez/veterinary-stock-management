import sqlite3
import uuid
import random

DB_PATH = "db/stock.db"

def seed_stock():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    productos = [
        (1002, "Alimento balanceado perro adulto", "Bolsa 20kg", "Royal Canin", 32000, 25000, 21, 15),
        (1003, "Alimento cachorro", "Bolsa 15kg", "Pedigree", 25000, 19000, 21, 12),
        (1004, "Alimento gato adulto", "Bolsa 10kg", "Whiskas", 18000, 13500, 21, 20),
        (1005, "Alimento gato kitten", "Bolsa 7kg", "Royal Canin", 22000, 17000, 21, 10),
        (1006, "Pipeta antipulgas", "Para perro mediano", "Frontline", 3500, 2600, 21, 25),
        (1007, "Collar antipulgas", "Tamaño perro grande", "Bayer", 4200, 3100, 21, 8),
        (1008, "Vacuna antirrábica", "Dosis individual", "Zoetis", 1500, 900, 10.5, 50),
        (1009, "Vacuna séxtuple", "Dosis individual", "Zoetis", 2700, 1800, 10.5, 40),
        (1010, "Jeringa 3ml", "Con aguja", "Descartable", 200, 100, 21, 100),
        (1011, "Jeringa 5ml", "Con aguja", "Descartable", 250, 120, 21, 90),
        (1012, "Shampoo medicado", "Perros y gatos 250ml", "Dermovet", 1800, 1200, 21, 30),
        (1013, "Shampoo antipulgas", "Perros 300ml", "PetClean", 1300, 800, 21, 25),
        (1014, "Corte uñas", "Acero inoxidable", "Tramontina", 2200, 1500, 21, 15),
        (1015, "Cepillo doble", "Mango ergonómico", "PetBrush", 1700, 1100, 21, 18),
        (1016, "Collar nylon", "Tamaño chico", "DogStyle", 900, 500, 21, 22),
        (1017, "Correa retráctil", "5 metros", "DogStyle", 3200, 2200, 21, 12),
        (1018, "Comedero plástico", "Grande", "PetHouse", 1200, 700, 21, 30),
        (1019, "Bebedero automático", "Capacidad 3L", "PetHouse", 4800, 3500, 21, 7),
        (1020,"Caja transporte", "Mediana", "PetTravel", 8500, 6000, 21, 5),
        (1021, "Cama acolchada", "Tamaño grande", "PetDreams", 9500, 7000, 21, 6)
    ]

    for id, name, description, brand, price, cost_price, iva, quantity in productos:
        cursor.execute('''
            INSERT INTO stock (id, name, description, brand, price, cost_price, iva, quantity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            id,
            name,
            description,
            brand,
            price,
            cost_price,
            iva,
            quantity
        ))

    conn.commit()
    conn.close()
    print("✅ 20 productos insertados en la base de datos")

if __name__ == "__main__":
    seed_stock()
