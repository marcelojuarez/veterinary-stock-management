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
from reportlab.platypus import Image


class InvoiceInternalPDFService:

    def __init__(self):
        self.styles = getSampleStyleSheet()

        # Título grande
        self.styles.add(ParagraphStyle(
            name="InvoiceTitle",
            fontSize=18,
            spaceAfter=10,
            alignment=1,  # centre
            textColor=colors.black,
            leading=22
        ))

        # Subtítulos
        self.styles.add(ParagraphStyle(
            name="SectionHeader",
            fontSize=11,
            textColor=colors.black,
            leading=14,
            spaceAfter=4,
            spaceBefore=8,
            fontName="Helvetica-Bold"
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
            textColor=colors.black,
            spaceBefore=4
        ))
        
        # Estilo para el tipo de factura (letra grande en el recuadro)
        self.styles.add(ParagraphStyle(
            name="InvoiceType",
            fontSize=24,
            alignment=1,
            textColor=colors.black,
            fontName="Helvetica-Bold",
            leading=28
        ))
        
        # Estilo para código
        self.styles.add(ParagraphStyle(
            name="InvoiceCode",
            fontSize=8,
            alignment=1,
            textColor=colors.black,
            leading=10
        ))

    # ---------------------------------------------------

    def generate_pdf(self, number, customer, items, subtotal, iva, total):
        """Genera la factura interna PDF con estilo moderno."""

        os.makedirs("comprobantes/facturas", exist_ok=True)
        filename = f"comprobantes/facturas/{number}.pdf"

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
        #   BANNER SUPERIOR "ORIGINAL"
        # ===============================
        original_banner = Table([[Paragraph("<b>ORIGINAL</b>", self.styles["InvoiceTitle"])]], 
                                colWidths=[180*mm])
        original_banner.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.white),
            ('BOX', (0,0), (-1,-1), 1.5, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(original_banner)
        elements.append(Spacer(1, 2))

        # ===============================
        #      ENCABEZADO PRINCIPAL
        # ===============================

        # COLUMNA IZQUIERDA: Logo + Datos empresa
        logo_path = "assets/logo.jpg"
        if os.path.exists(logo_path):
            logo_img = Image(logo_path, width=25*mm, height=25*mm)
        else:
            logo_img = Paragraph("<b>LOGO</b>", self.styles["InvoiceTitle"])

        company_info = Paragraph(f"""
        <b>{COMPANY_CONFIG['name']}</b><br/>
        <b>RAZON SOCIAL:</b> {COMPANY_CONFIG['name']}<br/>
        <b>DIRECCION:</b> {COMPANY_CONFIG['address']}<br/>
        <b>CONDICION IVA:</b> RESPONSABLE INSCRIPTO
        """, self.styles["NormalSmall"])

        left_block = Table([[logo_img], [Spacer(1, 3)], [company_info]])
        left_block.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))

        # COLUMNA CENTRAL: Recuadro con tipo de factura
        invoice_type_para = Paragraph("X", self.styles["InvoiceType"])
        invoice_code_para = Paragraph("COD. 006", self.styles["InvoiceCode"])
        
        center_block = Table([[invoice_type_para], [invoice_code_para]], 
                            colWidths=[25*mm])
        center_block.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 2, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            ('RIGHTPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (0,0), 8),
            ('BOTTOMPADDING', (0,0), (0,0), 2),
            ('TOPPADDING', (0,1), (0,1), 2),
            ('BOTTOMPADDING', (0,1), (0,1), 4),
        ]))

        # COLUMNA DERECHA: Número de factura y datos
        right_info = Paragraph(f"""
        <b>FACTURA</b><br/>
        <b>{number}</b><br/><br/>
        <b>FECHA:</b> {datetime.now().strftime('%d/%m/%Y')}<br/>
        <b>C.U.I.T.:</b> {COMPANY_CONFIG['cuit']}<br/>
        """, self.styles["NormalSmall"])

        # Tabla principal con 3 columnas
        header_table = Table(
            [[left_block, center_block, right_info]],
            colWidths=[65*mm, 25*mm, 90*mm]
        )

        header_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1.5, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (1,0), (1,0), 'CENTER'),
            ('LEFTPADDING', (0,0), (0,0), 6),
            ('LEFTPADDING', (1,0), (1,0), 0),
            ('RIGHTPADDING', (1,0), (1,0), 0),
            ('RIGHTPADDING', (2,0), (2,0), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))

        elements.append(header_table)
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

        table_data = [["Descripción", "Cant.", "P. Unit.", "Subtotal"]]
        
        # MODIFICADO: Manejar items con 4 o 5 elementos
        for item in items:
            if len(item) == 5:
                # Item con observaciones (honorario)
                _, name, q, price, observations = item
                # Crear descripción completa con observaciones
                full_description = f"{name}\n{observations}"
                description_para = Paragraph(full_description, self.styles["NormalSmall"])
            else:
                # Item normal (producto)
                _, name, q, price = item
                description_para = Paragraph(name, self.styles["NormalSmall"])
            
            subtotal_item = q * price
            table_data.append([
                description_para,  # Usar Paragraph para permitir texto multilínea
                str(q),
                f"${price:.2f}",
                f"${subtotal_item:.2f}"
            ])

        table = Table(table_data, colWidths=[90*mm, 20*mm, 30*mm, 30*mm])

        table_style = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (-1, 0), "CENTER"),
            ("ALIGN", (1, 1), (1, -1), "CENTER"),
            ("ALIGN", (2, 1), (2, -1), "RIGHT"),
            ("ALIGN", (3, 1), (3, -1), "RIGHT"),
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),  # Cambiado de MIDDLE a TOP
            ("LEFTPADDING", (0,0), (-1,-1), 4),
            ("RIGHTPADDING", (0,0), (-1,-1), 4),
            ("TOPPADDING", (0,1), (-1,-1), 6),      # Más padding para items
            ("BOTTOMPADDING", (0,1), (-1,-1), 6),
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
            ("LINEABOVE", (0,2), (-1,2), 1.5, colors.black),
            ("TOPPADDING", (0,2), (-1,2), 6),
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