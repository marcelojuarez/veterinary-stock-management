from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime
from config.settings import COMPANY_CONFIG
import os
from utils.receipts.paths import get_base_folder


class DailySalesReportService:

    def __init__(self):

        self.styles = getSampleStyleSheet()

        self.styles.add(ParagraphStyle(
            name="DailyTitle",
            parent=self.styles['Heading1'],
            fontSize=18,
            alignment=1,
            spaceAfter=15
        ))

        self.styles.add(ParagraphStyle(
            name="Company",
            fontSize=9,
            alignment=1,
            spaceAfter=10
        ))

    def generate(self, sales_rows, fecha_desde, fecha_hasta):

        ventas_dir = os.path.join(get_base_folder(), "Reportes", "Ventas")
        os.makedirs(ventas_dir, exist_ok=True)

        filename = os.path.join(
            ventas_dir,
            f"ventas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )

        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            leftMargin=30,
            rightMargin=30
        )

        elements = []

        # -----------------------------
        # ENCABEZADO EMPRESA
        # -----------------------------

        company_info = f"""
        <b>{COMPANY_CONFIG['name']}</b><br/>
        {COMPANY_CONFIG['address']} | Tel: {COMPANY_CONFIG['phone']} | CUIT: {COMPANY_CONFIG['cuit']}
        """

        elements.append(Paragraph(company_info, self.styles["Company"]))

        elements.append(
            Paragraph(
                "REPORTE DE VENTAS",
                self.styles["DailyTitle"]
            )
        )

        elements.append(
            Paragraph(
                f"<b>Periodo:</b> {fecha_desde} al {fecha_hasta}",
                self.styles["Normal"]
            )
        )

        elements.append(Spacer(1, 15))

        # -----------------------------
        # TABLA
        # -----------------------------

        data = [["ID", "Cliente", "Estado", "Total", "Hora"]]

        total_vendido = 0
        total_cobrado = 0
        total_saldo = 0

        ventas_pagadas = 0
        ventas_pendientes = 0

        for row in sales_rows:

            sale_id = row[0]
            fecha = row[1]
            hora = row[2]
            cliente = row[3]
            estado = row[4]

            total = float(
                str(row[5])
                .replace("$", "")
                .replace(".", "")
                .replace(",", ".")
            )

            pagado = float(
                str(row[6])
                .replace("$", "")
                .replace(".", "")
                .replace(",", ".")
            )

            saldo = float(
                str(row[7])
                .replace("$", "")
                .replace(".", "")
                .replace(",", ".")
            )

            total_vendido += total
            total_cobrado += pagado
            total_saldo += saldo

            if estado.lower() == "pagada":
                ventas_pagadas += 1
            else:
                ventas_pendientes += 1

            data.append([
                sale_id,
                cliente or "Consumidor Final",
                estado.upper(),
                f"${total:,.2f}",
                hora
            ])

        table = Table(data, colWidths=[50, 220, 80, 90, 70])

        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.grey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
            ("FONTSIZE", (0,0), (-1,-1), 9)
        ]))

        elements.append(table)

        elements.append(Spacer(1, 20))

        # -----------------------------
        # RESUMEN
        # -----------------------------

        resumen = f"""
        <b>Resumen del periodo</b><br/><br/>
        Ventas totales: {len(sales_rows)}<br/>
        Ventas pagadas: {ventas_pagadas}<br/>
        Ventas pendientes: {ventas_pendientes}<br/><br/>

        Total vendido: ${total_vendido:,.2f}<br/>
        Total cobrado: ${total_cobrado:,.2f}<br/>
        Saldo pendiente: ${total_saldo:,.2f}
        """

        elements.append(Paragraph(resumen, self.styles["Normal"]))

        doc.build(elements)

        return filename