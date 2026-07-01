from reportlab.lib.pagesizes import A4
from reportlab.platypus import BaseDocTemplate, SimpleDocTemplate, PageTemplate, Frame, FrameBreak, PageBreak, Table, TableStyle, Paragraph, Spacer, Image
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
            fontSize=13,
            alignment=1,
            spaceAfter=4,
            textColor=colors.black,
            leading=16
        ))

        self.styles.add(ParagraphStyle(
            name="SectionHeader",
            fontSize=9,
            textColor=colors.black,
            leading=12,
            spaceAfter=2,
            spaceBefore=4,
            fontName="Helvetica-Bold"
        ))

        self.styles.add(ParagraphStyle(
            name="NormalSmall",
            fontSize=7.5,
            leading=10
        ))

        self.styles.add(ParagraphStyle(
            name="RemitoType",
            fontSize=20,
            alignment=1,
            textColor=colors.black,
            fontName="Helvetica-Bold",
            leading=24
        ))

        self.styles.add(ParagraphStyle(
            name="RemitoCode",
            fontSize=7,
            alignment=1,
            textColor=colors.black,
            leading=9
        ))

    def _build_elements(self, number, customer, items, label="ORIGINAL"):
        """Build elements for one copy of the remito (sized for half-A4 frame)."""
        elements = []

        # Banner (ORIGINAL / DUPLICADO)
        banner = Table(
            [[Paragraph(f"<b>{label}</b>", self.styles["RemitoTitle"])]],
            colWidths=[176 * mm]
        )
        banner.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        elements.append(banner)
        elements.append(Spacer(1, 2))

        # Header: logo + R box + number
        logo_path = "assets/logo.png"
        if os.path.exists(logo_path):
            logo_img = Image(logo_path, width=18 * mm, height=18 * mm)
        else:
            logo_img = Paragraph("<b>LOGO</b>", self.styles["RemitoTitle"])

        company_info = Paragraph(f"""
        <b>{COMPANY_CONFIG['name']}</b><br/>
        <b>RAZON SOCIAL:</b> {COMPANY_CONFIG['name']}<br/>
        <b>DIRECCION:</b> {COMPANY_CONFIG['address']}<br/>
        <b>CONDICION IVA:</b> RESPONSABLE INSCRIPTO
        """, self.styles["NormalSmall"])

        left_block = Table([[logo_img], [Spacer(1, 2)], [company_info]])
        left_block.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        remito_type_para = Paragraph("R", self.styles["RemitoType"])
        remito_code_para = Paragraph("COD. 999", self.styles["RemitoCode"])
        center_block = Table([[remito_type_para], [remito_code_para]], colWidths=[22 * mm])
        center_block.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (0, 0), 5),
            ('BOTTOMPADDING', (0, 0), (0, 0), 1),
            ('TOPPADDING', (0, 1), (0, 1), 1),
            ('BOTTOMPADDING', (0, 1), (0, 1), 3),
        ]))

        right_info = Paragraph(f"""
        <b>REMITO N° {number}</b><br/>
        <b>FECHA:</b> {datetime.now().strftime('%d/%m/%Y')}<br/>
        <b>C.U.I.T.:</b> {COMPANY_CONFIG['cuit']}<br/>
        """, self.styles["NormalSmall"])

        header_table = Table(
            [[left_block, center_block, right_info]],
            colWidths=[62 * mm, 22 * mm, 92 * mm]
        )
        header_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('LEFTPADDING', (0, 0), (0, 0), 5),
            ('LEFTPADDING', (1, 0), (1, 0), 0),
            ('RIGHTPADDING', (1, 0), (1, 0), 0),
            ('RIGHTPADDING', (2, 0), (2, 0), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        elements.append(header_table)
        elements.append(Spacer(1, 6))

        # Customer data
        elements.append(Paragraph("Datos del cliente", self.styles["SectionHeader"]))
        customer_text = f"""
            <b>{customer[1]}</b><br/>
            CUIT/DNI: {customer[2] or '-'}<br/>
            Domicilio: {customer[3] or '-'}<br/>
            Teléfono: {customer[4] or '-'}
        """
        elements.append(Paragraph(customer_text, self.styles["NormalSmall"]))
        elements.append(Spacer(1, 6))

        # Products table
        table_data = [["Código", "Descripción", "Cantidad"]]
        for it in items:
            table_data.append([it['product_id'], f'{it["name"]} {it["pack"]}', it['quantity']])

        table = Table(table_data, colWidths=[18 * mm, 120 * mm, 28 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 12))

        # Signatures
        firma_style = ParagraphStyle(name="FirmaStyle", fontSize=8, leading=11)
        elements.append(Paragraph("<b>Firma del Cliente:</b> _____________________________", firma_style))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph("<b>Aclaración:</b> _____________________________", firma_style))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph("<b>DNI:</b> _____________________________", firma_style))
        elements.append(Spacer(1, 8))

        # Footer
        elements.append(Paragraph("Documento no válido como factura.", self.styles["NormalSmall"]))

        return elements

    _HALF_PAGE_SAFETY_MM = 5  # buffer for inter-element spacing not captured by wrap()

    def _fits_in_half_page(self, number, customer, items) -> bool:
        """Measure actual rendered height to decide between 1-page and 2-page layout."""
        frame_w   = A4[0] - 16 * mm          # lm=8mm + rm=8mm
        available = A4[1] / 2 - 12 * mm      # half height minus tm+bm (6mm each)
        try:
            elements   = self._build_elements(number, customer, items, "ORIGINAL")
            measured_h = sum(el.wrap(frame_w, A4[1])[1] for el in elements)
            return measured_h + self._HALF_PAGE_SAFETY_MM * mm <= available
        except Exception:
            return False  # on any error, prefer the safe 2-page layout

    def _generate_two_on_one(self, filename, number, customer, items):
        """Both copies on a single A4 — cut along the dashed centre line."""
        lm, rm, tm, bm = 8*mm, 8*mm, 6*mm, 6*mm
        half_h = A4[1] / 2

        top_frame = Frame(
            x1=lm, y1=half_h + bm,
            width=A4[0] - lm - rm, height=half_h - tm - bm,
            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0
        )
        bottom_frame = Frame(
            x1=lm, y1=bm,
            width=A4[0] - lm - rm, height=half_h - tm - bm,
            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0
        )

        def draw_separator(canvas, _doc):
            canvas.saveState()
            canvas.setLineWidth(0.5)
            canvas.setDash(5, 3)
            canvas.line(5 * mm, half_h, A4[0] - 5 * mm, half_h)
            canvas.setDash()
            canvas.restoreState()

        template = PageTemplate(id='duplex', frames=[top_frame, bottom_frame], onPage=draw_separator)
        doc = BaseDocTemplate(filename, pagesize=A4, pageTemplates=[template])

        story = []
        story.extend(self._build_elements(number, customer, items, "ORIGINAL"))
        story.append(FrameBreak())
        story.extend(self._build_elements(number, customer, items, "DUPLICADO"))
        doc.build(story)

    def _generate_one_per_page(self, filename, number, customer, items):
        """ORIGINAL on page 1, DUPLICADO on page 2 — each on a full A4 sheet."""
        doc = SimpleDocTemplate(
            filename, pagesize=A4,
            leftMargin=8*mm, rightMargin=8*mm,
            topMargin=6*mm, bottomMargin=6*mm
        )
        story = []
        story.extend(self._build_elements(number, customer, items, "ORIGINAL"))
        story.append(PageBreak())
        story.extend(self._build_elements(number, customer, items, "DUPLICADO"))
        doc.build(story)

    def generate_remito(self, number, customer, items):
        customer_name = customer[1] if isinstance(customer, (tuple, list)) else customer.get("nombre", "Cliente")
        filename = remito_path(customer_name, number)

        if self._fits_in_half_page(number, customer, items):
            self._generate_two_on_one(filename, number, customer, items)
        else:
            self._generate_one_per_page(filename, number, customer, items)

        return filename
