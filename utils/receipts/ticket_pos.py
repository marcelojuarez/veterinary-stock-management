from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from datetime import datetime
import os

def generate_payment_ticket(
    *,
    file_path,
    commerce_name,
    commerce_address,
    commerce_cuit,
    client_name,
    sale_id,
    amount,
    method,
    approved=True,
    ticket_width_mm=80
):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    W = ticket_width_mm * mm
    H = 120 * mm
    L = 5 * mm
    R = W - 5 * mm

    c = canvas.Canvas(file_path, pagesize=(W, H))
    y = H - 10

    def tl(t, s=8, b=False):
        c.setFont("Helvetica-Bold" if b else "Helvetica", s)
        c.drawString(L, y, t)

    def tr(t, s=8, b=False):
        c.setFont("Helvetica-Bold" if b else "Helvetica", s)
        c.drawRightString(R, y, t)

    def lr(l, r, s=8, bl=False, br=False):
        c.setFont("Helvetica-Bold" if bl else "Helvetica", s)
        c.drawString(L, y, l)
        c.setFont("Helvetica-Bold" if br else "Helvetica", s)
        c.drawRightString(R, y, r)

    def sep(d=False):
        c.setLineWidth(0.6)
        c.setDash(1, 2) if d else c.setDash()
        c.line(L, y, R, y)
        c.setDash()

    def pill(label):
        s = 7.5
        p = 3
        c.setFont("Helvetica-Bold", s)
        w = c.stringWidth(label, "Helvetica-Bold", s) + p * 2
        c.setFillColor(colors.HexColor("#3a3a3a"))
        c.roundRect(R - w, y - s - 4, w, s + 6, 2, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.drawString(R - w + p, y - s - 1, label)
        c.setFillColor(colors.black)

    tl("ORIGINAL", 7.5)
    pill("COMPROBANTE CLIENTE")
    y -= 22

    now = datetime.now()
    tr(f"{now:%d/%m/%y} - {now:%H:%M} h", 7.5)
    y -= 10
    sep()
    y -= 8

    tl(commerce_name.upper(), 9, True)
    y -= 11
    tl(commerce_address.upper(), 7.5)
    y -= 9
    tl(f"CUIT: {commerce_cuit}", 7.5)
    y -= 10
    sep()
    y -= 8

    tl(f"CLIENTE: {client_name}", 7.5)
    y -= 9
    tl(f"VENTA N°: {sale_id}", 7.5)
    y -= 9
    tl(method.upper(), 7.5)
    y -= 8
    sep(True)
    y -= 10

    lr("TOTAL", f"$ {amount:,.2f}", 9, True, True)
    y -= 10
    sep()
    y -= 14

    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(W / 2, y, "APROBADO" if approved else "RECHAZADO")
    y -= 18

    c.setFont("Helvetica", 7)
    c.drawCentredString(W / 2, y, "Gracias por su compra")
    y -= 10
    c.setFont("Helvetica", 6.5)
    c.drawCentredString(W / 2, y, "No válido como factura")

    c.showPage()
    c.save()

def generate_global_payment_ticket(
    *,
    file_path,
    commerce_name,
    commerce_address,
    commerce_cuit,
    client_name,
    amount,
    result_data,
    sales_items=None,
    ticket_width_mm=80
):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    W = ticket_width_mm * mm
    # Altura dinámica según cantidad de productos
    base_height = 150
    if sales_items:
        total_items = sum(len(items) for items in sales_items.values())
        base_height += (total_items * 14) + (len(sales_items) * 20)  # Espacio por item y por venta
    
    H = base_height * mm
    L = 5 * mm
    R = W - 5 * mm

    c = canvas.Canvas(file_path, pagesize=(W, H))
    y = H - 10

    def tl(t, s=8, b=False):
        nonlocal y
        c.setFont("Helvetica-Bold" if b else "Helvetica", s)
        c.drawString(L, y, t)
        y -= s + 2

    def tr(t, s=8, b=False):
        nonlocal y
        c.setFont("Helvetica-Bold" if b else "Helvetica", s)
        c.drawRightString(R, y, t)
        y -= s + 2

    def lr(l, r, s=8, bl=False, br=False):
        nonlocal y
        c.setFont("Helvetica-Bold" if bl else "Helvetica", s)
        c.drawString(L, y, l)
        c.setFont("Helvetica-Bold" if br else "Helvetica", s)
        c.drawRightString(R, y, r)
        y -= s + 2

    def sep(d=False):
        nonlocal y
        y -= 6
        c.setLineWidth(0.6)
        c.setDash(1, 2) if d else c.setDash()
        c.line(L, y, R, y)
        c.setDash()
        y -= 8

    def pill(label):
        nonlocal y
        s = 7.5
        p = 3
        c.setFont("Helvetica-Bold", s)
        w = c.stringWidth(label, "Helvetica-Bold", s) + p * 2
        c.setFillColor(colors.HexColor("#3a3a3a"))
        c.roundRect(R - w, y - s - 4, w, s + 6, 2, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.drawString(R - w + p, y - s - 1, label)
        c.setFillColor(colors.black)

    # ================================================================
    # ENCABEZADO
    # ================================================================
    tl("ORIGINAL", 7.5)
    pill("COMPROBANTE CLIENTE")
    y -= 20

    now = datetime.now()
    tr(f"{now:%d/%m/%y} - {now:%H:%M} h", 7.5)
    y -= 8
    sep()

    tl(commerce_name.upper(), 9, True)
    tl(commerce_address.upper(), 7.5)
    tl(f"CUIT: {commerce_cuit}", 7.5)
    y -= 2
    sep()

    tl(f"CLIENTE: {client_name}", 7.5)
    tl("PAGO GLOBAL A CUENTA", 7.5)
    y -= 2
    sep(True)

    lr("MONTO ENTREGADO", f"$ {amount:,.2f}", 8, True, True)
    y -= 2
    sep()
    y -= 4

    # ================================================================
    # DETALLE DE PRODUCTOS POR VENTA
    # ================================================================
    if sales_items and len(sales_items) > 0:
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(L, y, "DETALLE DE PRODUCTOS")
        y -= 12
        
        for sale_id, amount_paid in result_data["updated_debts"]:
            # Encabezado de venta
            c.setFont("Helvetica-Bold", 7)
            c.drawString(L, y, f"Venta #{sale_id}")
            c.drawRightString(R, y, f"${amount_paid:,.2f}")
            y -= 12
            
            # Productos
            if sale_id in sales_items and sales_items[sale_id]:
                items = sales_items[sale_id]
                c.setFont("Helvetica", 6.5)
                
                for item in items:
                    nombre, cantidad, precio, subtotal = item
                    
                    # Truncar nombre para que entre en el ticket
                    nombre_display = nombre[:22] + "..." if len(str(nombre)) > 22 else str(nombre)
                    
                    # Línea 1: Nombre del producto
                    c.drawString(L + 2*mm, y, nombre_display)
                    y -= 9
                    
                    # Línea 2: Cantidad x Precio = Subtotal
                    c.drawString(L + 2*mm, y, f"  {int(cantidad)}u x ${float(precio):,.2f}")
                    c.drawRightString(R, y, f"${float(subtotal):,.2f}")
                    y -= 10
                
                y -= 6
            else:
                c.setFont("Helvetica", 6.5)
                c.drawString(L + 2*mm, y, "(Sin detalle)")
                y -= 10
    
        sep()

    # ================================================================
    # RESUMEN
    # ================================================================
    lr("Total Aplicado", f"${result_data['used']:,.2f}", 7.5, True, True)
    lr("Deuda Restante (Cuenta corriente)", f"${result_data['still_owed']:,.2f}", 7.5, True, True)
    
    if result_data.get('credit_added', 0) > 0.01:
        lr("Saldo a Favor", f"${result_data['credit_added']:,.2f}", 7.5, True, True)
    
    y -= 4

    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(W / 2, y, "APROBADO")
    y -= 14

    c.setFont("Helvetica", 7)
    c.drawCentredString(W / 2, y, "Gracias por su compra")
    y -= 8
    c.setFont("Helvetica", 6.5)
    c.drawCentredString(W / 2, y, "No válido como factura")

    c.showPage()
    c.save()
    
    return file_path