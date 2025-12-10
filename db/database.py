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
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;") 
        return conn
    
    def create_tables(self):
        """Crear todas las tablas necesarias"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Tabla de usuarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                )
            ''')

            # Tabla de stock
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock (
                id TEXT PRIMARY KEY,
                cuit_supplier TEXT,
                name TEXT NOT NULL,
                pack TEXT NOT NULL,
                profit REAL NOT NULL,
                cost_price REAL NOT NULL,
                price REAL NOT NULL,
                iva REAL NOT NULL,
                price_with_iva REAL NOT NULL,
                quantity INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_DATE,
                last_price_update TEXT DEFAULT CURRENT_DATE
                );
            ''')

            # Tabla de clientes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    cuit TEXT UNIQUE,
                    domicilio TEXT,
                    telefono TEXT,
                    condicion_iva TEXT DEFAULT 'Consumidor Final'
                )
            ''')

            # Tabla de proveedores
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS supplier (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cuit TEXT UNIQUE,
                    name TEXT NOT NULL,
                    home TEXT,
                    phone TEXT,
                    email TEXT,
                    debt REAL,
                    last_debt_update TEXT DEFAULT CURRENT_DATE
                );
            ''')

            # Tabla pagos proveedor 
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS supplier_movement (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_supplier INTEGER,
                    
                    receipt_number TEXT, -- recibo que te entrega el proveedor                           

                    amount REAL NOT NULL,     
                    method TEXT,        -- EFECTIVO, TRANSFERENCIA, CHEQUE, MERCADO PAGO                                                        
                    observation TEXT,

                    -- TRANSFERENCIA
                    operation_num INTEGER,  
                    origin TEXT,
                    destination TEXT,
                           
                    -- CHEQUE
                    check_number TEXT, 
                           
                    -- TRANSFERENCIA o CHEQUE
                    bank TEXT,  
                           
                    previous_debt REAL,
                    subsequent_debt REAL,
                    date TEXT DEFAULT CURRENT_DATE,
                    FOREIGN KEY (id_supplier) REFERENCES supplier (id)
                );
            ''')

            # Tabla facturas de compra proveedor
            cursor.execute(''' 
                CREATE TABLE IF NOT EXISTS factura_proveedor(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_proveedor INTEGER,
                    tipo_factura TEXT,
                    punto_de_venta INTEGER, 
                    factura_id INTEGER,
                    fecha TEXT CURRENT_DATE
                    total REAL,
                    subtotal REAL,
                    iva REAL
                    tipo_de_pago TEXT,
                    estado TEXT DEFAULT 'pendiente',
                    FOREIGN KEY (id_proveedor) REFERENCES proveedores (id)
                );
            ''')

            # Tabla de facturas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS invoice (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    number TEXT,
                    date TEXT DEFAULT CURRENT_TIMESTAMP,
                    customer_id INTEGER,
                    subtotal REAL,
                    iva REAL,
                    total REAL,
                    estado TEXT DEFAULT 'borrador',  -- o 'emitida'
                    FOREIGN KEY(customer_id) REFERENCES clientes(id)
                );
            ''')

            # Tabla de items de factura
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS invoice_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER,
                    product_id TEXT,
                    quantity INTEGER,
                    price REAL,
                    subtotal REAL,
                    FOREIGN KEY(invoice_id) REFERENCES invoice(id),
                    FOREIGN KEY(product_id) REFERENCES stock(id)
                );
            ''')

            # Tabla de ventas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT DEFAULT CURRENT_TIMESTAMP,
                    total REAL NOT NULL,
                    cliente_id INTEGER,
                    estado TEXT DEFAULT 'pagada',
                    FOREIGN KEY(cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
                );
            ''')

            # Detalle de cada producto vendido
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    product_id TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    subtotal REAL NOT NULL,
                    FOREIGN KEY(sale_id) REFERENCES sales(id) ON DELETE CASCADE,
                    FOREIGN KEY(product_id) REFERENCES stock(id)
                );
            ''')

            # Remito
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS delivery_note (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT NOT NULL,
                date TEXT DEFAULT CURRENT_TIMESTAMP,
                sale_id INTEGER NOT NULL,
                customer_id INTEGER NOT NULL,
                status TEXT DEFAULT 'issued',
                notes TEXT,
                FOREIGN KEY(customer_id) REFERENCES clientes(id)
            );

            ''')

            # Remito items
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS delivery_note_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    delivery_note_id INTEGER NOT NULL,
                    product_id TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    FOREIGN KEY(delivery_note_id) REFERENCES delivery_note(id) ON DELETE CASCADE,
                    FOREIGN KEY(product_id) REFERENCES stock(id)
                );
            ''')

            conn.commit()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    client_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    date TEXT DEFAULT CURRENT_TIMESTAMP,
                    method TEXT,
                    notes TEXT,
                    FOREIGN KEY(sale_id) REFERENCES sales(id) ON DELETE CASCADE,
                    FOREIGN KEY(client_id) REFERENCES clientes(id) ON DELETE CASCADE
                );
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
