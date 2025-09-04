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
                CREATE TABLE IF NOT EXISTS supplier(
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    razon_social VARCHAR(150) NOT NULL,
                    nombre VARCHAR(150) NOT NULL,
                    activo BOOLEAN DEFAULT TRUE
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
        
    def fetch_all(self, query, params=None):
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