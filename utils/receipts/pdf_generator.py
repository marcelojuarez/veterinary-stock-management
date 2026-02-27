"""
Generador de comprobantes A4 - Estilo Ticket profesional (Blanco y Negro)
Con detalle de productos vendidos
Ubicación: utils/receipts/pdf_generator.py
"""

import os
from datetime import datetime
from decimal import Decimal
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from utils.utils import format_currency
from reportlab.lib.pagesizes import A4

from utils.receipts.paths import a4_pago_venta, a4_pago_global


# ============================================================
#               RECIBO DE PAGO INDIVIDUAL
# ============================================================
def generate_payment_receipt(*, file_path, client_name, sale_id, payment_amount, method, sale_info, payments, sale_items=None):
    """
    Genera comprobante A4 de pago de venta individual.
    Estilo ticket profesional en blanco y negro.
    Incluye detalle de productos.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Configuración de página
    W, H = A4
    margin = 45 * mm
    
    c = canvas.Canvas(file_path, pagesize=A4)
    y = H - 35 * mm
    
    # Colores (blanco y negro)
    black = colors.black
    dark_gray = colors.HexColor("#333333")
    gray = colors.HexColor("#666666")
    light_gray = colors.HexColor("#cccccc")
    
    # ================================================================
    # FUNCIONES HELPER
    # ================================================================
    def draw_text_left(text, size=10, bold=False, extra_spacing=0):
        nonlocal y
        font = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font, size)
        c.setFillColor(black)
        c.drawString(margin, y, text)
        y -= size + 8 + extra_spacing  # Espacio adicional opcional
    
    def draw_text_center(text, size=10, bold=False, extra_spacing=0):
        nonlocal y
        font = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font, size)
        c.setFillColor(black)
        c.drawCentredString(W / 2, y, text)
        y -= size + 8 + extra_spacing  # Espacio adicional opcional
    
    def draw_text_right(text, size=10, bold=False):
        nonlocal y
        font = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font, size)
        c.setFillColor(gray)
        c.drawRightString(W - margin, y, text)
    
    def draw_line_lr(left, right, size=10, bold_l=False, bold_r=False, extra_spacing=0):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold_l else "Helvetica", size)
        c.setFillColor(black)
        c.drawString(margin, y, left)
        c.setFont("Helvetica-Bold" if bold_r else "Helvetica", size)
        c.drawRightString(W - margin, y, right)
        y -= size + 8 + extra_spacing  # Espacio adicional opcional
    
    def draw_separator(dashed=False, thick=False, extra_spacing=12):
        nonlocal y
        y -= 4
        c.setStrokeColor(black if thick else light_gray)
        c.setLineWidth(1.5 if thick else 0.5)
        if dashed:
            c.setDash(3, 3)
        else:
            c.setDash()
        c.line(margin, y, W - margin, y)
        c.setDash()
        y -= extra_spacing
    
    def draw_pill(text):
        nonlocal y
        pill_width = 160
        pill_height = 18
        x = W - margin - pill_width
        c.setFillColor(black)
        c.roundRect(x, y - 3, pill_width, pill_height, 3, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x + pill_width/2, y + 3, text)
        c.setFillColor(black)
        y -= 2
    
    # ================================================================
    # ENCABEZADO
    # ================================================================
    draw_text_left("ORIGINAL", 8, bold=True)
    y += 15
    draw_pill("COMPROBANTE DE PAGO")
    y -= 20
    
    now = datetime.now()
    draw_text_right(f"{now:%d/%m/%Y} - {now:%H:%M} h", 8)
    y -= 5 

    draw_separator(thick=True, extra_spacing=15)
    
    # ================================================================
    # DATOS DEL COMERCIO
    # ================================================================
    draw_text_center("AGROVETERINARIA EL FORTÍN", 14, bold=True)
    y -= 4
    c.setFont("Helvetica", 9)
    c.setFillColor(gray)
    c.drawCentredString(W / 2, y, "Ruta Nacional N° 8, Km 681 – Chaján, Córdoba")
    y -= 14
    c.drawCentredString(W / 2, y, "CUIT: 20-12345678-3 – Responsable Inscripto")
    y -= 18
    
    draw_separator(extra_spacing=15)
    
    # ================================================================
    # DATOS DEL CLIENTE Y VENTA
    # ================================================================
    draw_text_left(f"CLIENTE: {client_name}", 11, bold=True, extra_spacing=2)
    draw_text_left(f"VENTA N°: {sale_id}", 10, extra_spacing=2)
    draw_text_left(f"MÉTODO DE PAGO: {method.upper()}", 10, extra_spacing=2)
    
    draw_separator(extra_spacing=15)
    
    # ================================================================
    # DETALLE DE PRODUCTOS
    # ================================================================
    if sale_items and len(sale_items) > 0:
        draw_text_left("DETALLE DE PRODUCTOS", 10, bold=True)
        y -= 8
        
        # Definir posiciones de columnas (desde el margen izquierdo)
        col_producto = margin
        col_cant = margin + 60*mm      # Cantidad
        col_precio = margin + 100*mm    # Precio
        col_subtotal = margin + 90*mm   # Subtotal (alineado a la derecha)
        
        # Encabezado de tabla
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(black)
        c.drawString(col_producto, y, "Producto")
        c.drawRightString(col_cant + 10*mm, y, "Cant.")
        c.drawRightString(col_precio + 15*mm, y, "Precio")
        c.drawRightString(col_subtotal, y, "Subtotal")
        y -= 14
        
        # Línea bajo encabezado
        c.setStrokeColor(black)
        c.setLineWidth(0.5)
        c.line(margin, y + 8, W - margin, y + 8)
        
        # Items
        c.setFont("Helvetica", 8)
        for item in sale_items:
            nombre, cantidad, precio, subtotal = item
            
            # Truncar nombre si es muy largo
            nombre_display = nombre[:30] + "..." if len(nombre) > 30 else nombre
            
            c.drawString(col_producto, y, nombre_display)       
            c.drawRightString(col_cant + 10*mm, y, str(cantidad))
            c.drawRightString(col_precio + 15*mm, y, f"${precio}")
            c.drawRightString(col_subtotal, y, f"${subtotal}")
            y -= 14
        
        y -= 6
        draw_separator(extra_spacing=15)
    
    # ================================================================
    # RESUMEN DE LA VENTA
    # ================================================================
    prev_paid = sale_info["paid"] - payment_amount
    prev_balance = sale_info["balance"] + payment_amount
    
    draw_line_lr("Total Venta:", f"${sale_info['total']}", 10, bold_r=True, extra_spacing=4)
    draw_line_lr("Pagado Anteriormente:", f"${prev_paid}", 10, extra_spacing=4)
    draw_line_lr("Saldo Anterior:", f"${prev_balance}", 10, extra_spacing=4)
    
    draw_separator(dashed=True, extra_spacing=18)
    
    # ================================================================
    # MONTO PAGADO (destacado)
    # ================================================================
    y -= 5
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(black)
    c.drawString(margin, y, "MONTO PAGADO:")
    c.drawRightString(W - margin, y, f"${payment_amount}")
    y -= 22
    
    draw_separator(dashed=True, extra_spacing=18)
    
    # ================================================================
    # SALDO RESTANTE
    # ================================================================
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(black)
    c.drawString(margin, y, "SALDO RESTANTE:")
    c.drawRightString(W - margin, y, f"${sale_info['balance']}")
    y -= 18
    
    draw_separator(extra_spacing=18)
    
    # ================================================================
    # HISTORIAL DE PAGOS
    # ================================================================
    if payments and len(payments) > 0:
        draw_text_left("HISTORIAL DE PAGOS", 10, bold=True)
        y -= 8
        
        # Definir posiciones de columnas (mejor distribuidas)
        col_fecha = margin
        col_metodo = margin + 70*mm    # Más espacio para la fecha
        col_monto = W - margin
        
        # Encabezado
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(black)
        c.drawString(col_fecha, y, "Fecha")
        c.drawString(col_metodo, y, "Método")
        c.drawRightString(col_monto, y, "Monto")
        y -= 14
        
        c.setStrokeColor(black)
        c.setLineWidth(0.5)
        c.line(margin, y + 8, W - margin, y + 8)
        
        c.setFont("Helvetica", 8)
        c.setFillColor(black)
        for p in payments:
            _, date, amount, mth = p
            # Formatear fecha más corta
            date_str = str(date)[:10] if len(str(date)) > 10 else str(date)
            
            c.drawString(col_fecha, y, date_str)
            c.drawString(col_metodo, y, mth or "-")
            c.drawRightString(col_monto, y, f"${amount}")
            y -= 13
        
        y -= 6
        draw_separator()
    
    # ================================================================
    # ESTADO APROBADO
    # ================================================================
    y -= 10
    
    # Círculo con check
    c.setFillColor(black)
    c.circle(W/2, y + 5, 12, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(W/2, y + 1, "✓")
    y -= 26
    
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(W / 2, y, "APROBADO")
    y -= 26
    
    # ================================================================
    # PIE DE PÁGINA
    # ================================================================
    c.setFillColor(gray)
    c.setFont("Helvetica", 9)
    c.drawCentredString(W / 2, y, "Gracias por su compra")
    y -= 16
    c.setFont("Helvetica", 7)
    c.drawCentredString(W / 2, y, "Este documento no es válido como factura")
    y -= 40
    
    # ================================================================
    # FIRMA
    # ================================================================
    c.setStrokeColor(black)
    c.setLineWidth(0.5)
    line_width = 70 * mm
    c.line(W/2 - line_width/2, y, W/2 + line_width/2, y)
    y -= 12
    c.setFont("Helvetica", 8)
    c.setFillColor(gray)
    c.drawCentredString(W / 2, y, "Firma del Cliente")
    
    c.showPage()
    c.save()
    
    return file_path


# ============================================================
#               RECIBO DE PAGO GLOBAL 
# ============================================================
def generate_global_payment_receipt(*, file_path, client_name, payment_amount, method, result_data, sales_with_items=None):
    """
    Genera comprobante A4 de pago global.
    Estilo ticket profesional en blanco y negro.
    Incluye detalle de productos de cada venta pagada.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    W, H = A4
    margin = 45 * mm
    
    c = canvas.Canvas(file_path, pagesize=A4)
    y = H - 35 * mm
    
    # Colores (blanco y negro)
    black = colors.black
    gray = colors.HexColor("#666666")
    light_gray = colors.HexColor("#cccccc")
    
    # ================================================================
    # FUNCIONES HELPER
    # ================================================================
    def draw_text_left(text, size=10, bold=False, extra_spacing=0):
        nonlocal y
        font = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font, size)
        c.setFillColor(black)
        c.drawString(margin, y, text)
        y -= size + 8 + extra_spacing
    
    def draw_text_center(text, size=10, bold=False, extra_spacing=0):
        nonlocal y
        font = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font, size)
        c.setFillColor(black)
        c.drawCentredString(W / 2, y, text)
        y -= size + 8 + extra_spacing
    
    def draw_text_right(text, size=10, bold=False):
        nonlocal y
        font = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font, size)
        c.setFillColor(gray)
        c.drawRightString(W - margin, y, text)
    
    def draw_line_lr(left, right, size=10, bold_l=False, bold_r=False, extra_spacing=0):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold_l else "Helvetica", size)
        c.setFillColor(black)
        c.drawString(margin, y, left)
        c.setFont("Helvetica-Bold" if bold_r else "Helvetica", size)
        c.drawRightString(W - margin, y, right)
        y -= size + 8 + extra_spacing
    
    def draw_separator(dashed=False, thick=False, extra_spacing=12):
        nonlocal y
        y -= 4
        c.setStrokeColor(black if thick else light_gray)
        c.setLineWidth(1.5 if thick else 0.5)
        if dashed:
            c.setDash(3, 3)
        else:
            c.setDash()
        c.line(margin, y, W - margin, y)
        c.setDash()
        y -= extra_spacing
    
    def draw_pill(text):
        nonlocal y
        pill_width = 180
        pill_height = 18
        x = W - margin - pill_width
        c.setFillColor(black)
        c.roundRect(x, y - 3, pill_width, pill_height, 3, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x + pill_width/2, y + 3, text)
        c.setFillColor(black)
        y -= 2
    
    # ================================================================
    # ENCABEZADO
    # ================================================================
    draw_text_left("ORIGINAL", 8, bold=True)
    y += 15
    draw_pill("COMPROBANTE DE PAGO")
    y -= 20
    
    now = datetime.now()
    draw_text_right(f"{now:%d/%m/%Y} - {now:%H:%M} h", 8)
    y -= 5
    
    draw_separator(thick=True, extra_spacing=15)
    
    # ================================================================
    # DATOS DEL COMERCIO
    # ================================================================
    draw_text_center("AGROVETERINARIA EL FORTÍN", 14, bold=True)
    y -= 4
    c.setFont("Helvetica", 9)
    c.setFillColor(gray)
    c.drawCentredString(W / 2, y, "Ruta Nacional N° 8, Km 681 – Chaján, Córdoba")
    y -= 14
    c.drawCentredString(W / 2, y, "CUIT: 20-12345678-3 – Responsable Inscripto")
    y -= 18
    
    draw_separator(extra_spacing=15)
    
    # ================================================================
    # DATOS DEL CLIENTE
    # ================================================================
    draw_text_left(f"CLIENTE: {client_name}", 11, bold=True, extra_spacing=2)
    draw_text_left("TIPO: PAGO A CUENTA", 10, extra_spacing=2)
    draw_text_left(f"MÉTODO DE PAGO: {method.upper()}", 10, extra_spacing=2)
    
    draw_separator(extra_spacing=15)
    
    # ================================================================
    # MONTO ENTREGADO
    # ================================================================
    y -= 5
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(black)
    c.drawString(margin, y, "MONTO ENTREGADO:")
    c.drawRightString(W - margin, y, f"${payment_amount}")
    y -= 22
    
    draw_separator(dashed=True, extra_spacing=18)
    
    # ================================================================
    # DETALLE DE PRODUCTOS POR VENTA
    # ================================================================
    if sales_with_items and len(sales_with_items) > 0:
        draw_text_left("DETALLE DE PRODUCTOS", 10, bold=True, extra_spacing=4)
        
        # Recorrer cada venta pagada
        for sale_id, amount_paid in result_data["updated_debts"]:
            # Título de la venta
            y -= 4
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(black)
            c.drawString(margin, y, f"■ Venta #{sale_id}")
            c.drawRightString(W - margin, y, f"Pagado: ${format_currency(amount_paid)}")
            y -= 12
            
            # Verificar si hay items para esta venta
            if sale_id in sales_with_items and sales_with_items[sale_id]:
                items = sales_with_items[sale_id]
                
                # Definir posiciones de columnas (ALINEADAS CON PDF COMÚN)
                col_producto = margin + 5*mm
                col_cant = margin + 65*mm
                col_precio = margin + 95*mm
                col_subtotal = W - margin
                
                # Encabezado de tabla
                c.setFont("Helvetica-Bold", 8)
                c.setFillColor(gray)
                c.drawString(col_producto, y, "Producto")
                c.drawRightString(col_cant + 5*mm, y, "Cant.")
                c.drawRightString(col_precio + 10*mm, y, "Precio")
                c.drawRightString(col_subtotal, y, "Subtotal")
                y -= 16
                
                # Línea bajo encabezado
                c.setStrokeColor(black)
                c.setLineWidth(0.5)
                c.line(margin + 5*mm, y + 6, W - margin, y + 6)
                y -= 8
                
                # Items
                c.setFont("Helvetica", 8)
                c.setFillColor(black)
                for item in items:
                    _, nombre, cantidad, precio, subtotal, _ = item
                    
                    # Truncar nombre si es muy largo
                    nombre_display = nombre[:28] + "..." if len(nombre) > 28 else nombre
                    
                    c.drawString(col_producto, y, nombre_display)
                    c.drawRightString(col_cant + 5*mm, y, str(cantidad))
                    c.drawRightString(col_precio + 10*mm, y, f"${format_currency(precio)}")
                    c.drawRightString(col_subtotal, y, f"${format_currency(subtotal)}")
                    y -= 14
                
                y -= 4
            else:
                c.setFont("Helvetica", 8)
                c.setFillColor(gray)
                c.drawString(margin + 8*mm, y, "(Sin detalle de productos)")
                y -= 12
            
        
        y -= 4
        draw_separator(extra_spacing=15)
    
    # ================================================================
    # RESUMEN DEL PAGO
    # ================================================================
    draw_line_lr("Total Aplicado:", f"${format_currency(result_data['used'])}", 10, 
                 bold_l=True, bold_r=True, extra_spacing=4)
    draw_line_lr("Deuda Restante (Cuenta corriente):", f"${format_currency(result_data['still_owed'])}", 10, 
                 bold_l=True, bold_r=True, extra_spacing=4)
    
    # Saldo a favor si aplica
    print(result_data)
    if result_data.get('credit_added', 0) > Decimal('0.00'):
        draw_line_lr("Saldo a Favor Generado:", 
                    f"${result_data['credit_added']}", 10, 
                    bold_l=True, bold_r=True, extra_spacing=4)
    
    draw_separator(extra_spacing=18)
    
    # ================================================================
    # ESTADO APROBADO
    # ================================================================
    y -= 10
    
    # Círculo con check
    c.setFillColor(black)
    c.circle(W/2, y + 5, 12, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(W/2, y + 1, "✓")
    y -= 26
    
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(W / 2, y, "APROBADO")
    y -= 26
    
    # ================================================================
    # PIE DE PÁGINA
    # ================================================================
    c.setFillColor(gray)
    c.setFont("Helvetica", 9)
    c.drawCentredString(W / 2, y, "Gracias por su compra")
    y -= 16
    
    c.setFont("Helvetica", 7)
    c.drawCentredString(W / 2, y, "Este documento no es válido como factura")
    y -= 40
    
    # ================================================================
    # FIRMA
    # ================================================================
    c.setStrokeColor(black)
    c.setLineWidth(0.5)
    line_width = 70 * mm
    c.line(W/2 - line_width/2, y, W/2 + line_width/2, y)
    y -= 12
    
    c.setFont("Helvetica", 8)
    c.setFillColor(gray)
    c.drawCentredString(W / 2, y, "Firma del Cliente")
    
    c.showPage()
    c.save()
    
    return file_path