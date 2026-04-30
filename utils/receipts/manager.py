import os
from datetime import datetime
from decimal import Decimal

from utils.receipts.ticket_pos import generate_global_payment_ticket
from utils.receipts.pdf_generator import generate_global_payment_receipt
from utils.receipts.payment_order import generate_orden_pago
from utils.receipts.paths import (
    ticket_pago_venta,
    ticket_pago_global,
    a4_pago_venta,
    a4_pago_global,
    orden_pago_path,
)


COMMERCE = {
    "name": "Agroveterinaria El Fortín",
    "address": "Ruta Nacional N° 8, Km 681 – Chaján, Córdoba",
    "cuit": "20-14221046-1",
}


def _open_file(path: str):
    """Abre el archivo con el programa predeterminado del sistema"""
    try:
        os.startfile(path)  # Windows
    except AttributeError:
        import subprocess
        try:
            subprocess.run(['xdg-open', path], check=False)
        except:
            pass
    except Exception:
        pass

def generate_receipts_for_payment(
    *,
    mode: str,                  # "sale" | "global"
    format: str,                # "ticket" | "a4" | "both"
    client_name: str,
    method: str,
    amount: Decimal,
    check_data: dict | None = None,   # datos del cheque/eCheq si aplica

    # Para sale:
    sale_id: int | None = None,
    sale_info=None,
    payments=None,
    sales_with_items=None,

    # Para global:
    customer_id: int | None = None,
    result_data=None,

    # Impresión directa
    auto_print: bool = False,
):
    paths = []

    if format in ("ticket", "both"):
        ticket_path = ticket_pago_global(client_name)
        generate_global_payment_ticket(
            file_path=ticket_path,
            commerce_name=COMMERCE["name"],
            commerce_address=COMMERCE["address"],
            commerce_cuit=COMMERCE["cuit"],
            client_name=client_name,
            amount=amount,
            method=method,
            result_data=result_data,
            sales_with_items=sales_with_items,
            check_data=check_data,
        )
        paths.append(("ticket", ticket_path))

    if format in ("a4", "both"):
        a4_path = a4_pago_global(client_name)
        generate_global_payment_receipt(
            file_path=a4_path,
            commerce_name=COMMERCE["name"],
            commerce_address=COMMERCE["address"],
            commerce_cuit=COMMERCE["cuit"],
            client_name=client_name,
            payment_amount=amount,
            method=method,
            result_data=result_data,
            sales_with_items=sales_with_items,
            check_data=check_data,
        )
        paths.append(("a4", a4_path))

    for fmt_type, p in paths:
        if auto_print:
            _print_file(p)
        else:
            _open_file(p)

    return [p for _, p in paths]


def generate_orden_pago_proveedor(
    *,
    supplier_name: str,
    supplier_cuit: str = "",
    # ── Modo multi-medio (recomendado) ──────────────────────────
    # Lista de dicts: [{method, amount, ...campos según método}]
    payments: list | None = None,
    # ── Modo legacy (un solo medio, compatibilidad) ─────────────
    amount: Decimal | None = None,
    method: str = "",
    receipt_number: str = "",
    observation: str = "",
    purchase_id: int | None = None,
    purchase_total: str = "",
    purchase_remaining: str = "",
    check_number: str = "",
    check_bank: str = "",
    check_due: str = "",
    operation_num: str = "",
    origin: str = "",
    destination: str = "",
    auto_print: bool = False,
) -> str:
    """Genera e imprime una orden de pago a proveedor."""
    path = orden_pago_path(supplier_name)

    generate_orden_pago(
        file_path=path,
        # op_number=None → se auto-genera con correlativo
        commerce_name=COMMERCE["name"],
        commerce_address=COMMERCE["address"],
        commerce_cuit=COMMERCE["cuit"],
        supplier_name=supplier_name,
        supplier_cuit=supplier_cuit,
        payments=payments,          # multi-medio (None = usar legacy)
        amount=amount,
        method=method,
        receipt_number=receipt_number,
        observation=observation,
        purchase_id=purchase_id,
        purchase_total=purchase_total,
        purchase_remaining=purchase_remaining,
        check_number=check_number,
        check_bank=check_bank,
        check_due=check_due,
        operation_num=operation_num,
        origin=origin,
        destination=destination,
    )

    if auto_print:
        _print_file(path)
    else:
        _open_file(path)

    return path


def _print_file(path: str):
    """Intenta imprimir directamente con SumatraPDF, fallback a ShellExecute."""
    sumatra = r"C:\Program Files\SumatraPDF\SumatraPDF.exe"
    try:
        if os.path.exists(sumatra):
            import subprocess
            subprocess.Popen([sumatra, "-print-to-default", "-silent", path])
            return
    except Exception:
        pass
    # Fallback: abrir con programa predeterminado
    _open_file(path)