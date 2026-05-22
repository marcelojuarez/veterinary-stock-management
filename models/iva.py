from db.database import db
from datetime import datetime, timedelta
from decimal import Decimal
from utils.utils import norm_to_2_dec

class IVAModel:
    def __init__(self, db_connection=None):
        self.db = db_connection or db

    # ================================================================
    # SALES - VAT DEBIT (FISCAL DEBT)
    # ================================================================

    def get_sales_iva(self, from_date, until_date):
        """Get VAT charged on sales (fiscal debt)"""
        query = """
            SELECT
                s.id as sale_id,
                s.date as date,
                COALESCE(c.name, 'Consumidor Final') as customer,
                COALESCE(c.cuit, '') as customer_cuit,
                COALESCE(c.iva_condition, 'Consumidor Final') as iva_condition,
                si.iva_rate as aliquot_iva,
                SUM(si.subtotal - si.iva_amount) as net,
                SUM(si.iva_amount) as iva,
                SUM(si.subtotal) as total
            FROM sales s
            LEFT JOIN customer c ON c.id = s.cliente_id
            JOIN sale_items si ON si.sale_id = s.id
            WHERE date(s.date) BETWEEN ? AND ?
            GROUP BY s.id, si.iva_rate
            ORDER BY s.date, s.id
        """
        return self.db.fetch_all(query, (from_date, until_date))

    def get_summary_sales_iva(self, from_date, until_date):
        query = """
            SELECT
                si.iva_rate as aliquot,
                SUM(si.subtotal - si.iva_amount) as taxable_net,
                SUM(si.iva_amount) as iva,
                SUM(si.subtotal) as total,
                COUNT(DISTINCT s.id) as transaction_count
            FROM sales s
            JOIN sale_items si ON si.sale_id = s.id
            WHERE date(s.date) BETWEEN ? AND ?
            GROUP BY si.iva_rate
            ORDER BY si.iva_rate DESC
        """
        rows = self.db.fetch_all(query, (from_date, until_date))
        result = []
        for row in rows:
            result.append({
                'aliquot': f"{float(row[0]):.1f}%" if row[0] else "0.0%",
                'taxable_net': norm_to_2_dec(Decimal(str(row[1] or 0))),
                'iva': norm_to_2_dec(Decimal(str(row[2] or 0))),
                'total': norm_to_2_dec(Decimal(str(row[3] or 0))),
                'transactions': int(row[4])
            })
        return result

    # ================================================================
    # PURCHASES - VAT CREDIT (FISCAL CREDIT)
    # ================================================================

    def get_purchases_iva(self, from_date, until_date):
        query = """
            SELECT
                p.id as purchase_id,
                p.date as date,
                COALESCE(s.name, 'Supplier') as supplier,
                COALESCE(s.cuit, '') as supplier_cuit,
                pi.iva_rate as aliquot_iva,
                SUM(pi.subtotal) as net,
                SUM(pi.iva_amount) as iva,
                SUM(pi.total) as total
            FROM purchase p
            LEFT JOIN supplier s ON s.id = p.supplier_id
            JOIN purchase_item pi ON pi.purchase_id = p.id
            WHERE date(p.date) BETWEEN ? AND ?
            GROUP BY p.id, pi.iva_rate
            ORDER BY p.date, p.id
        """
        return self.db.fetch_all(query, (from_date, until_date))

    def get_summary_purchases_iva(self, from_date, until_date):
        query = """
            SELECT
                pi.iva_rate as aliquot,
                SUM(pi.subtotal) as taxable_net,
                SUM(pi.iva_amount) as iva,
                SUM(pi.total) as total,
                COUNT(DISTINCT p.id) as transaction_count
            FROM purchase p
            JOIN purchase_item pi ON pi.purchase_id = p.id
            WHERE date(p.date) BETWEEN ? AND ?
            GROUP BY pi.iva_rate
            ORDER BY CAST(pi.iva_rate AS REAL) DESC
        """
        rows = self.db.fetch_all(query, (from_date, until_date))
        result = []
        for row in rows:
            result.append({
                'aliquot': f"{float(row[0] or 0):.1f}%",
                'taxable_net': norm_to_2_dec(Decimal(str(row[1] or 0))),
                'iva': norm_to_2_dec(Decimal(str(row[2] or 0))),
                'total': norm_to_2_dec(Decimal(str(row[3] or 0))),
                'transactions': int(row[4])
            })
        return result

    # ================================================================
    # IVA POSITION
    # ================================================================

    def get_iva_retentions_by_period(self, from_date, until_date):
        """Total IVA retentions suffered in the period (reduces fiscal debt)"""
        query = """
            SELECT COALESCE(SUM(CAST(sr.amount AS REAL)), 0)
            FROM sale_retentions sr
            JOIN sales s ON s.id = sr.sale_id
            WHERE sr.tax_type = 'IVA'
            AND date(s.date) BETWEEN ? AND ?
        """
        result = self.db.fetch_one(query, (from_date, until_date))
        return norm_to_2_dec(Decimal(str(result[0] if result else 0)))

    def get_iva_perceptions_by_period(self, from_date, until_date):
        """Total IVA perceptions suffered on purchases (increases fiscal credit)"""
        query = """
            SELECT COALESCE(SUM(CAST(ip.amount AS REAL)), 0)
            FROM invoice_perceptions ip
            JOIN supplier_invoice si ON si.id = ip.invoice_id
            WHERE ip.tax_type = 'IVA_PER'
            AND date(si.date) BETWEEN ? AND ?
        """
        result = self.db.fetch_one(query, (from_date, until_date))
        return norm_to_2_dec(Decimal(str(result[0] if result else 0)))

    def get_detailed_iva_position(self, from_date, until_date):
        sales_summary     = self.get_summary_sales_iva(from_date, until_date)
        purchases_summary = self.get_summary_purchases_iva(from_date, until_date)

        # IVA retentions suffered (reduce fiscal debt)
        ret_iva = self.get_iva_retentions_by_period(from_date, until_date)
        # IVA perceptions suffered on purchases (increase fiscal credit)
        per_iva = self.get_iva_perceptions_by_period(from_date, until_date)

        aliquots = set()
        for v in sales_summary:
            aliquots.add(v['aliquot'])
        for c in purchases_summary:
            aliquots.add(c['aliquot'])

        rows = []
        total_iva_sales     = Decimal('0.00')
        total_purchases_iva = Decimal('0.00')

        for aliquot in sorted(aliquots, reverse=True):
            aliquot_sales = next((v for v in sales_summary if v['aliquot'] == aliquot), None)
            iva_sales     = Decimal(str(aliquot_sales['iva'] if aliquot_sales else 0))
            sales_net     = Decimal(str(aliquot_sales['taxable_net'] if aliquot_sales else 0))

            aliquot_purchases = next((c for c in purchases_summary if c['aliquot'] == aliquot), None)
            purchases_iva     = Decimal(str(aliquot_purchases['iva'] if aliquot_purchases else 0))
            purchases_net     = Decimal(str(aliquot_purchases['taxable_net'] if aliquot_purchases else 0))

            # Gross balance (before retentions and perceptions)
            gross_balance = norm_to_2_dec(iva_sales - purchases_iva)

            rows.append({
                'aliquot':       aliquot,
                'sales_net':     sales_net,
                'iva_sales':     iva_sales,
                'purchases_net': purchases_net,
                'purchases_iva': purchases_iva,
                'balance':       gross_balance,  # gross (for display table)
            })

            total_iva_sales     += iva_sales
            total_purchases_iva += purchases_iva

        total_iva_sales     = norm_to_2_dec(total_iva_sales)
        total_purchases_iva = norm_to_2_dec(total_purchases_iva)

        # Real fiscal debt and credit (including retentions/perceptions)
        fiscal_debt   = norm_to_2_dec(total_iva_sales  - ret_iva)
        fiscal_credit = norm_to_2_dec(total_purchases_iva + per_iva)
        net_balance   = norm_to_2_dec(fiscal_debt - fiscal_credit)

        return {
            'rows':                rows,
            'total_iva_sales':     total_iva_sales,
            'total_purchases_iva': total_purchases_iva,
            'ret_iva':             ret_iva,
            'per_iva':             per_iva,
            'fiscal_debt':         fiscal_debt,
            'fiscal_credit':       fiscal_credit,
            'balance_gross':       norm_to_2_dec(total_iva_sales - total_purchases_iva),
            'balance_total':       net_balance,
            'status': 'PAYABLE' if net_balance > 0 else ('CREDIT BALANCE' if net_balance < 0 else 'NO BALANCE')
        }

    def _get_iibb_retentions_by_period(self, from_date, until_date):
        query = """
            SELECT COALESCE(SUM(CAST(sr.amount AS REAL)), 0)
            FROM sale_retentions sr
            JOIN sales s ON s.id = sr.sale_id
            WHERE sr.tax_type = 'IIBB'
            AND date(s.date) BETWEEN ? AND ?
        """
        result = self.db.fetch_one(query, (from_date, until_date))
        return norm_to_2_dec(Decimal(str(result[0] if result else 0)))

    def _get_iibb_perceptions_by_period(self, from_date, until_date):
        query = """
            SELECT COALESCE(SUM(CAST(ip.amount AS REAL)), 0)
            FROM invoice_perceptions ip
            JOIN supplier_invoice si ON si.id = ip.invoice_id
            WHERE ip.tax_type = 'IIBB_PER'
            AND date(si.date) BETWEEN ? AND ?
        """
        result = self.db.fetch_one(query, (from_date, until_date))
        return norm_to_2_dec(Decimal(str(result[0] if result else 0)))

    def get_iva_position(self, from_date, until_date):
        sales_summary     = self.get_summary_sales_iva(from_date, until_date)
        purchases_summary = self.get_summary_purchases_iva(from_date, until_date)

        iva_sales     = norm_to_2_dec(sum((r['iva'] for r in sales_summary),     Decimal('0')))
        purchases_iva = norm_to_2_dec(sum((r['iva'] for r in purchases_summary), Decimal('0')))

        retentions_iva  = self.get_iva_retentions_by_period(from_date, until_date)
        retentions_iibb = self._get_iibb_retentions_by_period(from_date, until_date)
        perceptions_iva = self.get_iva_perceptions_by_period(from_date, until_date)
        perceptions_iibb = self._get_iibb_perceptions_by_period(from_date, until_date)

        fiscal_debt   = norm_to_2_dec(iva_sales - retentions_iva)
        fiscal_credit = norm_to_2_dec(purchases_iva + perceptions_iva)
        iva_balance   = norm_to_2_dec(fiscal_debt - fiscal_credit)

        return {
            'iva_sales':        iva_sales,
            'retentions_iva':   retentions_iva,
            'retentions_iibb':  retentions_iibb,
            'fiscal_debt':      fiscal_debt,
            'purchases_iva':    purchases_iva,
            'perceptions_iva':  perceptions_iva,
            'perceptions_iibb': perceptions_iibb,
            'fiscal_credit':    fiscal_credit,
            'balance':          iva_balance,
            'status': 'PAYABLE' if iva_balance > 0 else ('CREDIT BALANCE' if iva_balance < 0 else 'NO BALANCE')
        }

    # ================================================================
    # PERCEPTIONS - DETAIL
    # ================================================================

    def get_suffered_perceptions(self, from_date, until_date):
        query = """
            SELECT
                si.date as date,
                si.invoice_id as invoice_number,
                COALESCE(s.name, 'Supplier') as supplier,
                COALESCE(s.cuit, '') as cuit,
                ip.tax_type,
                CAST(ip.amount AS REAL) as amount
            FROM invoice_perceptions ip
            JOIN supplier_invoice si ON si.id = ip.invoice_id
            LEFT JOIN supplier s ON s.id = si.supplier_id
            WHERE date(si.date) BETWEEN ? AND ?
            ORDER BY si.date, si.id
        """
        return self.db.fetch_all(query, (from_date, until_date))

    def get_made_perceptions(self, _from_date, _until_date):
        return []

    def get_total_perceptions(self, from_date, until_date):
        suffered = self.get_suffered_perceptions(from_date, until_date)
        made     = self.get_made_perceptions(from_date, until_date)

        total_suffered = sum(norm_to_2_dec(Decimal(str(r[5] or 0))) for r in suffered)
        total_made     = sum(norm_to_2_dec(Decimal(str(r[5] or 0))) for r in made)

        return norm_to_2_dec(total_suffered), norm_to_2_dec(total_made)

    def get_suffered_retentions(self, from_date, until_date):
        query = """
            SELECT
                s.date as date,
                s.id as sale_id,
                COALESCE(c.name, 'Final Consumer') as customer,
                COALESCE(c.cuit, '') as cuit,
                sr.tax_type,
                COALESCE(sr.certificate_number, '') as certificate,
                CAST(sr.amount AS REAL) as amount
            FROM sale_retentions sr
            JOIN sales s ON s.id = sr.sale_id
            LEFT JOIN customer c ON c.id = s.cliente_id
            WHERE date(s.date) BETWEEN ? AND ?
            ORDER BY s.date, s.id
        """
        return self.db.fetch_all(query, (from_date, until_date))

    def get_made_retentions(self, _from_date, _until_date):
        return []

    def get_total_retentions(self, from_date, until_date):
        suffered = self.get_suffered_retentions(from_date, until_date)
        made     = self.get_made_retentions(from_date, until_date)

        total_suffered = sum(norm_to_2_dec(Decimal(str(r[6] or 0))) for r in suffered)
        total_made     = sum(norm_to_2_dec(Decimal(str(r[6] or 0))) for r in made)

        return norm_to_2_dec(total_suffered), norm_to_2_dec(total_made)

    # ================================================================
    # UTILITIES
    # ================================================================

    def get_current_period(self):
        today = datetime.now()
        first_day = today.replace(day=1).strftime("%Y-%m-%d")
        if today.month == 12:
            last_day = today.replace(day=31).strftime("%Y-%m-%d")
        else:
            next_month = today.replace(month=today.month + 1, day=1)
            last_day = (next_month - timedelta(days=1)).strftime("%Y-%m-%d")
        return first_day, last_day

    def get_month_period(self, month, year):
        from calendar import monthrange
        first_day = f"{year}-{month:02d}-01"
        last_day_number = monthrange(year, month)[1]
        last_day = f"{year}-{month:02d}-{last_day_number:02d}"
        return first_day, last_day

    def validate_iva_data(self):
        query = """
            SELECT id, name, iva
            FROM stock
            WHERE iva IS NULL OR CAST(iva AS REAL) <= 0
        """
        return self.db.fetch_all(query)

    def validate_sales_without_iva(self):
        query = """
            SELECT COUNT(*)
            FROM sale_items
            WHERE iva_amount IS NULL OR iva_amount = 0
        """
        result = self.db.fetch_one(query)
        return result[0] if result else 0
