import os
from decimal import Decimal
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from utils.utils import format_currency


def _draw_ticket_copy(
    c, y_start, W, L, R,
    label,
    commerce_name, commerce_address, commerce_cuit,
    client_name, amount, method,
    result_data, sales_with_items, check_data,
):
    y = y_start

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

    def pill(text):
        nonlocal y
        s = 7.5
        p = 3
        c.setFont("Helvetica-Bold", s)
        w = c.stringWidth(text, "Helvetica-Bold", s) + p * 2
        c.setFillColor(colors.HexColor("#3a3a3a"))
        c.roundRect(R - w, y - s - 4, w, s + 6, 2, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.drawString(R - w + p, y - s - 1, text)
        c.setFillColor(colors.black)

    # Header
    tl(label, 7.5)
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
    tl("PAGO A CUENTA", 7.5)
    tl(f"{method.upper()}", 7.5)

    if check_data:
        y -= 4
        tl(f"Nro. Cheque: {check_data['number']}", 7.5)
        tl(f"Banco: {check_data['bank'].upper()}", 7.5)
        try:
            from datetime import datetime as _dt
            due_fmt = _dt.strptime(check_data['due_date'], "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            due_fmt = check_data['due_date']
        tl(f"Vencimiento: {due_fmt}", 7.5)

    y -= 2
    sep(True)

    lr("MONTO ENTREGADO", f"$ {format_currency(amount)}", 8, True, True)
    y -= 2
    sep()
    y -= 4

    # Product detail
    if sales_with_items and len(sales_with_items) > 0:
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(L, y, "DETALLE DE PRODUCTOS")
        y -= 12

        for sale_id, amount_paid in result_data["updated_debts"]:
            c.setFont("Helvetica-Bold", 7)
            c.drawString(L, y, f"Venta #{sale_id}")
            c.drawRightString(R, y, f"${format_currency(amount_paid)}")
            y -= 12

            if sale_id in sales_with_items and sales_with_items[sale_id]:
                items = sales_with_items[sale_id]
                c.setFont("Helvetica", 6)

                for item in items:
                    _, nombre, pack, cantidad, precio, subtotal, _ = item
                    nombre_display = nombre[:45] + "..." if len(nombre) > 45 else nombre
                    c.drawString(L + 2 * mm, y, nombre_display)
                    y -= 9
                    if pack:
                        c.drawString(L + 2 * mm, y, f"  {pack}")
                        y -= 9
                    c.drawString(L + 2 * mm, y, f"  {cantidad}u x ${format_currency(precio)}")
                    c.drawRightString(R, y, f"${format_currency(subtotal)}")
                    y -= 10
                y -= 6
            else:
                c.setFont("Helvetica", 6.5)
                c.drawString(L + 2 * mm, y, "(Sin detalle)")
                y -= 10

        sep()

    # Summary
    lr("Total Aplicado", f"${format_currency(result_data['used'])}", 7.5, True, True)
    lr("Deuda Restante (Cuenta corriente)", f"${format_currency(result_data['still_owed'])}", 7.5, True, True)

    if result_data.get('credit_added', 0) > Decimal('0.00'):
        lr("Saldo a Favor", f"${format_currency(result_data['credit_added'])}", 7.5, True, True)

    y -= 4
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(W / 2, y, "APROBADO")
    y -= 14
    c.setFont("Helvetica", 7)
    c.drawCentredString(W / 2, y, "Gracias por su compra")
    y -= 8
    c.setFont("Helvetica", 6.5)
    c.drawCentredString(W / 2, y, "No válido como factura")


def generate_global_payment_ticket(
    *,
    file_path,
    commerce_name,
    commerce_address,
    commerce_cuit,
    client_name,
    amount,
    method,
    result_data,
    sales_with_items=None,
    check_data=None,
    ticket_width_mm=80
):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    W = ticket_width_mm * mm
    base_height = 150
    if sales_with_items:
        total_items = sum(len(items) for items in sales_with_items.values())
        base_height += (total_items * 14) + (len(sales_with_items) * 20)

    H = base_height * mm
    L = 5 * mm
    R = W - 5 * mm

    c = canvas.Canvas(file_path, pagesize=(W, H))

    _draw_ticket_copy(
        c, y_start=H - 10,
        W=W, L=L, R=R,
        label="ORIGINAL",
        commerce_name=commerce_name,
        commerce_address=commerce_address,
        commerce_cuit=commerce_cuit,
        client_name=client_name,
        amount=amount,
        method=method,
        result_data=result_data,
        sales_with_items=sales_with_items,
        check_data=check_data,
    )

    c.showPage()
    c.save()

    return file_path
