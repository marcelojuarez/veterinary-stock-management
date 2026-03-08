from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import datetime

## Redondea value a un valor con 2 decimales
def norm_to_2_dec(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

## Redondea value a un valor con 4 decimales
def norm_to_4_dec(value):
    return Decimal(value).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

# Dado un decimal determina si tiene mas de 4 decimales 
def has_more_than_4_decimals(value: Decimal) -> bool:
    exponent = value.as_tuple().exponent
    return exponent < -4

# Dado un decimal determina si tiene menos de 2 decimales
def has_less_than_2_decimals(value: Decimal) -> bool:
    exponent = value.as_tuple().exponent
    return exponent > -2

# Normaliza eliminando ceros no significativos
def trim_trailing_zeros_to_min_2(dec: Decimal) -> Decimal:
    normalized = dec.normalize()

    # Si quedó con exponente mayor a -2 (menos de 2 decimales),
    # aseguramos mínimo 2
    if normalized.as_tuple().exponent > -2:
        normalized = normalized.quantize(Decimal("0.01"))

    return normalized
    
## Dado un valor retorna un Obj Decimal manteniendo entre 2 y 4 decimales
def flex_dec(value):
    try:
        if isinstance(value, Decimal):
            dec = value
        else:
            dec = Decimal(str(value))  
        
        if has_more_than_4_decimals(dec):
            dec = norm_to_4_dec(dec)

        dec = trim_trailing_zeros_to_min_2(dec)
        return dec

    except (InvalidOperation, ValueError) as e:
        return None

## Dado un string devuelve su representacion como entero
def string_to_dec(value):
    if value.strip() == "":
        return None
    
    try:
        return int(value)
    except:
        return None

## Dado un string devuelve su representacion en decimal flexible
def string_to_flex_dec(value):
    if value.strip() == "":
        return None

    # reemplazar ',' por '.'
    value = value.replace(",", ".")
    try:
        return flex_dec(value)
    except:
        return None
    
## Dado un string devuelve su representacion con 2 decimales
def string_to_2_dec(value):
    if value.strip() == "":
        return None

    # reemplazar ',' por '.'
    value = value.replace(",", ".")
    try:
        return norm_to_2_dec(value)
    except:
        return None

## Convierte un Decimal a string con formato monetario
def format_currency(value):
    number = norm_to_2_dec(value)
    
    formatted = f"{number:,.2f}"
    
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    
    return formatted

## Convierte un Decimal a string con formato monetario extendido hasta 4 decimales
def format_currency_flex(value):
    number = norm_to_4_dec(value)
    
    formatted = f"{number:,.4f}"
    
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    
    return formatted

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


