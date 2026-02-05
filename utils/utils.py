from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from views.view_helpers import show_error
import re

# funcion con anotaciones
## Convierte un valor en un objeto Decimal redondeado 2 decimales
def normalize_decimal(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

## Dado un string devuelve su representacion como entero
def normalize_int_to_dec(value):
    if value.strip() == "":
        return None
    
    try:
        return int(value)
    except:
        return None
## Dado un string devuelve su representacion en decimal
def normalize_string_to_dec(value):
    if value.strip() == "":
        return None

    # reemplazar coma por punto
    value = value.replace(",", ".")
    try:
        return normalize_decimal(value)
    except:
        return None


def format_money(value):
    try:
        if value is None:
            return "$0.00"

        dec = Decimal(str(value))
        return f"${dec:,.2f}"
    except (InvalidOperation, ValueError):
        return "$0.00"


def format_percent(value):
    try:
        return f"{float(Decimal(value)):.1f}%"
    except (InvalidOperation, TypeError, ValueError):
        return "0.0%"


