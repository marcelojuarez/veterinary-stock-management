import os
import subprocess
from datetime import datetime
from decimal import Decimal

from utils.receipts.ticket_pos import generate_global_payment_ticket
from utils.receipts.pdf_generator import generate_global_payment_receipt
from utils.receipts.paths import (
    ticket_pago_venta,
    ticket_pago_global,
    a4_pago_venta,
    a4_pago_global
)


COMMERCE = {
    "name": "Agroveterinaria El Fortín",
    "address": "Ruta Nacional N° 8, Km 681 – Chaján, Córdoba",
    "cuit": "20-14221046-1",
}


def _open_file(path: str):
    """Abre el archivo con el programa predeterminado del sistema"""
    try:
        os.startfile(path)          # Windows
    except AttributeError:
        try:
            subprocess.run(['xdg-open', path], check=False)
        except Exception:
            pass
    except Exception:
        pass


def print_file(path: str):
    """
    Envía el PDF directamente a la impresora predeterminada (Windows).
    Usa SumatraPDF si está disponible, si no, ShellExecute print verb.
    """
    try:
        # Opción 1: SumatraPDF (impresión silenciosa, ideal para tickets)
        sumatra_paths = [
            r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
            r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
        ]
        for sp in sumatra_paths:
            if os.path.exists(sp):
                subprocess.Popen([sp, "-print-to-default", "-silent", path])
                return

        # Opción 2: ShellExecute con verbo "print" (abre el diálogo de impresión)
        import ctypes
        ctypes.windll.shell32.ShellExecuteW(None, "print", path, None, None, 1)

    except Exception as e:
        print(f"[print_file] Error al imprimir: {e}")
        # Fallback: abrir para imprimir manualmente
        _open_file(path)


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
            print_file(p)
        else:
            _open_file(p)

    return [p for _, p in paths]