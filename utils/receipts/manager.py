import os
from datetime import datetime

from utils.receipts.ticket_pos import generate_payment_ticket, generate_global_payment_ticket
from utils.receipts.pdf_generator import generate_payment_receipt, generate_global_payment_receipt
from utils.receipts.paths import (
    ticket_pago_venta,
    ticket_pago_global,
    a4_pago_venta,
    a4_pago_global
)


COMMERCE = {
    "name": "Agroveterinaria El Fortín",
    "address": "Ruta Nacional N° 8, Km 681 – Chaján, Córdoba",
    "cuit": "20-12345678-3",
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
    mode: str,                 # "sale" | "global"
    format: str,               # "ticket" | "a4" | "both"
    client_name: str,
    method: str,
    amount: float,

    # Para sale:
    sale_id: int | None = None,
    sale_info=None,
    payments=None,
    sale_items=None, 

    # Para global:
    customer_id: int | None = None,
    result_data=None,
):
    paths = []

    # ================================================================
    # TICKET (80mm) - Simple, solo monto para el cliente
    # ================================================================
    if format in ("ticket", "both"):
        if mode == "sale":
            ticket_path = ticket_pago_venta(client_name, sale_id)
            generate_payment_ticket(
                file_path=ticket_path,
                commerce_name=COMMERCE["name"],
                commerce_address=COMMERCE["address"],
                commerce_cuit=COMMERCE["cuit"],
                client_name=client_name,
                sale_id=sale_id,
                amount=amount,
                method=method
            )
            paths.append(ticket_path)

        elif mode == "global":
            ticket_path = ticket_pago_global(client_name)
            generate_global_payment_ticket(
                file_path=ticket_path,
                commerce_name=COMMERCE["name"],
                commerce_address=COMMERCE["address"],
                commerce_cuit=COMMERCE["cuit"],
                client_name=client_name,
                amount=amount,
                result_data=result_data,
                sales_items=sale_items
            )
            paths.append(ticket_path)

    # ================================================================
    # COMPROBANTE A4 - Completo con detalle de productos
    # ================================================================
    if format in ("a4", "both"):
        if mode == "sale":
            a4_path = a4_pago_venta(client_name, sale_id)
            generate_payment_receipt(
                file_path=a4_path,
                client_name=client_name,
                sale_id=sale_id,
                payment_amount=amount,
                method=method,
                sale_info=sale_info,
                payments=payments,
                sale_items=sale_items 
            )
            paths.append(a4_path)

        elif mode == "global":
            a4_path = a4_pago_global(client_name)
            generate_global_payment_receipt(
                file_path=a4_path,
                client_name=client_name,
                payment_amount=amount,
                result_data=result_data,
                sale_items=sale_items
            )
            paths.append(a4_path)

    # Abrir archivos generados
    for p in paths:
        _open_file(p)

    return paths