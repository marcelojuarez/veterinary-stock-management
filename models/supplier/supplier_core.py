# models/supplier/supplier_core.py

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SupplierCore():
    def __init__(self, db):
        self.db = db

    
    def get_all_suppliers(self):
        """Solo devuelve proveedores activos."""
        try:
            query = "SELECT * FROM supplier WHERE active = 1 ORDER BY name"
            return self.db.fetch_all(query)
        except ValueError as e:
            logger.error("Error getting suppliers: %s", e)
            return []
    
    def find_supplier_by_id(self, supplier_id, conn=None):
        # Obtener proveedor a traves de id
        try:
            query = "SELECT * FROM supplier where id = ?"
            return self.db.fetch_one(query, (supplier_id, ), conn=conn)
        except ValueError as e:
            logger.error("Error getting supplier by ID: %s", e)
            return None
        
    def find_supplier_by_cuit_and_name(self, cuit, name):
        try:
            query = "SELECT * FROM supplier WHERE cuit = ? AND UPPER(name) = ? LIMIT 1"
            return self.db.fetch_one(query, (cuit, name.strip().upper()))
        except ValueError as e:
            logger.error("Error getting supplier by cuit and name: %s", e)
            return None

    def find_supplier_by_address(self, address, city):
        try:
            query = "SELECT * FROM supplier WHERE UPPER(address) = ? AND UPPER(city) = ? LIMIT 1"
            return self.db.fetch_one(query, (address, city.strip().upper()))
        except ValueError as e:
            logger.error("Error getting supplier by address: %s", e)
            return None
        
    def find_supplier_by_cuit(self, supplier_cuit):
        try:
            query = "SELECT * FROM supplier where cuit = ?"
            return self.db.fetch_one(query, (supplier_cuit,))
        except ValueError as e:
            logger.error("Error getting supplier by CUIT: %s", e)
            return None

    def add_supplier(self, supplier_data):
        # Agregar nuevo proveedor a la base de datos
        date = datetime.now().strftime("%d/%m/%Y %H:%M")
        query = """
            INSERT INTO supplier (name, cuit, address, city, province, country, phone, email, iva_condition, last_debt_update)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            supplier_data['name'],
            supplier_data['cuit'],
            supplier_data['address'],
            supplier_data['city'],
            supplier_data['province'],
            supplier_data['country'],
            supplier_data['phone'],
            supplier_data['email'],
            supplier_data['iva_condition'],
            date
        ]

        return self.db.execute_query(query, params)
    
    def update_supplier_data(self, supplier_id, supplier_data):
        query = """
        UPDATE supplier
        SET
            name = ?,
            cuit = ?,
            address = ?,
            city = ?,
            province = ?,
            country = ?,
            phone = ?,
            email = ?,
            iva_condition = ?
        WHERE id = ?
        """

        params = [
            supplier_data['name'],
            supplier_data['cuit'],
            supplier_data['address'],
            supplier_data['city'],
            supplier_data['province'],
            supplier_data['country'],
            supplier_data['phone'],
            supplier_data['email'],
            supplier_data['iva_condition'],
            supplier_id
        ]

        self.db.execute_query(query, params)

    def has_purchases(self, supplier_id):
        """Retorna True si el proveedor tiene compras asociadas."""
        query = "SELECT COUNT(*) FROM purchase WHERE supplier_id = ?"
        row = self.db.fetch_one(query, (supplier_id,))
        return row[0] > 0 if row else False

    def deactivate_supplier(self, supplier_id):
        """Borrado lógico: desactiva el proveedor sin eliminar sus datos."""
        try:
            query = "UPDATE supplier SET active = 0 WHERE id = ?"
            return self.db.execute_query(query, (supplier_id,))
        except Exception as e:
            logger.error("Error deactivating supplier: %s", e)
            return None

    def delete_supplier(self, supplier_id):
        """Elimina físicamente solo si no tiene compras asociadas."""
        try:
            query = "DELETE FROM supplier WHERE id = ?"
            return self.db.execute_query(query, (supplier_id,))
        except Exception as e:
            logger.error("Error deleting supplier: %s", e)
            return None


