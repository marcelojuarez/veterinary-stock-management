from db.database import db
from datetime import datetime, timedelta

class IVAModel:
    def __init__(self, db_connection=None):
        self.db = db_connection or db
    
    # ================================================================
    # VENTAS - IVA DÉBITO FISCAL
    # ================================================================
    
    def get_iva_ventas(self, fecha_desde, fecha_hasta):
        """
        Obtener IVA cobrado en ventas (débito fiscal)
        ACTUALIZADO: Usa campos iva_rate e iva_amount guardados
        """
        query = """
            SELECT 
                s.id as venta_id,
                s.date as fecha,
                COALESCE(c.nombre, 'Consumidor Final') as cliente,
                COALESCE(c.cuit, '') as cuit_cliente,
                COALESCE(c.condicion_iva, 'Consumidor Final') as condicion_iva,
                si.iva_rate as alicuota_iva,

                -- Neto real
                SUM(si.subtotal - si.iva_amount) as neto,

                -- IVA real
                SUM(si.iva_amount) as iva,

                -- Total CORRECTO
                SUM(si.subtotal) as total

            FROM sales s
            LEFT JOIN clientes c ON c.id = s.cliente_id
            JOIN sale_items si ON si.sale_id = s.id
            WHERE s.date BETWEEN ? AND ?
            GROUP BY s.id, si.iva_rate
            ORDER BY s.date, s.id;
        """
        return self.db.fetch_all(query, (fecha_desde, fecha_hasta))
    
    def get_resumen_iva_ventas(self, fecha_desde, fecha_hasta):
        """
        Resumen de IVA ventas por alícuota
        ACTUALIZADO: Usa campos guardados
        """
        query = """
            SELECT 
                si.iva_rate as alicuota,
                
                -- Neto gravado
                SUM(si.quantity * si.price) as neto_gravado,
                
                -- IVA - DIRECTO
                SUM(si.iva_amount) as iva,
                
                -- Total
                SUM(si.subtotal) as total,
                
                -- Cantidad de operaciones
                COUNT(DISTINCT s.id) as cantidad_operaciones
                
            FROM sales s
            JOIN sale_items si ON si.sale_id = s.id
            WHERE s.date BETWEEN ? AND ?
            GROUP BY si.iva_rate
            ORDER BY si.iva_rate DESC
        """
        rows = self.db.fetch_all(query, (fecha_desde, fecha_hasta))
        
        result = []
        for row in rows:
            result.append({
                'alicuota': f"{float(row[0]):.1f}%" if row[0] else "0.0%",
                'neto_gravado': round(float(row[1] or 0), 2),
                'iva': round(float(row[2] or 0), 2),
                'total': round(float(row[3] or 0), 2),
                'operaciones': int(row[4])
            })
        
        return result
    
    # ================================================================
    # COMPRAS - IVA CRÉDITO FISCAL
    # ================================================================
    
    def get_iva_compras(self, fecha_desde, fecha_hasta):
        """
        Obtener IVA pagado en compras (crédito fiscal)
        ACTUALIZADO: Conversión segura de TEXT a REAL
        """
        query = """
            SELECT 
                p.id as compra_id,
                p.date as fecha,
                COALESCE(s.name, 'Proveedor') as proveedor,
                COALESCE(s.cuit, '') as cuit_proveedor,
                CAST(pi.iva_rate AS REAL) as alicuota_iva,
                
                -- Neto (subtotal sin IVA)
                SUM(CAST(pi.subtotal AS REAL)) as neto,
                
                -- IVA
                SUM(CAST(pi.iva_amount AS REAL)) as iva,
                
                -- Total
                SUM(CAST(pi.total AS REAL)) as total
                
            FROM purchase p
            LEFT JOIN supplier s ON s.id = p.supplier_id
            JOIN purchase_item pi ON pi.purchase_id = p.id
            WHERE p.date BETWEEN ? AND ?
            GROUP BY p.id, pi.iva_rate
            ORDER BY p.date, p.id
        """
        return self.db.fetch_all(query, (fecha_desde, fecha_hasta))
    
    def get_resumen_iva_compras(self, fecha_desde, fecha_hasta):
        """
        Resumen de IVA compras por alícuota
        ACTUALIZADO: Conversión segura de TEXT a REAL
        """
        query = """
            SELECT 
                CAST(pi.iva_rate AS REAL) as alicuota,
                SUM(CAST(pi.subtotal AS REAL)) as neto_gravado,
                SUM(CAST(pi.iva_amount AS REAL)) as iva,
                SUM(CAST(pi.total AS REAL)) as total,
                COUNT(DISTINCT p.id) as cantidad_operaciones
            FROM purchase p
            JOIN purchase_item pi ON pi.purchase_id = p.id
            WHERE p.date BETWEEN ? AND ?
            GROUP BY pi.iva_rate
            ORDER BY CAST(pi.iva_rate AS REAL) DESC
        """
        rows = self.db.fetch_all(query, (fecha_desde, fecha_hasta))
        
        result = []
        for row in rows:
            result.append({
                'alicuota': f"{float(row[0] or 0):.1f}%",
                'neto_gravado': round(float(row[1] or 0), 2),
                'iva': round(float(row[2] or 0), 2),
                'total': round(float(row[3] or 0), 2),
                'operaciones': int(row[4])
            })
        
        return result
    
    # ================================================================
    # POSICIÓN DE IVA - SALDO
    # ================================================================
    
    def get_posicion_iva(self, fecha_desde, fecha_hasta):
        """
        Calcular posición de IVA del periodo
        ACTUALIZADO: Usa campos guardados directamente
        """
        # Total IVA ventas (débito fiscal)
        ventas_query = """
            SELECT COALESCE(SUM(si.iva_amount), 0) as total_iva
            FROM sales s
            JOIN sale_items si ON si.sale_id = s.id
            WHERE s.date BETWEEN ? AND ?
        """
        iva_ventas_row = self.db.fetch_one(ventas_query, (fecha_desde, fecha_hasta))
        iva_ventas = round(float(iva_ventas_row[0] or 0), 2)
        
        # Total IVA compras (crédito fiscal)
        compras_query = """
            SELECT COALESCE(SUM(CAST(pi.iva_amount AS REAL)), 0) as total_iva
            FROM purchase p
            JOIN purchase_item pi ON pi.purchase_id = p.id
            WHERE p.date BETWEEN ? AND ?
        """
        iva_compras_row = self.db.fetch_one(compras_query, (fecha_desde, fecha_hasta))
        iva_compras = round(float(iva_compras_row[0] or 0), 2)
        
        # Saldo
        saldo = round(iva_ventas - iva_compras, 2)
        
        return {
            'iva_ventas': iva_ventas,
            'iva_compras': iva_compras,
            'saldo': saldo,
            'tipo': 'A PAGAR' if saldo > 0 else ('SALDO A FAVOR' if saldo < 0 else 'SIN SALDO')
        }
    
    def get_posicion_iva_detallada(self, fecha_desde, fecha_hasta):
        """
        Posición de IVA con detalle por alícuota
        ACTUALIZADO: Manejo consistente de alícuotas
        """
        resumen_ventas = self.get_resumen_iva_ventas(fecha_desde, fecha_hasta)
        resumen_compras = self.get_resumen_iva_compras(fecha_desde, fecha_hasta)
        
        # Agrupar por alícuota
        alicuotas = set()
        for v in resumen_ventas:
            alicuotas.add(v['alicuota'])
        for c in resumen_compras:
            alicuotas.add(c['alicuota'])
        
        detalle = []
        total_ventas = 0
        total_compras = 0
        
        for alicuota in sorted(alicuotas, reverse=True):
            # Buscar datos de ventas
            ventas_alicuota = next((v for v in resumen_ventas if v['alicuota'] == alicuota), None)
            iva_ventas = ventas_alicuota['iva'] if ventas_alicuota else 0
            ventas_neto = ventas_alicuota['neto_gravado'] if ventas_alicuota else 0
            
            # Buscar datos de compras
            compras_alicuota = next((c for c in resumen_compras if c['alicuota'] == alicuota), None)
            iva_compras = compras_alicuota['iva'] if compras_alicuota else 0
            compras_neto = compras_alicuota['neto_gravado'] if compras_alicuota else 0
            
            saldo_alicuota = round(iva_ventas - iva_compras, 2)
            
            detalle.append({
                'alicuota': alicuota,
                'ventas_neto': ventas_neto,
                'iva_ventas': iva_ventas,
                'compras_neto': compras_neto,
                'iva_compras': iva_compras,
                'saldo': saldo_alicuota
            })
            
            total_ventas += iva_ventas
            total_compras += iva_compras
        
        saldo_total = round(total_ventas - total_compras, 2)
        
        return {
            'detalle': detalle,
            'total_iva_ventas': round(total_ventas, 2),
            'total_iva_compras': round(total_compras, 2),
            'saldo_total': saldo_total,
            'tipo': 'A PAGAR' if saldo_total > 0 else ('SALDO A FAVOR' if saldo_total < 0 else 'SIN SALDO')
        }
    
    # ================================================================
    # UTILIDADES
    # ================================================================
    
    def get_periodo_actual(self):
        """Obtener primer y último día del mes actual"""
        hoy = datetime.now()
        primer_dia = hoy.replace(day=1).strftime("%Y-%m-%d")
        
        if hoy.month == 12:
            ultimo_dia = hoy.replace(day=31).strftime("%Y-%m-%d")
        else:
            siguiente_mes = hoy.replace(month=hoy.month + 1, day=1)
            ultimo_dia = (siguiente_mes - timedelta(days=1)).strftime("%Y-%m-%d")
        
        return primer_dia, ultimo_dia
    
    def get_periodo_mes(self, mes, anio):
        """
        Obtener primer y último día de un mes específico
        mes: 1-12
        anio: ej. 2026
        """
        from calendar import monthrange
        
        primer_dia = f"{anio}-{mes:02d}-01"
        ultimo_dia_numero = monthrange(anio, mes)[1]
        ultimo_dia = f"{anio}-{mes:02d}-{ultimo_dia_numero:02d}"
        
        return primer_dia, ultimo_dia
    
    def validar_datos_iva(self):
        """
        Validar que todos los productos tengan IVA configurado
        """
        query = """
            SELECT id, name, iva
            FROM stock
            WHERE iva IS NULL OR CAST(iva AS REAL) <= 0
        """
        return self.db.fetch_all(query)
    
    def validar_ventas_sin_iva(self):
        """
        Detectar ventas que no tienen IVA guardado
        """
        query = """
            SELECT COUNT(*) 
            FROM sale_items 
            WHERE iva_amount IS NULL OR iva_amount = 0
        """
        result = self.db.fetch_one(query)
        return result[0] if result else 0