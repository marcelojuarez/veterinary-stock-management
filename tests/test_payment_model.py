import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import tempfile
from decimal import Decimal
from unittest.mock import MagicMock
from db.database import Database
from models.payment_model import PaymentModel


def make_test_db():
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp.close()
    db = Database(tmp.name)
    return db, tmp.name


def _make_model(db):
    checks_model = MagicMock()
    checks_model.get_cartera_total_from_client.return_value = "0.00"
    sale_model = MagicMock()
    customer_credit = MagicMock()
    customer_model = MagicMock()
    model = PaymentModel(
        sales_model=sale_model,
        customer_credit=customer_credit,
        checks_model=checks_model,
        customer_model=customer_model
    )
    model.db = db
    return model, sale_model, customer_credit, customer_model


def _insert_customer(db, cid=1):
    db.execute_query(
        "INSERT INTO customer (id, name, cuit, home, iva_condition) VALUES (?, 'TEST', NULL, 'CITY', 'CF')",
        (cid,)
    )


def _insert_sale(db, sale_id, cliente_id, total, estado='pending'):
    db.execute_query(
        "INSERT INTO sales (id, date, total, cliente_id, estado) "
        "VALUES (?, '2026-05-10 10:00:00', ?, ?, ?)",
        (sale_id, str(total), cliente_id, estado)
    )


def _insert_payment(db, sale_id, client_id, amount, valid=1):
    db.execute_query(
        "INSERT INTO payments (sale_id, client_id, amount, method, valid) "
        "VALUES (?, ?, ?, 'Efectivo', ?)",
        (sale_id, client_id, str(amount), valid)
    )


class TestGetTotalAmountOfPayForSale(unittest.TestCase):

    def setUp(self):
        self.db, self.db_path = make_test_db()
        self.model, *_ = _make_model(self.db)
        _insert_customer(self.db)

    def tearDown(self):
        os.unlink(self.db_path)

    def test_no_payments_returns_zero(self):
        _insert_sale(self.db, 1, 1, "500.00")
        self.assertEqual(self.model.get_total_amount_of_pay_for_a_sale(1), Decimal("0.00"))

    def test_single_payment(self):
        _insert_sale(self.db, 1, 1, "500.00")
        _insert_payment(self.db, 1, 1, "200.00")
        self.assertEqual(self.model.get_total_amount_of_pay_for_a_sale(1), Decimal("200.00"))

    def test_multiple_payments_summed(self):
        _insert_sale(self.db, 1, 1, "500.00")
        _insert_payment(self.db, 1, 1, "100.00")
        _insert_payment(self.db, 1, 1, "150.00")
        _insert_payment(self.db, 1, 1, "250.00")
        self.assertEqual(self.model.get_total_amount_of_pay_for_a_sale(1), Decimal("500.00"))

    def test_cancelled_payments_excluded(self):
        _insert_sale(self.db, 1, 1, "500.00")
        _insert_payment(self.db, 1, 1, "300.00", valid=1)
        _insert_payment(self.db, 1, 1, "200.00", valid=0)  # cancelled
        self.assertEqual(self.model.get_total_amount_of_pay_for_a_sale(1), Decimal("300.00"))

    def test_different_sales_not_mixed(self):
        _insert_sale(self.db, 1, 1, "500.00")
        _insert_sale(self.db, 2, 1, "300.00")
        _insert_payment(self.db, 1, 1, "500.00")
        _insert_payment(self.db, 2, 1, "300.00")
        self.assertEqual(self.model.get_total_amount_of_pay_for_a_sale(1), Decimal("500.00"))
        self.assertEqual(self.model.get_total_amount_of_pay_for_a_sale(2), Decimal("300.00"))


