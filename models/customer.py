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
            INSERT INTO clientes (nombre, cuit, domicilio, telefono, condicion_iva, cv, cuig, renspa, establecimiento)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            customer_data['nombre'].upper(),
            customer_data['cuit'],
            customer_data['domicilio'].upper(),
            customer_data['telefono'],
            customer_data['condicion_iva'],
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

    def _is_cash_sale(self, sale_id, fecha_venta):
        """
        Determina si una venta fue de CONTADO.
        
        Es CONTADO únicamente si:
        - Estado es 'paid' Y no tiene NINGÚN pago registrado en la tabla payments
        (significa que se pagó en el momento de crear la venta)
        
        Si tiene aunque sea UN pago registrado, es CRÉDITO (se muestra en historial)
        """
        payments_query = """
            SELECT COUNT(*) 
            FROM payments 
            WHERE sale_id = ?
        """
        result = self.db.fetch_one(payments_query, (sale_id,))
        
        # Es CONTADO solo si NO tiene pagos registrados
        # Si tiene pagos (parciales o totales), es CRÉDITO y debe mostrarse
        return result is None or result[0] == 0

    def get_customer_account_history(self, cliente_id):
        """
        Historial de cuenta corriente:
        - Ventas de CONTADO NO aparecen (se omiten completamente)
        - Solo ventas a CRÉDITO aparecen en el historial
        """
        movements = []
        contado_sales = set()  # IDs de ventas de contado a excluir
        
        # ================================================================
        # PASO 1: OBTENER TODAS LAS VENTAS Y DETECTAR CUÁLES SON CONTADO
        # ================================================================
        sales_query = """
            SELECT 
                s.id,
                s.date,
                CASE 
                    WHEN s.estado = 'paid' AND s.total_cerrado IS NOT NULL 
                    THEN s.total_cerrado
                    ELSE COALESCE(SUM(si.quantity * st.price_with_iva), 0)
                END AS total,
                s.estado,
                COUNT(si.id) AS cant_productos
            FROM sales s
            LEFT JOIN sale_items si ON si.sale_id = s.id
            LEFT JOIN stock st ON st.id = si.product_id
            WHERE s.cliente_id = ? 
            AND s.estado IN ('pending', 'partial', 'paid')
            GROUP BY s.id
            ORDER BY s.date, s.id
        """
        sales = self.db.fetch_all(sales_query, (cliente_id,))
        
        # Identificar ventas de contado
        for sale_id, fecha_venta, total, estado, cant_prod in sales:
            if estado == 'paid' and self._is_cash_sale(sale_id, fecha_venta):
                contado_sales.add(sale_id)
        
        # ================================================================
        # PASO 2: REGISTRAR SOLO VENTAS A CRÉDITO (omitir contado)
        # ================================================================
        for sale_id, fecha, total, estado, cant_prod in sales:
            # OMITIR ventas de contado
            if sale_id in contado_sales:
                continue
                
            total = round(float(total), 2)
            cant_prod = int(cant_prod) if cant_prod else 0
            
            estado_map = {
                "pending": "Pendiente",
                "partial": "Pago parcial",
                "paid": "Pagada"
            }
            estado_txt = estado_map.get(estado, estado)
            
            movements.append({
                "fecha": fecha,
                "tipo": "VENTA",
                "descripcion": f"Venta #{sale_id} · {cant_prod} producto(s) · {estado_txt}",
                "debe": total,
                "haber": 0.0,
                "saldo": 0.0,
                "sale_id": sale_id,
                "referencia": ""
            })
        
        # ================================================================
        # PASO 3: PAGOS (solo de ventas a crédito)
        # ================================================================
        payments_query = """
            SELECT 
                p.id,
                p.date,
                p.amount,
                p.method,
                p.sale_id,
                p.notes
            FROM payments p
            WHERE p.client_id = ?
            ORDER BY p.date, p.id
        """
        payments = self.db.fetch_all(payments_query, (cliente_id,))
        
        method_map = {
            "cash": "Efectivo",
            "transfer": "Transferencia",
            "card": "Tarjeta",
            "efectivo": "Efectivo",
            "transferencia": "Transferencia",
            "saldo a favor": "Saldo a Favor",
            "cheque": "Cheque",
            "deposito": "Depósito",
            "global": "Global"
        }
        
        for pay_id, fecha, monto, method, sale_id, notes in payments:
            # OMITIR pagos de ventas de contado
            if sale_id in contado_sales:
                continue
                
            monto = round(float(monto), 2)
            method_txt = method_map.get(method.lower() if method else "", method.capitalize() if method else "Efectivo")
            
            if sale_id:
                desc = f"Pago Venta #{sale_id} · {method_txt}"
            else:
                desc = f"Pago a cuenta · {method_txt}"
            
            movements.append({
                "fecha": fecha,
                "tipo": "PAGO",
                "descripcion": desc,
                "debe": 0.0,
                "haber": monto,
                "saldo": 0.0,
                "sale_id": sale_id,
                "referencia": notes or ""
            })
        
        # ================================================================
        # PASO 4: NOTAS DE CRÉDITO (si existe la tabla)
        # ================================================================
        try:
            table_check = "SELECT name FROM sqlite_master WHERE type='table' AND name='customer_credit'"
            if self.db.fetch_one(table_check):
                credits_query = """
                    SELECT 
                        id,
                        created_at,
                        amount,
                        reason,
                        sale_id
                    FROM customer_credit
                    WHERE client_id = ?
                    ORDER BY created_at, id
                """
                credits = self.db.fetch_all(credits_query, (cliente_id,))
                
                for credit_id, fecha, monto, reason, sale_id in credits:
                    monto = round(float(monto), 2)
                    
                    if monto > 0:
                        desc = f"Nota de crédito"
                        if reason:
                            desc += f" · {reason}"
                        
                        movements.append({
                            "fecha": fecha,
                            "tipo": "CRÉDITO",
                            "descripcion": desc,
                            "debe": 0.0,
                            "haber": monto,
                            "saldo": 0.0,
                            "sale_id": sale_id,
                            "referencia": reason or ""
                        })
                    else:
                        desc = f"Aplicación de saldo"
                        if sale_id:
                            desc += f" · Venta #{sale_id}"
                        
                        movements.append({
                            "fecha": fecha,
                            "tipo": "USO CRÉDITO",
                            "descripcion": desc,
                            "debe": abs(monto),
                            "haber": 0.0,
                            "saldo": 0.0,
                            "sale_id": sale_id,
                            "referencia": reason or ""
                        })
        except Exception as e:
            print(f"Tabla customer_credit no disponible: {e}")
        
        # ================================================================
        # PASO 5: ORDENAR CRONOLÓGICAMENTE
        # ================================================================
        movements.sort(key=lambda x: (x["fecha"], x.get("sale_id", 0) or 0))
        
        # ================================================================
        # PASO 6: CALCULAR SALDO ACUMULADO
        # ================================================================
        saldo_acumulado = 0.0
        for mov in movements:
            saldo_acumulado += mov["debe"] - mov["haber"]
            mov["saldo"] = round(saldo_acumulado, 2)
        
        # ================================================================
        # PASO 7: RESUMEN (solo cuenta ventas a crédito)
        # ================================================================
        total_debe = sum(m["debe"] for m in movements)
        total_haber = sum(m["haber"] for m in movements)
        saldo_final = round(saldo_acumulado, 2)

        ventas_totales = len([m for m in movements if m["tipo"] == "VENTA"])
        
        # Contar ventas pagadas
        ventas_credito_pagadas = 0
        for m in movements:
            if m["tipo"] == "VENTA":
                sale_id = m["sale_id"]
                check = "SELECT estado FROM sales WHERE id = ?"
                result = self.db.fetch_one(check, (sale_id,))
                if result and result[0] == 'paid':
                    ventas_credito_pagadas += 1
        
        ventas_pagadas = ventas_credito_pagadas

        summary = {
            'total_comprado': round(total_debe, 2),
            'total_pagado': round(total_haber, 2),
            'saldo_a_favor': abs(saldo_final) if saldo_final < 0 else 0.0,
            'deuda_pendiente': saldo_final if saldo_final > 0 else 0.0,
            'ventas_pagadas': ventas_pagadas,
            'total_ventas': ventas_totales,
            'ventas_texto': f"{ventas_pagadas}/{ventas_totales} pagadas"
        }

        return movements, summary