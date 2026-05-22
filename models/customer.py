import logging
import sqlite3
from datetime import datetime
from decimal import Decimal
from tkinter import messagebox
from db.database import db
from utils.utils import norm_to_2_dec, iso_to_traditional

logger = logging.getLogger(__name__)
class CustomerModel:
    def __init__(self, pay_model, customer_credit, sales_model, db_connection=None):
        self.db = db_connection or db 
        self.pay_model = pay_model
        self.customer_credit = customer_credit
        self.sales_model = sales_model

    def get_all_customers(self): 
        # Obtener todos los clientes
        try: 
            query = "SELECT * FROM customer ORDER BY id"
            return db.fetch_all(query)
        except ValueError as e: 
            logger.error("Error getting customers: %s", e)
            return []
        
    def get_all_clients(self):
        query = "SELECT id, name FROM customer ORDER BY name"
        return db.fetch_all(query)
    
    def get_client_by_name(self, name):
        """Buscar cliente por nombre exacto"""
        query = """
            SELECT id, name, cuit, home, iva_condition
            FROM customer
            WHERE name = ?
        """
        return db.fetch_one(query, (name,))

    def get_client_id_by_name(self, name):
        query = "SELECT id FROM customer WHERE name = ?"
        row = db.fetch_one(query, (name,))
        return row[0] if row else None


    def find_customer_by_id(self, customer_id):
        try:
            query = "SELECT * FROM customer WHERE id = ?"
            return db.fetch_one(query, (customer_id,))
        except Exception as e:
            logger.error("Error getting customer by ID: %s", e)
            return None

    def check_duplicate_customer(self, customer_data, exclude_id=None):
        cuit = customer_data['cuit'].strip() if customer_data.get('cuit') else ''
        telefono = customer_data['phone'].strip() if customer_data.get('phone') else ''

        # Verificar CUIT duplicado
        if cuit:
            if exclude_id:
                existing = db.fetch_one(
                    "SELECT id, name FROM customer WHERE cuit = ? AND id != ?", 
                    (cuit, exclude_id)
                )
            else:
                existing = db.fetch_one(
                    "SELECT id, name FROM customer WHERE cuit = ?", 
                    (cuit,)
                )
            if existing:
                return f"Ya existe un cliente con el CUIT '{cuit}': {existing[1]}"

        # Verificar teléfono duplicado
        if telefono:
            if exclude_id:
                existing = db.fetch_one(
                    "SELECT id, name FROM customer WHERE phone = ? AND id != ?", 
                    (telefono, exclude_id)
                )
            else:
                existing = db.fetch_one(
                    "SELECT id, name FROM customer WHERE phone = ?", 
                    (telefono,)
                )
            if existing:
                return f"Ya existe un cliente con el teléfono '{telefono}': {existing[1]}"

        return None

    def add_customer(self, customer_data):
        # Verificar duplicados ANTES de insertar
        duplicate_error = self.check_duplicate_customer(customer_data)
        if duplicate_error:
            raise ValueError(duplicate_error)
        
        # Agregar nuevo cliente a la base de datos
        query = """
            INSERT INTO customer (name, cuit, home, phone, iva_condition, cv, cuig, renspa, establishment)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            customer_data['name'].upper(),
            customer_data['cuit'],
            customer_data['home'].upper(),
            customer_data['phone'],
            customer_data['iva_condition'],
            customer_data.get('cv', ''),
            customer_data.get('cuig', ''),
            customer_data.get('renspa', ''),
            customer_data.get('establishment', '').upper(),
        ]
        try:
            return db.execute_query(query, params)
        except sqlite3.IntegrityError as e: 
            raise ValueError("Ya existe un cliente con alguno de esos datos.")

    def delete_customer(self, customer_id):
        # Eliminar la informacion del cliente
        try:
            query = "DELETE FROM customer where id = ?"
            return db.execute_query(query, (customer_id,))
        except Exception as e: 
            logger.error("Error deleting customer: %s", e)
            return None

    def edit_customer(self, customer_id, data):
        query = """
            UPDATE customer SET
                name          = ?,
                cuit          = ?,
                home          = ?,
                phone         = ?,
                iva_condition = ?,
                cv            = ?,
                cuig          = ?,
                renspa        = ?,
                establishment = ?
            WHERE id = ?
        """
        params = [
            data['name'].upper(),
            data['cuit'] or None,
            data['home'].upper(),
            data['phone'] or None,
            data['iva_condition'],
            data.get('cv', ''),
            data.get('cuig', ''),
            data.get('renspa', ''),
            data.get('establishment', '').upper(),
            customer_id,
        ]
        try:
            return db.execute_query(query, params)
        except Exception as e:
            raise ValueError(f"Error al actualizar cliente: {e}")
    
    def search_customer(self, search_term):
        # Busco a un cliente por nombre o id 
        try:
            if search_term.isdigit():
                query = "SELECT * FROM customer WHERE id = ?"
                return self.db.fetch_all(query, (int(search_term),))
            else:
                query = "SELECT * FROM customer WHERE name LIKE ?"
                return self.db.fetch_all(query, (f"%{search_term.upper()}%",))
        except Exception as e:
            logger.error("Error searching customer: %s", e)
            return []
            
    # --------------------------------------------------------------------
    # 💳 GESTIÓN DE DEUDAS DE CLIENTES
    # --------------------------------------------------------------------
    ## -- Inserta una fila en el historial de un cliente  -- ##
    def add_row_in_customer_ledger(self, data, conn=None, commit=True):
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
            INSERT INTO customer_ledger 
                (client_id, date, type, description, amount, payment, debt, reference_id, reference) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

        params = [
            data['client_id'],
            date,
            data['type'],
            data['description'],
            str(data.get('amount', '0.00')),
            str(data.get('payment', '0.00')),
            str(data.get('debt', '0.00')),
            data.get('reference_id'),
            data.get('reference', '')
        ]

        self.db.execute_query(query, params, conn=conn, commit=commit)

    ## -- Obtiene el historial de un cliente  -- ##
    def get_account_history_from_client(self, client_id):
        query = """
        SELECT * FROM customer_ledger WHERE client_id = ? ORDER BY id DESC
        """

        return self.db.fetch_all(query, (client_id, ))

    ## -- Registra un ajuste de precio en customer_ledger -- ##
    def register_price_adjustment_in_account(
            self, 
            sale_id, 
            client_id, 
            old_total, 
            new_total, 
            conn=None, 
            commit=True
        ):
        difference = norm_to_2_dec(new_total - old_total)
        if difference == Decimal('0.00'):
            return

        balance = self.get_total_debt(client_id, conn=conn)

        data = {
            'client_id': client_id,
            'type': 'AJUSTE PRECIO',
            'description': f"Ajuste de precio Venta #{sale_id} · ${old_total} → ${new_total}",
            'amount': difference,
            'payment': Decimal('0.00'),
            'debt': balance,
            'reference_id': sale_id,
            'reference': f"Precio actualizado"
        }
        self.add_row_in_customer_ledger(data, conn=conn, commit=commit)

    ## -- Registra un pago en el historial del cliente-- ##
    def register_payment_in_account(
            self, 
            sale_id, 
            client_id,
            payment,
            method,
            type, 
            sale_status,
            conn=None, 
            commit=True
        ):

        method_map = {
            "cash": "Efectivo",
            "transfer": "Transferencia",
            "card": "Tarjeta",
            "efectivo": "Efectivo",
            "transferencia": "Transferencia",
            "saldo a favor": "Saldo a Favor",
            "cheque": "Cheque",
            "deposito": "Depósito",
            "global": "Global"
        }

        method_txt = method_map.get(method.lower() if method else "", method.capitalize() if method else "Efectivo")

        estado_map = {
            "pending": "Pendiente",
            "partial": "Pago parcial",
            "paid": "Pagada"
        }
        status_txt = estado_map.get(sale_status, sale_status)

        debt = self.get_total_debt(client_id, conn=conn)

        data = {
            'client_id': client_id,
            'type': type,
            'description': f"Pago Venta #{sale_id} · {method_txt} . {status_txt.upper()}",
            'amount': Decimal('0.00'),
            'payment': payment,
            'debt': debt,
            'reference_id': sale_id,
            'reference': f"Pago venta #{sale_id}"
        }
        self.add_row_in_customer_ledger(data, conn=conn, commit=commit)

    ## -- Registra un movimiento de saldo a favor  en el historial del cliente -- ##
    def register_credit_balance_in_account(self, client_id, reference_id, description, conn=None, commit=True):
        data = {
            'client_id': client_id,
            'type': 'SALDO FAVOR',
            'description': description,
            'amount': Decimal('0.00'),
            'payment': Decimal('0.00'),
            'debt': self.get_total_debt(client_id, conn=conn),
            'reference_id': reference_id,
            'reference': 'Saldo a favor'
        }
        self.add_row_in_customer_ledger(data, conn=conn, commit=commit)

    ## -- Registra la operacion de cheque rechazado en el historial del cliente -- ##
    def register_bounced_check_in_account(self, client_id, check_amount, debt_amount, conn=None, commit=True):
        data = {
            'client_id': client_id,
            'type': 'CHEQUE RECHAZADO',
            'description': f'Cheque rechazado · Monto: ${check_amount} ',
            'amount': Decimal('0.00'),
            'payment': Decimal('0.00'),
            'debt': debt_amount,
            'reference_id': None,
            'reference': 'Cheque rechazado'
        }
        self.add_row_in_customer_ledger(data, conn=conn, commit=commit)

    ## -- Obtiene la deuda total de un cliente en detalle -- ##
    def get_customer_debts(self, cliente_id):
        query = """
        SELECT 
            id,
            date,
            total,
            estado
        FROM sales
        WHERE cliente_id = ? AND estado IN ('pending', 'partial')
        GROUP BY id
        ORDER BY id DESC;
        """
        rows = self.db.fetch_all(query, (cliente_id,))

        state_map = {
            "pending": "Pendiente",
            "partial": "Pago parcial",
            "paid": "Pagada"
        }

        formatted = []
        for sale_id, date, total, estado in rows:
            pagado = self.pay_model.get_total_amount_of_pay_for_a_sale(sale_id)
            estado_es = state_map.get(estado, estado)
            saldo = Decimal(total) - Decimal(pagado)

            fecha_formateada = iso_to_traditional(date.split()[0]) if date else ""

            formatted.append((sale_id, fecha_formateada, total, pagado, saldo, estado_es))

        return formatted
    
    def get_sale_items(self, sale_id):
        query = """
            SELECT
                s.id,
                s.name,
                s.pack,
                si.quantity, 
                si.price,
                si.subtotal,
                si.observations
            FROM sale_items si
            JOIN stock s ON si.product_id = s.id
            WHERE si.sale_id = ?
        """
        return self.db.fetch_all(query, (sale_id,))

    def mark_debt_as_paid(self, sale_id):
        """Marcar deuda como pagada"""
        query = "UPDATE sales SET estado = 'paid' WHERE id = ?"
        self.db.execute_query(query, (sale_id,))

    def get_total_debt(self, cliente_id, conn=None):
        query = """
            SELECT s.id, s.total
            FROM sales s
            WHERE s.cliente_id = ?
            AND (
                s.estado IN ('pending', 'partial')
                OR (
                    s.estado = 'paid' 
                    AND EXISTS (
                        SELECT 1 FROM payments p WHERE p.sale_id = s.id
                    )
                )
            )
        """
        rows = self.db.fetch_all(query, (cliente_id,), conn=conn)
        total_pending = Decimal('0.00')

        for sale_id, total in rows:
            paid = self.pay_model.get_total_amount_of_pay_for_a_sale(sale_id, conn=conn)
            saldo = Decimal(total) - paid
            if saldo > Decimal('0.00'):
                total_pending += saldo

        return norm_to_2_dec(total_pending)

    def _is_cash_sale(self, sale_id):
        """
        Determina si una venta fue de CONTADO.
        
        Es CONTADO únicamente si:
        - Estado es 'paid' Y no tiene NINGÚN pago registrado en la tabla payments
        (significa que se pagó en el momento de crear la venta)
        
        Si tiene aunque sea UN pago registrado, es CRÉDITO (se muestra en historial)
        """
        payments_query = """
            SELECT COUNT(*) 
            FROM payments 
            WHERE sale_id = ?
        """
        result = self.db.fetch_one(payments_query, (sale_id,))
        
        # Es CONTADO solo si NO tiene pagos registrados
        # Si tiene pagos (parciales o totales), es CRÉDITO y debe mostrarse
        return result is None or result[0] == 0

    def get_account_history(self, client_id):
        # Guardar y obtener los movimientos de cuenta corriente del cliente
        movements = self.get_account_history_from_client(client_id)
        # Ledger vacío = cuenta reseteada, tarjetas en cero excepto credit y total_debt
        if not movements:
            credit     = self.customer_credit.get_customer_credit(client_id)
            summary = {
                'total_purchased': Decimal('0.00'),
                'total_paid':      Decimal('0.00'),
                'credit':          credit,
                'total_debt':      Decimal('0.00'),
                'sales_paid':      0,
                'total_sales':     0,
                'sales_balance':   "0/0 pagadas"
            }
            return movements, summary

        ## Generar resumen
        # Monto total en compras
        data_total_p = self.sales_model.get_total_of_all_sales(client_id)
        total_purchased = sum((Decimal(m[1]) for m in data_total_p), Decimal('0.00'))

        # Monto total en pagos reales — excluye aplicaciones de saldo a favor
        # (tipo CRÉDITO = plata interna, no dinero nuevo recibido)
        total_paid = self.pay_model.get_total_paid_by_client(client_id)

        # Deuda total
        total_debt = self.get_total_debt(client_id)
        
        # Contar ventas pagadas
        total_sales, sales_paid = self.count_sales_paid(movements)

        # saldo a favor
        credit = self.customer_credit.get_customer_credit(client_id)

        summary = {
            'total_purchased': total_purchased,
            'total_paid': total_paid,
            'credit': credit,        
            'total_debt': total_debt,  
            'sales_paid': sales_paid,
            'total_sales': total_sales,
            'sales_balance': f"{sales_paid}/{total_sales} pagadas"
        }

        print(f'summary: {summary}')

        return movements, summary
    
    ## -- count total sales and sales paid -- ##
    def count_sales_paid(self, movements):
        try:
            total_sales, sales_paid = 0, 0
            for m in movements:
                if m[3] == "VENTA":
                    total_sales += 1
                    result = self.db.fetch_one("SELECT estado FROM sales WHERE id = ?", (m[8],))
                    if result and result[0] == 'paid':
                        sales_paid += 1
            return total_sales, sales_paid
        except Exception as e:
            logger.error("Error contando ventas: %s", e)
            return 0, 0

    def get_customers_with_debt(self):
        query = """
            SELECT DISTINCT c.id, c.name, c.cuit, c.home, c.phone,
                c.iva_condition, c.cv, c.cuig, c.renspa, c.establishment
            FROM customer c
            JOIN sales s ON s.cliente_id = c.id
            WHERE s.estado IN ('pending', 'partial')
        """
        return self.db.fetch_all(query)

