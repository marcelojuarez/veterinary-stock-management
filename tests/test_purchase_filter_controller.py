import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import patch, MagicMock
from controllers.purchase_filter_controller import PurchaseFilterController


def _make_ctrl():
    ctrl = PurchaseFilterController.__new__(PurchaseFilterController)
    ctrl.model = MagicMock()
    ctrl.supplier_id_var = MagicMock()
    ctrl.search_var = MagicMock()
    ctrl.treeview = MagicMock()
    return ctrl


class TestValidateDate(unittest.TestCase):

    def setUp(self):
        self.ctrl = _make_ctrl()

    def test_valid_date(self):
        self.assertTrue(self.ctrl.validate_date("15/06/2024"))

    def test_invalid_iso_format(self):
        self.assertFalse(self.ctrl.validate_date("2024-06-15"))

    def test_invalid_us_format(self):
        self.assertFalse(self.ctrl.validate_date("06/15/2024"))

    def test_empty_string(self):
        self.assertFalse(self.ctrl.validate_date(""))

    def test_letters(self):
        self.assertFalse(self.ctrl.validate_date("ab/cd/efgh"))

    def test_valid_date_end_of_year(self):
        self.assertTrue(self.ctrl.validate_date("31/12/2023"))

    def test_single_digit_day_month(self):
        self.assertTrue(self.ctrl.validate_date("01/01/2024"))


class TestValidateInvoiceNumber(unittest.TestCase):

    def setUp(self):
        self.ctrl = _make_ctrl()

    def _call(self, number):
        with patch("controllers.purchase_filter_controller.show_error"):
            return self.ctrl.validate_invoice_number(number)

    def test_digits_only(self):
        self.assertTrue(self._call("123456789"))

    def test_empty_string(self):
        self.assertFalse(self._call(""))

    def test_with_letters(self):
        self.assertFalse(self._call("123abc"))

    def test_with_dashes(self):
        self.assertFalse(self._call("12-34"))

    def test_single_digit(self):
        self.assertTrue(self._call("1"))

    def test_long_number(self):
        self.assertTrue(self._call("00011234567890"))


if __name__ == "__main__":
    unittest.main()
