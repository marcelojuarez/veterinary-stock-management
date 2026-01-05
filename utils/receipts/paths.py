import os
import re
from datetime import datetime


def sanitize_folder_name(name: str) -> str:
    """
    Limpia el nombre del cliente para usarlo como nombre de carpeta.
    Remueve caracteres inválidos para Windows/Linux.
    """
    # Reemplazar caracteres problemáticos
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Reemplazar múltiples espacios por uno solo
    name = re.sub(r'\s+', ' ', name)
    # Limitar longitud
    return name.strip()[:50]


def get_client_folder(client_name: str) -> str:
    """
    Retorna la ruta base de la carpeta del cliente.
    Ejemplo: comprobantes/Pet Shop Los Andes/
    """
    safe_name = sanitize_folder_name(client_name)
    return os.path.join("comprobantes", safe_name)


def get_ticket_path(client_name: str, prefix: str, identifier: str = "") -> str:
    """
    Genera ruta para tickets (80mm).
    Ejemplo: comprobantes/Pet Shop Los Andes/tickets/ticket_venta_41_20260104_165000.pdf
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = os.path.join(get_client_folder(client_name), "tickets")
    os.makedirs(folder, exist_ok=True)
    
    if identifier:
        filename = f"{prefix}_{identifier}_{timestamp}.pdf"
    else:
        filename = f"{prefix}_{timestamp}.pdf"
    
    return os.path.join(folder, filename)


def get_a4_path(client_name: str, prefix: str, identifier: str = "") -> str:
    """
    Genera ruta para comprobantes A4.
    Ejemplo: comprobantes/Pet Shop Los Andes/comprobantes_a4/comprobante_venta_41_20260104_165000.pdf
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = os.path.join(get_client_folder(client_name), "comprobantes_a4")
    os.makedirs(folder, exist_ok=True)
    
    if identifier:
        filename = f"{prefix}_{identifier}_{timestamp}.pdf"
    else:
        filename = f"{prefix}_{timestamp}.pdf"
    
    return os.path.join(folder, filename)


def get_statement_path(client_name: str) -> str:
    """
    Genera ruta para estados de cuenta.
    Ejemplo: comprobantes/Pet Shop Los Andes/estados_cuenta/estado_cuenta_20260104_180000.pdf
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = os.path.join(get_client_folder(client_name), "estados_cuenta")
    os.makedirs(folder, exist_ok=True)
    
    filename = f"estado_cuenta_{timestamp}.pdf"
    return os.path.join(folder, filename)


# ============================================================
# FUNCIONES DE CONVENIENCIA PARA CADA TIPO DE COMPROBANTE
# ============================================================

def ticket_pago_venta(client_name: str, sale_id: int) -> str:
    """Ticket de pago de venta individual"""
    return get_ticket_path(client_name, "ticket_venta", str(sale_id))


def ticket_pago_global(client_name: str) -> str:
    """Ticket de pago global"""
    return get_ticket_path(client_name, "ticket_global")


def a4_pago_venta(client_name: str, sale_id: int) -> str:
    """Comprobante A4 de pago de venta"""
    return get_a4_path(client_name, "comprobante_venta", str(sale_id))


def a4_pago_global(client_name: str) -> str:
    """Comprobante A4 de pago global"""
    return get_a4_path(client_name, "comprobante_global")


def estado_cuenta(client_name: str) -> str:
    """Estado de cuenta del cliente"""
    return get_statement_path(client_name)