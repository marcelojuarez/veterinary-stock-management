from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
import os
from utils.receipts.paths import remito_path
from datetime import datetime
from config.settings import COMPANY_CONFIG

class RemitoPDF:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        
        self.styles.add(ParagraphStyle(
            name="RemitoTitle",
            fontSize=18,
            alignment=1,
            spaceAfter=10,
            textColor=colors.black,
            leading=22
        ))
        
        self.styles.add(ParagraphStyle(
            name="SectionHeader",
            fontSize=11,
            textColor=colors.black,
            leading=14,
            spaceAfter=4,
            spaceBefore=8,
            fontName="Helvetica-Bold"
        ))
        
        self.styles.add(ParagraphStyle(
            name="NormalSmall",
            fontSize=9,
            leading=12
        ))
        
        self.styles.add(ParagraphStyle(
            name="RemitoType",
            fontSize=24,
            alignment=1,
            textColor=colors.black,
            fontName="Helvetica-Bold",
            leading=28
        ))
        
        self.styles.add(ParagraphStyle(
            name="RemitoCode",
            fontSize=8,
            alignment=1,
            textColor=colors.black,
            leading=10
        ))

    def generate_remito(self, number, customer, items):
        customer_name = customer[1] if isinstance(customer, (tuple, list)) else customer.get("nombre", "Cliente")
        filename = remito_path(customer_name, number)

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
        original_banner = Table([[Paragraph("<b>ORIGINAL</b>", self.styles["RemitoTitle"])]], 
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
        logo_path = "assets/logo.png"
        if os.path.exists(logo_path):
            logo_img = Image(logo_path, width=25*mm, height=25*mm)
        else:
            logo_img = Paragraph("<b>LOGO</b>", self.styles["RemitoTitle"])

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

        # COLUMNA CENTRAL: Recuadro con R de REMITO
        remito_type_para = Paragraph("R", self.styles["RemitoType"])
        remito_code_para = Paragraph("COD. 999", self.styles["RemitoCode"])
        
        center_block = Table([[remito_type_para], [remito_code_para]], 
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

        # COLUMNA DERECHA: Número de remito y datos
        right_info = Paragraph(f"""
        <b>REMITO N° {number}</b><br/>
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
            CUIT/DNI: {customer[2]}<br/>
            Domicilio: {customer[3]}<br/>
            Teléfono: {customer[4]}
        """
        elements.append(Paragraph(customer_text, self.styles["NormalSmall"]))
        elements.append(Spacer(1, 12))

        # ===============================
        #    TABLA DE PRODUCTOS
        # ===============================
        table_data = [["Código", "Descripción", "Cantidad"]]
        for it in items:
            table_data.append([it['product_id'], f'{it['name']} {it['pack']}', it['quantity']])

        table = Table(table_data, colWidths=[40*mm, 100*mm, 30*mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 4),
            ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 30))

        # ===============================
        #          FIRMAS
        # ===============================
        firma_style = ParagraphStyle(
            name="FirmaStyle",
            fontSize=10,
            leading=14
        )
        
        elements.append(Paragraph("<b>Firma del Cliente:</b> _____________________________", firma_style))
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("<b>Aclaración:</b> _____________________________", firma_style))
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("<b>DNI:</b> _____________________________", firma_style))

        elements.append(Spacer(1, 20))

        # ===============================
        #       PIE DE PÁGINA
        # ===============================
        footer = Paragraph(
            "Documento no válido como factura.",
            self.styles["NormalSmall"]
        )
        elements.append(footer)

        doc.build(elements)
        return filename