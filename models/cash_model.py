"""
Modelo de Caja Diaria
Maneja ingresos, egresos y gastos
"""

from datetime import datetime
from db.database import db as default_db
from decimal import Decimal
from models.customer import CustomerModel
from utils.utils import norm_to_2_dec


class CashModel:
    def __init__(self, customer_model, db_connection=None):
        self.db = db_connection or default_db
        self.customer_model = customer_model

    # ================================================================== #
    # APERTURA Y CIERRE DE CAJA                                           #
    # ================================================================== #
    
    def get_cash_opening(self, date):
        """Obtener apertura de caja para una fecha"""
        query = """
        SELECT id, date, opening_amount, closing_amount, expected_closing, 
               difference, notes, opened_by, closed_by, opened_at, closed_at, status
        FROM cash_opening
        WHERE date = ?
        """
        result = self.db.fetch_one(query, (date,))
        if result:
            return {
                'id': result[0],
                'date': result[1],
                'opening_amount': Decimal(result[2]),
                'closing_amount': Decimal(result[3]) if result[3] else None,
                'expected_closing': Decimal(result[4]) if result[4] else None,
                'difference': Decimal(result[5]) if result[5] else None,
                'notes': result[6],
                'opened_by': result[7],
                'closed_by': result[8],
                'opened_at': result[9],
                'closed_at': result[10],
                'status': result[11]
            }
        return None
    
    def open_cash(self, date, opening_amount, opened_by='Usuario', notes=''):
        """Abrir caja para una fecha"""
        opened_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        query = """
        INSERT INTO cash_opening (date, opening_amount, opened_by, opened_at, notes, status)
        VALUES (?, ?, ?, ?, ?, 'ABIERTA')
        """
        
        params = (date, str(opening_amount), opened_by, opened_at, notes)
        self.db.execute_query(query, params)
    
    def close_cash(self, date, closing_amount, closed_by='Usuario', notes=''):
        """Cerrar caja para una fecha"""
        # Calcular saldo esperado
        summary = self.get_cash_summary(date)
        opening = self.get_cash_opening(date)
        
        if not opening:
            raise Exception("No hay apertura de caja para esta fecha")
        
        # FIX: Usar saldo_final en lugar de saldo
        expected_closing = summary['saldo_final']
        difference = Decimal(closing_amount) - expected_closing
        closed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        query = """
        UPDATE cash_opening
        SET closing_amount = ?,
            expected_closing = ?,
            difference = ?,
            closed_by = ?,
            closed_at = ?,
            notes = ?,
            status = 'CERRADA'
        WHERE date = ?
        """
        
        params = (
            str(closing_amount),
            str(expected_closing),
            str(difference),
            closed_by,
            closed_at,
            notes,
            date
        )
        
        self.db.execute_query(query, params)
        
        return {
            'expected_closing': expected_closing,
            'actual_closing': Decimal(closing_amount),
            'difference': difference
        }
    
    def is_cash_open(self, date):
        """Verificar si la caja está abierta para una fecha"""
        opening = self.get_cash_opening(date)
        return opening and opening['status'] == 'ABIERTA'
    
    def is_cash_closed(self, date):
        """Verificar si la caja está cerrada para una fecha"""
        opening = self.get_cash_opening(date)
        return opening and opening['status'] == 'CERRADA'
    
    # ================================================================== #
    # GASTOS                                                              
    # ================================================================== #
    
    def add_expense(self, date, category, description, amount, payment_method='EFECTIVO', observations=''):
        """Registrar un nuevo gasto"""
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        query = """
        INSERT INTO cash_expenses (date, category, description, amount, payment_method, observations, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (date, category, description, str(amount), payment_method, observations, created_at)
        self.db.execute_query(query, params)
    
    def get_expenses_by_date(self, date):
        """Obtener gastos de una fecha específica"""
        query = """
        SELECT id, date, category, description, amount, payment_method, observations, created_at
        FROM cash_expenses
        WHERE date = ?
        ORDER BY created_at DESC
        """
        return self.db.fetch_all(query, (date,))
    
    def get_expenses_by_range(self, date_from, date_to):
        """Obtener gastos en un rango de fechas"""
        query = """
        SELECT id, date, category, description, amount, payment_method, observations, created_at
        FROM cash_expenses
        WHERE date BETWEEN ? AND ?
        ORDER BY date DESC, created_at DESC
        """
        return self.db.fetch_all(query, (date_from, date_to))
    
    def delete_expense(self, expense_id):
        """Eliminar un gasto"""
        query = "DELETE FROM cash_expenses WHERE id = ?"
        self.db.execute_query(query, (expense_id,))
    
    # ================================================================== #
    # RESUMEN DE CAJA                                                     #
    # ================================================================== #
    
    def get_cash_sales(self, date):
        """Obtener ventas del dia (solo de contado - pagadas y sin pagos asociados)"""
        try:
            # FIX: Agregar ambos estados 'paid' y 'pagada'
            ventas_query = """
                SELECT id, total 
                FROM sales 
                WHERE DATE(date) = ? 
                AND (estado = 'paid' OR estado = 'pagada')
                """

            cash_summary = Decimal('0.00')
            for ventas in self.db.fetch_all(ventas_query, (date,)):
                # Verificar que sea venta de contado (no fiada)
                if self.customer_model._is_cash_sale(ventas[0]):
                    cash_summary += Decimal(ventas[1])

            return norm_to_2_dec(cash_summary)
        except Exception as e:
            print(f"Error al obtener ventas de contado: {e}")
            return Decimal('0.00')

    def get_payment_client(self, date):
        """Obtener cobros a clientes del día (monto REAL ingresado, incluyendo cheques completos)"""
        try:
            # Query que considera el monto real del cheque cuando existe
            cobros_query = """
                SELECT 
                    p.id,
                    p.amount as amount_applied,
                    p.method,
                    p.check_id,
                    c.amount as check_amount
                FROM payments p
                LEFT JOIN checks c ON c.id = p.check_id
                WHERE DATE(p.date) = ? 
                AND p.valid = 1
            """

            cobros_summary = Decimal('0.00')
            
            for pago in self.db.fetch_all(cobros_query, (date,)):
                payment_id = pago[0]
                amount_applied = Decimal(pago[1])
                method = pago[2]
                check_id = pago[3]
                check_amount = pago[4]
                
                # Si es pago con cheque, usar el monto del cheque (monto REAL que ingresó)
                if check_id and check_amount:
                    cobros_summary += Decimal(check_amount)
                else:
                    # Si es efectivo/transferencia, usar el monto aplicado
                    cobros_summary += amount_applied

            return norm_to_2_dec(cobros_summary)
            
        except Exception as e:
            print(f"Error al obtener cobros a clientes: {e}")
            return Decimal('0.00')


    def get_supplier_payments(self, date):
        """Obtener pagos a proveedores del día (fecha real del pago)"""
        try:
            compras_query = """
                SELECT amount
                FROM supplier_payment
                WHERE DATE(date) = ?
            """

            compras_summary = Decimal('0.00')
            for compras in self.db.fetch_all(compras_query, (date,)):
                compras_summary += Decimal(compras[0])

            return norm_to_2_dec(compras_summary)
        
        except Exception as e:
            print(f"Error al obtener pagos a proveedores: {e}")
            return Decimal('0.00')

    def get_cash_expenses(self, date):
        """Obtener gastos varios del día"""
        try:
            gastos_query = """
                SELECT amount
                FROM cash_expenses
                WHERE date = ?
            """

            gastos_summary = Decimal('0.00')
            for gastos in self.db.fetch_all(gastos_query, (date,)):
                gastos_summary += Decimal(gastos[0])

            return norm_to_2_dec(gastos_summary)
        
        except Exception as e:
            print(f"Error al obtener gastos varios: {e}")
            return Decimal('0.00')
        

    def get_cash_summary(self, date):
        """
        Obtener resumen completo de caja para una fecha
        Retorna dict con ingresos, egresos y saldo
        """
        # 0. SALDO INICIAL - Apertura de caja
        opening = self.get_cash_opening(date)
        saldo_inicial = opening['opening_amount'] if opening else Decimal('0.00')
        
        # 1. INGRESOS - Ventas del día (solo contado)
        ventas = self.get_cash_sales(date)
        
        # 2. INGRESOS - Cobros a clientes del día
        cobros = self.get_payment_client(date)
        
        # 3. EGRESOS - Pagos a proveedores del día
        compras = self.get_supplier_payments(date)
        
        # 4. EGRESOS - Gastos varios del día
        gastos = self.get_cash_expenses(date)
        
        # Calcular totales
        total_ingresos = ventas + cobros
        total_egresos = compras + gastos
        saldo_movimientos = total_ingresos - total_egresos
        saldo_final = saldo_inicial + saldo_movimientos
        
        return {
            'saldo_inicial': saldo_inicial,
            'ingresos': {
                'ventas': ventas,
                'cobros': cobros,
                'total': total_ingresos
            },
            'egresos': {
                'compras': compras,
                'gastos': gastos,
                'total': total_egresos
            },
            'saldo_movimientos': saldo_movimientos,
            'saldo_final': saldo_final,
            'saldo': saldo_movimientos,  # Mantener por compatibilidad
            'tipo': 'POSITIVO' if saldo_final >= 0 else 'NEGATIVO',
            'caja_abierta': opening is not None and opening['status'] == 'ABIERTA',
            'caja_cerrada': opening is not None and opening['status'] == 'CERRADA'
        }
    
    # ================================================================== #
    # DETALLE DE MOVIMIENTOS                                              #
    # ================================================================== #

    def get_movements_sales(self, date):
        """Obtener los detalles de la ventas del dia (solo contado)"""
        ventas_query = """
            SELECT date, id, total 
            FROM sales 
            WHERE DATE(date) = ? 
            AND (estado = 'pagada' OR estado = 'paid')
            AND id NOT IN (SELECT sale_id FROM payments)
        """
        return self.db.fetch_all(ventas_query, (date,))

    def get_movements_cobros(self, date):
        """Obtener cobros del día (con monto real de cheques)"""
        query = """
            SELECT 
                p.date, 
                p.amount as amount_applied,
                COALESCE(c.name, 'Consumidor Final') as client_name,
                p.sale_id,
                p.method,
                p.check_id,
                ch.amount as check_amount,
                ch.number as check_number
            FROM payments p
            LEFT JOIN customer c ON c.id = p.client_id
            LEFT JOIN checks ch ON ch.id = p.check_id
            WHERE DATE(p.date) = ?
            AND p.valid = 1
        """
        return self.db.fetch_all(query, (date,))

    def get_movements_compras(self, date):
        """Obtener pagos a proveedores del día"""
        query = """
            SELECT 
                COALESCE(sp.created_at, sp.date || ' 00:00:00') as datetime,
                pp.amount_applied, 
                sp.method, 
                pp.purchase_id, 
                s.name
            FROM purchase_payment pp
            JOIN supplier_payment sp ON sp.id = pp.payment_id
            JOIN supplier s ON s.id = sp.supplier_id
            WHERE DATE(sp.date) = ?
        """
        return self.db.fetch_all(query, (date,))

    def get_movements_gastos(self, date):
        """Gastos varios del día"""
        query = """
            SELECT created_at, amount, category, description
            FROM cash_expenses
            WHERE date = ?
        """
        return self.db.fetch_all(query, (date,))
        
    def get_movements_detail(self, date):
        """Obtener detalle completo de movimientos del día"""
        movements = []

        # Ventas de contado
        for row in self.get_movements_sales(date):
            movements.append((row[0], 'VENTA', f'Venta #{row[1]}', Decimal(row[2])))

        # Cobros (con monto real de cheques)
        for row in self.get_movements_cobros(date):
            fecha = row[0]
            amount_applied = Decimal(row[1])
            client_name = row[2]
            sale_id = row[3]
            method = row[4]
            check_id = row[5]
            check_amount = row[6] if row[6] else None
            check_number = row[7] if row[7] else None
            
            # Determinar monto real y concepto
            if check_id and check_amount:
                # Pago con cheque - mostrar monto total del cheque
                monto_real = Decimal(check_amount)
                concepto = f'Cobro cliente: {client_name} — Venta #{sale_id} — Cheque #{check_number}'
                
                # Si hay diferencia, indicar saldo a favor
                diferencia = monto_real - amount_applied
                if diferencia > 0:
                    concepto += f' — Saldo a favor: ${diferencia:,.2f}'
            else:
                # Pago en efectivo/transferencia - monto aplicado
                monto_real = amount_applied
                concepto = f'Cobro cliente: {client_name} — Venta #{sale_id}'
            
            movements.append((fecha, 'COBRO', concepto, monto_real))

        # Pagos a proveedores
        for row in self.get_movements_compras(date):
            movements.append((row[0], 'PAGO PROV', f'[{row[4]}] Compra #{row[3]} — {row[2]}', -Decimal(row[1])))

        # Gastos varios
        for row in self.get_movements_gastos(date):
            movements.append((row[0], 'GASTO', f'[{row[2]}] {row[3]}', -Decimal(row[1])))

        # Ordenar por fecha/hora
        movements.sort(key=lambda x: x[0])
        return movements

    # ================================================================== #
    # CATEGORÍAS DE GASTOS                                                #
    # ================================================================== #
    
    @staticmethod
    def get_expense_categories():
        """Retornar categorías predefinidas de gastos"""
        return [
            "Servicios",           # Luz, agua, gas, internet, teléfono
            "Alquileres",          # Alquiler del local
            "Sueldos",             # Salarios del personal
            "Impuestos",           # Tasas, impuestos varios
            "Mantenimiento",       # Reparaciones, mantenimiento
            "Insumos",             # Papelería, limpieza, etc.
            "Transporte",          # Combustible, fletes
            "Honorarios",          # Contador, abogado, etc.
            "Otros"                # Gastos varios
        ]
    
    @staticmethod
    def get_payment_methods():
        """Retornar métodos de pago"""
        return [
            "Efectivo",
            "Transferencia",
            "Tarjeta Débito",
            "Tarjeta Crédito",
            "Cheque"
        ]
    
    # ================================================================== #
    # ESTADÍSTICAS                                                        #
    # ================================================================== #
    
    def get_period_summary(self, date_from, date_to):
        """Resumen de un período (semana, mes, etc.)"""
        
        # Ingresos
        ventas_query = """
        SELECT COALESCE(SUM(CAST(total AS REAL)), 0)
        FROM sales
        WHERE DATE(date) BETWEEN ? AND ?
        AND (estado = 'pagada' OR estado = 'paid')
        """
        ventas = float(self.db.fetch_one(ventas_query, (date_from, date_to))[0])
        
        cobros_query = """
        SELECT COALESCE(SUM(CAST(amount AS REAL)), 0)
        FROM payments
        WHERE DATE(date) BETWEEN ? AND ?
        AND valid = 1
        """
        cobros = float(self.db.fetch_one(cobros_query, (date_from, date_to))[0])
        
        # Egresos - Pagos a proveedores (fecha real del pago)
        # FIX: Usar sp.date en lugar de pp.applied_at
        compras_query = """
        SELECT COALESCE(SUM(CAST(sp.amount AS REAL)), 0)
        FROM supplier_payment sp
        WHERE DATE(sp.date) BETWEEN ? AND ?
        """
        compras = float(self.db.fetch_one(compras_query, (date_from, date_to))[0])
        
        gastos_query = """
        SELECT COALESCE(SUM(CAST(amount AS REAL)), 0)
        FROM cash_expenses
        WHERE date BETWEEN ? AND ?
        """
        gastos = float(self.db.fetch_one(gastos_query, (date_from, date_to))[0])
        
        # Totales
        total_ingresos = ventas + cobros
        total_egresos = compras + gastos
        saldo = total_ingresos - total_egresos
        
        return {
            'ventas': round(ventas, 2),
            'cobros': round(cobros, 2),
            'total_ingresos': round(total_ingresos, 2),
            'compras': round(compras, 2),
            'gastos': round(gastos, 2),
            'total_egresos': round(total_egresos, 2),
            'saldo': round(saldo, 2)
        }
    
    def get_expenses_by_category(self, date_from, date_to):
        """Gastos agrupados por categoría en un período"""
        query = """
        SELECT 
            category,
            COUNT(*) as cantidad,
            SUM(CAST(amount AS REAL)) as total
        FROM cash_expenses
        WHERE date BETWEEN ? AND ?
        GROUP BY category
        ORDER BY total DESC
        """
        return self.db.fetch_all(query, (date_from, date_to))