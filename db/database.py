import sqlite3
import os
import sys

class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            base_dir = self.get_writable_data_dir()
            db_path = os.path.join(base_dir, 'stock.db')

        self.db_path = db_path
        self.ensure_db_exists()
        self.create_tables()

    def get_writable_data_dir(self):
        """Obtener una ruta donde se pueda escribir, según plataforma"""
        if getattr(sys, 'frozen', False):  # Si está empaquetado con PyInstaller
            base_dir = os.path.join(os.environ['LOCALAPPDATA'], 'StockManager', 'db')
        else:
            # En desarrollo: usar carpeta local db/
            base_dir = os.path.join(os.path.dirname(__file__))
        os.makedirs(base_dir, exist_ok=True)
        return base_dir
    
    def ensure_db_exists(self):
        """Asegurar que el directorio de la base de datos existe"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_connection(self):
        """Obtener conexión a la base de datos"""
        return sqlite3.connect(self.db_path)
    
    def create_tables(self):
        """Crear todas las tablas necesarias"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Tabla de usuarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuario (
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                )
            ''')

            # Tabla de stock
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    brand REAL NOT NULL,
                    price REAL NOT NULL,
                    quantity INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_DATE
                )
            ''')

            # Tabla de clientes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cliente (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    cuit TEXT,
                    domicilio TEXT,
                    condicion_iva TEXT DEFAULT 'Consumidor Final'
                )
            ''')

            # Tabla de proveedores
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS proveedor (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    cuit TEXT,
                    domicilio TEXT,
                    telefono TEXT,
                    email TEXT
                )
            ''')

            # Tabla de facturas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS factura (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_factura TEXT NOT NULL,
                    fecha_emision TEXT NOT NULL,
                    cae TEXT,
                    fecha_vencimiento_cae TEXT,
                    cliente_id INTEGER NOT NULL,
                    subtotal REAL NOT NULL,
                    iva REAL NOT NULL,
                    total REAL NOT NULL,
                    estado TEXT DEFAULT 'autorizada',
                    FOREIGN KEY(cliente_id) REFERENCES clientes(id)
                )
            ''')

            # Tabla de items de factura
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS factura_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    factura_id INTEGER NOT NULL,
                    producto_id TEXT NOT NULL,
                    cantidad INTEGER NOT NULL,
                    precio_unitario REAL NOT NULL,
                    subtotal REAL NOT NULL,
                    FOREIGN KEY(factura_id) REFERENCES facturas(id),
                    FOREIGN KEY(producto_id) REFERENCES stock(id)
                )
            ''')

            conn.commit()

    
    def execute_query(self, query, params=None):
        """Ejecutar una consulta que no devuelve resultados"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.lastrowid
    
    def fetch_all(self, query, params=None):
        """Ejecutar una consulta que devuelve múltiples resultados"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def fetch_one(self, query, params=None):
        """Ejecutar una consulta que devuelve un resultado"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()


db = Database('db/stock.db')