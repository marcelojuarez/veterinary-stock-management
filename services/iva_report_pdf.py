import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from config.settings import COMPANY_CONFIG
from utils.receipts.paths import get_base_folder


# ─────────────────────────────────────────────
#  Paleta de colores
# ─────────────────────────────────────────────
COLOR_HEADER    = colors.HexColor("#1565C0")
COLOR_SUBHEADER = colors.HexColor("#1976D2")
COLOR_TOTAL_BG  = colors.HexColor("#E3F2FD")
COLOR_ALT_ROW   = colors.HexColor("#F5F5F5")
COLOR_RED       = colors.HexColor("#C62828")
COLOR_GREEN     = colors.HexColor("#2E7D32")
COLOR_GRID      = colors.HexColor("#BDBDBD")

PAGE_W, PAGE_H = A4
L_MARGIN = R_MARGIN = 15 * mm
USABLE_W = PAGE_W - L_MARGIN - R_MARGIN


def _money(value):
    try:
        v = float(value or 0)
        return f"${v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "$0,00"


def _pct(value):
    try:
        return f"{float(value or 0):.1f}%"
    except Exception:
        return "0.0%"


class IVAReportPDF:
    """
    Genera el reporte fiscal IVA/Percepciones/Retenciones en PDF.

    Uso:
        pdf = IVAReportPDF()
        path = pdf.generate(
            month=3, year=2026,
            position=...,
            position_detail=...,
            sales=..., purchases=...,
            suffered_percept=..., made_percept=...,
            suffered_ret=..., made_ret=...,
            total_per=(total_s, total_e),
            total_ret=(total_s, total_e),
        )
    """

    MESES = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._add_styles()

    # ─────────────────────────────────────────
    #  Estilos
    # ─────────────────────────────────────────
    def _add_styles(self):
        self.styles.add(ParagraphStyle(
            "ReportTitle", fontSize=18, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=1, leading=22
        ))
        self.styles.add(ParagraphStyle(
            "SectionTitle", fontSize=12, fontName="Helvetica-Bold",
            textColor=colors.white, leading=16
        ))
        self.styles.add(ParagraphStyle(
            "SubSection", fontSize=10, fontName="Helvetica-Bold",
            textColor=COLOR_SUBHEADER, leading=14, spaceBefore=8
        ))
        self.styles.add(ParagraphStyle(
            "Normal9", fontSize=9, fontName="Helvetica", leading=12
        ))
        self.styles.add(ParagraphStyle(
            "Normal9Bold", fontSize=9, fontName="Helvetica-Bold", leading=12
        ))
        self.styles.add(ParagraphStyle(
            "CompanyInfo", fontSize=9, fontName="Helvetica",
            textColor=colors.white, leading=13
        ))

    # ─────────────────────────────────────────
    #  Helpers de tablas
    # ─────────────────────────────────────────
    def _base_style(self):
        return [
            ("FONTNAME",    (0, 0), (-1,  0), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 8),
            ("BACKGROUND",  (0, 0), (-1,  0), COLOR_HEADER),
            ("TEXTCOLOR",   (0, 0), (-1,  0), colors.white),
            ("ALIGN",       (0, 0), (-1,  0), "CENTER"),
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
            ("GRID",        (0, 0), (-1, -1), 0.4, COLOR_GRID),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_ALT_ROW]),
            ("TOPPADDING",  (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0,0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING",(0, 0), (-1, -1), 5),
        ]

    def _total_row_style(self, row_idx):
        return [
            ("BACKGROUND",  (0, row_idx), (-1, row_idx), COLOR_TOTAL_BG),
            ("FONTNAME",    (0, row_idx), (-1, row_idx), "Helvetica-Bold"),
            ("LINEABOVE",   (0, row_idx), (-1, row_idx), 1, COLOR_HEADER),
        ]

    def _section_header(self, text, color=None):
        color = color or COLOR_HEADER
        bg = Table(
            [[Paragraph(text, self.styles["SectionTitle"])]],
            colWidths=[USABLE_W]
        )
        bg.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, -1), color),
            ("LEFTPADDING",  (0, 0), (-1, -1), 10),
            ("TOPPADDING",   (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ]))
        return bg

    # ─────────────────────────────────────────
    #  Encabezado del documento
    # ─────────────────────────────────────────
    def _build_header(self, mes, anio):
        elements = []

        periodo = f"{self.MESES[mes - 1]} {anio}"
        generado = datetime.now().strftime("%d/%m/%Y %H:%M")

        header_data = [[
            Paragraph(
                f"<b>{COMPANY_CONFIG.get('name', 'Empresa')}</b><br/>"
                f"<font size=8>CUIT: {COMPANY_CONFIG.get('cuit', '')} · "
                f"{COMPANY_CONFIG.get('address', '')}</font>",
                self.styles["CompanyInfo"]
            ),
            Paragraph(
                f"REPORTE FISCAL<br/>"
                f"<font size=11>Período: {periodo}</font>",
                self.styles["ReportTitle"]
            ),
            Paragraph(
                f"Generado: {generado}<br/>"
                f"<font size=8>Documento interno</font>",
                self.styles["CompanyInfo"]
            ),
        ]]

        header_table = Table(
            header_data,
            colWidths=[USABLE_W * 0.35, USABLE_W * 0.30, USABLE_W * 0.35]
        )
        header_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), COLOR_HEADER),
            ("TEXTCOLOR",     (0, 0), (-1, -1), colors.white),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN",         (1, 0), (1,  0),  "CENTER"),
            ("ALIGN",         (2, 0), (2,  0),  "RIGHT"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))

        elements.append(header_table)
        elements.append(Spacer(1, 10))
        return elements

    # ─────────────────────────────────────────
    #  Cards resumen IVA
    # ─────────────────────────────────────────
    def _build_iva_cards(self, posicion):
        elements = []
        elements.append(self._section_header("📊  RESUMEN IVA"))
        elements.append(Spacer(1, 6))

        saldo = float(posicion.get("balance", 0) or 0)
        saldo_color = "#C62828" if saldo > 0 else "#2E7D32"
        saldo_tipo  = posicion.get("status", "")

        cards_data = [[
            Paragraph(
                f"<b>IVA VENTAS</b><br/>"
                f"<font size=14><b>{_money(posicion.get('iva_sales', 0))}</b></font><br/>"
                f"<font size=8>Débito Fiscal</font>",
                self.styles["Normal9"]
            ),
            Paragraph(
                f"<b>IVA COMPRAS</b><br/>"
                f"<font size=14><b>{_money(posicion.get('purchases_iva', 0))}</b></font><br/>"
                f"<font size=8>Crédito Fiscal</font>",
                self.styles["Normal9"]
            ),
            Paragraph(
                f"<b>SALDO IVA</b><br/>"
                f"<font size=14 color='{saldo_color}'>"
                f"<b>{_money(abs(saldo))}</b></font><br/>"
                f"<font size=8>{saldo_tipo}</font>",
                self.styles["Normal9"]
            ),
        ]]

        cards_table = Table(cards_data, colWidths=[USABLE_W / 3] * 3)
        cards_table.setStyle(TableStyle([
            ("BOX",          (0, 0), (0, 0), 1, COLOR_GRID),
            ("BOX",          (1, 0), (1, 0), 1, COLOR_GRID),
            ("BOX",          (2, 0), (2, 0), 1, COLOR_GRID),
            ("BACKGROUND",   (0, 0), (0, 0), colors.HexColor("#E8F5E9")),
            ("BACKGROUND",   (1, 0), (1, 0), colors.HexColor("#FFF3E0")),
            ("BACKGROUND",   (2, 0), (2, 0), colors.HexColor("#E3F2FD")),
            ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",   (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ]))

        elements.append(cards_table)
        elements.append(Spacer(1, 10))
        return elements

    # ─────────────────────────────────────────
    #  Tabla resumen por alícuota
    # ─────────────────────────────────────────
    def _build_resumen_aliquots(self, detalle_posicion):
        elements = []
        elements.append(Paragraph("Posición IVA por Alícuota", self.styles["SubSection"]))

        cols = ["Alícuota", "Neto Ventas", "IVA Ventas", "Neto Compras",
                "IVA Compras", "Saldo Bruto", "Saldo Neto"]
        col_w = [USABLE_W * p for p in [0.11, 0.15, 0.14, 0.15, 0.14, 0.155, 0.155]]

        data = [cols]
        for item in detalle_posicion.get("rows", []):
            data.append([
                item.get("aliquot", ""),
                _money(item.get("sales_net", 0)),
                _money(item.get("iva_sales", 0)),
                _money(item.get("purchases_net", 0)),
                _money(item.get("purchases_iva", 0)),
                _money(item.get("balance", 0)),
                "—",
            ])

        # Fila subtotal bruto
        data.append([
            "Subtotal", "—",
            _money(detalle_posicion.get("total_iva_sales", 0)),
            "—",
            _money(detalle_posicion.get("total_purchases_iva", 0)),
            _money(detalle_posicion.get("balance_gross", 0)),
            "—",
        ])
        subtotal_row = len(data) - 1

        # Filas de ajuste
        ret_iva = detalle_posicion.get("ret_iva", 0)
        per_iva = detalle_posicion.get("per_iva", 0)
        ajuste_rows = []
        if ret_iva:
            data.append(["Ret. IVA sufridas", "—", f"-{_money(ret_iva)}",
                         "—", "—", "—", "—"])
            ajuste_rows.append(len(data) - 1)
        if per_iva:
            data.append(["Perc. IVA sufridas", "—", "—",
                         "—", f"+{_money(per_iva)}", "—", "—"])
            ajuste_rows.append(len(data) - 1)

        # Fila TOTAL NETO
        data.append([
            "TOTAL NETO", "—",
            _money(detalle_posicion.get("fiscal_debt",
                   detalle_posicion.get("total_iva_sales", 0))),
            "—",
            _money(detalle_posicion.get("fiscal_credit",
                   detalle_posicion.get("total_purchases_iva", 0))),
            _money(detalle_posicion.get("balance_gross", 0)),
            _money(detalle_posicion.get("balance_total", 0)),
        ])
        total_row = len(data) - 1

        style = self._base_style()
        style += self._total_row_style(total_row)
        style += [
            ("ALIGN",      (1, 1), (-1, -1), "RIGHT"),
            ("BACKGROUND", (0, subtotal_row), (-1, subtotal_row), colors.HexColor("#F5F5F5")),
            ("FONTNAME",   (0, subtotal_row), (-1, subtotal_row), "Helvetica-Bold"),
        ]
        for ar in ajuste_rows:
            style += [
                ("BACKGROUND", (0, ar), (-1, ar), colors.HexColor("#FFF9C4")),
                ("FONTNAME",   (0, ar), (-1, ar), "Helvetica-Oblique"),
            ]

        t = Table(data, colWidths=col_w)
        t.setStyle(TableStyle(style))
        elements.append(t)
        elements.append(Spacer(1, 10))
        return elements

    # ─────────────────────────────────────────
    #  Tabla detalle ventas / compras
    # ─────────────────────────────────────────
    def _build_detalle_table(self, titulo, rows, cols, col_widths, extract_fn, subtitulo=None):
        elements = []
        if subtitulo:
            elements.append(Paragraph(subtitulo, self.styles["SubSection"]))
        else:
            elements.append(Paragraph(titulo, self.styles["SubSection"]))

        data = [cols]
        total_neto = total_iva = total_total = 0.0

        for row in rows:
            extracted = extract_fn(row)
            data.append(extracted)
            try:
                total_neto  += float(row[-3] or 0)
                total_iva   += float(row[-2] or 0)
                total_total += float(row[-1] or 0)
            except Exception:
                pass

        # Fila totales
        empty = [""] * (len(cols) - 4)
        data.append(["TOTAL"] + empty + [
            _money(total_neto), _money(total_iva), _money(total_total)
        ])

        style = self._base_style()
        style += self._total_row_style(len(data) - 1)
        style += [("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                  ("ALIGN", (0, 1), (0, -1), "LEFT")]

        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle(style))
        elements.append(t)
        elements.append(Spacer(1, 8))
        return elements

    # ─────────────────────────────────────────
    #  Tabla percepciones / retenciones
    # ─────────────────────────────────────────
    def _build_simple_table(self, subtitulo, rows, cols, col_widths, extract_fn, monto_col_idx=-1):
        elements = []
        elements.append(Paragraph(subtitulo, self.styles["SubSection"]))

        if not rows:
            elements.append(Paragraph(
                "Sin movimientos en el período.", self.styles["Normal9"]
            ))
            elements.append(Spacer(1, 6))
            return elements

        data = [cols]
        total = 0.0
        for row in rows:
            extracted = extract_fn(row)
            data.append(extracted)
            try:
                total += float(row[monto_col_idx] or 0)
            except Exception:
                pass

        # Fila TOTAL
        empty = [""] * (len(cols) - 2)
        data.append(["", "TOTAL"] + empty + [_money(total)])

        style = self._base_style()
        style += self._total_row_style(len(data) - 1)
        style += [("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                  ("ALIGN", (0, 1), (2, -1), "LEFT")]

        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle(style))
        elements.append(t)
        elements.append(Spacer(1, 8))
        return elements

    # ─────────────────────────────────────────
    #  Sección otros (per + ret) cards
    # ─────────────────────────────────────────
    def _build_otros_cards(self, totales_per, totales_ret):
        elements = []
        elements.append(self._section_header("📋  PERCEPCIONES Y RETENCIONES"))
        elements.append(Spacer(1, 6))

        total_per_s, total_per_e = totales_per
        total_ret_s, total_ret_e = totales_ret

        cards_data = [[
            Paragraph(
                f"<b>PERC. SUFRIDAS</b><br/>"
                f"<font size=12><b>{_money(total_per_s)}</b></font><br/>"
                f"<font size=7>En compras a proveedores</font>",
                self.styles["Normal9"]
            ),
            Paragraph(
                f"<b>PERC. EFECTUADAS</b><br/>"
                f"<font size=12><b>{_money(total_per_e)}</b></font><br/>"
                f"<font size=7>Cobradas a clientes</font>",
                self.styles["Normal9"]
            ),
            Paragraph(
                f"<b>RET. SUFRIDAS</b><br/>"
                f"<font size=12><b>{_money(total_ret_s)}</b></font><br/>"
                f"<font size=7>Realizadas por clientes</font>",
                self.styles["Normal9"]
            ),
            Paragraph(
                f"<b>RET. EFECTUADAS</b><br/>"
                f"<font size=12><b>{_money(total_ret_e)}</b></font><br/>"
                f"<font size=7>Realizadas a proveedores</font>",
                self.styles["Normal9"]
            ),
        ]]

        cards_table = Table(cards_data, colWidths=[USABLE_W / 4] * 4)
        cards_table.setStyle(TableStyle([
            ("BOX",          (c, 0), (c, 0), 1, COLOR_GRID) for c in range(4)
        ] + [
            ("BACKGROUND",   (0, 0), (-1, -1), colors.HexColor("#F3E5F5")),
            ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",   (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ]))

        elements.append(cards_table)
        elements.append(Spacer(1, 10))
        return elements

    # ─────────────────────────────────────────
    #  Método principal
    # ─────────────────────────────────────────
    def generate(self, month, year, position, position_detail,
                 sales, purchases,
                 suffered_percept, made_percept,
                 suffered_ret, made_ret,
                 total_per, total_ret):

        # unpack totals tuples
        total_per_s, total_per_e = total_per
        total_ret_s, total_ret_e = total_ret

        periodo = f"{self.MESES[month - 1]}_{year}"
        reportes_dir = os.path.join(get_base_folder(), "Reportes")
        os.makedirs(reportes_dir, exist_ok=True)
        filename = os.path.join(reportes_dir, f"reporte_iva_{periodo}.pdf")

        doc = SimpleDocTemplate(
            filename, pagesize=A4,
            leftMargin=L_MARGIN, rightMargin=R_MARGIN,
            topMargin=12 * mm, bottomMargin=12 * mm
        )

        elements = []

        # ── Encabezado ──
        elements += self._build_header(month, year)

        # ── Sección IVA ──
        elements += self._build_iva_cards(position)
        elements += self._build_resumen_aliquots(position_detail)

        # Detalle ventas
        elements.append(self._section_header("💰  DETALLE VENTAS"))
        elements.append(Spacer(1, 4))
        cols_v = ["Fecha", "Venta#", "Cliente", "CUIT", "Alíc.", "Neto", "IVA", "Total"]
        w_v = [USABLE_W * p for p in [0.09, 0.07, 0.22, 0.14, 0.07, 0.14, 0.13, 0.14]]

        def extract_venta(v):
            fecha = v[1][:10] if v[1] and len(v[1]) > 10 else (v[1] or "")
            return [fecha, str(v[0]), str(v[2]), str(v[3]),
                    _pct(v[5]), _money(v[6]), _money(v[7]), _money(v[8])]

        elements += self._build_detalle_table(
            "Detalle Ventas", sales, cols_v, w_v, extract_venta, subtitulo="Ventas del período"
        )

        # Detalle compras
        elements.append(self._section_header("🛒  DETALLE COMPRAS"))
        elements.append(Spacer(1, 4))
        cols_c = ["Fecha", "Compra#", "Proveedor", "CUIT", "Alíc.", "Neto", "IVA", "Total"]
        w_c = w_v

        def extract_compra(c):
            fecha = c[1][:10] if c[1] and len(c[1]) > 10 else (c[1] or "")
            return [fecha, str(c[0]), str(c[2]), str(c[3]),
                    _pct(c[4]), _money(c[5]), _money(c[6]), _money(c[7])]

        elements += self._build_detalle_table(
            "Detalle Compras", purchases, cols_c, w_c, extract_compra, subtitulo="Compras del período"
        )

        # ── Sección Percepciones / Retenciones ──
        elements.append(PageBreak())
        elements += self._build_otros_cards(
            (total_per_s, total_per_e),
            (total_ret_s, total_ret_e)
        )

        # Percepciones sufridas
        cols_ps = ["Fecha", "Factura#", "Proveedor", "CUIT", "Tipo", "Monto"]
        w_ps = [USABLE_W * p for p in [0.12, 0.12, 0.28, 0.18, 0.12, 0.18]]

        def extract_perc_s(p):
            fecha = p[0][:10] if p[0] and len(p[0]) > 10 else (p[0] or "")
            return [fecha, str(p[1]), str(p[2]), str(p[3]), str(p[4]), _money(p[5])]

        elements += self._build_simple_table(
            "Percepciones Sufridas (en compras)", suffered_percept,
            cols_ps, w_ps, extract_perc_s, monto_col_idx=5
        )

        def extract_perc_e(p):
            fecha = p[0][:10] if p[0] and len(p[0]) > 10 else (p[0] or "")
            return [fecha, str(p[1]), str(p[2]), str(p[3]), str(p[4]), _money(p[5])]

        elements += self._build_simple_table(
            "Percepciones Efectuadas (a clientes)", made_percept,
            cols_ps, w_ps, extract_perc_e, monto_col_idx=5
        )

        # Retenciones sufridas
        cols_rs = ["Fecha", "Venta#", "Cliente", "CUIT", "Tipo", "Certificado", "Monto"]
        w_rs = [USABLE_W * p for p in [0.11, 0.09, 0.22, 0.16, 0.10, 0.14, 0.18]]

        def extract_ret_s(r):
            fecha = r[0][:10] if r[0] and len(r[0]) > 10 else (r[0] or "")
            return [fecha, str(r[1]), str(r[2]), str(r[3]),
                    str(r[4]), str(r[5] or "—"), _money(r[6])]

        elements += self._build_simple_table(
            "Retenciones Sufridas (en ventas)", suffered_ret,
            cols_rs, w_rs, extract_ret_s, monto_col_idx=6
        )

        cols_re = ["Fecha", "Compra#", "Proveedor", "CUIT", "Tipo", "Certificado", "Monto"]

        def extract_ret_e(r):
            fecha = r[0][:10] if r[0] and len(r[0]) > 10 else (r[0] or "")
            return [fecha, str(r[1]), str(r[2]), str(r[3]),
                    str(r[4]), str(r[5] or "—"), _money(r[6])]

        elements += self._build_simple_table(
            "Retenciones Efectuadas (a proveedores)", made_ret,
            cols_re, w_rs, extract_ret_e, monto_col_idx=6
        )

        doc.build(elements)
        return filename