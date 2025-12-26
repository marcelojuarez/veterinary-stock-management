from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
from config.settings import COMPANY_CONFIG
import os

class DailySalesReportService:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            name="DailyTitle",
            parent=self.styles['Heading1'],
            fontSize=18,
            leading=22,
            alignment=1,  # centrado
            spaceAfter=20
        ))

        self.styles.add(ParagraphStyle(
            name="Company",
            fontSize=9,
            alignment=1,
            spaceAfter=10
        ))

    def generate(self, sales_rows):
        """
        sales_rows: lista de tuplas → (id, fecha, total, cliente, estado)
        """
        os.makedirs("ventas", exist_ok=True)
        filename = f"ventas/ventas_{datetime.now().strftime('%Y%m%d')}.pdf"

        doc = SimpleDocTemplate(filename, pagesize=A4, leftMargin=30, rightMargin=30)
        elements = []

        # ENCABEZADO EMPRESA
        company_info = f"""
        <b>{COMPANY_CONFIG['name']}</b><br/>
        {COMPANY_CONFIG['address']} | Tel: {COMPANY_CONFIG['phone']} | CUIT: {COMPANY_CONFIG['cuit']}
        """
        elements.append(Paragraph(company_info, self.styles["Company"]))

        # Título
        elements.append(Paragraph(f"VENTAS DEL DÍA: {datetime.now().strftime('%d/%m/%Y')}", self.styles["Title"]))

        # TABLA PRINCIPAL
        data = [["ID", "Cliente", "Estado", "Total", "Hora"]]

        total_dia = 0
        for sale_id, date, total, cliente, estado in sales_rows:
            hora = date.split(" ")[1] if " " in date else date
            data.append([sale_id, cliente or "Consumidor Final", estado.upper(), f"${total:.2f}", hora])
            total_dia += total

        table = Table(data, colWidths=[50, 200, 80, 80, 80])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.grey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
            ("FONTSIZE", (0,0), (-1,-1), 9)
        ]))
        elements.append(table)

        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"<b>TOTAL DEL DÍA:</b> ${total_dia:.2f}", self.styles["Normal"]))

        doc.build(elements)
        return filename
