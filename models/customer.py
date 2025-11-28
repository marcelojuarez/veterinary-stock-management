import sqlite3
from db.database import db

class CustomerModel:
    def __init__(self, db_connection=None):
        self.db = db_connection or db 

    def get_all_customers(self): 
        # Obtener todos los clientes
        try: 
            query = "SELECT * FROM clientes ORDER BY id"
            return db.fetch_all(query)
        except ValueError as e: 
            print(f'Error getting customers: {e}')
            return []
        
    def get_all_clients(self):
        query = "SELECT id, nombre FROM clientes ORDER BY nombre"
        return db.fetch_all(query)
    
    def get_client_by_name(self, name):
        """Buscar cliente por nombre exacto"""
        query = """
            SELECT id, nombre, cuit, domicilio
            FROM clientes
            WHERE nombre = ?
        """
        return db.fetch_one(query, (name,))

    def get_client_id_by_name(self, name):
        query = "SELECT id FROM clientes WHERE nombre = ?"
        row = db.fetch_one(query, (name,))
        return row[0] if row else None


    def find_customer_by_id(self, customer_id):
        try:
            query = "SELECT * FROM clientes WHERE id = ?"
            return db.fetch_one(query, (customer_id,))
        except Exception as e:
            print(f'Error getting customer by ID: {e}')
            return None


    def add_customer(self, customer_data):
        # Agregar nuevo cliente a la base de datos
        query = """
            INSERT INTO clientes (nombre, cuit, domicilio, telefono)
            VALUES(?, ?, ?, ?)
        """
        params = [
            customer_data['nombre'].upper(),
            customer_data['cuit'],
            customer_data['domicilio'].upper(),
            customer_data['telefono']
        ]
        try:
            return db.execute_query(query, params)
        except sqlite3.IntegrityError as e: 
            raise ValueError("ya existe un cliente con alguno de esos datos.")

    def delete_customer(self, customer_id):
        # Eliminar la informacion del cliente
        try:
            query = "DELETE FROM clientes where id = ?"
            return db.execute_query(query, (customer_id,))
        except Exception as e: 
            print(f'Error : {e}')
            return None 
    
    def search_customer(self, search_term):
        # Busco a un cliente por nombre o id 
        try:
            if search_term.isdigit():
                query = "SELECT * FROM clientes WHERE id = ?"
                return self.db.fetch_all(query, (int(search_term),))
            else:
                query = "SELECT * FROM clientes WHERE nombre LIKE ?"
                return self.db.fetch_all(query, (f"%{search_term.upper()}%",))
        except Exception as e:
            print(f"Error searching customer: {e}")
            return []
            
    # --------------------------------------------------------------------
    # 💳 GESTIÓN DE DEUDAS DE CLIENTES
    # --------------------------------------------------------------------
    def get_customer_debts(self, cliente_id):
        query = """
            SELECT 
                s.id AS sale_id,
                s.date,
                s.total,
                IFNULL(SUM(p.amount), 0) AS pagado,
                (s.total - IFNULL(SUM(p.amount), 0)) AS saldo,
                s.estado
            FROM sales s
            LEFT JOIN payments p ON s.id = p.sale_id
            WHERE s.cliente_id = ?
            GROUP BY s.id
            ORDER BY sale_id DESC;
        """
        
        rows = self.db.fetch_all(query, (cliente_id,))

        state_map = {
            "fiada": "Fiada",
            "pending": "Pendiente",
            "partial": "Pago parcial",
            "paid": "Pagada"
        }

        formatted = []
        for row in rows:
            sale_id, date, total, pagado, saldo, estado = row

            # 🔥 Formateo profesional de floats
            total = round(float(total), 2)
            pagado = round(float(pagado), 2)
            saldo = round(float(saldo), 2)

            estado_es = state_map.get(estado, estado)

            formatted.append((sale_id, date, total, pagado, saldo, estado_es))

        return formatted



    def get_sale_items(self, sale_id):
        """Detalle de productos vendidos en una venta fiada"""
        query = """
            SELECT st.name, si.quantity, si.price, si.subtotal
            FROM sale_items si
            JOIN stock st ON st.id = si.product_id
            WHERE si.sale_id = ?
        """
        return self.db.fetch_all(query, (sale_id,))

    def mark_debt_as_paid(self, sale_id):
        """Marcar deuda como pagada"""
        query = "UPDATE sales SET estado = 'pagada' WHERE id = ?"
        self.db.execute_query(query, (sale_id,))

    def get_total_debt(self, cliente_id):
        """Devuelve el total pendiente del cliente (suma de saldos positivos)."""
        query = """
            SELECT 
                s.total,
                IFNULL((SELECT SUM(amount) FROM payments WHERE sale_id = s.id), 0) AS paid
            FROM sales s
            WHERE s.cliente_id = ?;
        """

        rows = self.db.fetch_all(query, (cliente_id,))

        total_pending = 0
        for total, paid in rows:
            saldo = total - paid
            if saldo > 0:
                total_pending += saldo

        return total_pending
