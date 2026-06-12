"""
Generador de Orden de Pago a Proveedor - A4 blanco y negro
Ubicación: utils/receipts/orden_pago_pdf.py

Soporta múltiples medios de pago en una misma OP.
El número correlativo se gestiona con un archivo contador local.
"""

import logging
import os
import json

logger = logging.getLogger(__name__)
from datetime import datetime
from decimal import Decimal
from utils.utils import format_currency
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4


# ================================================================
# NÚMERO CORRELATIVO
# ================================================================

def _get_counter_path() -> str:
    """Ruta del archivo que guarda el último número de OP."""
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "op_counter.json")


def get_next_op_number() -> int:
    """
    Devuelve el próximo número correlativo de OP y lo incrementa.
    El contador se persiste en op_counter.json junto a este módulo.
    """
    path = _get_counter_path()
    try:
        with open(path, "r") as f:
            data = json.load(f)
        current = int(data.get("last", 0))
    except (FileNotFoundError, ValueError, KeyError):
        current = 0

    next_num = current + 1

    try:
        with open(path, "w") as f:
            json.dump({"last": next_num}, f)
    except Exception as e:
        logger.error("No se pudo guardar contador de orden de pago: %s", e)

    return next_num


# ================================================================
# HELPER ETIQUETAS DE MÉTODO
# ================================================================

def _method_label(method: str) -> str:
    labels = {
        "EFECTIVO":      "Efectivo",
        "TRANSFERENCIA": "Transferencia bancaria",
        "CHEQUE":        "Cheque de terceros",
        "ECHEQ":         "eCheq",
        "CHEQUE_PROPIO": "Cheque propio",
        "SALDO_A_FAVOR": "Saldo a favor",
    }
    return labels.get(method.upper(), method.title())


# ================================================================
# GENERADOR DE PDF
# ================================================================

