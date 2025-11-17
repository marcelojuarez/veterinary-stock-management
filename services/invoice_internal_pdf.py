from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from datetime import datetime
import os
from config.settings import COMPANY_CONFIG

class InvoiceInternalPDFService:

    def __init__(self):
        self.styles = getSampleStyleSheet()

        # Título grande
        self.styles.add(ParagraphStyle(
            name="InvoiceTitle",
            fontSize=18,
            spaceAfter=10,
            alignment=1,  # centre
            textColor="black",
            leading=22
        ))

        # Subtítulos
        self.styles.add(ParagraphStyle(
            name="SectionHeader",
            fontSize=11,
            textColor="black",
            leading=14,
            spaceAfter=4,
            spaceBefore=8
        ))

        # Texto general
        self.styles.add(ParagraphStyle(
            name="NormalSmall",
            fontSize=9,
            leading=12
        ))

        self.styles.add(ParagraphStyle(
            name="TotalBold",
            fontSize=12,
            leading=14,
            textColor="black",
            spaceBefore=4
        ))

    # ---------------------------------------------------

    def generate_pdf(self, number, customer, items, subtotal, iva, total):
        """Genera la factura interna PDF con estilo moderno."""

        os.makedirs("facturas", exist_ok=True)
        filename = f"facturas/{number}.pdf"

        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            leftMargin=15*mm,
            rightMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )

        elements = []

        # ===============================
        #      ENCABEZADO FACTURA
        # ===============================
        title = Paragraph(f"<b>FACTURA X</b>", self.styles["InvoiceTitle"])
        elements.append(title)

        subtitle = Paragraph(f"N° {number} — Fecha: {datetime.now().strftime('%d/%m/%Y')}",
                             self.styles["SectionHeader"])
        elements.append(subtitle)
        elements.append(Spacer(1, 8))

        # ===============================
        #        DATOS EMPRESA
        # ===============================
        company_text = f"""
        <b>{COMPANY_CONFIG['name']}</b><br/>
        CUIT: {COMPANY_CONFIG['cuit']}<br/>
        {COMPANY_CONFIG['address']}<br/>
        Tel: {COMPANY_CONFIG['phone']} - Email: {COMPANY_CONFIG['email']}
        """

        elements.append(Paragraph(company_text, self.styles["NormalSmall"]))
        elements.append(Spacer(1, 12))

        # ===============================
        #       DATOS DEL CLIENTE
        # ===============================
        elements.append(Paragraph("Datos del cliente", self.styles["SectionHeader"]))

        customer_text = f"""
            <b>{customer[1]}</b><br/>
            CUIT: {customer[2]}<br/>
            Domicilio: {customer[3]}<br/>
            Teléfono: {customer[4]}
        """

        elements.append(Paragraph(customer_text, self.styles["NormalSmall"]))
        elements.append(Spacer(1, 12))

        # ===============================
        #           TABLA ITEMS
        # ===============================

        table_data = [["Código", "Cant.", "P. Unit.", "Subtotal"]]

        for pid, q, price in items:
            table_data.append([pid, q, f"${price:.2f}", f"${q*price:.2f}"])

        table = Table(table_data, colWidths=[30*mm, 60*mm, 20*mm, 30*mm, 30*mm])

        table_style = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (2, 1), (4, -1), "CENTER"),
            ("ALIGN", (3, 1), (3, -1), "RIGHT"),
            ("ALIGN", (4, 1), (4, -1), "RIGHT"),
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
        
        table.setStyle(table_style)
        elements.append(table)
        elements.append(Spacer(1, 15))

        # ===============================
        #            TOTALES
        # ===============================
        totals_data = [
            ["Subtotal:", f"${subtotal:.2f}"],
            ["IVA 21%:", f"${iva:.2f}"],
            ["TOTAL:", f"${total:.2f}"]
        ]

        totals_table = Table(totals_data, colWidths=[120*mm, 40*mm])
        totals_table.setStyle(TableStyle([
            ("FONTNAME", (0,2), (-1,2), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 11),
            ("ALIGN", (1,0), (1,-1), "RIGHT"),
            ("LINEBELOW", (0,2), (-1,2), 1, colors.black),
        ]))
        elements.append(totals_table)

        elements.append(Spacer(1, 20))

        # ===============================
        #       PIE DE PÁGINA
        # ===============================

        footer = Paragraph(
            "Documento interno sin validez fiscal.",
            self.styles["NormalSmall"]
        )
        elements.append(footer)

        doc.build(elements)
        return filename
