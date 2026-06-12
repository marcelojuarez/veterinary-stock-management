import os
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, HRFlowable
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from datetime import datetime
from utils.receipts.paths import get_base_folder
from utils.utils import format_currency


# ── Paleta de colores ────────────────────────────────────────────────────────
COLOR_PRIMARY   = colors.HexColor("#1B5E20")   # verde oscuro — encabezados
COLOR_SECONDARY = colors.HexColor("#E8F5E9")   # verde muy claro — fondo header tabla
COLOR_ACCENT    = colors.HexColor("#388E3C")   # verde medio — líneas / totales
COLOR_LIGHT     = colors.HexColor("#F5F5F5")   # gris muy claro — filas alternas
COLOR_TEXT      = colors.HexColor("#212121")   # texto principal
COLOR_MUTED     = colors.HexColor("#757575")   # texto secundario


class PurchaseDetail():
    def __init__(self, model):
        self.model = model

    # ── Carga de datos ────────────────────────────────────────────────────────
    def load_data(self, purchase_id):
        purchase_data = self.model.purchase.get_purchase_by_id(purchase_id)
        supplier_data = self.model.core.find_supplier_by_id(supplier_id=purchase_data[1])

        self.purchase = {
            'id':               purchase_data[0],
            'supplier_name':    supplier_data[2],
            'supplier_cuit':    supplier_data[1],
            'document_type':    purchase_data[2],
            'date':             purchase_data[5],
            'expiration_date':  purchase_data[6],
            'state':            purchase_data[7],
            'observations':     purchase_data[8],
            'pending':          purchase_data[9],
            'total':            purchase_data[10],
        }

        self.items = self.model.purchase.get_purchase_items(purchase_id)

        if self.purchase['document_type'] == 'REMITO':
            doc_id      = purchase_data[4]
            receipt     = self.model.purchase.supplier_receipt.get_receipt_data(doc_id)
            self.doc_data = {
                'Nº Remito':  receipt[2] if receipt else '—',
            }
        else:
            doc_id   = purchase_data[3]
            inv      = self.model.purchase.supplier_invoice.get_invoice_data(doc_id)
            # Índices confirmados contra purchase_info_invoice_view.py:
            # [2]=número  [3]=tipo  [4]=fecha  [5]=venc  [6]=cond_iva_prov
            # [8]=obs  [9]=pay_cond  [10]=pay_period
            # [11]=orig_subtotal  [12]=dto%  [13]=dto_amount  [14]=subtotal_c_dto
            # [15]=iva  [16]=total
            self.doc_data = {
                'Nº Factura':          inv[2]  if inv else '—',
                'Tipo':                inv[3]  if inv else '—',
                'Condición de pago':   inv[9]  if inv else '—',
                'Plazo (días)':        inv[10] if inv else '—',
                'Subtotal':            f"$ {format_currency(inv[11])}" if inv else '—',
                'Descuento %':         f"{inv[12]}%"  if inv else '—',
                'Monto descuento':     f"$ {format_currency(inv[13])}" if inv else '—',
                'Subtotal c/ dto.':    f"$ {format_currency(inv[14])}" if inv else '—',
                'Monto IVA':           f"$ {format_currency(inv[15])}" if inv else '—',
                'Total factura':       f"$ {format_currency(inv[16])}" if inv else '—',
            }

    # ── Generación del PDF ────────────────────────────────────────────────────
    def generate_purchase_detail(self, purchase_id):
        self.load_data(purchase_id)

        date        = self.purchase['date']
        
        supplier_name = self.purchase['supplier_name']
        # Limpiar caracteres inválidos para nombre de carpeta
        #safe_name = "".join(c for c in supplier_name if c.isalnum() or c in (' ', '-', '_')).strip()
        compras_dir = os.path.join(get_base_folder(), "Proveedores", supplier_name, "Compras")
        #compras_dir = os.path.join(get_base_folder(), "Proveedores", "Compras")
        os.makedirs(compras_dir, exist_ok=True)
        filename = os.path.join(
            compras_dir, f"{date}_compra_nro_{purchase_id}.pdf"
        )

        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        styles  = getSampleStyleSheet()
        W, _    = A4
        usable  = W - 40 * mm

        # ── Estilos personalizados ─────────────────────────────────────────
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Normal"],
            fontSize=18,
            fontName="Helvetica-Bold",
            textColor=COLOR_PRIMARY,
            spaceAfter=2,
        )
        subtitle_style = ParagraphStyle(
            "Subtitle",
            parent=styles["Normal"],
            fontSize=10,
            fontName="Helvetica",
            textColor=COLOR_MUTED,
            spaceAfter=0,
        )
        section_style = ParagraphStyle(
            "Section",
            parent=styles["Normal"],
            fontSize=9,
            fontName="Helvetica-Bold",
            textColor=COLOR_PRIMARY,
            spaceBefore=10,
            spaceAfter=4,
        )
        field_key_style = ParagraphStyle(
            "FieldKey",
            parent=styles["Normal"],
            fontSize=9,
            fontName="Helvetica-Bold",
            textColor=COLOR_TEXT,
        )
        field_val_style = ParagraphStyle(
            "FieldVal",
            parent=styles["Normal"],
            fontSize=9,
            fontName="Helvetica",
            textColor=COLOR_TEXT,
        )
        footer_style = ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontSize=8,
            fontName="Helvetica",
            textColor=COLOR_MUTED,
            alignment=1,   # centrado
        )

        elements = []

        # ── Encabezado ─────────────────────────────────────────────────────
        date_fmt = datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")
        try:
            exp_fmt = datetime.strptime(
                self.purchase["expiration_date"], "%Y-%m-%d"
            ).strftime("%d/%m/%Y")
        except Exception:
            exp_fmt = self.purchase["expiration_date"] or "—"

        header_data = [[
            Paragraph(
                f"Detalle de Compra &nbsp;&nbsp;<font color='#757575' size='12'>#{self.purchase['id']}</font>",
                title_style
            ),
            Paragraph(
                f"<b>{self.purchase['document_type']}</b><br/>"
                f"<font color='#757575'>Fecha: {date_fmt}</font>",
                ParagraphStyle("HR", parent=styles["Normal"], fontSize=10,
                               fontName="Helvetica", alignment=2)
            ),
        ]]
        header_table = Table(header_data, colWidths=[usable * 0.6, usable * 0.4])
        header_table.setStyle(TableStyle([
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
            ("LINEBELOW",   (0, 0), (-1, 0),  1.5, COLOR_ACCENT),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 8))

        # ── Tarjeta: Proveedor + Estado ────────────────────────────────────
        state       = self.purchase["state"]
        state_color = "#1B5E20" if state == "PAGADA" else \
                      "#E65100" if state == "BORRADOR" else "#1565C0"

        info_data = [
            [
                Paragraph("PROVEEDOR", section_style),
                Paragraph("ESTADO", section_style),
            ],
            [
                Paragraph(
                    f"<b>{self.purchase['supplier_name']}</b><br/>"
                    f"<font color='#757575'>CUIT: {self.purchase['supplier_cuit']}</font>",
                    field_val_style
                ),
                Paragraph(
                    f"<font color='{state_color}'><b>{state}</b></font><br/>"
                    f"<font color='#757575'>Venc.: {exp_fmt}</font>",
                    field_val_style
                ),
            ],
        ]
        info_table = Table(info_data, colWidths=[usable * 0.55, usable * 0.45])
        info_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), COLOR_SECONDARY),
            ("ROUNDEDCORNERS", (0, 0), (-1, -1), [4, 4, 4, 4]),
            ("BOX",           (0, 0), (-1, -1), 0.5, COLOR_ACCENT),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("LINEBELOW",     (0, 0), (-1, 0), 0.5, COLOR_ACCENT),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 10))

        # ── Datos del documento (factura / remito) ─────────────────────────
        elements.append(Paragraph(
            f"DATOS DEL {'REMITO' if self.purchase['document_type'] == 'REMITO' else 'COMPROBANTE'}",
            section_style
        ))

        doc_items = list(self.doc_data.items())
        # Organizar en 2 columnas
        mid = (len(doc_items) + 1) // 2
        left_col  = doc_items[:mid]
        right_col = doc_items[mid:]

        doc_rows = []
        for i in range(mid):
            lk, lv = left_col[i]
            if i < len(right_col):
                rk, rv = right_col[i]
            else:
                rk, rv = "", ""
            doc_rows.append([
                Paragraph(lk, field_key_style),
                Paragraph(str(lv), field_val_style),
                Paragraph(rk, field_key_style),
                Paragraph(str(rv), field_val_style),
            ])

        col_w = usable / 4
        doc_table = Table(doc_rows, colWidths=[col_w, col_w, col_w, col_w])
        doc_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), COLOR_LIGHT),
            ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#BDBDBD")),
            ("INNERGRID",     (0, 0), (-1, -1), 0.3, colors.HexColor("#E0E0E0")),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            # columnas de valor alineadas a la derecha
            ("ALIGN",         (1, 0), (1, -1), "RIGHT"),
            ("ALIGN",         (3, 0), (3, -1), "RIGHT"),
        ]))
        elements.append(doc_table)
        elements.append(Spacer(1, 12))

        # ── Tabla de ítems ─────────────────────────────────────────────────
        elements.append(Paragraph("ARTÍCULOS", section_style))

        col_widths = [
            usable * 0.35,  # Producto  — más ancho para nombres largos
            usable * 0.09,  # Envase
            usable * 0.06,  # Cant.
            usable * 0.11,  # P. Costo
            usable * 0.07,  # IVA %
            usable * 0.11,  # Subtotal
            usable * 0.10,  # IVA $
            usable * 0.11,  # Total
        ]

        cell_style = ParagraphStyle(
            "Cell", parent=styles["Normal"],
            fontSize=8, fontName="Helvetica",
            textColor=COLOR_TEXT, leading=10
        )
        cell_right = ParagraphStyle(
            "CellR", parent=cell_style, alignment=2
        )

        # Índices de get_purchase_items confirmados por headers de la sheet:
        # [0]id  [1]nombre  [2]envase  [3]cantidad  [4]precio_lista  [5]dto%
        # [6]precio_costo  [7]iva%  [8]monto_dto  [9]subtotal  [10]monto_iva  [11]total

        header_row = ["Producto", "Envase", "Cant.", "P. Costo", "IVA %", "Subtotal", "IVA $", "Total"]
        table_data = [header_row]

        for item in self.items:
            table_data.append([
                Paragraph(str(item[1]), cell_style),   # nombre — único que necesita wrap
                str(item[2]),                          # envase
                str(item[3]),                          # cantidad
                f"$ {format_currency(item[6])}",                        # precio costo
                f"{item[7]}",                         # iva %
                f"$ {format_currency(item[9])}",                        # subtotal neto
                f"$ {format_currency(item[10])}",                       # monto iva
                f"$ {format_currency(item[11])}",                       # total
            ])

        items_table = Table(table_data, colWidths=col_widths, repeatRows=1)

        row_styles = [
            ("BACKGROUND",    (0, 0), (-1, 0),  COLOR_PRIMARY),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, 0),  8),
            ("BOTTOMPADDING", (0, 0), (-1, 0),  8),
            ("TOPPADDING",    (0, 0), (-1, 0),  8),
            ("ALIGN",         (0, 0), (-1, 0),  "CENTER"),
            # Datos
            ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",      (0, 1), (-1, -1), 8),
            ("TOPPADDING",    (0, 1), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
            ("VALIGN",        (0, 1), (-1, -1), "TOP"),   # alinear arriba para celdas multi-línea
            ("ALIGN",         (1, 1), (-1, -1), "RIGHT"),  # todas las col numéricas a la derecha
            ("ALIGN",         (0, 1), (0, -1),  "LEFT"),   # producto a la izquierda
            ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#CFD8DC")),
            ("BOX",           (0, 0), (-1, -1), 0.8, COLOR_ACCENT),
        ]
        # Filas alternas
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                row_styles.append(("BACKGROUND", (0, i), (-1, i), COLOR_LIGHT))

        items_table.setStyle(TableStyle(row_styles))
        elements.append(items_table)
        elements.append(Spacer(1, 12))

        # ── Bloque de totales ──────────────────────────────────────────────
        totals_data = [
            [
                Paragraph("Saldo pendiente:", field_key_style),
                Paragraph(f"$ {format_currency(self.purchase['pending'])}", field_val_style),
            ],
            [
                Paragraph("<b>TOTAL:</b>", ParagraphStyle(
                    "TotalKey", parent=styles["Normal"],
                    fontSize=11, fontName="Helvetica-Bold", textColor=COLOR_PRIMARY
                )),
                Paragraph(f"<b>$ {format_currency(self.purchase['total'])}</b>", ParagraphStyle(
                    "TotalVal", parent=styles["Normal"],
                    fontSize=11, fontName="Helvetica-Bold",
                    textColor=COLOR_PRIMARY, alignment=2
                )),
            ],
        ]
        total_col = usable * 0.3
        totals_table = Table(
            totals_data,
            colWidths=[total_col, total_col],
            hAlign="RIGHT"
        )
        totals_table.setStyle(TableStyle([
            ("ALIGN",         (1, 0), (1, -1), "RIGHT"),
            ("LINEABOVE",     (0, -1), (-1, -1), 1, COLOR_ACCENT),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(totals_table)

        # ── Observaciones ──────────────────────────────────────────────────
        if self.purchase.get("observations"):
            elements.append(Spacer(1, 10))
            elements.append(HRFlowable(
                width=usable, thickness=0.5, color=colors.HexColor("#BDBDBD")
            ))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph("OBSERVACIONES", section_style))
            elements.append(Paragraph(self.purchase["observations"], field_val_style))

        # ── Pie de página ──────────────────────────────────────────────────
        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(
            width=usable, thickness=0.5, color=colors.HexColor("#BDBDBD")
        ))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(
            f"Documento generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} &nbsp;·&nbsp; Uso interno",
            footer_style
        ))

        doc.build(elements)
        return filename