import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import tempfile
from decimal import Decimal
from unittest.mock import MagicMock
from db.database import Database
from models.customer import CustomerModel
from models.payment_model import PaymentModel
from models.customer_credit import CustomerCredit
import models.customer as customer_module


def make_test_db():
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp.close()
    db = Database(tmp.name)
    return db, tmp.name


def _make_customer_model(db):
    """Builds CustomerModel with real PaymentModel — all wired to the same test DB."""
    checks_mock = MagicMock()
    checks_mock.get_cartera_total_from_client.return_value = "0.00"

    credit_model = CustomerCredit.__new__(CustomerCredit)
    credit_model.db = db

    pay_model = PaymentModel(
        sales_model=MagicMock(),
        customer_credit=credit_model,
        checks_model=checks_mock,
        customer_model=None
    )
    pay_model.db = db

    sales_mock = MagicMock()

    customer_model = CustomerModel(
        pay_model=pay_model,
        customer_credit=credit_model,
        sales_model=sales_mock,
        db_connection=db
    )
    return customer_model


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


class TestGetTotalDebt(unittest.TestCase):

    def setUp(self):
        self.db, self.db_path = make_test_db()
        _insert_customer(self.db)
        self.model = _make_customer_model(self.db)

    def tearDown(self):
        os.unlink(self.db_path)

    def test_no_sales_returns_zero(self):
        self.assertEqual(self.model.get_total_debt(1), Decimal("0.00"))

    def test_one_fully_unpaid_sale(self):
        _insert_sale(self.db, 1, 1, "500.00", estado='pending')
        self.assertEqual(self.model.get_total_debt(1), Decimal("500.00"))

    def test_one_partial_sale(self):
        _insert_sale(self.db, 1, 1, "500.00", estado='partial')
        _insert_payment(self.db, 1, 1, "200.00")
        self.assertEqual(self.model.get_total_debt(1), Decimal("300.00"))

    def test_one_fully_paid_sale_no_debt(self):
        _insert_sale(self.db, 1, 1, "500.00", estado='paid')
        # Paid sales with no payments entry → cash sale, not in debt query
        self.assertEqual(self.model.get_total_debt(1), Decimal("0.00"))

    def test_paid_sale_with_payment_record_no_balance(self):
        # paid + payment registered = no balance remaining
        _insert_sale(self.db, 1, 1, "500.00", estado='paid')
        _insert_payment(self.db, 1, 1, "500.00")
        self.assertEqual(self.model.get_total_debt(1), Decimal("0.00"))

    def test_multiple_pending_sales_summed(self):
        _insert_sale(self.db, 1, 1, "300.00", estado='pending')
        _insert_sale(self.db, 2, 1, "400.00", estado='pending')
        self.assertEqual(self.model.get_total_debt(1), Decimal("700.00"))

    def test_mix_paid_and_pending(self):
        _insert_sale(self.db, 1, 1, "300.00", estado='paid')   # cash, no payments
        _insert_sale(self.db, 2, 1, "400.00", estado='pending')
        _insert_sale(self.db, 3, 1, "200.00", estado='partial')
        _insert_payment(self.db, 3, 1, "100.00")
        # Only sales 2 and 3 count: 400 + 100 = 500
        self.assertEqual(self.model.get_total_debt(1), Decimal("500.00"))

    def test_different_clients_not_mixed(self):
        _insert_customer(self.db, cid=2)
        _insert_sale(self.db, 1, 1, "300.00", estado='pending')
        _insert_sale(self.db, 2, 2, "999.00", estado='pending')
        self.assertEqual(self.model.get_total_debt(1), Decimal("300.00"))
        self.assertEqual(self.model.get_total_debt(2), Decimal("999.00"))

    def test_cancelled_payments_ignored(self):
        _insert_sale(self.db, 1, 1, "500.00", estado='partial')
        _insert_payment(self.db, 1, 1, "300.00", valid=1)
        _insert_payment(self.db, 1, 1, "200.00", valid=0)  # cancelled
        # Only the valid payment counts: debt = 500 - 300 = 200
        self.assertEqual(self.model.get_total_debt(1), Decimal("200.00"))


class TestCheckDuplicateCustomer(unittest.TestCase):
    """
    check_duplicate_customer uses the module-level `db` (not self.db),
    so we redirect customer_module.db to the test DB in setUp/tearDown.
    """

    def setUp(self):
        self.db, self.db_path = make_test_db()
        self._original_db = customer_module.db
        customer_module.db = self.db  # redirect module-level db to test db
        self.model = _make_customer_model(self.db)
        self.db.execute_query(
            "INSERT INTO customer (id, name, cuit, phone, home, iva_condition) "
            "VALUES (1, 'EXISTING', '20-12345678-9', '1234567890', 'CITY', 'CF')"
        )

    def tearDown(self):
        customer_module.db = self._original_db  # restore
        os.unlink(self.db_path)

    def test_no_duplicate_returns_none(self):
        result = self.model.check_duplicate_customer({'cuit': '99-99999999-9', 'phone': '9999999999'})
        self.assertIsNone(result)

    def test_duplicate_cuit_returns_message(self):
        result = self.model.check_duplicate_customer({'cuit': '20-12345678-9', 'phone': ''})
        self.assertIsNotNone(result)
        self.assertIn("CUIT", result)

    def test_duplicate_phone_returns_message(self):
        result = self.model.check_duplicate_customer({'cuit': '', 'phone': '1234567890'})
        self.assertIsNotNone(result)
        self.assertIn("teléfono", result)

    def test_exclude_same_id_on_edit(self):
        # Editing customer 1 with its own data must not flag as duplicate
        result = self.model.check_duplicate_customer(
            {'cuit': '20-12345678-9', 'phone': '1234567890'},
            exclude_id=1
        )
        self.assertIsNone(result)

    def test_empty_cuit_and_phone_no_check(self):
        result = self.model.check_duplicate_customer({'cuit': '', 'phone': ''})
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
