import sqlite3
from db.database import db

from models.payment_model import PaymentModel
from decimal import Decimal
from utils.utils import norm_to_2_dec, flex_dec, iso_to_traditional
from datetime import datetime
class CustomerModel:
    def __init__(self, db_connection=None):
        self.db = db_connection or db 
        self.pay_model = PaymentModel()

    def get_all_customers(self): 
        # Obtener todos los clientes
        try: 
            query = "SELECT * FROM customer ORDER BY id"
            return db.fetch_all(query)
        except ValueError as e: 
            print(f'Error getting customers: {e}')
            return []
        
    def get_all_clients(self):
        query = "SELECT id, name FROM customer ORDER BY name"
        return db.fetch_all(query)
    
    def get_client_by_name(self, name):
        """Buscar cliente por nombre exacto"""
        query = """
            SELECT id, name, cuit, home, iva_condition
            FROM customer
            WHERE name = ?
        """
        return db.fetch_one(query, (name,))

    def get_client_id_by_name(self, name):
        query = "SELECT id FROM customer WHERE name = ?"
        row = db.fetch_one(query, (name,))
        return row[0] if row else None


    def find_customer_by_id(self, customer_id):
        try:
            query = "SELECT * FROM customer WHERE id = ?"
            return db.fetch_one(query, (customer_id,))
        except Exception as e:
            print(f'Error getting customer by ID: {e}')
            return None

    def check_duplicate_customer(self, customer_data, exclude_id=None):
        cuit = customer_data['cuit'].strip() if customer_data.get('cuit') else ''
        telefono = customer_data['phone'].strip() if customer_data.get('phone') else ''

        # Verificar CUIT duplicado
        if cuit:
            if exclude_id:
                existing = db.fetch_one(
                    "SELECT id, name FROM customer WHERE cuit = ? AND id != ?", 
                    (cuit, exclude_id)
                )
            else:
                existing = db.fetch_one(
                    "SELECT id, name FROM customer WHERE cuit = ?", 
                    (cuit,)
                )
            if existing:
                return f"Ya existe un cliente con el CUIT '{cuit}': {existing[1]}"

        # Verificar teléfono duplicado
        if telefono:
            if exclude_id:
                existing = db.fetch_one(
                    "SELECT id, name FROM customer WHERE phone = ? AND id != ?", 
                    (telefono, exclude_id)
                )
            else:
                existing = db.fetch_one(
                    "SELECT id, name FROM customer WHERE phone = ?", 
                    (telefono,)
                )
            if existing:
                return f"Ya existe un cliente con el teléfono '{telefono}': {existing[1]}"

        return None

    def add_customer(self, customer_data):
        # Verificar duplicados ANTES de insertar
        duplicate_error = self.check_duplicate_customer(customer_data)
        if duplicate_error:
            raise ValueError(duplicate_error)
        
        # Agregar nuevo cliente a la base de datos
        query = """
            INSERT INTO customer (name, cuit, home, phone, iva_condition, cv, cuig, renspa, establishment)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            customer_data['name'].upper(),
            customer_data['cuit'],
            customer_data['home'].upper(),
            customer_data['phone'],
            customer_data['iva_condition'],
            customer_data.get('cv', ''),
            customer_data.get('cuig', ''),
            customer_data.get('renspa', ''),
            customer_data.get('establishment', '').upper(),
        ]
        try:
            return db.execute_query(query, params)
        except sqlite3.IntegrityError as e: 
            raise ValueError("Ya existe un cliente con alguno de esos datos.")

    def delete_customer(self, customer_id):
        # Eliminar la informacion del cliente
        try:
            query = "DELETE FROM customer where id = ?"
            return db.execute_query(query, (customer_id,))
        except Exception as e: 
            print(f'Error : {e}')
            return None 
    
    def search_customer(self, search_term):
        # Busco a un cliente por nombre o id 
        try:
            if search_term.isdigit():
                query = "SELECT * FROM customer WHERE id = ?"
                return self.db.fetch_all(query, (int(search_term),))
            else:
                query = "SELECT * FROM customer WHERE name LIKE ?"
                return self.db.fetch_all(query, (f"%{search_term.upper()}%",))
        except Exception as e:
            print(f"Error searching customer: {e}")
            return []
            
    # --------------------------------------------------------------------
    # 💳 GESTIÓN DE DEUDAS DE CLIENTES
    # --------------------------------------------------------------------
    ## -- Obtiene todas las deudas de un cliente -- ##
    def get_customer_debts(self, cliente_id):
        query = """
        SELECT 
            id,
            date,
            total,
            estado
        FROM sales
        WHERE cliente_id = ? AND estado IN ('pending', 'partial')
        GROUP BY id
        ORDER BY id DESC;
        """
        rows = self.db.fetch_all(query, (cliente_id,))

        state_map = {
            "pending": "Pendiente",
            "partial": "Pago parcial",
            "paid": "Pagada"
        }

        formatted = []
        for sale_id, date, total, estado in rows:
            pagado = self.pay_model.get_total_amount_of_pay_for_a_sale(sale_id)
            estado_es = state_map.get(estado, estado)
            saldo = Decimal(total) - Decimal(pagado)

            fecha_formateada = iso_to_traditional(date.split()[0]) if date else ""

            formatted.append((sale_id, fecha_formateada, total, pagado, saldo, estado_es))

        return formatted
    
    def get_sale_items(self, sale_id):
        query = """
            SELECT
                s.id,
                s.name,
                s.pack,
                si.quantity, 
                si.price,
                si.subtotal,
                si.observations
            FROM sale_items si
            JOIN stock s ON si.product_id = s.id
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
                total
            FROM sales s
            WHERE s.cliente_id = ? AND s.estado IN ('pending', 'partial')
            GROUP BY s.id
        """

        rows = self.db.fetch_all(query, (cliente_id,))

        total_pending = Decimal('0.00')
        for sale_id, total in rows:
            paid = self.pay_model.get_total_amount_of_pay_for_a_sale(sale_id)
            saldo = Decimal(total) - paid
            if saldo > Decimal('0.00'):
                total_pending += saldo

        return norm_to_2_dec(total_pending)

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
                s.total,
                s.estado,
                COUNT(si.id) AS cant_productos
            FROM sales s
            LEFT JOIN sale_items si ON si.sale_id = s.id
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
                
            total = Decimal(total)
            cant_prod = int(cant_prod) if cant_prod else 0
            
            estado_map = {
                "pending": "Pendiente",
                "partial": "Pago parcial",
                "paid": "Pagada"
            }
            estado_txt = estado_map.get(estado, estado)
            
            fecha_formateada = iso_to_traditional(fecha.split()[0]) if fecha else ""

            movements.append({
                "fecha": fecha_formateada,
                "fecha_original": fecha,
                "tipo": "VENTA",
                "descripcion": f"Venta #{sale_id} · {cant_prod} producto(s) · {estado_txt}",
                "debe": total,
                "haber": Decimal('0.00'),
                "saldo": Decimal('0.00'),
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
                
            monto = Decimal(monto)
            method_txt = method_map.get(method.lower() if method else "", method.capitalize() if method else "Efectivo")
            
            if sale_id:
                desc = f"Pago Venta #{sale_id} · {method_txt}"
            else:
                desc = f"Pago a cuenta · {method_txt}"

            fecha_formateada = iso_to_traditional(fecha.split()[0]) if fecha else ""
            
            movements.append({
                "fecha": fecha_formateada,
                "fecha_original": fecha,
                "tipo": "PAGO",
                "descripcion": desc,
                "debe": Decimal('0.00'),
                "haber": monto,
                "saldo": Decimal('0.00'),
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
                    monto = norm_to_2_dec(monto)
                    
                    if monto > Decimal('0.00'):
                        # Ignorar créditos de sobrepago — ya están reflejados en el pago
                        if reason and reason.startswith("AJUSTE:"):
                            continue
                        
                        desc = f"Nota de crédito"
                        if reason:
                            desc += f" · {reason}"
                        
                        fecha_formateada = iso_to_traditional(fecha.split()[0]) if fecha else ""
                        movements.append({
                            "fecha": fecha_formateada,
                            "fecha_original": fecha,
                            "tipo": "CRÉDITO",
                            "descripcion": desc,
                            "debe": Decimal('0.00'),
                            "haber": monto,
                            "saldo": Decimal('0.00'),
                            "sale_id": sale_id,
                            "referencia": reason or ""
                        })
                    else:
                        pass # Créditos de monto negativo (ajustes por sobrepago) se omiten porque ya afectan el saldo en los pagos
                                        
        except Exception as e:
            print(f"Tabla customer_credit no disponible: {e}")
        
        # ================================================================
        # PASO 5: ORDENAR CRONOLÓGICAMENTE
        # ================================================================
        movements.sort(key=lambda x: (x["fecha_original"], x.get("sale_id", 0) or 0))

        for mov in movements:
            mov.pop("fecha_original", None)

        # ================================================================
        # PASO 6: CALCULAR SALDO ACUMULADO
        # ================================================================
        saldo_acumulado = Decimal('0.00')
        credito_acumulado = Decimal('0.00')

        for mov in movements:
            delta = mov["debe"] - mov["haber"]
            saldo_acumulado += delta
            
            if saldo_acumulado < Decimal('0.00'):
                credito_acumulado += abs(saldo_acumulado)
                saldo_acumulado = Decimal('0.00')
    
        mov["saldo"] = norm_to_2_dec(saldo_acumulado)
        
        # ================================================================
        # PASO 7: RESUMEN (solo cuenta ventas a crédito)
        # ================================================================
        total_debe = sum(norm_to_2_dec(m["debe"]) for m in movements)
        total_haber = sum(norm_to_2_dec(m["haber"]) for m in movements)
        saldo_final = norm_to_2_dec(saldo_acumulado)

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

        saldo_final = norm_to_2_dec(saldo_acumulado)
        credito_final = norm_to_2_dec(credito_acumulado)

        summary = {
            'total_comprado': norm_to_2_dec(total_debe),
            'total_pagado': norm_to_2_dec(total_haber),
            'saldo_a_favor': credito_final,        # ← crédito calculado del historial
            'deuda_pendiente': saldo_final,        # ← nunca baja de 0
            'ventas_pagadas': ventas_pagadas,
            'total_ventas': ventas_totales,
            'ventas_texto': f"{ventas_pagadas}/{ventas_totales} pagadas"
        }

        return movements, summary