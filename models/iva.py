from db.database import db
from datetime import datetime, timedelta
from decimal import Decimal
from utils.utils import norm_to_2_dec

class IVAModel:
    def __init__(self, db_connection=None):
        self.db = db_connection or db
    
    # ================================================================
    # VENTAS - IVA DÉBITO FISCAL
    # ================================================================
    
    def get_iva_ventas(self, fecha_desde, fecha_hasta):
        """Obtener IVA cobrado en ventas (débito fiscal)"""
        query = """
            SELECT 
                s.id as venta_id,
                s.date as fecha,
                COALESCE(c.name, 'Consumidor Final') as cliente,
                COALESCE(c.cuit, '') as cuit_cliente,
                COALESCE(c.iva_condition, 'Consumidor Final') as condicion_iva,
                si.iva_rate as alicuota_iva,
                SUM(si.subtotal) as neto,
                SUM(si.iva_amount) as iva,
                SUM(si.subtotal + si.iva_amount) as total
            FROM sales s
            LEFT JOIN customer c ON c.id = s.cliente_id
            JOIN sale_items si ON si.sale_id = s.id
            WHERE s.date BETWEEN ? AND ?
            GROUP BY s.id, si.iva_rate
            ORDER BY s.date, s.id
        """
        return self.db.fetch_all(query, (fecha_desde, fecha_hasta))
    
    def get_resumen_iva_ventas(self, fecha_desde, fecha_hasta):
        query = """
            SELECT 
                si.iva_rate as alicuota,
                SUM(si.quantity * si.price) as neto_gravado,
                SUM(si.iva_amount) as iva,
                SUM(si.subtotal) as total,
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
                'neto_gravado': norm_to_2_dec(Decimal(str(row[1] or 0))),
                'iva': norm_to_2_dec(Decimal(str(row[2] or 0))),
                'total': norm_to_2_dec(Decimal(str(row[3] or 0))),
                'operaciones': int(row[4])
            })
        return result
    
    # ================================================================
    # COMPRAS - IVA CRÉDITO FISCAL
    # ================================================================
    
    def get_iva_compras(self, fecha_desde, fecha_hasta):
        query = """
            SELECT 
                p.id as compra_id,
                p.date as fecha,
                COALESCE(s.name, 'Proveedor') as proveedor,
                COALESCE(s.cuit, '') as cuit_proveedor,
                CAST(pi.iva_rate AS REAL) as alicuota_iva,
                SUM(CAST(pi.subtotal AS REAL)) as neto,
                SUM(CAST(pi.iva_amount AS REAL)) as iva,
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
                'neto_gravado': norm_to_2_dec(Decimal(str(row[1] or 0))),
                'iva': norm_to_2_dec(Decimal(str(row[2] or 0))),
                'total': norm_to_2_dec(Decimal(str(row[3] or 0))),
                'operaciones': int(row[4])
            })
        return result
    
    # ================================================================
    # POSICIÓN DE IVA
    # ================================================================
    
    def get_posicion_iva_detallada(self, fecha_desde, fecha_hasta):
        resumen_ventas = self.get_resumen_iva_ventas(fecha_desde, fecha_hasta)
        resumen_compras = self.get_resumen_iva_compras(fecha_desde, fecha_hasta)
        
        alicuotas = set()
        for v in resumen_ventas:
            alicuotas.add(v['alicuota'])
        for c in resumen_compras:
            alicuotas.add(c['alicuota'])
        
        detalle = []
        total_ventas = 0
        total_compras = 0
        
        for alicuota in sorted(alicuotas, reverse=True):
            ventas_alicuota = next((v for v in resumen_ventas if v['alicuota'] == alicuota), None)
            iva_ventas = ventas_alicuota['iva'] if ventas_alicuota else 0
            ventas_neto = ventas_alicuota['neto_gravado'] if ventas_alicuota else 0
            
            compras_alicuota = next((c for c in resumen_compras if c['alicuota'] == alicuota), None)
            iva_compras = compras_alicuota['iva'] if compras_alicuota else 0
            compras_neto = compras_alicuota['neto_gravado'] if compras_alicuota else 0
            
            saldo_alicuota = norm_to_2_dec(iva_ventas - iva_compras)
            
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
        
        saldo_total = norm_to_2_dec(total_ventas - total_compras)
        
        return {
            'detalle': detalle,
            'total_iva_ventas': norm_to_2_dec(total_ventas),
            'total_iva_compras': norm_to_2_dec(total_compras),
            'saldo_total': saldo_total,
            'tipo': 'A PAGAR' if saldo_total > 0 else ('SALDO A FAVOR' if saldo_total < 0 else 'SIN SALDO')
        }
    
    def get_posicion_iva(self, fecha_desde, fecha_hasta):
        query_ventas = """
            SELECT COALESCE(SUM(CAST(si.iva_amount AS REAL)), 0)
            FROM sales s
            JOIN sale_items si ON si.sale_id = s.id
            WHERE s.date BETWEEN ? AND ?
        """
        iva_ventas = norm_to_2_dec(Decimal(str(self.db.fetch_one(query_ventas, (fecha_desde, fecha_hasta))[0])))
        
        query_retenciones = """
            SELECT COALESCE(SUM(CAST(sr.amount AS REAL)), 0)
            FROM sale_retentions sr
            JOIN sales s ON s.id = sr.sale_id
            WHERE sr.tax_type = 'IVA'
            AND s.date BETWEEN ? AND ?
        """
        retenciones_iva = norm_to_2_dec(Decimal(str(self.db.fetch_one(query_retenciones, (fecha_desde, fecha_hasta))[0])))
        
        query_retenciones_iibb = """
            SELECT COALESCE(SUM(CAST(sr.amount AS REAL)), 0)
            FROM sale_retentions sr
            JOIN sales s ON s.id = sr.sale_id
            WHERE sr.tax_type = 'IIBB'
            AND s.date BETWEEN ? AND ?
        """
        retenciones_iibb = norm_to_2_dec(Decimal(str(self.db.fetch_one(query_retenciones_iibb, (fecha_desde, fecha_hasta))[0])))
        
        query_compras = """
            SELECT COALESCE(SUM(CAST(pi.iva_amount AS REAL)), 0)
            FROM purchase p
            JOIN purchase_item pi ON pi.purchase_id = p.id
            WHERE p.date BETWEEN ? AND ?
        """
        iva_compras = norm_to_2_dec(Decimal(str(self.db.fetch_one(query_compras, (fecha_desde, fecha_hasta))[0])))
        
        query_percepciones = """
            SELECT COALESCE(SUM(CAST(ip.amount AS REAL)), 0)
            FROM invoice_perceptions ip
            JOIN supplier_invoice si ON si.id = ip.invoice_id
            WHERE ip.tax_type = 'IVA_PER'
            AND si.date BETWEEN ? AND ?
        """
        percepciones_iva = norm_to_2_dec(Decimal(str(self.db.fetch_one(query_percepciones, (fecha_desde, fecha_hasta))[0])))
        
        query_percepciones_iibb = """
            SELECT COALESCE(SUM(CAST(ip.amount AS REAL)), 0)
            FROM invoice_perceptions ip
            JOIN supplier_invoice si ON si.id = ip.invoice_id
            WHERE ip.tax_type = 'IIBB_PER'
            AND si.date BETWEEN ? AND ?
        """
        percepciones_iibb = norm_to_2_dec(Decimal(str(self.db.fetch_one(query_percepciones_iibb, (fecha_desde, fecha_hasta))[0])))
        
        debito_fiscal = iva_ventas - retenciones_iva
        credito_fiscal = iva_compras + percepciones_iva
        saldo_iva = debito_fiscal - credito_fiscal
        
        return {
            'iva_ventas': norm_to_2_dec(iva_ventas),
            'retenciones_iva': norm_to_2_dec(retenciones_iva),
            'retenciones_iibb': norm_to_2_dec(retenciones_iibb),
            'debito_fiscal': norm_to_2_dec(debito_fiscal),
            'iva_compras': norm_to_2_dec(iva_compras),
            'percepciones_iva': norm_to_2_dec(percepciones_iva),
            'percepciones_iibb': norm_to_2_dec(percepciones_iibb),
            'credito_fiscal': norm_to_2_dec(credito_fiscal),
            'saldo': norm_to_2_dec(saldo_iva),
            'tipo': 'A PAGAR' if saldo_iva > 0 else ('SALDO A FAVOR' if saldo_iva < 0 else 'SIN SALDO')
        }
    
    # ================================================================
    # PERCEPCIONES - DETALLE
    # ================================================================

    def get_percepciones_sufridas(self, fecha_desde, fecha_hasta):
        query = """
            SELECT
                si.date as fecha,
                si.invoice_id as numero_factura,
                COALESCE(s.name, 'Proveedor') as proveedor,
                COALESCE(s.cuit, '') as cuit,
                ip.tax_type,
                CAST(ip.amount AS REAL) as monto
            FROM invoice_perceptions ip
            JOIN supplier_invoice si ON si.id = ip.invoice_id
            LEFT JOIN supplier s ON s.id = si.supplier_id
            WHERE si.date BETWEEN ? AND ?
            ORDER BY si.date, si.id
        """
        return self.db.fetch_all(query, (fecha_desde, fecha_hasta))

    def get_percepciones_efectuadas(self, fecha_desde, fecha_hasta):
        return []

    def get_totales_percepciones(self, fecha_desde, fecha_hasta):
        sufridas = self.get_percepciones_sufridas(fecha_desde, fecha_hasta)
        efectuadas = self.get_percepciones_efectuadas(fecha_desde, fecha_hasta)

        total_sufridas = sum(norm_to_2_dec(Decimal(str(r[5] or 0))) for r in sufridas)
        total_efectuadas = sum(norm_to_2_dec(Decimal(str(r[5] or 0))) for r in efectuadas)

        return norm_to_2_dec(total_sufridas), norm_to_2_dec(total_efectuadas)

    def get_retenciones_sufridas(self, fecha_desde, fecha_hasta):
        query = """
            SELECT
                s.date as fecha,
                s.id as venta_id,
                COALESCE(c.name, 'Consumidor Final') as cliente,
                COALESCE(c.cuit, '') as cuit,
                sr.tax_type,
                COALESCE(sr.certificate_number, '') as certificado,
                CAST(sr.amount AS REAL) as monto
            FROM sale_retentions sr
            JOIN sales s ON s.id = sr.sale_id
            LEFT JOIN customer c ON c.id = s.cliente_id
            WHERE s.date BETWEEN ? AND ?
            ORDER BY s.date, s.id
        """
        return self.db.fetch_all(query, (fecha_desde, fecha_hasta))

    def get_retenciones_efectuadas(self, fecha_desde, fecha_hasta):
        return []

    def get_totales_retenciones(self, fecha_desde, fecha_hasta):
        sufridas = self.get_retenciones_sufridas(fecha_desde, fecha_hasta)
        efectuadas = self.get_retenciones_efectuadas(fecha_desde, fecha_hasta)

        total_sufridas = sum(norm_to_2_dec(Decimal(str(r[6] or 0))) for r in sufridas)
        total_efectuadas = sum(norm_to_2_dec(Decimal(str(r[6] or 0))) for r in efectuadas)

        return norm_to_2_dec(total_sufridas), norm_to_2_dec(total_efectuadas)
    
    # ================================================================
    # UTILIDADES
    # ================================================================
    
    def get_periodo_actual(self):
        hoy = datetime.now()
        primer_dia = hoy.replace(day=1).strftime("%Y-%m-%d")
        if hoy.month == 12:
            ultimo_dia = hoy.replace(day=31).strftime("%Y-%m-%d")
        else:
            siguiente_mes = hoy.replace(month=hoy.month + 1, day=1)
            ultimo_dia = (siguiente_mes - timedelta(days=1)).strftime("%Y-%m-%d")
        return primer_dia, ultimo_dia
    
    def get_periodo_mes(self, mes, anio):
        from calendar import monthrange
        primer_dia = f"{anio}-{mes:02d}-01"
        ultimo_dia_numero = monthrange(anio, mes)[1]
        ultimo_dia = f"{anio}-{mes:02d}-{ultimo_dia_numero:02d}"
        return primer_dia, ultimo_dia
    
    def validar_datos_iva(self):
        query = """
            SELECT id, name, iva
            FROM stock
            WHERE iva IS NULL OR CAST(iva AS REAL) <= 0
        """
        return self.db.fetch_all(query)
    
    def validar_ventas_sin_iva(self):
        query = """
            SELECT COUNT(*) 
            FROM sale_items 
            WHERE iva_amount IS NULL OR iva_amount = 0
        """
        result = self.db.fetch_one(query)
        return result[0] if result else 0