import os
import sys

def _resolve_db_path():
    if getattr(sys, 'frozen', False):
        base = os.path.join(os.environ['LOCALAPPDATA'], 'StockManager', 'db')
    else:
        base = os.path.join(os.path.dirname(__file__), '..', 'db')
    return os.path.normpath(os.path.join(base, 'stock.db'))

DB_PATH = _resolve_db_path()

settings = {
    "VIEW_CONFIG" : {
        'window-title':"Agroveterinaria El Fortín",
        'window-size':"1366x768",
    }
}

COMPANY_CONFIG = {
    "name": "Agroveterinaria El Fortín",
    "address": "Ruta Nacional N° 8, Km 681, Chaján, Córdoba",
    "phone": "+54 9 358 4123456",
    "email": "chajaneguizabal@hotmail.com",
    "cuit": "20-14221046-1"
}
