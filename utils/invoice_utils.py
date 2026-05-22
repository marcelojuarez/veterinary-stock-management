import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

## Calcula los dias de plazo disponibles segun condicion de pago ##
def pay_period_control(pay_cond_var, pay_period_var, pay_period_wid):
    try:
        cond = pay_cond_var.get()

        if cond == "CONTADO":
            pay_period_var.set("0")
            pay_period_wid.configure(state="disabled")

        else:
            pay_period_var.set("30")
            pay_period_wid.configure(state="readonly")
            

    except ValueError as e:
        logger.error("Error en pay_period_control: %s", e)
        return

def is_valid_date(date):
    try:
        datetime.strptime(date, "%d/%m/%Y")
        return True
    except:
        return False

## Calcula la fecha de vencimiento segun el plazo de dias ##
def calculate_exp_date(date_var, pay_period_var, expiration_var):
    try:
        actual_date_str = date_var.get()
        term_str = pay_period_var.get() or "0"
        
        if is_valid_date(actual_date_str):
            
            fecha_base = datetime.strptime(actual_date_str, "%d/%m/%Y")
            term = int(term_str)
            
            fecha_vencimiento = fecha_base + timedelta(days=term)

            expiration_var.set(fecha_vencimiento.strftime("%d/%m/%Y"))

    except ValueError as e: 
        pass
    
