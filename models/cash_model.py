"""
Modelo de Caja Diaria
Maneja ingresos, egresos y gastos
"""

from datetime import datetime
from db.database import db as default_db
from decimal import Decimal


class CashModel:
    def __init__(self, db_connection=None):
        self.db = db_connection or default_db
    
    # ================================================================== #
    # GASTOS                                                              #
    # ================================================================== #
    
    def add_expense(self, date, category, description, amount, payment_method='EFECTIVO', observations=''):
        """Registrar un nuevo gasto"""
        query = """
        INSERT INTO cash_expenses (date, category, description, amount, payment_method, observations)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        params = (date, category, description, str(amount), payment_method, observations)
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
    
    def get_cash_summary(self, date):
        """
        Obtener resumen completo de caja para una fecha
        Retorna dict con ingresos, egresos y saldo
        """
        
        # 1. INGRESOS - Ventas del día (pagadas o paid)
        ventas_query = """
        SELECT COALESCE(SUM(CAST(total AS REAL)), 0)
        FROM sales
        WHERE DATE(date) = ?
        AND (estado = 'pagada' OR estado = 'paid')
        """
        ventas = float(self.db.fetch_one(ventas_query, (date,))[0])
        
        # 2. INGRESOS - Cobros a clientes del día
        cobros_query = """
        SELECT COALESCE(SUM(CAST(amount AS REAL)), 0)
        FROM payments
        WHERE DATE(date) = ?
        """
        cobros = float(self.db.fetch_one(cobros_query, (date,))[0])
        
        # 3. EGRESOS - Pagos a proveedores del día
        # Usa purchase_payment.applied_at (fecha real del pago)
        # NO usa supplier_payment.date (fecha de registro del pago, puede ser anterior)
        compras_query = """
        SELECT COALESCE(SUM(CAST(pp.amount_applied AS REAL)), 0)
        FROM purchase_payment pp
        WHERE DATE(pp.applied_at) = ?
        """
        compras = float(self.db.fetch_one(compras_query, (date,))[0])
        
        # 4. EGRESOS - Gastos varios del día
        gastos_query = """
        SELECT COALESCE(SUM(CAST(amount AS REAL)), 0)
        FROM cash_expenses
        WHERE date = ?
        """
        gastos = float(self.db.fetch_one(gastos_query, (date,))[0])
        
        # Calcular totales
        total_ingresos = ventas + cobros
        total_egresos = compras + gastos
        saldo = total_ingresos - total_egresos
        
        return {
            'ingresos': {
                'ventas': round(ventas, 2),
                'cobros': round(cobros, 2),
                'total': round(total_ingresos, 2)
            },
            'egresos': {
                'compras': round(compras, 2),
                'gastos': round(gastos, 2),
                'total': round(total_egresos, 2)
            },
            'saldo': round(saldo, 2),
            'tipo': 'POSITIVO' if saldo >= 0 else 'NEGATIVO'
        }
    
    # ================================================================== #
    # DETALLE DE MOVIMIENTOS                                              #
    # ================================================================== #
    
    def get_movements_detail(self, date):
        """
        Obtener detalle de todos los movimientos del día
        Retorna lista ordenada por hora
        """
        movements = []
        
        # 1. Ventas
        ventas_query = """
        SELECT 
            date,
            'VENTA' as tipo,
            'Venta #' || id as concepto,
            CAST(total AS REAL) as monto,
            '💰' as icono
        FROM sales
        WHERE DATE(date) = ?
        AND (estado = 'pagada' OR estado = 'paid')
        """
        ventas = self.db.fetch_all(ventas_query, (date,))
        movements.extend([(v[0], v[1], v[2], v[3], v[4]) for v in ventas])
        
        # 2. Cobros
        cobros_query = """
        SELECT 
            p.date,
            'COBRO' as tipo,
            'Cliente: ' || COALESCE(c.name, 'Consumidor Final') as concepto,
            CAST(p.amount AS REAL) as monto,
            '💰' as icono
        FROM payments p
        LEFT JOIN customer c ON c.id = p.client_id
        WHERE DATE(p.date) = ?
        """
        cobros = self.db.fetch_all(cobros_query, (date,))
        movements.extend([(c[0], c[1], c[2], c[3], c[4]) for c in cobros])
        
        # 3. Pagos a proveedores (fecha real del pago)
        compras_query = """
        SELECT 
            pp.applied_at as fecha,
            'PAGO PROV' as tipo,
            'Pago ' || sp.method || ' - Compra #' || pp.purchase_id as concepto,
            -CAST(pp.amount_applied AS REAL) as monto,
            '💸' as icono
        FROM purchase_payment pp
        JOIN supplier_payment sp ON sp.id = pp.payment_id
        WHERE DATE(pp.applied_at) = ?
        """
        compras = self.db.fetch_all(compras_query, (date,))
        movements.extend([(c[0], c[1], c[2], c[3], c[4]) for c in compras])
        
        # 4. Gastos
        gastos_query = """
        SELECT 
            created_at,
            'GASTO' as tipo,
            category || ': ' || description as concepto,
            -CAST(amount AS REAL) as monto,
            '💸' as icono
        FROM cash_expenses
        WHERE date = ?
        """
        gastos = self.db.fetch_all(gastos_query, (date,))
        movements.extend([(g[0], g[1], g[2], g[3], g[4]) for g in gastos])
        
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
        """
        cobros = float(self.db.fetch_one(cobros_query, (date_from, date_to))[0])
        
        # Egresos - Pagos a proveedores (fecha real del pago)
        compras_query = """
        SELECT COALESCE(SUM(CAST(pp.amount_applied AS REAL)), 0)
        FROM purchase_payment pp
        WHERE DATE(pp.applied_at) BETWEEN ? AND ?
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