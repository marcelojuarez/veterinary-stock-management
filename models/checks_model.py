"""
Modelo para gestión de cheques físicos y eCheq.
Ciclo de vida: EN_CARTERA → COBRADO | ENDOSADO | RECHAZADO

Las tablas checks y check_id en payments se crean en database.py.
"""

from db.database import db
from decimal import Decimal


class ChecksModel:
    def __init__(self):
        self.db = db

    # ----------------------------------------------------------------
    # CREAR CHEQUE
    # ----------------------------------------------------------------
    def create_check(self, *, number, bank, check_type, amount,
                     issue_date, due_date, origin="CLIENTE",
                     client_id, purchase_id=None, notes=None,
                     conn=None, commit=True):
        query = """
            INSERT INTO checks
                (number, bank, type, amount, issue_date, due_date,
                 status, origin, client_id, purchase_id, notes) 
            VALUES (?, ?, ?, ?, ?, ?, 'EN_CARTERA', ?, ?, ?, ?)
        """
        return self.db.execute_query(
            query,
            (
                number.strip().upper(),
                bank.strip().upper(),
                check_type.strip().upper(),
                str(amount),
                issue_date,
                due_date,
                origin.strip().upper(),
                client_id,
                purchase_id,
                notes.strip().upper() if notes else None,
            ),
            conn=conn, commit=commit
        )

    # ----------------------------------------------------------------
    # CONSULTAS
    # ----------------------------------------------------------------
    def get_all_checks(self, status=None, origin=None):
        """Devuelve cheques filtrados opcionalmente por status y/u origin."""
        params = []
        where_clauses = []

        if status:
            where_clauses.append("status = ?")
            params.append(status)
        if origin:
            where_clauses.append("origin = ?")
            params.append(origin)

        where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        query = f"""
        SELECT
            c.id, c.number, c.bank, c.type,
            c.amount, c.issue_date, c.due_date, c.status, c.origin,
            c.client_id, c.purchase_id, c.notes,
            cu.name AS client_name
        FROM checks c
        LEFT JOIN customer cu ON cu.id = c.client_id
            {where}
            ORDER BY c.due_date ASC
        """
        return self.db.fetch_all(query, params) or []

    def get_check_by_id(self, check_id, conn=None):
        return self.db.fetch_one(
            "SELECT * FROM checks WHERE id = ?", (check_id,), conn=conn
        )

    def get_checks_en_cartera(self):
        return self.get_all_checks(status="EN_CARTERA")

    # ----------------------------------------------------------------
    # CAMBIOS DE ESTADO
    # ----------------------------------------------------------------
    def update_status(self, check_id, new_status, purchase_id=None, conn=None, commit=True):
        """Cambia el estado del cheque. Si se endosa, guarda purchase_id."""
        new_status = new_status.upper()
        if purchase_id:
            return self.db.execute_query(
                "UPDATE checks SET status = ?, purchase_id = ? WHERE id = ?",
                (new_status, purchase_id, check_id),
                conn=conn, commit=commit
            )
        return self.db.execute_query(
            "UPDATE checks SET status = ? WHERE id = ?",
            (new_status, check_id),
            conn=conn, commit=commit
        )

    def endorse_to_purchase(self, check_id, purchase_id):
        """Endosa el cheque a una compra de proveedor."""
        return self.update_status(check_id, "ENDOSADO", purchase_id=purchase_id)

    def mark_cobrado(self, check_id):
        return self.update_status(check_id, "COBRADO")

    def mark_rechazado(self, check_id, conn=None, commit=True):
        return self.update_status(check_id, "RECHAZADO", None, conn=conn, commit=commit)

    # ----------------------------------------------------------------
    # LINK payment → check (post-insert)
    # ----------------------------------------------------------------
    # def link_payment(self, check_id, payment_id, conn=None, commit=True):
    #     """Una vez creado el payment, enlaza su id al cheque."""
    #     return self.db.execute_query(
    #         "UPDATE checks SET client_payment_id = ? WHERE id = ?",
    #         (payment_id, check_id),
    #         conn=conn, commit=commit
    #     )

    # ----------------------------------------------------------------
    # STATS
    # ----------------------------------------------------------------
    def get_cartera_total(self) -> Decimal:
        rows = self.db.fetch_all(
            "SELECT amount FROM checks WHERE status = 'EN_CARTERA'"
        )
        return sum((Decimal(r[0]) for r in rows), Decimal('0.00'))

    def get_cartera_total_from_client(self, client_id):
        rows = self.db.fetch_all(
            """
            SELECT amount 
            FROM checks 
            WHERE status = 'EN_CARTERA' and client_id = ?
            """,
            (client_id, )
        )
        return sum((Decimal(r[0]) for r in rows), Decimal('0.00'))


    def get_sales_affected_by_check(self, check_id, conn=None):
        query = """
            SELECT DISTINCT sale_id, client_id
            FROM payments
            WHERE check_id = ?
        """
        return self.db.fetch_all(query, (check_id,), conn=conn)
