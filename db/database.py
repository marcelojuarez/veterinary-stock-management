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
                name TEXT NOT NULL,
                pack TEXT NOT NULL,
                list_price TEXT NOT NULL,
                discount TEXT NOT NULL,
                cost_price TEXT NOT NULL,
                profit TEXT NOT NULL,
                price TEXT NOT NULL,
                iva TEXT NOT NULL,
                price_with_iva TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_DATE,
                last_price_update TEXT DEFAULT CURRENT_DATE,
                UNIQUE (name, pack)           
                );
            ''')

            # Tabla de clientes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customer (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    cuit TEXT UNIQUE,
                    home TEXT,
                    phone TEXT UNIQUE,
                    iva_condition TEXT,
                    cv TEXT,
                    cuig TEXT,
                    renspa TEXT,
                    establishment TEXT
                )
            ''')

            # Tabla de proveedores
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS supplier (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cuit TEXT,
                    name TEXT NOT NULL,
                    address TEXT,
                    city TEXT,
                    province TEXT,
                    country TEXT,
                    phone TEXT,
                    email TEXT,
                    iva_condition TEXT,
                    last_debt_update TEXT DEFAULT CURRENT_DATE,
                    active INTEGER NOT NULL DEFAULT 1
                );
            ''')

            # Tabla de saldo a favor proveedores
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS supplier_credit_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id INTEGER NOT NULL,
                    date TEXT DEFAULT CURRENT_DATE,
                    amount TEXT NOT NULL,
                    type TEXT,
                    purchase_id INTEGER NULL,
                    check_id INTEGER NULL,
                    notes TEXT,
                    valid INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY (supplier_id) REFERENCES supplier(id)
                );
            '''
            )

            # Tabla de empresa
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS company (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    business_name TEXT,
                    cuit TEXT,
                    iva_condition TEXT,
                    start_date TEXT,
                    address TEXT,
                    city TEXT,
                    province TEXT,
                    postal_code TEXT,
                    phone1 TEXT,
                    phone2 TEXT 
                );
            ''')

            # Tabla pagos proveedor 
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS supplier_payment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id INTEGER,
                    
                    receipt_number TEXT, -- recibo que te entrega el proveedor                           

                    amount TEXT NOT NULL,     
                    method TEXT,        -- EFECTIVO, TRANSFERENCIA, CHEQUE, MERCADO PAGO                                                        
                    observation TEXT,

                    -- TRANSFERENCIA
                    operation_num INTEGER,  
                    origin TEXT,
                    destination TEXT,
                        
                    -- CHEQUE
                    check_id INTEGER NULL,    
                    check_number TEXT,
                        
                    -- TRANSFERENCIA o CHEQUE
                    bank TEXT,  

                    date TEXT DEFAULT CURRENT_DATE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,  -- ← NUEVO: Guarda fecha + hora
                    valid INTEGER NOT NULL DEFAULT 1,
                    
                    FOREIGN KEY (supplier_id) REFERENCES supplier (id),
                    FOREIGN KEY (check_id) REFERENCES checks(id) ON DELETE SET NULL
                );
            ''')

            # Tabla que vincula pagos con compras
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS purchase_payment(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    purchase_id INTEGER NOT NULL,
                    payment_id INTEGER NOT NULL,
                    amount_applied TEXT NOT NULL,
                    applied_at TEXT DEFAULT CURRENT_DATE,
                    FOREIGN KEY (purchase_id) REFERENCES purchase(id),
                    FOREIGN KEY (payment_id) REFERENCES supplier_payment(id)
                );
            ''')

            # Tabla de compras 
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS purchase (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id INTEGER,
                    document_type TEXT,
                    invoice_id INTEGER NULL,
                    receipt_id INTEGER NULL,
                    date TEXT DEFAULT CURRENT_DATE,
                    expiration_date TEXT NULL,
                    state TEXT,
                    observations TEXT,
                    pending TEXT NOT NULL,
                    total TEXT NOT NULL,
                    FOREIGN KEY (supplier_id) REFERENCES supplier(id),
                    FOREIGN KEY (receipt_id) REFERENCES supplier_receipt(id), 
                    FOREIGN KEY (invoice_id) REFERENCES supplier_invoice(id)
                );
            ''')

            cursor.execute(''' 
                CREATE TABLE IF NOT EXISTS purchase_item (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    purchase_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    product_name TEXT NOT NULL,
                    pack TEXT NOT NULL,

                    quantity INTEGER NOT NULL,
                    list_price TEXT NOT NULL,
                    discount TEXT NOT NULL,
                    cost_price TEXT NOT NULL,
                    iva_rate TEXT NOT NULL,
                    discount_amount TEXT NOT NULL,

                    subtotal TEXT NOT NULL,
                    iva_amount TEXT NOT NULL,
                    total TEXT NOT NULL,

                    FOREIGN KEY (purchase_id) REFERENCES purchase(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES stock(id)
                );
            ''')

            # Tabla facturas asociada a un proveedor
            cursor.execute(''' 
                CREATE TABLE IF NOT EXISTS supplier_invoice(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id INTEGER,
                           
                    invoice_id TEXT UNIQUE,
                    invoice_type TEXT,
                    
                    date TEXT CURRENT_DATE,
                    expiration_date TEXT CURRENT_DATE,
                    supplier_iva_condition TEXT,
                    state TEXT,
                    observations TEXT,
                    pay_condition TEXT,
                    pay_period TEXT,
        
                    orig_subtotal TEXT NOT NULL,
                    discount TEXT NOT NULL,
                    discount_amount TEXT NOT NULL,
                    subtotal_w_discount TEXT NOT NULL,
                    iva TEXT NOT NULL,
                           
                    total TEXT NOT NULL,
                           
                    FOREIGN KEY (supplier_id) REFERENCES supplier (id)
                );
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS invoice_perceptions(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    tax_type TEXT NOT NULL,
                    amount TEXT NOT NULL,
                           
                    FOREIGN KEY (invoice_id) REFERENCES supplier_invoice(id) ON DELETE CASCADE         
                );
            ''')


            cursor.execute('''
                CREATE TABLE IF NOT EXISTS supplier_receipt (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id INTEGER NOT NULL,
                    receipt_id TEXT,
                    date TEXT CURRENT_DATE,
                    expiration_date TEXT,
                    observations TEXT,
                    state TEXT,
                    total TEXT NOT NULL,
                    FOREIGN KEY (supplier_id) REFERENCES supplier(id)
                );
            ''')

            # Tabla de facturas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS invoice (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    number TEXT,
                    date TEXT DEFAULT CURRENT_TIMESTAMP,
                    customer_id INTEGER,
                    subtotal TEXT NOT NULL,
                    iva TEXT NOT NULL,
                    total TEXT NOT NULL,
                    estado TEXT DEFAULT 'borrador',  -- o 'emitida'
                    FOREIGN KEY(customer_id) REFERENCES customer(id)
                );
            ''')

            # Tabla de items de factura
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS invoice_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER,
                    product_id TEXT,
                    quantity INTEGER,
                    price TEXT NOT NULL,
                    subtotal TEXT NOT NULL,
                    FOREIGN KEY(invoice_id) REFERENCES invoice(id),
                    FOREIGN KEY(product_id) REFERENCES stock(id)
                );
            ''')

            # Tabla de ventas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT DEFAULT CURRENT_TIMESTAMP,
                    total TEXT NOT NULL,
                    cliente_id INTEGER,
                    estado TEXT DEFAULT 'paid',
                    total_cerrado TEXT,
                    fecha_cierre TEXT,
                    FOREIGN KEY(cliente_id) REFERENCES customer(id) ON DELETE CASCADE
                );
            ''')

            # Detalle de cada producto vendido
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    price TEXT NOT NULL,
                    subtotal TEXT NOT NULL,
                    iva_rate TEXT NOT NULL,
                    iva_amount TEXT NOT NULL,
                    observations TEXT,
                    FOREIGN KEY(sale_id) REFERENCES sales(id) ON DELETE CASCADE,
                    FOREIGN KEY(product_id) REFERENCES stock(id)
                );
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sale_retentions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    tax_type TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    certificate_number TEXT,
                    FOREIGN KEY(sale_id) REFERENCES sales(id) ON DELETE CASCADE
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
                    FOREIGN KEY(customer_id) REFERENCES customer(id)
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

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS checks (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    number            TEXT NOT NULL,
                    bank              TEXT NOT NULL,
                    type              TEXT NOT NULL DEFAULT 'FÍSICO',
                    amount            TEXT NOT NULL,
                    issue_date        TEXT NOT NULL,
                    due_date          TEXT NOT NULL,
                    status            TEXT NOT NULL DEFAULT 'EN_CARTERA',
                    origin            TEXT NOT NULL DEFAULT 'CLIENTE',
                    client_id         INTEGER NULL,
                    purchase_id       INTEGER NULL,
                    notes             TEXT NULL,
                    FOREIGN KEY (client_id) REFERENCES customer(id) ON DELETE SET NULL,
                    FOREIGN KEY (purchase_id) REFERENCES purchase(id) ON DELETE SET NULL
                );
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    client_id INTEGER NOT NULL,
                    amount TEXT NOT NULL,
                    date TEXT DEFAULT CURRENT_TIMESTAMP,
                    method TEXT,
                    notes TEXT,
                    check_id INTEGER NULL,
                    valid INTEGER NOT NULL,
                    FOREIGN KEY(sale_id) REFERENCES sales(id) ON DELETE CASCADE,
                    FOREIGN KEY(client_id) REFERENCES customer(id) ON DELETE CASCADE,
                    FOREIGN KEY(check_id) REFERENCES checks(id) ON DELETE SET NULL
                );
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customer_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    type TEXT NOT NULL,     -- 'SALE' | 'PAYMENT' | 'CREDIT' | 'PRICE_ADJUSTMENT'
                    description TEXT,
                    amount TEXT NOT NULL DEFAULT '0.00',
                    payment TEXT NOT NULL DEFAULT '0.00',
                    debt TEXT NOT NULL DEFAULT '0.00',
                    reference_id INTEGER, -- sales or payments
                    reference TEXT,
                    FOREIGN KEY (client_id) REFERENCES customer(id)
                );                          
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cash_expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    payment_method TEXT DEFAULT 'EFECTIVO',
                    observations TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            ''')


            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customer_credit(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    amount TEXT NOT NULL,
                    used TEXT NOT NULL DEFAULT '0.00',
                    reason TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    sale_id INTEGER,
                    check_id INTEGER NULL,
                    valid INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY(client_id) REFERENCES customer(id) ON DELETE CASCADE,
                    FOREIGN KEY(sale_id) REFERENCES sales(id) ON DELETE SET NULL,
                    FOREIGN KEY(check_id) REFERENCES checks(id) ON DELETE SET NULL
                );
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_movement (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id    INTEGER NOT NULL,
                    product_name  TEXT NOT NULL,
                    date          TEXT NOT NULL,
                    event_type    TEXT NOT NULL,
                    detail        TEXT,
                    qty_before    INTEGER,
                    qty_after     INTEGER,
                    cost_before   TEXT,
                    cost_after    TEXT,
                    price_before  TEXT,
                    price_after   TEXT,
                    FOREIGN KEY (product_id) REFERENCES stock(id)
                )
            ''')

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cash_opening (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL UNIQUE,
                    opening_amount TEXT NOT NULL DEFAULT '0.00',
                    closing_amount TEXT,
                    expected_closing TEXT,
                    difference TEXT,
                    notes TEXT,
                    opened_by TEXT,
                    closed_by TEXT,
                    opened_at TEXT NOT NULL,
                    closed_at TEXT,
                    status TEXT NOT NULL DEFAULT 'ABIERTA'
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_fraction_config (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id      INTEGER NOT NULL UNIQUE,
                    unit            TEXT    NOT NULL DEFAULT 'KG',   -- KG | GR | LITRO | ML
                    qty_per_package REAL    NOT NULL,                 -- cuánto tiene cada unidad cerrada (ej. 15 para bolsa 15kg)
                    fraction_price  TEXT    NOT NULL,                 -- precio de venta por unidad fraccionada (sin IVA)
                    created_at      TEXT    DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES stock(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS open_fractions (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id  INTEGER NOT NULL,
                    remaining   REAL    NOT NULL,   -- cantidad restante en la unidad abierta
                    opened_at   TEXT    DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES stock(id) ON DELETE CASCADE
                )
            """)

            # Índice para búsquedas rápidas por producto
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_open_fractions_product
                ON open_fractions (product_id)
            """)

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
            conn = self.get_connection()
            own_conn = True

        try:
            cursor = conn.cursor()

            if params is not None:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if commit:
                conn.commit()

            return cursor.lastrowid

        except Exception as e:
            if own_conn:
                conn.rollback()
            raise e

        finally:
            if own_conn:
                conn.close()
    
    def fetch_all(self, query, params=None, conn=None):
        """
        Ejecutar una consulta que devuelve múltiples resultados

        - Si conn es None → abre su propia conexión (modo normal)
        - Si conn se pasa → usa esa conexión (modo transacción)
        - si commit=True hace commit si la conexión es propia
        """
        own_conn = False
        if conn is None:
            conn = self.get_connection()
            own_conn = True
    
        cursor = conn.cursor()

        if params is not None:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        rows = cursor.fetchall()

        if own_conn:
            conn.close()
        
        return rows
        
    
    def fetch_one(self, query, params=None, conn=None):
        """
        Ejecutar una consulta que devuelve un resultado

        - Si conn es None → abre su propia conexión (modo normal)
        - Si conn se pasa → usa esa conexión (modo transacción)
        - si commit=True hace commit si la conexión es propia
        """
        own_conn = False
        if conn is None:
            conn = self.get_connection()
            own_conn = True

        cursor = conn.cursor()
        if params is not None:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        row = cursor.fetchone()

        if own_conn:
            conn.close()

        return row


db = Database('db/stock.db')