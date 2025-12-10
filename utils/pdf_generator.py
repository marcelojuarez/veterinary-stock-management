from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm
from datetime import datetime
import os

os.makedirs("comprobantes/pagos", exist_ok=True)


# ============================================================
#   FUNCIÓN BASE PARA TITULO, COMERCIO, Y FORMATO
# ============================================================
def _build_common_header(elements, title_text):
    styles = getSampleStyleSheet()
    title = styles["Heading1"]
    title.fontSize = 16
    title.leading = 20
    normal = styles["Normal"]

    # TÍTULO
    elements.append(Paragraph(f"<b>{title_text}</b>", title))
    elements.append(Spacer(1, 6))

    # DATOS DEL COMERCIO
    comercio_text = """
    <b>Agroveterinaria El Fortín</b><br/>
    Ruta Nacional N° 8, Km 681 – Chaján, Córdoba<br/>
    C.U.I.T.: 20-12345678-3 – Responsable Inscripto<br/>
    """
    elements.append(Paragraph(comercio_text, normal))
    elements.append(Spacer(1, 10))


# ============================================================
#               RECIBO DE PAGO INDIVIDUAL
# ============================================================
def generate_payment_receipt(client_name, sale_id, payment_amount, method, sale_info, payments):
    file_path = f"comprobantes/pagos/comprobante_pago_venta_{sale_id}.pdf"

    doc = SimpleDocTemplate(
        file_path, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=15*mm, bottomMargin=15*mm
    )

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    elements = []

    # Encabezado común
    _build_common_header(elements, "COMPROBANTE DE PAGO")

    # ------------------------------------
    # INFO GENERAL DEL COMPROBANTE
    # ------------------------------------
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    general_info = [
        ["Fecha y Hora", now],
        ["Venta Asociada", f"#{sale_id}"],
    ]

    tbl = Table(general_info, colWidths=[120, 280])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor("#eeeeee")),
        ('BOX', (0, 0), (-1, -1), 0.6, colors.grey),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    elements.append(tbl)
    elements.append(Spacer(1, 15))

    # ------------------------------------
    # DATOS DEL CLIENTE
    # ------------------------------------
    prev_paid = sale_info["paid"] - payment_amount
    prev_balance = sale_info["balance"] + payment_amount

    client_data = f"""
    <b>Cliente:</b> {client_name}<br/>
    <b>Total Venta:</b> ${sale_info["total"]:.2f}<br/>
    <b>Pagado Antes:</b> ${prev_paid:.2f}<br/>
    <b>Saldo Previo:</b> ${prev_balance:.2f}<br/>
    """

    elements.append(Paragraph("<b>Datos del Cliente</b>", styles["Heading3"]))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(client_data, normal))
    elements.append(Spacer(1, 12))

    # ------------------------------------
    # DETALLE DEL PAGO
    # ------------------------------------
    payment_details = [
        ["Monto del Pago", f"${payment_amount:.2f}"],
        ["Método", method],
        ["Saldo Restante", f"${sale_info['balance']:.2f}"]
    ]

    tbl2 = Table(payment_details, colWidths=[150, 200])
    tbl2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e5f4ef")),
        ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor("#009688")),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#009688")),
    ]))
    elements.append(Paragraph("<b>Detalle del Pago</b>", styles["Heading3"]))
    elements.append(Spacer(1, 4))
    elements.append(tbl2)
    elements.append(Spacer(1, 12))

    # ------------------------------------
    # HISTORIAL DE PAGOS
    # ------------------------------------
    if payments:
        elements.append(Paragraph("<b>Historial de Pagos</b>", styles["Heading3"]))
        elements.append(Spacer(1, 4))

        rows = [["Fecha", "Monto", "Método"]]
        for p in payments:
            _, date, amount, mth = p
            rows.append([date, f"${float(amount):.2f}", mth])

        tbl3 = Table(rows, colWidths=[150, 120, 130])
        tbl3.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
            ('BOX', (0, 0), (-1, -1), 0.4, colors.grey),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ]))
        elements.append(tbl3)
        elements.append(Spacer(1, 10))

    # ------------------------------------
    # NOTA LEGAL + FIRMA
    # ------------------------------------
    legal = """
    <i>Este documento certifica la recepción de un pago registrado en el sistema.
    No válido como factura.</i>
    """
    signature = """
    <br/><br/><br/>
    ________________________________<br/>
    Firma del Cliente
    """

    elements.append(Paragraph(legal, normal))
    elements.append(Spacer(1, 25))
    elements.append(Paragraph(signature, normal))

    doc.build(elements)
    return file_path

def generate_global_payment_receipt(client_name, payment_amount, result_data):

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"comprobantes/pagos/comprobante_global_{client_name.replace(' ', '_')}_{timestamp}.pdf"

    doc = SimpleDocTemplate(
        file_path, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=15*mm, bottomMargin=15*mm
    )

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    elements = []

    # Encabezado común
    _build_common_header(elements, "COMPROBANTE DE PAGO GLOBAL")

    # ------------------------------------
    # INFO GENERAL
    # ------------------------------------
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    general_info = [
        ["Fecha y Hora", now],
        ["Tipo de Movimiento", "Pago Global a Cuenta"]
    ]

    tbl = Table(general_info, colWidths=[120, 280])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor("#eeeeee")),
        ('BOX', (0, 0), (-1, -1), 0.6, colors.grey),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    elements.append(tbl)
    elements.append(Spacer(1, 15))

    # ------------------------------------
    # DATOS DEL CLIENTE
    # ------------------------------------
    client_data = f"""
    <b>Cliente:</b> {client_name}<br/>
    <b>Monto Entregado:</b> ${payment_amount:.2f}<br/>
    <b>Total Aplicado:</b> ${result_data['used']:.2f}<br/>
    """
    elements.append(Paragraph("<b>Datos del Cliente</b>", styles["Heading3"]))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(client_data, normal))
    elements.append(Spacer(1, 12))

    # ------------------------------------
    # DISTRIBUCIÓN DEL PAGO (TABLA)
    # ------------------------------------
    elements.append(Paragraph("<b>Distribución del Pago</b>", styles["Heading3"]))
    elements.append(Spacer(1, 4))

    rows = [["Venta ID", "Monto Aplicado"]]
    for sid, amt in result_data["updated_debts"]:
        rows.append([f"#{sid}", f"${amt:.2f}"])

    rows.append(["", ""])
    rows.append(["Total Aplicado", f"${result_data['used']:.2f}"])
    rows.append(["Deuda Restante", f"${result_data['still_owed']:.2f}"])

    tbl2 = Table(rows, colWidths=[200, 150])
    tbl2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e5f4ef")),
        ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor("#009688")),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#009688")),

        ('LINEABOVE', (0, -3), (-1, -3), 1, colors.black),
        ('FONTWEIGHT', (0, -3), (-1, -1), 'BOLD'),
    ]))
    elements.append(tbl2)
    elements.append(Spacer(1, 12))

    # ------------------------------------
    # NOTA LEGAL + FIRMA (IGUAL A INDIVIDUAL)
    # ------------------------------------
    legal = """
    <i>Este documento certifica la recepción de un pago registrado en el sistema.
    No válido como factura.</i>
    """
    signature = """
    <br/><br/><br/>
    ________________________________<br/>
    Firma del Cliente
    """

    elements.append(Paragraph(legal, normal))
    elements.append(Spacer(1, 25))
    elements.append(Paragraph(signature, normal))

    doc.build(elements)
    return file_path
