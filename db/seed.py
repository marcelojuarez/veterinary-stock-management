import sqlite3
from datetime import datetime

DB_PATH = "stock.db"  # ruta a tu base de datos

def seed_stock():
    productos = [
        {"id":"1001","name":"Alimento Canino Adulto","pack":"Bolsas 15kg","profit":30,"cost_price":5000,"iva":21,"quantity":10},
        {"id":"1002","name":"Alimento Felino Adulto","pack":"Bolsas 10kg","profit":25,"cost_price":3500,"iva":21,"quantity":8},
        {"id":"1003","name":"Arena Sanitaria","pack":"Caja 10L","profit":20,"cost_price":800,"iva":21,"quantity":15},
        {"id":"1004","name":"Shampoo Canino","pack":"Botella 500ml","profit":40,"cost_price":500,"iva":21,"quantity":12},
        {"id":"1005","name":"Juguete Pelota","pack":"Unidad","profit":50,"cost_price":150,"iva":21,"quantity":20},
        {"id":"1006","name":"Collar Perro Mediano","pack":"Unidad","profit":35,"cost_price":400,"iva":21,"quantity":18},
        {"id":"1007","name":"Cama Felina","pack":"Unidad","profit":30,"cost_price":1200,"iva":21,"quantity":5},
        {"id":"1008","name":"Vitaminas Caninas","pack":"Caja 30 pastillas","profit":25,"cost_price":600,"iva":21,"quantity":10},
        {"id":"1009","name":"Antipulgas Perro","pack":"Caja 3 unidades","profit":20,"cost_price":900,"iva":21,"quantity":7},
        {"id":"1010","name":"Antipulgas Gato","pack":"Caja 3 unidades","profit":20,"cost_price":800,"iva":21,"quantity":6},
        {"id":"1011","name":"Correa Perro","pack":"Unidad","profit":40,"cost_price":350,"iva":21,"quantity":14},
        {"id":"1012","name":"Comedero Acero Inox","pack":"Unidad","profit":25,"cost_price":700,"iva":21,"quantity":9},
        {"id":"1013","name":"Placa Identificación","pack":"Unidad","profit":50,"cost_price":200,"iva":21,"quantity":25},
        {"id":"1014","name":"Cama Canina Pequeña","pack":"Unidad","profit":30,"cost_price":1000,"iva":21,"quantity":5},
        {"id":"1015","name":"Arena Biodegradable","pack":"Caja 10L","profit":25,"cost_price":850,"iva":21,"quantity":10},
        {"id":"1016","name":"Snack Gato","pack":"Bolsa 500g","profit":35,"cost_price":450,"iva":21,"quantity":20},
        {"id":"1017","name":"Snack Perro","pack":"Bolsa 500g","profit":35,"cost_price":500,"iva":21,"quantity":15},
        {"id":"1018","name":"Cepillo Canino","pack":"Unidad","profit":40,"cost_price":300,"iva":21,"quantity":12},
        {"id":"1019","name":"Cinturón de Seguridad Perro","pack":"Unidad","profit":30,"cost_price":600,"iva":21,"quantity":8},
        {"id":"1020","name":"Transportadora Gato","pack":"Unidad","profit":25,"cost_price":1500,"iva":21,"quantity":4},
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
