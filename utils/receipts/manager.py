import os
from datetime import datetime

from utils.receipts.ticket_pos import generate_payment_ticket, generate_global_payment_ticket
from utils.receipts.pdf_generator import generate_payment_receipt, generate_global_payment_receipt


COMMERCE = {
    "name": "Agroveterinaria El Fortín",
    "address": "Ruta Nacional N° 8, Km 681 – Chaján, Córdoba",
    "cuit": "20-12345678-3",
}

def _open_file(path: str):
    try:
        os.startfile(path)  # Windows
    except:
        pass

def _build_ticket_path(prefix: str, identifier: str):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"comprobantes/tickets/{prefix}_{identifier}_{ts}.pdf"

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

    # Para global:
    customer_id: int | None = None,
    result_data=None,
):
    paths = []

    if format in ("ticket", "both"):
        if mode == "sale":
            ticket_path = _build_ticket_path("ticket", str(sale_id))
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
            ticket_path = _build_ticket_path("ticket_global", str(customer_id))
            generate_global_payment_ticket(
                file_path=ticket_path,
                commerce_name=COMMERCE["name"],
                commerce_address=COMMERCE["address"],
                commerce_cuit=COMMERCE["cuit"],
                client_name=client_name,
                amount=amount,
                result_data=result_data
            )
            paths.append(ticket_path)

    if format in ("a4", "both"):
        if mode == "sale":
            a4_path = generate_payment_receipt(
                client_name=client_name,
                sale_id=sale_id,
                payment_amount=amount,
                method=method,
                sale_info=sale_info,
                payments=payments
            )
            paths.append(a4_path)

        elif mode == "global":
            a4_path = generate_global_payment_receipt(
                client_name,
                amount,
                result_data
            )
            paths.append(a4_path)

    for p in paths:
        _open_file(p)

    return paths
