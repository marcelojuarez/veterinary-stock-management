from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os
from datetime import datetime
from config.settings import COMPANY_CONFIG

class RemitoPDF:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            name="RemitoTitle",
            fontSize=16,
            alignment=1,
            spaceAfter=20,
            textColor=colors.darkblue
        ))

    def generate_remito(self, number, customer, items):
        os.makedirs("remitos", exist_ok=True)
        filename = f"remitos/REM-{number}.pdf"

        doc = SimpleDocTemplate(filename, pagesize=A4)
        elements = []

        # TITULO
        title = Paragraph(f"<b>REMITO Nº {number}</b>", self.styles["RemitoTitle"])
        elements.append(title)

        # FECHA
        date = datetime.now().strftime("%d/%m/%Y")
        elements.append(Paragraph(f"Fecha: {date}", self.styles["Normal"]))
        elements.append(Spacer(1, 10))

        # EMPRESA
        empresa_text = f"""
            <b>{COMPANY_CONFIG['name']}</b><br/>
            {COMPANY_CONFIG['address']}<br/>
            CUIT: {COMPANY_CONFIG['cuit']} - Tel: {COMPANY_CONFIG['phone']}
        """
        elements.append(Paragraph(empresa_text, self.styles["Normal"]))
        elements.append(Spacer(1, 15))

        # CLIENTE
        customer_text = f"""
            <b>Cliente:</b> {customer[1]}<br/>
            CUIT/DNI: {customer[2]}<br/>
            Domicilio: {customer[3]}
            Teléfono: {customer[4]}
        """
        elements.append(Paragraph(customer_text, self.styles["Normal"]))
        elements.append(Spacer(1, 10))

        # TABLA DE PRODUCTOS
        table_data = [["Código", "Descripción", "Cantidad"]]
        for it in items:
            table_data.append([it['product_id'], it['name'], it['quantity']])

        table = Table(table_data, colWidths=[80, 300, 80])
        table.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 1, colors.black),
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold")
        ]))

        elements.append(table)
        elements.append(Spacer(1, 40))

        # FIRMAS
        elements.append(Paragraph("<b>Firma del Cliente: _________________________</b>", self.styles["Normal"]))
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Aclaración: __________________________________", self.styles["Normal"]))

        doc.build(elements)
        return filename
