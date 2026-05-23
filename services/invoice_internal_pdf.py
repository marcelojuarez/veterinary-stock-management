import logging
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

logger = logging.getLogger(__name__)
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from datetime import datetime
import os
from config.settings import COMPANY_CONFIG
from reportlab.platypus import Image
from decimal import Decimal
from utils.utils import format_currency
from utils.receipts.paths import get_base_folder
import os
from utils.receipts.paths import get_client_folder

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
            fontSize=6,
            alignment=1,
            textColor=colors.black,
            leading=10
        ))

    # ---------------------------------------------------

    def generate_pdf(self, invoice_id, number, customer, items, subtotal, iva_breakdown, total):
        """Genera la factura interna PDF con estilo moderno."""
        facturas_dir = os.path.join(get_client_folder(customer[1]), "Facturas")
        os.makedirs(facturas_dir, exist_ok=True)
        filename = os.path.join(facturas_dir, f"{number}.pdf")
        
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
        logo_path = "assets/logo.png"
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
        invoice_code_para = Paragraph(f"COD. {invoice_id}", self.styles["InvoiceCode"])
        
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

        # Encabezado de tabla: precio neto + columna IVA%
        table_data = [["Descripción", "Cant.", "P. Neto Unit.", "IVA %", "Subtotal Neto"]]

        for item in items:
            # Formato enriquecido: (id, name, qty, net_unit, [observations,] rate)
            if len(item) == 7:
                # con observaciones (honorarios)
                _, name, _, q, net_unit, observations, rate = item
                full_description = f"{name}\n{observations}" if observations else name
                description_para = Paragraph(full_description, self.styles["NormalSmall"])
            else:
                # producto normal
                _, name, pack, q, net_unit, rate = item
                description_para = Paragraph(f'{name} {pack}', self.styles["NormalSmall"])

            line_net = q * net_unit
            iva_pct_str = f"{rate * 100:.1f}%" if rate > 0 else "Exento"

            table_data.append([
                description_para,
                str(int(q)),
                f"${format_currency(net_unit)}",
                iva_pct_str,
                f"${format_currency(line_net)}"
            ])

        table = Table(table_data, colWidths=[80*mm, 18*mm, 32*mm, 20*mm, 30*mm])

        table_style = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (-1, 0), "CENTER"),
            ("ALIGN", (1, 1), (1, -1), "CENTER"),   # Cant.
            ("ALIGN", (2, 1), (2, -1), "RIGHT"),    # P. Neto Unit.
            ("ALIGN", (3, 1), (3, -1), "CENTER"),   # IVA %
            ("ALIGN", (4, 1), (4, -1), "RIGHT"),    # Subtotal Neto
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 4),
            ("RIGHTPADDING", (0,0), (-1,-1), 4),
            ("TOPPADDING", (0,1), (-1,-1), 6),
            ("BOTTOMPADDING", (0,1), (-1,-1), 6),
        ])
        
        table.setStyle(table_style)
        elements.append(table)
        elements.append(Spacer(1, 15))

        # ===============================
        #            TOTALES
        # ===============================

        # Subtotal neto
        totals_data = [["Subtotal neto:", f"${format_currency(subtotal)}"]]

        # Una línea por cada alícuota que tenga monto > 0
        sorted_rates = sorted(
            [(Decimal(k), v) for k, v in iva_breakdown.items() if v > 0],
            key=lambda x: x[0],
            reverse=True
        )

        for pct_key, iva_amount in sorted_rates:
            if pct_key == 0:
                label = "IVA Exento:"
            else:
                label = f"IVA {pct_key.normalize()}%:"
            totals_data.append([label, f"${format_currency(iva_amount)}"])

        # Total final
        totals_data.append(["TOTAL:", f"${format_currency(total)}"])

        total_row_idx = len(totals_data) - 1

        totals_table = Table(totals_data, colWidths=[120*mm, 40*mm])
        totals_table.setStyle(TableStyle([
            ("FONTNAME", (0, total_row_idx), (-1, total_row_idx), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("LINEABOVE", (0, total_row_idx), (-1, total_row_idx), 1.5, colors.black),
            ("TOPPADDING", (0, total_row_idx), (-1, total_row_idx), 6),
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