class TestUpdateSaleStatus(unittest.TestCase):

    def setUp(self):
        self.db, self.db_path = make_test_db()
        self.model, *_ = _make_model(self.db)
        _insert_customer(self.db)

    def tearDown(self):
        os.unlink(self.db_path)

    def test_no_payment_is_pending(self):
        _insert_sale(self.db, 1, 1, "500.00", estado='pending')
        self.assertEqual(self.model.update_sale_status(1), 'pending')

    def test_partial_payment_is_partial(self):
        _insert_sale(self.db, 1, 1, "500.00")
        _insert_payment(self.db, 1, 1, "300.00")
        self.assertEqual(self.model.update_sale_status(1), 'partial')

    def test_exact_payment_is_paid(self):
        _insert_sale(self.db, 1, 1, "500.00")
        _insert_payment(self.db, 1, 1, "500.00")
        self.assertEqual(self.model.update_sale_status(1), 'paid')

    def test_nonexistent_sale_returns_false(self):
        self.assertFalse(self.model.update_sale_status(9999))

    def test_status_written_to_db(self):
        _insert_sale(self.db, 1, 1, "500.00")
        _insert_payment(self.db, 1, 1, "500.00")
        self.model.update_sale_status(1)
        row = self.db.fetch_one("SELECT estado FROM sales WHERE id = 1")
        self.assertEqual(row[0], 'paid')


class TestApplyGlobalPaymentFIFO(unittest.TestCase):
    """FIFO distribution across multiple pending sales."""

    def setUp(self):
        self.db, self.db_path = make_test_db()
        self.model, self.sale_model, self.customer_credit, self.customer_model = _make_model(self.db)
        _insert_customer(self.db)

    def tearDown(self):
        os.unlink(self.db_path)

    def test_exact_payment_one_sale(self):
        _insert_sale(self.db, 1, 1, "500.00", estado='pending')
        self.sale_model.get_total_of_all_sales.return_value = [(1, "500.00")]

        result = self.model.apply_global_payment(1, Decimal("500.00"), method="Efectivo")

        self.assertIsNot(result, False)
        self.assertEqual(result['used'], Decimal("500.00"))
        self.assertEqual(result['remaining'], Decimal("0.00"))
        self.assertEqual(result['still_owed'], Decimal("0.00"))

    def test_fifo_oldest_sale_paid_first(self):
        """$400 payment against two $300 sales: first fully paid, second partial."""
        _insert_sale(self.db, 1, 1, "300.00", estado='pending')
        _insert_sale(self.db, 2, 1, "300.00", estado='pending')
        self.sale_model.get_total_of_all_sales.return_value = [(1, "300.00"), (2, "300.00")]

        result = self.model.apply_global_payment(1, Decimal("400.00"), method="Efectivo")

        self.assertIsNot(result, False)
        debts = dict(result['updated_debts'])
        self.assertEqual(debts[1], Decimal("300.00"), "First sale must be fully covered")
        self.assertEqual(debts[2], Decimal("100.00"), "Second sale gets the remainder")
        self.assertEqual(result['remaining'], Decimal("0.00"))
        self.assertEqual(result['still_owed'], Decimal("200.00"))

    def test_payment_exceeds_all_debt(self):
        """Surplus cash (no check_id) should not create credit."""
        _insert_sale(self.db, 1, 1, "300.00", estado='pending')
        self.sale_model.get_total_of_all_sales.return_value = [(1, "300.00")]

        result = self.model.apply_global_payment(1, Decimal("300.00"), method="Efectivo")

        self.assertEqual(result['surplus'], Decimal("0.00"))
        self.customer_credit.add_customer_credit.assert_not_called()

    def test_result_keys_present(self):
        _insert_sale(self.db, 1, 1, "300.00", estado='pending')
        self.sale_model.get_total_of_all_sales.return_value = [(1, "300.00")]

        result = self.model.apply_global_payment(1, Decimal("300.00"), method="Efectivo")

        for key in ('used', 'remaining', 'updated_debts', 'still_owed', 'surplus', 'credit_added'):
            self.assertIn(key, result, f"Missing key: '{key}'")

    def test_invalid_customer_returns_empty_distribution(self):
        """No pending sales for customer → nothing distributed."""
        self.sale_model.get_total_of_all_sales.return_value = []

        result = self.model.apply_global_payment(999, Decimal("500.00"), method="Efectivo")

        self.assertIsNot(result, False)
        self.assertEqual(result['updated_debts'], [])
        self.assertEqual(result['used'], Decimal("0.00"))


if __name__ == "__main__":
    unittest.main()
