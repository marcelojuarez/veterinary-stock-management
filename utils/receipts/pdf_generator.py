"""
Generador de comprobantes A4 - Estilo Ticket profesional (Blanco y Negro)
Con detalle de productos vendidos
Ubicación: utils/receipts/pdf_generator.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from datetime import datetime
import os

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
            nombre_display = nombre[:30] + "..." if len(str(nombre)) > 30 else str(nombre)
            
            c.drawString(col_producto, y, nombre_display)
            c.drawRightString(col_cant + 10*mm, y, str(int(cantidad)))
            c.drawRightString(col_precio + 15*mm, y, f"${float(precio):,.2f}")
            c.drawRightString(col_subtotal, y, f"${float(subtotal):,.2f}")
            y -= 14
        
        y -= 6
        draw_separator(extra_spacing=15)
    
    # ================================================================
    # RESUMEN DE LA VENTA
    # ================================================================
    prev_paid = sale_info["paid"] - payment_amount
    prev_balance = sale_info["balance"] + payment_amount
    
    draw_line_lr("Total Venta:", f"${sale_info['total']:,.2f}", 10, bold_r=True, extra_spacing=4)
    draw_line_lr("Pagado Anteriormente:", f"${prev_paid:,.2f}", 10, extra_spacing=4)
    draw_line_lr("Saldo Anterior:", f"${prev_balance:,.2f}", 10, extra_spacing=4)
    
    draw_separator(dashed=True, extra_spacing=18)
    
    # ================================================================
    # MONTO PAGADO (destacado)
    # ================================================================
    y -= 5
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(black)
    c.drawString(margin, y, "MONTO PAGADO:")
    c.drawRightString(W - margin, y, f"${payment_amount:,.2f}")
    y -= 22
    
    draw_separator(dashed=True, extra_spacing=18)
    
    # ================================================================
    # SALDO RESTANTE
    # ================================================================
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(black)
    c.drawString(margin, y, "SALDO RESTANTE:")
    c.drawRightString(W - margin, y, f"${sale_info['balance']:,.2f}")
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
            c.drawRightString(col_monto, y, f"${float(amount):,.2f}")
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
def generate_global_payment_receipt(*, file_path, client_name, payment_amount, result_data):
    """
    Genera comprobante A4 de pago global.
    Estilo ticket profesional en blanco y negro.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    W, H = A4
    margin = 45 * mm  # Aumentado de 40mm a 45mm
    
    c = canvas.Canvas(file_path, pagesize=A4)
    y = H - 35 * mm  # Aumentado de 30mm a 35mm
    
    # Colores (blanco y negro)
    black = colors.black
    gray = colors.HexColor("#666666")
    light_gray = colors.HexColor("#cccccc")
    
    # ================================================================
    # FUNCIONES HELPER (MODIFICADAS CON MÁS ESPACIO)
    # ================================================================
    def draw_text_left(text, size=10, bold=False, extra_spacing=0):
        nonlocal y
        font = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font, size)
        c.setFillColor(black)
        c.drawString(margin, y, text)
        y -= size + 4 + extra_spacing  # Espacio adicional opcional
    
    def draw_text_center(text, size=10, bold=False, extra_spacing=0):
        nonlocal y
        font = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font, size)
        c.setFillColor(black)
        c.drawCentredString(W / 2, y, text)
        y -= size + 4 + extra_spacing  # Espacio adicional opcional
    
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
        y -= size + 4 + extra_spacing  # Espacio adicional opcional
    
    def draw_separator(dashed=False, thick=False, extra_spacing=12):  # Aumentado de 8 a 12
        nonlocal y
        y -= 4  # Aumentado de 3 a 4
        c.setStrokeColor(black if thick else light_gray)
        c.setLineWidth(1.5 if thick else 0.5)
        if dashed:
            c.setDash(3, 3)
        else:
            c.setDash()
        c.line(margin, y, W - margin, y)
        c.setDash()
        y -= extra_spacing  # Usa el parámetro extra_spacing
    
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
        y -= 2  # Espacio adicional después del píldora
    
    # ================================================================
    # ENCABEZADO (CON MÁS ESPACIO)
    # ================================================================
    draw_text_left("ORIGINAL", 8, bold=True)
    y += 15  # Aumentado de 12 a 15
    draw_pill("COMPROBANTE PAGO GLOBAL")
    y -= 20  # Aumentado de 18 a 20
    
    now = datetime.now()
    draw_text_right(f"{now:%d/%m/%Y} - {now:%H:%M} h", 8)
    y -= 5  # Aumentado de 3 a 5
    
    draw_separator(thick=True, extra_spacing=15)  # Más espacio después del separador
    
    # ================================================================
    # DATOS DEL COMERCIO (CON MÁS ESPACIO)
    # ================================================================
    draw_text_center("AGROVETERINARIA EL FORTÍN", 14, bold=True, extra_spacing=4)
    y -= 4  # Espacio adicional
    
    c.setFont("Helvetica", 9)
    c.setFillColor(gray)
    c.drawCentredString(W / 2, y, "Ruta Nacional N° 8, Km 681 – Chaján, Córdoba")
    y -= 14  # Aumentado de 12 a 14
    
    c.drawCentredString(W / 2, y, "CUIT: 20-12345678-3 – Responsable Inscripto")
    y -= 18  # Aumentado de 14 a 18
    
    draw_separator(extra_spacing=15)  # Más espacio después del separador
    
    # ================================================================
    # DATOS DEL CLIENTE (CON MÁS ESPACIO)
    # ================================================================
    draw_text_left(f"CLIENTE: {client_name}", 11, bold=True, extra_spacing=2)
    draw_text_left("TIPO: PAGO GLOBAL A CUENTA", 10, extra_spacing=2)
    
    draw_separator(extra_spacing=15)  # Más espacio después del separador
    
    # ================================================================
    # MONTO ENTREGADO (destacado) - CON MÁS ESPACIO
    # ================================================================
    y -= 5  # Espacio adicional antes
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(black)
    c.drawString(margin, y, "MONTO ENTREGADO:")
    c.drawRightString(W - margin, y, f"${payment_amount:,.2f}")
    y -= 22  # Aumentado de 18 a 22
    
    draw_separator(dashed=True, extra_spacing=18)  # Más espacio después del separador
    
    # ================================================================
    # DISTRIBUCIÓN DEL PAGO (CON MÁS ESPACIO)
    # ================================================================
    draw_text_left("DISTRIBUCIÓN DEL PAGO", 10, bold=True, extra_spacing=4)
    y -= 8  # Aumentado de 5 a 8
    
    # Encabezado
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin, y, "Venta N°")
    c.drawRightString(W - margin, y, "Monto Aplicado")
    y -= 14  # Aumentado de 12 a 14
    
    c.setStrokeColor(black)
    c.setLineWidth(0.5)
    c.line(margin, y + 8, W - margin, y + 8)
    
    c.setFont("Helvetica", 9)
    for sid, amt in result_data["updated_debts"]:
        c.drawString(margin, y, f"#{sid}")
        c.drawRightString(W - margin, y, f"${amt:,.2f}")
        y -= 13  # Aumentado de 11 a 13
    
    y -= 6  # Aumentado de 3 a 6
    draw_separator(dashed=True, extra_spacing=15)  # Más espacio después del separador
    
    # ================================================================
    # RESUMEN (CON MÁS ESPACIO)
    # ================================================================
    draw_line_lr("Total Aplicado:", f"${result_data['used']:,.2f}", 10, 
                 bold_l=True, bold_r=True, extra_spacing=4)
    draw_line_lr("Deuda Restante:", f"${result_data['still_owed']:,.2f}", 10, 
                 bold_l=True, bold_r=True, extra_spacing=4)
    
    # Saldo a favor si aplica
    if result_data.get('credit_added', 0) > 0.01:
        draw_line_lr("Saldo a Favor Generado:", 
                    f"${result_data['credit_added']:,.2f}", 10, 
                    bold_l=True, bold_r=True, extra_spacing=4)
    
    draw_separator(extra_spacing=18)  # Más espacio después del separador
    
    # ================================================================
    # ESTADO APROBADO (CON MÁS ESPACIO)
    # ================================================================
    y -= 10  # Aumentado de 8 a 10
    
    c.setFillColor(black)
    c.circle(W/2, y + 5, 12, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(W/2, y + 1, "✓")
    y -= 26  # Aumentado de 22 a 26
    
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(W / 2, y, "APROBADO")
    y -= 26  # Aumentado de 22 a 26
    
    # ================================================================
    # PIE DE PÁGINA (CON MÁS ESPACIO)
    # ================================================================
    c.setFillColor(gray)
    c.setFont("Helvetica", 9)
    c.drawCentredString(W / 2, y, "Gracias por su compra")
    y -= 16  # Aumentado de 12 a 16
    
    c.setFont("Helvetica", 7)
    c.drawCentredString(W / 2, y, "Este documento no es válido como factura")
    y -= 40  # Aumentado de 35 a 40
    
    # ================================================================
    # FIRMA (CON MÁS ESPACIO)
    # ================================================================
    c.setStrokeColor(black)
    c.setLineWidth(0.5)
    line_width = 70 * mm
    c.line(W/2 - line_width/2, y, W/2 + line_width/2, y)
    y -= 16  # Aumentado de 12 a 16
    
    c.setFont("Helvetica", 8)
    c.setFillColor(gray)
    c.drawCentredString(W / 2, y, "Firma del Cliente")
    
    c.showPage()
    c.save()
    
    return file_path