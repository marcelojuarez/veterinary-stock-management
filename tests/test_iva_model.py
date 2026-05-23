import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import tempfile
from decimal import Decimal
from db.database import Database
from models.iva import IVAModel


def make_test_db():
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp.close()
    db = Database(tmp.name)
    return db, tmp.name


def _insert_customer(db, cid=1):
    db.execute_query(
        "INSERT INTO customer (id, name, cuit, home, iva_condition) VALUES (?, 'TEST', NULL, 'CITY', 'RI')",
        (cid,)
    )


def _insert_product(db, pid=1):
    db.execute_query(
        "INSERT INTO stock (id, name, pack, list_price, discount, cost_price, profit, "
        "price, iva, price_with_iva, quantity) VALUES (?, 'PROD', 'UNIT', '100', '0', '80', '20', '100', '21', '121', 100)",
        (pid,)
    )


def _insert_sale(db, sale_id, cliente_id, date, total):
    db.execute_query(
        "INSERT INTO sales (id, date, total, cliente_id, estado) VALUES (?, ?, ?, ?, 'paid')",
        (sale_id, date, str(total), cliente_id)
    )


def _insert_sale_item(db, sale_id, product_id, quantity, price, subtotal, iva_rate, iva_amount):
    db.execute_query(
        "INSERT INTO sale_items (sale_id, product_id, quantity, price, subtotal, iva_rate, iva_amount) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (sale_id, product_id, quantity, str(price), str(subtotal), str(iva_rate), str(iva_amount))
    )


class TestDateFilterLastDay(unittest.TestCase):
    """Bug 1: date() wrapper — transactions on last day of period must be included."""

    def setUp(self):
        self.db, self.db_path = make_test_db()
        _insert_customer(self.db)
        _insert_product(self.db)
        self.model = IVAModel(db_connection=self.db)

    def tearDown(self):
        os.unlink(self.db_path)

    def test_last_day_late_evening_included(self):
        """Sale at 23:59 on the last day must appear in the period."""
        _insert_sale(self.db, 1, 1, "2026-05-31 23:59:59", "121.00")
        _insert_sale_item(self.db, 1, 1, 1, "121.00", "121.00", "21.00", "21.00")

        rows = self.model.get_sales_iva("2026-05-01", "2026-05-31")
        self.assertEqual(len(rows), 1, "Sale at 23:59 on last day must be included")

    def test_sale_day_before_start_excluded(self):
        """Sale on the day before period start must not appear."""
        _insert_sale(self.db, 2, 1, "2026-04-30 23:59:59", "121.00")
        _insert_sale_item(self.db, 2, 1, 1, "121.00", "121.00", "21.00", "21.00")

        rows = self.model.get_sales_iva("2026-05-01", "2026-05-31")
        self.assertEqual(len(rows), 0)

    def test_sale_day_after_end_excluded(self):
        """Sale on the day after period end must not appear."""
        _insert_sale(self.db, 3, 1, "2026-06-01 00:00:01", "121.00")
        _insert_sale_item(self.db, 3, 1, 1, "121.00", "121.00", "21.00", "21.00")

        rows = self.model.get_sales_iva("2026-05-01", "2026-05-31")
        self.assertEqual(len(rows), 0)

    def test_first_middle_and_last_day_all_included(self):
        for sid, date in [
            (4, "2026-05-01 08:00:00"),
            (5, "2026-05-15 14:30:00"),
            (6, "2026-05-31 22:00:00"),
        ]:
            _insert_sale(self.db, sid, 1, date, "121.00")
            _insert_sale_item(self.db, sid, 1, 1, "121.00", "121.00", "21.00", "21.00")

        rows = self.model.get_sales_iva("2026-05-01", "2026-05-31")
        self.assertEqual(len(rows), 3)

    def test_summary_also_respects_date_filter(self):
        """get_summary_sales_iva must also include last-day transactions."""
        _insert_sale(self.db, 7, 1, "2026-05-31 23:00:00", "121.00")
        _insert_sale_item(self.db, 7, 1, 1, "121.00", "121.00", "21.00", "21.00")

        summary = self.model.get_summary_sales_iva("2026-05-01", "2026-05-31")
        self.assertTrue(len(summary) > 0, "summary must have rows when period has sales")
        total_iva = sum(row['iva'] for row in summary)
        self.assertEqual(total_iva, Decimal("21.00"))


