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
        nonlocal y
        c.setFont("Helvetica-Bold" if b else "Helvetica", s)
        c.drawString(L, y, t)

    def tr(t, s=8, b=False):
        nonlocal y
        c.setFont("Helvetica-Bold" if b else "Helvetica", s)
        c.drawRightString(R, y, t)

    def lr(l, r, s=8, bl=False, br=False):
        nonlocal y
        c.setFont("Helvetica-Bold" if bl else "Helvetica", s)
        c.drawString(L, y, l)
        c.setFont("Helvetica-Bold" if br else "Helvetica", s)
        c.drawRightString(R, y, r)

    def sep(d=False):
        nonlocal y
        c.setLineWidth(0.6)
        c.setDash(1, 2) if d else c.setDash()
        c.line(L, y, R, y)
        c.setDash()

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
    tl("PAGO GLOBAL A CUENTA", 7.5)
    y -= 9
    sep(True)
    y -= 10

    lr("MONTO ENTREGADO", f"$ {amount:,.2f}", 8, True, True)
    y -= 10
    sep()
    y -= 14

    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(W / 2, y, "APROBADO")
    y -= 18

    c.setFont("Helvetica", 7)
    c.drawCentredString(W / 2, y, "No válido como factura")
    y -= 10

    c.showPage()
    c.save()
