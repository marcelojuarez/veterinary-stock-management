from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm
from datetime import datetime
import os
os.makedirs("comprobantes/pagos", exist_ok=True)


def generate_payment_receipt(client_name, sale_id, payment_amount, method, sale_info, payments):
    """
    Genera un comprobante PDF profesional de pago.
    Retorna la ruta del archivo generado.
    """

    file_path = f"comprobantes/pagos/comprobante_pago_venta_{sale_id}.pdf"

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    title = styles["Heading1"]
    title.fontSize = 16
    title.leading = 20

    elements = []

    # ============================
    # TÍTULO
    # ============================
    elements.append(Paragraph("<b>COMPROBANTE DE PAGO</b>", title))
    elements.append(Spacer(1, 6))

    # ============================
    # DATOS DEL COMERCIO
    # ============================
    comercio_text = """
    <b>Agroveterinaria El Fortín</b><br/>
    Ruta Nacional N° 8, Km 681 – Chaján, Córdoba<br/>
    C.U.I.T.: 20-12345678-3 – Responsable Inscripto<br/>
    """
    elements.append(Paragraph(comercio_text, normal))
    elements.append(Spacer(1, 10))

    # ============================
    # INFO GENERAL DEL COMPROBANTE
    # ============================
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    general_info = [
        ["Fecha y Hora", now],
        ["Venta asociada", f"#{sale_id}"],
    ]

    tbl = Table(general_info, colWidths=[100, 300])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor("#eeeeee")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(tbl)
    elements.append(Spacer(1, 15))

    # ============================
    # DATOS DEL CLIENTE
    # ============================
    client_data = f"""
    <b>Cliente:</b> {client_name}<br/>
    <b>Total venta:</b> ${sale_info["total"]:.2f}<br/>
    <b>Pagado antes del pago:</b> ${sale_info["paid"] - payment_amount:.2f}<br/>
    <b>Saldo previo:</b> ${sale_info["balance"] + payment_amount:.2f}<br/>
    """
    elements.append(Paragraph("<b>Datos del Cliente</b>", styles["Heading3"]))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(client_data, normal))
    elements.append(Spacer(1, 10))

    # ============================
    # DETALLE DEL PAGO
    # ============================
    sale_balance_after = sale_info["balance"]

    payment_details = [
        ["Monto del pago", f"${payment_amount:.2f}"],
        ["Método", method],
        ["Saldo restante", f"${sale_balance_after:.2f}"]
    ]

    tbl2 = Table(payment_details, colWidths=[150, 200])
    tbl2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor("#e5f4ef")),
        ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor("#009688")),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#009688")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    elements.append(Paragraph("<b>Detalle del Pago</b>", styles["Heading3"]))
    elements.append(Spacer(1, 4))
    elements.append(tbl2)
    elements.append(Spacer(1, 12))

    # ============================
    # HISTORIAL COMPLETO DE PAGOS
    # ============================
    if payments:
        elements.append(Paragraph("<b>Historial de Pagos</b>", styles["Heading3"]))
        elements.append(Spacer(1, 4))

        header = ["Fecha", "Monto", "Método"]
        rows = [header]

        for p in payments:
            pay_id, date, amount, pay_method = p
            rows.append([date, f"${float(amount):.2f}", pay_method])

        tbl3 = Table(rows, colWidths=[150, 120, 130])
        tbl3.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
            ('BOX', (0, 0), (-1, -1), 0.4, colors.grey),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ]))

        elements.append(tbl3)
        elements.append(Spacer(1, 12))

    # ============================
    # LEGALES / NOTA FINAL
    # ============================
    nota = """
    <i>Este documento certifica la recepción de un pago registrado en el sistema.
    No válido como factura.</i>
    """
    elements.append(Paragraph(nota, normal))
    elements.append(Spacer(1, 20))

    # ============================
    # FIRMAS
    # ============================
    firma = """
    <br/><br/><br/>
    ________________________________<br/>
    Firma del Cliente
    """
    elements.append(Paragraph(firma, normal))

    # GENERAR PDF
    doc.build(elements)

    return file_path
