import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import patch
from controllers.supplier_receipt_controller import SupplierReceiptController


# ─────────────────────────────────────────────────────────────────────────────
# is_valid_date
# ─────────────────────────────────────────────────────────────────────────────

class TestIsValidDate(unittest.TestCase):

    def test_valid_date(self):
        self.assertTrue(SupplierReceiptController.is_valid_date("15/06/2024"))

    def test_iso_format_invalid(self):
        self.assertFalse(SupplierReceiptController.is_valid_date("2024-06-15"))

    def test_us_format_invalid(self):
        self.assertFalse(SupplierReceiptController.is_valid_date("06/15/2024"))

    def test_empty_string(self):
        self.assertFalse(SupplierReceiptController.is_valid_date(""))

    def test_letters(self):
        self.assertFalse(SupplierReceiptController.is_valid_date("ab/cd/efgh"))

    def test_first_of_month(self):
        self.assertTrue(SupplierReceiptController.is_valid_date("01/01/2024"))


# ─────────────────────────────────────────────────────────────────────────────
# validate_receipt_data
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateReceiptData(unittest.TestCase):

    BASE = {
        'receipt_id':      'R-001',
        'date':            '15/06/2024',
        'expiration_date': '30/06/2024',
        'total':           '5000',
    }

    def _call(self, **overrides):
        data = dict(self.BASE)
        data.update(overrides)
        with patch("controllers.supplier_receipt_controller.show_error"):
            return SupplierReceiptController.validate_receipt_data(data)

    def test_valid_data(self):
        self.assertTrue(self._call())

    def test_missing_receipt_id(self):
        self.assertFalse(self._call(receipt_id=''))

    def test_missing_date(self):
        self.assertFalse(self._call(date=''))

    def test_missing_expiration_date(self):
        self.assertFalse(self._call(expiration_date=''))

    def test_missing_total(self):
        self.assertFalse(self._call(total=''))

    def test_invalid_date_format(self):
        self.assertFalse(self._call(date='2024-06-15'))

    def test_invalid_expiration_format(self):
        self.assertFalse(self._call(expiration_date='2024-06-30'))


if __name__ == "__main__":
    unittest.main()
