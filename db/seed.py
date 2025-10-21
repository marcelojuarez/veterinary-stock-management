import sqlite3
from datetime import datetime

DB_PATH = "stock.db"  # ruta a tu base de datos

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

if __name__ == "__main__":
    seed_stock()
