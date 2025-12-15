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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                    cuit TEXT,
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

            # Tabla de compras 
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS purchase (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id INTEGER,
                    document_type TEXT,
                    invoice_id TEXT NULL,
                    receipt_id TEXT NULL,
                    date TEXT DEFAULT CURRENT_DATE,
                    expiration_date TEXT NULL,
                    state TEXT DEFAULT 'PENDIENTE',
                    observations TEXT,
                    pending REAL,
                    total REAL,
                    FOREIGN KEY (supplier_id) REFERENCES supplier(id),
                    FOREIGN KEY (receipt_id) REFERENCES supplier_receipt(id), 
                    FOREIGN KEY (invoice_id) REFERENCES supplier_invoice(id)
                );
            ''')

            # cursor.execute('''
            #     CREATE TABLE IF NOT EXISTS purchase_items(
            #         id INTEGER PRIMARY KEY AUTOINCREMENT,
            #         product_id INTEGER,
            #         quantity INTEGER,
            #         cost_price REAL
            #         IVA REAL,
            #         total_line REAL,
            #         FOREIGN KEY product_id REFERENCES 
            #     );
            # ''')


            # Tabla facturas asociada a un proveedor
            cursor.execute(''' 
                CREATE TABLE IF NOT EXISTS supplier_invoice(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                           
                    -- Relacion
                    supplier_id INTEGER,
                           
                    -- Datos de la factura
                    invoice_id TEXT UNIQUE,
                    invoice_type TEXT,
                    point_of_sale INTEGER,
                    
                    -- Fechas
                    date TEXT CURRENT_DATE,
                    expiration_date TEXT CURRENT_DATE,

                    -- Montos     
                    total REAL,
                    subtotal REAL,
                    iva REAL,
                    discount REAL,
                    
                    -- Otros
                    state TEXT DEFAULT 'PENDIENTE',
                    observations TEXT,
                           
                    FOREIGN KEY (supplier_id) REFERENCES supplier (id)
                );
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS supplier_receipt (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id INTEGER NOT NULL,
                    receipt_id TEXT UNIQUE,
                    date TEXT CURRENT_DATE,
                    expiration_date TEXT,
                    observations TEXT,
                    state TEXT DEFAULT 'PENDIENTE',
                    total REAL,
                    FOREIGN KEY (supplier_id) REFERENCES supplier(id)
                );
            ''')

            # Tabla que vincula pagos con compras
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS supplier_purchase_payment(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    purchase_id INTEGER NOT NULL,
                    payment_id INTEGER NOT NULL,
                    amount_applied REAL NOT NULL,
                    FOREIGN KEY (purchase_id) REFERENCES purchase(id),
                    FOREIGN KEY (payment_id) REFERENCES supplier_payment(id)
                );
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
                    FOREIGN KEY(cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
                );
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
                    FOREIGN KEY(factura_id) REFERENCES factura(id) ON DELETE CASCADE,
                    FOREIGN KEY(producto_id) REFERENCES stock(id)
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

            conn.commit()

    def execute_query(self, query, params=None, conn=None, commit=True):
        """
        Ejecuta una consulta SQL.

        - Si conn es None → abre su propia conexión (modo normal)
        - Si conn se pasa → usa esa conexión (modo transacción)
        - si commit=True hace commit si la conexión es propia
        """

        own_conn = False
        if conn is None:
            print('entro aca')
            conn = self.get_connection()
            own_conn = True

        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)

        else:
            cursor.execute(query)

        if commit:
            conn.commit()

        if own_conn:
            conn.close()
            
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
