import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import tempfile
from decimal import Decimal
from db.database import Database
from models.customer_credit import CustomerCredit


def make_test_db():
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp.close()
    db = Database(tmp.name)
    return db, tmp.name


def _make_credit_model(db):
    model = CustomerCredit.__new__(CustomerCredit)
    model.db = db
    return model


def _insert_customer(db, cid=1):
    db.execute_query(
        "INSERT INTO customer (id, name, cuit, home, iva_condition) VALUES (?, 'TEST', NULL, 'CITY', 'CF')",
        (cid,)
    )


def _add_credit(db, client_id, amount, used="0.00", valid=1, sale_id=None, check_id=None):
    db.execute_query(
        "INSERT INTO customer_credit (client_id, amount, used, reason, sale_id, check_id, valid) "
        "VALUES (?, ?, ?, 'TEST', ?, ?, ?)",
        (client_id, str(amount), str(used), sale_id, check_id, valid)
    )


class TestGetCustomerCredit(unittest.TestCase):

    def setUp(self):
        self.db, self.db_path = make_test_db()
        _insert_customer(self.db)
        self.model = _make_credit_model(self.db)

    def tearDown(self):
        os.unlink(self.db_path)

    def test_no_credit_returns_zero(self):
        self.assertEqual(self.model.get_customer_credit(1), Decimal("0.00"))

    def test_single_full_credit(self):
        _add_credit(self.db, 1, "500.00")
        self.assertEqual(self.model.get_customer_credit(1), Decimal("500.00"))

    def test_partially_used_credit(self):
        _add_credit(self.db, 1, "500.00", used="200.00")
        self.assertEqual(self.model.get_customer_credit(1), Decimal("300.00"))

    def test_fully_used_credit_excluded(self):
        # valid=0 means fully consumed
        _add_credit(self.db, 1, "500.00", used="500.00", valid=0)
        self.assertEqual(self.model.get_customer_credit(1), Decimal("0.00"))

    def test_invalid_credit_row_excluded(self):
        _add_credit(self.db, 1, "300.00", valid=1)
        _add_credit(self.db, 1, "200.00", valid=0)
        self.assertEqual(self.model.get_customer_credit(1), Decimal("300.00"))

    def test_multiple_credits_summed(self):
        _add_credit(self.db, 1, "100.00")
        _add_credit(self.db, 1, "200.00")
        _add_credit(self.db, 1, "50.00", used="20.00")
        self.assertEqual(self.model.get_customer_credit(1), Decimal("330.00"))

    def test_different_clients_not_mixed(self):
        _insert_customer(self.db, cid=2)
        _add_credit(self.db, 1, "500.00")
        _add_credit(self.db, 2, "999.00")
        self.assertEqual(self.model.get_customer_credit(1), Decimal("500.00"))
        self.assertEqual(self.model.get_customer_credit(2), Decimal("999.00"))

    def test_no_credit_client_not_found(self):
        self.assertEqual(self.model.get_customer_credit(9999), Decimal("0.00"))


class TestUpdateCreditUsed(unittest.TestCase):

    def setUp(self):
        self.db, self.db_path = make_test_db()
        _insert_customer(self.db)
        self.model = _make_credit_model(self.db)

    def tearDown(self):
        os.unlink(self.db_path)

    def _get_row(self, credit_id):
        return self.db.fetch_one(
            "SELECT amount, used, valid FROM customer_credit WHERE id = ?", (credit_id,)
        )

    def test_partial_use_keeps_valid(self):
        _add_credit(self.db, 1, "500.00")
        credit_id = self.db.fetch_one("SELECT id FROM customer_credit WHERE client_id = 1")[0]
        self.model.update_credit_used(credit_id, "500.00", "200.00")
        row = self._get_row(credit_id)
        self.assertEqual(row[1], "200.00")
        self.assertEqual(row[2], 1)  # still valid

    def test_full_use_sets_invalid(self):
        _add_credit(self.db, 1, "500.00")
        credit_id = self.db.fetch_one("SELECT id FROM customer_credit WHERE client_id = 1")[0]
        self.model.update_credit_used(credit_id, "500.00", "500.00")
        row = self._get_row(credit_id)
        self.assertEqual(row[2], 0)  # no longer valid

    def test_overage_also_sets_invalid(self):
        # used > amount should still mark as invalid
        _add_credit(self.db, 1, "300.00")
        credit_id = self.db.fetch_one("SELECT id FROM customer_credit WHERE client_id = 1")[0]
        self.model.update_credit_used(credit_id, "300.00", "300.01")
        row = self._get_row(credit_id)
        self.assertEqual(row[2], 0)


class TestAddCustomerCredit(unittest.TestCase):

    def setUp(self):
        self.db, self.db_path = make_test_db()
        _insert_customer(self.db)
        self.model = _make_credit_model(self.db)

    def tearDown(self):
        os.unlink(self.db_path)

    def test_adds_row_with_correct_values(self):
        self.model.add_customer_credit({
            'client_id': 1,
            'amount': Decimal("250.00"),
            'reason': 'Sobrepago venta #5',
            'sale_id': None  # no FK dependency needed for this assertion
        })
        row = self.db.fetch_one(
            "SELECT client_id, amount, used, valid FROM customer_credit WHERE client_id = 1"
        )
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 1)
        self.assertEqual(Decimal(row[1]), Decimal("250.00"))
        self.assertEqual(row[2], "0.00")
        self.assertEqual(row[3], 1)

    def test_credit_visible_in_get_customer_credit(self):
        self.model.add_customer_credit({
            'client_id': 1,
            'amount': Decimal("100.00"),
            'reason': 'Test',
            'sale_id': None
        })
        self.assertEqual(self.model.get_customer_credit(1), Decimal("100.00"))


if __name__ == "__main__":
    unittest.main()
