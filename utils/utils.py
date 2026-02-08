from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

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

## Formato de fechas ##
## -- Convierte de "YYYY-MM-DD" a "DD/MM/YYYY" -- ##
def iso_to_traditional(date):
    # convierto el string a obj tipo date
    date_formated = datetime.strptime(date, "%Y-%m-%d").date()
    # formateo el obj a un string nuevamente
    return date_formated.strftime("%d/%m/%Y")

## -- Convierte de "DD/MM/YYYY" a "YYYY-MM-DD" -- ##
def traditional_to_iso(date):
    # convierto el string a obj tipo date
    date_formated = datetime.strptime(date, "%d/%m/%Y").date()
    # formateo el obj a un string nuevamente
    return date_formated.strftime("%Y-%m-%d")
