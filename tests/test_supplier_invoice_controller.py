import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import patch, MagicMock
from controllers.supplier_invoice_controller import SupplierInvoiceController


# ─────────────────────────────────────────────────────────────────────────────
# is_valid_invoice_number
# ─────────────────────────────────────────────────────────────────────────────

class TestIsValidInvoiceNumber(unittest.TestCase):

    def test_digits_only(self):
        self.assertTrue(SupplierInvoiceController.is_valid_invoice_number("0001123456789"))

    def test_digits_with_internal_spaces_stripped(self):
        # spaces stripped in method before check
        self.assertTrue(SupplierInvoiceController.is_valid_invoice_number("0001 123456789"))

    def test_with_letters(self):
        self.assertFalse(SupplierInvoiceController.is_valid_invoice_number("A0001123456789"))

    def test_with_dashes(self):
        self.assertFalse(SupplierInvoiceController.is_valid_invoice_number("0001-123456789"))

    def test_empty_string(self):
        self.assertFalse(SupplierInvoiceController.is_valid_invoice_number(""))

    def test_single_digit(self):
        self.assertTrue(SupplierInvoiceController.is_valid_invoice_number("1"))


# ─────────────────────────────────────────────────────────────────────────────
# is_valid_date
# ─────────────────────────────────────────────────────────────────────────────

class TestIsValidDate(unittest.TestCase):

    def test_valid_date(self):
        self.assertTrue(SupplierInvoiceController.is_valid_date("15/06/2024"))

    def test_iso_format_invalid(self):
        self.assertFalse(SupplierInvoiceController.is_valid_date("2024-06-15"))

    def test_empty_string(self):
        self.assertFalse(SupplierInvoiceController.is_valid_date(""))

    def test_letters(self):
        self.assertFalse(SupplierInvoiceController.is_valid_date("ab/cd/efgh"))

    def test_end_of_year(self):
        self.assertTrue(SupplierInvoiceController.is_valid_date("31/12/2023"))


# ─────────────────────────────────────────────────────────────────────────────
# is_decimal
# ─────────────────────────────────────────────────────────────────────────────

class TestIsDecimal(unittest.TestCase):

    def test_integer_string(self):
        self.assertTrue(SupplierInvoiceController.is_decimal("100"))

    def test_decimal_with_dot(self):
        self.assertTrue(SupplierInvoiceController.is_decimal("100.50"))

    def test_decimal_with_comma(self):
        self.assertTrue(SupplierInvoiceController.is_decimal("100,50"))

    def test_zero(self):
        self.assertTrue(SupplierInvoiceController.is_decimal("0"))

    def test_letters(self):
        self.assertFalse(SupplierInvoiceController.is_decimal("abc"))

    def test_empty_string(self):
        self.assertFalse(SupplierInvoiceController.is_decimal(""))


# ─────────────────────────────────────────────────────────────────────────────
# validate_invoice_data
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateInvoiceData(unittest.TestCase):

    BASE = {
        'invoice_id':       '00011234567890',
        'invoice_type':     'A',
        'date':             '15/06/2024',
        'expiration_date':  '30/06/2024',
        's_iva_c':          'Responsable Inscripto',
        'subtotal':         '1000',
        'iva':              '210',
        'discount':         '0',
        'iibb_per':         '0',
        'iva_per':          '0',
        'total':            '1210',
    }

    def _call(self, **overrides):
        data = dict(self.BASE)
        data.update(overrides)
        with patch("controllers.supplier_invoice_controller.show_error"):
            return SupplierInvoiceController.validate_invoice_data(data)

    def test_valid_data(self):
        self.assertTrue(self._call())

    def test_missing_invoice_id(self):
        self.assertFalse(self._call(invoice_id=''))

    def test_missing_invoice_type(self):
        self.assertFalse(self._call(invoice_type=''))

    def test_missing_date(self):
        self.assertFalse(self._call(date=''))

    def test_invalid_invoice_number_with_letters(self):
        self.assertFalse(self._call(invoice_id='A0001-123456789'))

    def test_invalid_expiration_date_format(self):
        self.assertFalse(self._call(expiration_date='2024-06-30'))

    def test_non_decimal_iibb_per(self):
        self.assertFalse(self._call(iibb_per='abc'))

    def test_negative_iibb_per(self):
        self.assertFalse(self._call(iibb_per='-10'))

    def test_non_decimal_iva_per(self):
        self.assertFalse(self._call(iva_per='abc'))

    def test_negative_iva_per(self):
        self.assertFalse(self._call(iva_per='-5'))

    def test_non_decimal_discount(self):
        self.assertFalse(self._call(discount='abc'))

    def test_discount_over_99(self):
        self.assertFalse(self._call(discount='100'))

    def test_negative_discount(self):
        self.assertFalse(self._call(discount='-1'))

    def test_discount_99_is_valid(self):
        self.assertTrue(self._call(discount='99'))

    def test_zero_perceptions_valid(self):
        self.assertTrue(self._call(iibb_per='0', iva_per='0'))


if __name__ == "__main__":
    unittest.main()
