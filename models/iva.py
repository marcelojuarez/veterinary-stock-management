from db.database import db
from datetime import datetime, timedelta

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
                COALESCE(c.nombre, 'Consumidor Final') as cliente,
                COALESCE(c.cuit, '') as cuit_cliente,
                COALESCE(c.condicion_iva, 'Consumidor Final') as condicion_iva,
                si.iva_rate as alicuota_iva,
                SUM(si.subtotal) as neto,
                SUM(si.iva_amount) as iva,
                SUM(si.subtotal + si.iva_amount) as total
            FROM sales s
            LEFT JOIN clientes c ON c.id = s.cliente_id
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
                'neto_gravado': round(float(row[1] or 0), 2),
                'iva': round(float(row[2] or 0), 2),
                'total': round(float(row[3] or 0), 2),
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
    
    def get_posicion_iva(self, fecha_desde, fecha_hasta):
        query_ventas = """
            SELECT COALESCE(SUM(CAST(si.iva_amount AS REAL)), 0)
            FROM sales s
            JOIN sale_items si ON si.sale_id = s.id
            WHERE s.date BETWEEN ? AND ?
        """
        iva_ventas = float(self.db.fetch_one(query_ventas, (fecha_desde, fecha_hasta))[0])
        
        query_retenciones = """
            SELECT COALESCE(SUM(CAST(sr.amount AS REAL)), 0)
            FROM sale_retentions sr
            JOIN sales s ON s.id = sr.sale_id
            WHERE sr.tax_type = 'IVA'
            AND s.date BETWEEN ? AND ?
        """
        retenciones_iva = float(self.db.fetch_one(query_retenciones, (fecha_desde, fecha_hasta))[0])
        
        query_retenciones_iibb = """
            SELECT COALESCE(SUM(CAST(sr.amount AS REAL)), 0)
            FROM sale_retentions sr
            JOIN sales s ON s.id = sr.sale_id
            WHERE sr.tax_type = 'IIBB'
            AND s.date BETWEEN ? AND ?
        """
        retenciones_iibb = float(self.db.fetch_one(query_retenciones_iibb, (fecha_desde, fecha_hasta))[0])
        
        query_compras = """
            SELECT COALESCE(SUM(CAST(pi.iva_amount AS REAL)), 0)
            FROM purchase p
            JOIN purchase_item pi ON pi.purchase_id = p.id
            WHERE p.date BETWEEN ? AND ?
        """
        iva_compras = float(self.db.fetch_one(query_compras, (fecha_desde, fecha_hasta))[0])
        
        query_percepciones = """
            SELECT COALESCE(SUM(CAST(ip.amount AS REAL)), 0)
            FROM invoice_perceptions ip
            JOIN supplier_invoice si ON si.id = ip.invoice_id
            WHERE ip.tax_type = 'IVA_PER'
            AND si.date BETWEEN ? AND ?
        """
        percepciones_iva = float(self.db.fetch_one(query_percepciones, (fecha_desde, fecha_hasta))[0])
        
        query_percepciones_iibb = """
            SELECT COALESCE(SUM(CAST(ip.amount AS REAL)), 0)
            FROM invoice_perceptions ip
            JOIN supplier_invoice si ON si.id = ip.invoice_id
            WHERE ip.tax_type = 'IIBB_PER'
            AND si.date BETWEEN ? AND ?
        """
        percepciones_iibb = float(self.db.fetch_one(query_percepciones_iibb, (fecha_desde, fecha_hasta))[0])
        
        debito_fiscal = iva_ventas - retenciones_iva
        credito_fiscal = iva_compras + percepciones_iva
        saldo_iva = debito_fiscal - credito_fiscal
        
        return {
            'iva_ventas': round(iva_ventas, 2),
            'retenciones_iva': round(retenciones_iva, 2),
            'retenciones_iibb': round(retenciones_iibb, 2),
            'debito_fiscal': round(debito_fiscal, 2),
            'iva_compras': round(iva_compras, 2),
            'percepciones_iva': round(percepciones_iva, 2),
            'percepciones_iibb': round(percepciones_iibb, 2),
            'credito_fiscal': round(credito_fiscal, 2),
            'saldo': round(saldo_iva, 2),
            'tipo': 'A PAGAR' if saldo_iva > 0 else ('SALDO A FAVOR' if saldo_iva < 0 else 'SIN SALDO')
        }
    
    # ================================================================
    # PERCEPCIONES - DETALLE
    # ================================================================

    def get_percepciones_sufridas(self, fecha_desde, fecha_hasta):
        """
        Percepciones que nos cobraron los proveedores en facturas.
        Retorna: (fecha, invoice_id, proveedor, cuit, tax_type, amount)
        """
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
        """
        Percepciones que nosotros cobramos a clientes en ventas.
        Si aún no tenés tabla propia, retorna lista vacía.
        Si tenés tabla sale_perceptions, descomentar la query.
        Retorna: (fecha, sale_id, cliente, cuit, tax_type, amount)
        """
        # Si tenés tabla sale_perceptions:
        # query = """
        #     SELECT
        #         s.date,
        #         s.id,
        #         COALESCE(c.nombre, 'Consumidor Final'),
        #         COALESCE(c.cuit, ''),
        #         sp.tax_type,
        #         CAST(sp.amount AS REAL)
        #     FROM sale_perceptions sp
        #     JOIN sales s ON s.id = sp.sale_id
        #     LEFT JOIN clientes c ON c.id = s.cliente_id
        #     WHERE s.date BETWEEN ? AND ?
        #     ORDER BY s.date, s.id
        # """
        # return self.db.fetch_all(query, (fecha_desde, fecha_hasta))
        return []

    def get_totales_percepciones(self, fecha_desde, fecha_hasta):
        """Totales para las cards"""
        sufridas = self.get_percepciones_sufridas(fecha_desde, fecha_hasta)
        efectuadas = self.get_percepciones_efectuadas(fecha_desde, fecha_hasta)

        total_sufridas = sum(float(r[5] or 0) for r in sufridas)
        total_efectuadas = sum(float(r[5] or 0) for r in efectuadas)

        return round(total_sufridas, 2), round(total_efectuadas, 2)

    # ================================================================
    # RETENCIONES - DETALLE
    # ================================================================

    def get_retenciones_sufridas(self, fecha_desde, fecha_hasta):
        """
        Retenciones que los clientes nos hicieron en ventas.
        Retorna: (fecha, sale_id, cliente, cuit, tax_type, certificate_number, amount)
        """
        query = """
            SELECT
                s.date as fecha,
                s.id as venta_id,
                COALESCE(c.nombre, 'Consumidor Final') as cliente,
                COALESCE(c.cuit, '') as cuit,
                sr.tax_type,
                COALESCE(sr.certificate_number, '') as certificado,
                CAST(sr.amount AS REAL) as monto
            FROM sale_retentions sr
            JOIN sales s ON s.id = sr.sale_id
            LEFT JOIN clientes c ON c.id = s.cliente_id
            WHERE s.date BETWEEN ? AND ?
            ORDER BY s.date, s.id
        """
        return self.db.fetch_all(query, (fecha_desde, fecha_hasta))

    def get_retenciones_efectuadas(self, fecha_desde, fecha_hasta):
        """
        Retenciones que nosotros le hicimos al proveedor en compras.
        Si aún no tenés tabla, retorna lista vacía.
        Retorna: (fecha, purchase_id, proveedor, cuit, tax_type, certificate_number, amount)
        """
        # Si tenés tabla purchase_retentions:
        # query = """
        #     SELECT
        #         p.date,
        #         p.id,
        #         COALESCE(s.name, 'Proveedor'),
        #         COALESCE(s.cuit, ''),
        #         pr.tax_type,
        #         COALESCE(pr.certificate_number, ''),
        #         CAST(pr.amount AS REAL)
        #     FROM purchase_retentions pr
        #     JOIN purchase p ON p.id = pr.purchase_id
        #     LEFT JOIN supplier s ON s.id = p.supplier_id
        #     WHERE p.date BETWEEN ? AND ?
        #     ORDER BY p.date, p.id
        # """
        # return self.db.fetch_all(query, (fecha_desde, fecha_hasta))
        return []

    def get_totales_retenciones(self, fecha_desde, fecha_hasta):
        """Totales para las cards"""
        sufridas = self.get_retenciones_sufridas(fecha_desde, fecha_hasta)
        efectuadas = self.get_retenciones_efectuadas(fecha_desde, fecha_hasta)

        total_sufridas = sum(float(r[6] or 0) for r in sufridas)
        total_efectuadas = sum(float(r[6] or 0) for r in efectuadas)

        return round(total_sufridas, 2), round(total_efectuadas, 2)
    
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