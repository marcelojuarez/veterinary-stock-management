import sqlite3
import os

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.ensure_db_exists()
        self.create_tables()

    def ensure_db_exists(self):
        """Asegurar que el directorio de la base de datos existe"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # supplier table
            cursor.execute('''
                CREATE TABLE supplier()
                    id_proveedor INT AUTO_INCREMENT PRIMARY KEY,
                    razon_social VARCHAR(150) NOT NULL,
                    cuit VARCHAR(20) UNIQUE NOT NULL,
                    direccion VARCHAR(200),
                    ciudad VARCHAR(100),
                    provincia VARCHAR(100),
                    telefono VARCHAR(50),
                    email VARCHAR(100),
                    condiciones_pago VARCHAR(100),
                    banco VARCHAR(100),
                    cbu VARCHAR(50),
                    fecha_alta DATE DEFAULT CURRENT_DATE,
                    activo BOOLEAN DEFAULT TRUE
                )
            ''')

            cursor.execute('''
                CREATE TABLE movimientos_proveedor (
                    id_movimiento INT AUTO_INCREMENT PRIMARY KEY,
                    id_proveedor INT NOT NULL,
                    fecha DATE NOT NULL,
                    concepto VARCHAR(200),
                    monto DECIMAL(12,2) NOT NULL,
                    tipo ENUM('COMPRA','PAGO','NOTA_CREDITO') NOT NULL,
                    FOREIGN KEY (id_proveedor) REFERENCES proveedores(id_proveedor)
                    )       
                ''')

            conn.commit()

    def execute_query(self, query, params=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.lastrowid
        
    def fetch_all(self, query, params):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()

    def fetch_one(self, query, params):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()


db = Database('db/veterinary.db')