class TestTaxableNetCalculation(unittest.TestCase):
    """Bug 2: taxable_net = SUM(subtotal - iva_amount), not SUM(quantity * price)."""

    def setUp(self):
        self.db, self.db_path = make_test_db()
        _insert_customer(self.db)
        _insert_product(self.db)
        self.model = IVAModel(db_connection=self.db)

    def tearDown(self):
        os.unlink(self.db_path)

    def test_taxable_net_is_net_without_iva(self):
        """
        price=121 (price_with_iva), subtotal=121, iva_amount=21.
        Correct taxable_net = 121 - 21 = 100.
        Old bug: SUM(quantity * price) = 121 (wrong).
        """
        _insert_sale(self.db, 1, 1, "2026-05-10 10:00:00", "121.00")
        _insert_sale_item(self.db, 1, 1, 1, "121.00", "121.00", "21.00", "21.00")

        summary = self.model.get_summary_sales_iva("2026-05-01", "2026-05-31")
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]['taxable_net'], Decimal("100.00"))
        self.assertEqual(summary[0]['iva'], Decimal("21.00"))
        self.assertEqual(summary[0]['total'], Decimal("121.00"))

    def test_taxable_net_two_items_same_sale(self):
        """Two items, each subtotal=121 iva=21 → net=200, total=242."""
        _insert_sale(self.db, 2, 1, "2026-05-15 10:00:00", "242.00")
        _insert_sale_item(self.db, 2, 1, 1, "121.00", "121.00", "21.00", "21.00")
        _insert_sale_item(self.db, 2, 1, 1, "121.00", "121.00", "21.00", "21.00")

        summary = self.model.get_summary_sales_iva("2026-05-01", "2026-05-31")
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]['taxable_net'], Decimal("200.00"))
        self.assertEqual(summary[0]['iva'], Decimal("42.00"))
        self.assertEqual(summary[0]['total'], Decimal("242.00"))

    def test_taxable_net_different_aliquots_separate_rows(self):
        """Items with different IVA rates produce separate summary rows."""
        _insert_sale(self.db, 3, 1, "2026-05-20 10:00:00", "231.50")
        # 21% aliquot: subtotal=121, iva=21
        _insert_sale_item(self.db, 3, 1, 1, "121.00", "121.00", "21.00", "21.00")
        # 10.5% aliquot: subtotal=110.50, iva=10.50
        _insert_sale_item(self.db, 3, 1, 1, "110.50", "110.50", "10.50", "10.50")

        summary = self.model.get_summary_sales_iva("2026-05-01", "2026-05-31")
        aliquots = {r['aliquot'] for r in summary}
        self.assertEqual(len(aliquots), 2)

        row_21 = next(r for r in summary if r['aliquot'] == "21.0%")
        self.assertEqual(row_21['taxable_net'], Decimal("100.00"))

        row_105 = next(r for r in summary if r['aliquot'] == "10.5%")
        self.assertEqual(row_105['taxable_net'], Decimal("100.00"))


class TestIVAPosition(unittest.TestCase):
    """get_iva_position and get_detailed_iva_position correctness."""

    def setUp(self):
        self.db, self.db_path = make_test_db()
        _insert_customer(self.db)
        _insert_product(self.db)
        self.model = IVAModel(db_connection=self.db)

    def tearDown(self):
        os.unlink(self.db_path)

    def test_empty_period_all_zeros(self):
        result = self.model.get_iva_position("2026-05-01", "2026-05-31")
        self.assertEqual(result['iva_sales'], Decimal("0.00"))
        self.assertEqual(result['purchases_iva'], Decimal("0.00"))
        self.assertEqual(result['balance'], Decimal("0.00"))
        self.assertEqual(result['status'], 'NO BALANCE')

    def test_payable_when_sales_iva_exceeds_purchases(self):
        _insert_sale(self.db, 1, 1, "2026-05-10 10:00:00", "121.00")
        _insert_sale_item(self.db, 1, 1, 1, "121.00", "121.00", "21.00", "21.00")

        result = self.model.get_iva_position("2026-05-01", "2026-05-31")
        self.assertEqual(result['iva_sales'], Decimal("21.00"))
        self.assertEqual(result['balance'], Decimal("21.00"))
        self.assertEqual(result['status'], 'PAYABLE')

    def test_required_keys_present(self):
        result = self.model.get_iva_position("2026-05-01", "2026-05-31")
        for key in ('iva_sales', 'retentions_iva', 'retentions_iibb', 'fiscal_debt',
                    'purchases_iva', 'perceptions_iva', 'perceptions_iibb',
                    'fiscal_credit', 'balance', 'status'):
            self.assertIn(key, result, f"Missing key: '{key}'")

    def test_detailed_position_keys_match_pdf_expectations(self):
        """Keys returned must match what iva_report_pdf.py reads."""
        result = self.model.get_detailed_iva_position("2026-05-01", "2026-05-31")
        for key in ('rows', 'balance_gross', 'balance_total', 'status',
                    'fiscal_debt', 'fiscal_credit', 'ret_iva', 'per_iva'):
            self.assertIn(key, result, f"Missing key: '{key}'")

    def test_detailed_position_row_has_balance_key(self):
        """Each row in 'rows' must have 'balance' key (not 'saldo')."""
        _insert_sale(self.db, 1, 1, "2026-05-10 10:00:00", "121.00")
        _insert_sale_item(self.db, 1, 1, 1, "121.00", "121.00", "21.00", "21.00")

        result = self.model.get_detailed_iva_position("2026-05-01", "2026-05-31")
        self.assertTrue(len(result['rows']) > 0)
        for row in result['rows']:
            self.assertIn('balance', row, "Each row must have 'balance' key")
            self.assertNotIn('saldo', row, "Old 'saldo' key must not be present")


if __name__ == "__main__":
    unittest.main()