def generate_orden_pago(
    *,
    file_path: str,
    op_number: int | None = None,
    # Empresa emisora
    commerce_name: str,
    commerce_address: str,
    commerce_cuit: str,
    commerce_iva: str = "Responsable Inscripto",
    # Proveedor
    supplier_name: str,
    supplier_cuit: str = "",
    # ── Modo multi-medio (recomendado) ──────────────────────────
    # Lista de dicts, cada uno con:
    #   method, amount  (obligatorios)
    #   + campos opcionales según método (ver abajo)
    payments: list | None = None,
    # ── Modo legacy (un solo medio) ─────────────────────────────
    amount: Decimal | None = None,
    method: str = "",
    receipt_number: str = "",
    observation: str = "",
    # Compra asociada (opcional)
    purchase_id: int | None = None,
    purchase_total: str = "",
    purchase_remaining: str = "",
    purchase_status: str = "",
    # Cheque (legacy)
    check_number: str = "",
    check_bank: str = "",
    check_due: str = "",
    # Transferencia (legacy)
    operation_num: str = "",
    origin: str = "",
    destination: str = "",
):
    """
    Genera una Orden de Pago en PDF.

    Modo multi-medio (recomendado):
        payments = [
            {"method": "EFECTIVO",      "amount": Decimal("1000")},
            {"method": "CHEQUE",        "amount": Decimal("5000"),
             "check_number": "001234",  "check_bank": "Galicia",
             "check_due": "30/04/2026"},
            {"method": "TRANSFERENCIA", "amount": Decimal("2000"),
             "operation_num": "9876543", "origin": "alias.a",
             "destination": "alias.b"},
        ]

    Modo legacy (un solo medio, compatibilidad hacia atrás):
        amount=Decimal("8000"), method="CHEQUE", check_number="...", ...
    """

    # ── Normalizar a lista de pagos ──────────────────────────────
    if payments is None:
        p = {"method": method.upper(), "amount": amount or Decimal("0")}
        if method.upper() in ("CHEQUE", "ECHEQ"):
            p.update(check_number=check_number, check_bank=check_bank,
                     check_due=check_due)
        elif method.upper() == "TRANSFERENCIA":
            p.update(operation_num=operation_num, origin=origin,
                     destination=destination)
        payments = [p]
    else:
        for p in payments:
            p["method"] = p.get("method", "").upper()

    total_amount = sum(p.get("amount", Decimal("0")) for p in payments)

    # ── Número de OP ─────────────────────────────────────────────
    if op_number is None:
        op_number = get_next_op_number()

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    W, H      = A4
    margin    = 20 * mm
    content_w = W - 2 * margin

    c = canvas.Canvas(file_path, pagesize=A4)
    y = H - 20 * mm

    black      = colors.black
    gray       = colors.HexColor("#555555")
    light_gray = colors.HexColor("#cccccc")
    bg_header  = colors.HexColor("#f0f0f0")

    # ── Helpers ──────────────────────────────────────────────────
    def text_c(text, size=10, bold=False, color=None, dy=None):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.setFillColor(color or black)
        c.drawCentredString(W / 2, y, text)
        y -= (dy if dy is not None else size + 6)

    def text_r(text, size=10, color=None):
        c.setFont("Helvetica", size)
        c.setFillColor(color or gray)
        c.drawRightString(W - margin, y, text)

    def sep(dashed=False, thick=False, gap_before=4, gap_after=10):
        nonlocal y
        y -= gap_before
        c.setStrokeColor(black if thick else light_gray)
        c.setLineWidth(1.2 if thick else 0.4)
        if dashed:
            c.setDash(3, 3)
        else:
            c.setDash()
        c.line(margin, y, W - margin, y)
        c.setDash()
        y -= gap_after

    def pill(text, x=None, pill_w=220, pill_h=20):
        nonlocal y
        px = x if x is not None else (W - margin - pill_w)
        c.setFillColor(black)
        c.roundRect(px, y - 4, pill_w, pill_h, 4, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(px + pill_w / 2, y + 3, text)
        c.setFillColor(black)

    def shaded_row(label, value, shade=False, indent=0):
        nonlocal y
        row_h = 18
        if shade:
            c.setFillColor(bg_header)
            c.rect(margin, y - 4, content_w, row_h, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(black)
        c.drawString(margin + 4 + indent, y + 2, label)
        c.setFont("Helvetica", 10)
        c.drawRightString(W - margin - 4, y + 2, value)
        y -= row_h

    # ==============================================================
    # ENCABEZADO
    # ==============================================================
    pill_w = 220
    pill("ORDEN DE PAGO", x=W / 2 - pill_w / 2, pill_w=pill_w)
    y -= 22

    now = datetime.now()
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(black)
    c.drawString(margin, y, f"N\u00b0 {op_number:05d}")
    text_r(f"{now:%d/%m/%Y}  {now:%H:%M} hs", size=8)
    y -= 14

    sep(thick=True, gap_before=4, gap_after=14)

    # ==============================================================
    # DATOS DEL COMERCIO
    # ==============================================================
    text_c(commerce_name, size=14, bold=True, dy=10)
    c.setFont("Helvetica", 9)
    c.setFillColor(gray)
    c.drawCentredString(W / 2, y, commerce_address)
    y -= 13
    c.drawCentredString(W / 2, y, f"CUIT: {commerce_cuit}  \u2014  {commerce_iva}")
    y -= 6

    sep(gap_before=8, gap_after=14)

    # ==============================================================
    # PROVEEDOR
    # ==============================================================
    sec_h = 42
    c.setFillColor(bg_header)
    c.rect(margin, y - sec_h + 14, content_w, sec_h, fill=1, stroke=0)

    c.setFont("Helvetica", 8)
    c.setFillColor(gray)
    c.drawString(margin + 4, y + 2, "PROVEEDOR")
    y -= 12

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(black)
    c.drawString(margin + 4, y, supplier_name)
    y -= 14

    if supplier_cuit:
        c.setFont("Helvetica", 9)
        c.setFillColor(gray)
        c.drawString(margin + 4, y, f"CUIT: {supplier_cuit}")
        y -= 12
    else:
        y -= 4

    sep(gap_before=10, gap_after=14)

    # ==============================================================
    # COMPRA ASOCIADA (opcional)
    # ==============================================================
    if purchase_id:
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(gray)
        c.drawString(margin, y, "COMPRA ASOCIADA")
        y -= 14

        shade = False
        shaded_row(f"Compra #{purchase_id}", "", shade=shade); shade = not shade
        if purchase_total:
            shaded_row("  Total Compra:", f"$ {format_currency(purchase_total)}", shade=shade); shade = not shade
        if purchase_remaining:
            shaded_row("  Saldo Pendiente:", f"$ {format_currency(purchase_remaining)}", shade=shade)
        if purchase_status:
            shaded_row("  Estado de Compra:", purchase_status, shade=shade); shade = not shade

        sep(dashed=True, gap_before=8, gap_after=14)

    # ==============================================================
    # MEDIOS DE PAGO
    # ==============================================================
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(gray)
    c.drawString(margin, y, "DETALLE DE MEDIOS DE PAGO")
    y -= 14

    shade = False
    for idx, pago in enumerate(payments, 1):
        met   = pago.get("method", "")
        p_amt = pago.get("amount", Decimal("0"))

        # Fila principal del medio
        shaded_row(
            f"{idx}. {_method_label(met)}",
            f"$ {format_currency(p_amt)}",
            shade=shade
        )
        shade = not shade

        # Campos específicos
        if met in ("CHEQUE", "ECHEQ"):
            if pago.get("check_number"):
                shaded_row("   N° cheque:", str(pago["check_number"]), shade=shade, indent=8)
                shade = not shade
            if pago.get("check_bank"):
                shaded_row("   Banco:", pago["check_bank"], shade=shade, indent=8)
                shade = not shade
            if pago.get("check_due"):
                shaded_row("   Vencimiento:", pago["check_due"], shade=shade, indent=8)
                shade = not shade

        elif met == "TRANSFERENCIA":
            if pago.get("operation_num"):
                shaded_row("   N\u00b0 Operaci\u00f3n:", str(pago["operation_num"]), shade=shade, indent=8)
                shade = not shade
            if pago.get("origin"):
                shaded_row("   CBU/Alias origen:", pago["origin"], shade=shade, indent=8)
                shade = not shade
            if pago.get("destination"):
                shaded_row("   CBU/Alias destino:", pago["destination"], shade=shade, indent=8)
                shade = not shade

    # Campos generales
    if receipt_number:
        shaded_row("N\u00b0 Recibo:", receipt_number, shade=shade); shade = not shade
    if observation:
        shaded_row("Observaciones:", observation, shade=shade)

    sep(dashed=True, gap_before=10, gap_after=14)

    # ==============================================================
    # TOTAL
    # ==============================================================
    box_h = 32
    c.setFillColor(black)
    c.rect(margin, y - box_h + 14, content_w, box_h, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin + 8, y - 2, "TOTAL ABONADO")
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(W - margin - 8, y - 2, f"$ {format_currency(total_amount)}")
    y -= box_h + 10

    sep(gap_before=10, gap_after=20)

    # ==============================================================
    # FIRMAS
    # ==============================================================
    firma_w = (content_w - 20 * mm) / 2
    x_left  = margin
    x_right = W - margin - firma_w
    y_firma = y - 20

    c.setStrokeColor(black)
    c.setLineWidth(0.5)
    c.line(x_left,  y_firma, x_left  + firma_w, y_firma)
    c.line(x_right, y_firma, x_right + firma_w, y_firma)

    c.setFont("Helvetica", 8)
    c.setFillColor(gray)
    c.drawCentredString(x_left  + firma_w / 2, y_firma - 12, "Firma y aclaración (emisor)")
    c.drawCentredString(x_right + firma_w / 2, y_firma - 12, "Firma y aclaración (proveedor)")

    # ==============================================================
    # PIE
    # ==============================================================
    c.setFont("Helvetica", 7)
    c.setFillColor(light_gray)
    c.drawCentredString(
        W / 2, 12 * mm,
        f"OP N\u00b0 {op_number:05d} \u2014 Generada el {now:%d/%m/%Y %H:%M} \u2014 {commerce_name}"
    )

    c.save()
    return file_path