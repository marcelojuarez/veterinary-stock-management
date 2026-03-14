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
        """Obtener ventas del dia (solo de contado)"""
        try:
            ventas_query = """
                SELECT id, total 
                FROM sales 
                WHERE DATE(date) = ?
                """

            cash_summary = Decimal('0.00')
            for ventas in self.db.fetch_all(ventas_query, (date,)):
                if self.customer_model._is_cash_sale(ventas[0]):
                    cash_summary += Decimal(ventas[1])

            return norm_to_2_dec(cash_summary)
        except Exception as e:
            print(f"Error al obtener ventas de contado: {e}")
            return Decimal('0.00')

    def get_payment_client(self, date):
        """Obtener cobros a clientes del día"""
        try:
            cobros_query = """
                SELECT amount 
                FROM payments 
                WHERE DATE(date) = ? 
                AND valid = 1
                """

            cobros_summary = Decimal('0.00')
            for cobros in self.db.fetch_all(cobros_query, (date,)):
                cobros_summary += Decimal(cobros[0])

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
                -- posible validacion adicional: AND valid = 1
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
        saldo = total_ingresos - total_egresos
        
        return {
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
            'saldo': saldo,
            'tipo': 'POSITIVO' if saldo >= 0 else 'NEGATIVO'
        }  
    # ================================================================== #
    # DETALLE DE MOVIMIENTOS                                              #
    # ================================================================== #

    def get_movements_sales(self, date):
        """Obtener los detalles de la ventas del dia"""
        ventas_query = """
            SELECT date, id, total 
            FROM sales 
            WHERE DATE(date) = ? 
            AND estado IN ('pagada', 'paid')
            AND id NOT IN (SELECT sale_id FROM payments)
        """

        return self.db.fetch_all(ventas_query, (date,))

    def get_movements_cobros(self, date):
        query = """
            SELECT p.date, p.amount, COALESCE(c.name, 'Consumidor Final'), p.sale_id
            FROM payments p
            LEFT JOIN customer c ON c.id = p.client_id
            WHERE DATE(p.date) = ?
            AND p.valid = 1
        """
        return self.db.fetch_all(query, (date,))

    def get_movements_compras(self, date):
        query = """
            SELECT sp.date, pp.amount_applied, sp.method, pp.purchase_id, s.name
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

    def get_movements_sales_fiadas(self, date):
        """Ventas fiadas del día (no entran en caja)"""
        query = """
            SELECT date, id, total
            FROM sales
            WHERE DATE(date) = ?
            AND estado IN ('pagada', 'paid')
            AND id IN (SELECT sale_id FROM payments)
        """
        return self.db.fetch_all(query, (date,))
        
    def get_movements_detail(self, date):
        movements = []

        for row in self.get_movements_sales(date):
            movements.append((row[0], 'VENTA', f'Venta #{row[1]}', Decimal(row[2])))

        for row in self.get_movements_sales_fiadas(date):
            movements.append((row[0], 'FIADA', f'Venta #{row[1]} (fiada — cobro pendiente o ya cobrado)', Decimal('0.00')))

        for row in self.get_movements_cobros(date):
            nombre  = row[2]
            sale_id = row[3]
            movements.append((row[0], 'COBRO', f'Cobro cliente: {nombre} — Venta #{sale_id}', Decimal(row[1])))

        for row in self.get_movements_compras(date):
            movements.append((row[0], 'PAGO PROV', f'[{row[4]}] Compra #{row[3]} — {row[2]}', -Decimal(row[1])))

        for row in self.get_movements_gastos(date):
            movements.append((row[0], 'GASTO', f'[{row[2]}] {row[3]}', -Decimal(row[1])))

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