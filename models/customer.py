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
            INSERT INTO clientes (nombre, cuit, domicilio, telefono, cv, cuig, renspa, establecimiento)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            customer_data['nombre'].upper(),
            customer_data['cuit'],
            customer_data['domicilio'].upper(),
            customer_data['telefono'],
            customer_data.get('cv', ''),
            customer_data.get('cuig', ''),
            customer_data.get('renspa', ''),
            customer_data.get('establecimiento', '').upper(),
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
            CASE 
                WHEN s.estado = 'paid' AND s.total_cerrado IS NOT NULL 
                THEN s.total_cerrado
                ELSE COALESCE(SUM(si.quantity * st.price_with_iva), 0)
            END AS total,
            COALESCE((SELECT SUM(p.amount) FROM payments p WHERE p.sale_id = s.id), 0) AS pagado,
            s.estado
        FROM sales s
        JOIN sale_items si ON si.sale_id = s.id
        JOIN stock st ON st.id = si.product_id
        WHERE s.cliente_id = ? AND s.estado IN ('pending', 'partial')
        GROUP BY s.id
        ORDER BY sale_id DESC;
        """
        rows = self.db.fetch_all(query, (cliente_id,))

        state_map = {
            "pending": "Pendiente",
            "partial": "Pago parcial",
            "paid": "Pagada"
        }

        formatted = []
        for sale_id, date, total, pagado, estado in rows:
            total = round(float(total), 2)
            pagado = round(float(pagado), 2)
            estado_es = state_map.get(estado, estado)
            saldo = round(max(0.0, total - pagado), 2)
            formatted.append((sale_id, date, total, pagado, saldo, estado_es))

        return formatted

    def get_sale_items(self, sale_id):
        """Detalle de productos vendidos en una venta fiada"""
        query = """
            SELECT st.name, si.quantity, st.price_with_iva, (si.quantity * st.price_with_iva) AS subtotal
            FROM sale_items si
            JOIN stock st ON st.id = si.product_id
            WHERE si.sale_id = ?
        """
        return self.db.fetch_all(query, (sale_id,))

    def mark_debt_as_paid(self, sale_id):
        """Marcar deuda como pagada"""
        query = "UPDATE sales SET estado = 'paid' WHERE id = ?"
        self.db.execute_query(query, (sale_id,))

    def get_total_debt(self, cliente_id):
        """Devuelve el total pendiente del cliente (suma de saldos positivos)."""
        query = """
            SELECT 
                s.id,
                COALESCE(SUM(si.quantity * st.price_with_iva), 0) AS total_variable,
                COALESCE((SELECT SUM(p.amount) FROM payments p WHERE p.sale_id = s.id), 0) AS pagado
                FROM sales s
                JOIN sale_items si ON si.sale_id = s.id
                JOIN stock st ON st.id = si.product_id
                WHERE s.cliente_id = ? AND s.estado IN ('pending', 'partial')
                GROUP BY s.id
        """

        rows = self.db.fetch_all(query, (cliente_id,))

        total_pending = 0.0
        for _, total_variable, paid in rows:
            saldo = max(0.0, float(total_variable) - float(paid))
            if saldo > 0.01:
                total_pending += saldo

        return round(total_pending, 2)

    def get_customer_account_history(self, cliente_id):
        """
        Obtiene el historial completo de cuenta del cliente.
        """
        movements = []
        
        # 1. VENTAS - Sin payment_method (no existe en tu tabla)
        sales_query = """
            SELECT 
                s.id,
                s.date,
                CASE 
                    WHEN s.estado = 'paid' AND s.total_cerrado IS NOT NULL 
                    THEN s.total_cerrado
                    ELSE COALESCE(SUM(si.quantity * st.price_with_iva), 0)
                END AS monto,
                s.estado,
                COALESCE(SUM(si.quantity), 0) AS cant_productos
            FROM sales s
            LEFT JOIN sale_items si ON si.sale_id = s.id
            LEFT JOIN stock st ON st.id = si.product_id
            WHERE s.cliente_id = ?
            GROUP BY s.id
        """
        sales = self.db.fetch_all(sales_query, (cliente_id,))

        for sale_id, fecha, monto, estado, cant_prod in sales:
            cant_prod = int(cant_prod) if cant_prod else 0
            prod_txt = f"{cant_prod} {'producto' if cant_prod == 1 else 'productos'}"
            monto = round(float(monto), 2)
            
            if estado == "paid":
                # Venta pagada al contado - NO suma a deuda, solo informativo
                movements.append({
                    "fecha": fecha,
                    "tipo": "CONTADO",
                    "descripcion": f"Venta #{sale_id} · {prod_txt} · Contado",
                    "debe": 0.0,      # NO suma a deuda
                    "haber": 0.0,     # NO suma a pagos de cta cte
                    "monto_ref": monto,  # Solo para mostrar en columna Contado
                    "ref_id": sale_id
                })
            else:
                estado_txt = "Pago parcial" if estado == "partial" else "Pendiente"
                movements.append({
                    "fecha": fecha,
                    "tipo": "COMPRA",
                    "descripcion": f"Venta #{sale_id} · {prod_txt} · {estado_txt}",
                    "debe": monto,
                    "haber": 0.0,
                    "monto_ref": 0.0,
                    "ref_id": sale_id
                })
                        
        # 2. PAGOS - Excluir pagos de ventas al contado
        payments_query = """
            SELECT 
                p.id,
                p.date,
                p.amount,
                p.method,
                p.sale_id,
                p.notes
            FROM payments p
            LEFT JOIN sales s ON s.id = p.sale_id
            WHERE p.client_id = ?
            AND (
                p.sale_id IS NULL 
                OR s.estado IN ('pending', 'partial')
            )
        """
        payments = self.db.fetch_all(payments_query, (cliente_id,))

        for pay_id, fecha, monto, method, sale_id, notes in payments:
            method_map = {
                "cash": "Efectivo",
                "transfer": "Transferencia", 
                "card": "Tarjeta",
                "efectivo": "Efectivo",
                "transferencia": "Transferencia"
            }
            method_txt = method_map.get(method.lower(), method.capitalize()) if method else "Efectivo"
            
            # Construir descripción clara
            if notes and "Global" in notes:
                desc = f"Pago a cuenta · {method_txt}"
            elif sale_id:
                desc = f"Pago Venta #{sale_id} · {method_txt}"
            else:
                desc = f"Pago a cuenta · {method_txt}"
                
            movements.append({
                "fecha": fecha,
                "tipo": "PAGO",
                "descripcion": desc,
                "debe": 0.0,
                "haber": round(float(monto), 2),
                "ref_id": pay_id
            })
        
        # 3. CRÉDITOS (igual que antes)
        credits_query = """
            SELECT 
                cc.id,
                cc.created_at,
                cc.amount,
                cc.reason,
                cc.sale_id
            FROM customer_credit cc
            WHERE cc.client_id = ?
            AND cc.reason NOT LIKE 'AJUSTE:%'
            AND cc.reason NOT LIKE 'SALDO A FAVOR:%'
        """
        credits = self.db.fetch_all(credits_query, (cliente_id,))
        
        for credit_id, fecha, monto, reason, sale_id in credits:
            monto = float(monto)
            if monto > 0:
                desc = f"Nota de crédito · {reason}" if reason else "Saldo a favor generado"
                movements.append({
                    "fecha": fecha,
                    "tipo": "CRÉDITO",
                    "descripcion": desc,
                    "debe": 0.0,
                    "haber": round(monto, 2),
                    "ref_id": credit_id
                })
            else:
                desc = f"Aplicación de saldo a favor"
                if sale_id:
                    desc += f" · Venta #{sale_id}"
                movements.append({
                    "fecha": fecha,
                    "tipo": "USO CRÉDITO",
                    "descripcion": desc,
                    "debe": round(abs(monto), 2),
                    "haber": 0.0,
                    "ref_id": credit_id
                })
        
        # Ordenar por fecha
        movements.sort(key=lambda x: x["fecha"])
        
        # Calcular saldo acumulado
        saldo = 0.0
        for mov in movements:
            saldo += mov["debe"] - mov["haber"]
            mov["saldo"] = round(saldo, 2)
        
        return movements
    
    def get_customer_account_summary(self, cliente_id):
        """Resumen de cuenta del cliente"""
        movements = self.get_customer_account_history(cliente_id)
        
        total_debe = sum(m["debe"] for m in movements)
        total_haber = sum(m["haber"] for m in movements)
        saldo_final = total_debe - total_haber
        
        # Contar ventas
        total_ventas = len([m for m in movements if m["tipo"] == "VENTA"])
        ventas_pagadas = len([m for m in movements if m["tipo"] == "VENTA" and "Pagada" in m["descripcion"]])
        
        return {
            "total_comprado": round(total_debe, 2),
            "total_pagado": round(total_haber, 2),
            "saldo_actual": round(saldo_final, 2),
            "total_ventas": total_ventas,
            "ventas_pagadas": ventas_pagadas,
            "saldo_a_favor": round(abs(saldo_final), 2) if saldo_final < 0 else 0.0,
            "deuda_pendiente": round(saldo_final, 2) if saldo_final > 0 else 0.0
        }