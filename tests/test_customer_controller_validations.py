import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import patch, MagicMock
from controllers.customer_controller import CustomerController


def _make_ctrl():
    ctrl = CustomerController.__new__(CustomerController)
    ctrl.view = None
    ctrl.model = MagicMock()
    ctrl.payment_model = MagicMock()
    ctrl.customer_credit = MagicMock()
    ctrl.event_bus = MagicMock()
    ctrl.checks_model = None
    ctrl.all_customers = []
    ctrl.pending_price_changes = []
    return ctrl


class TestValidateCustomerData(unittest.TestCase):

    def setUp(self):
        self.ctrl = _make_ctrl()

    def _call(self, **overrides):
        base = {'name': 'Juan', 'cuit': '20-12345678-1', 'home': 'Calle 1', 'phone': '3514001234'}
        base.update(overrides)
        with patch("controllers.customer_controller.show_warning"):
            return self.ctrl._CustomerController__validate_customer_data(base)

    def test_all_fields_present_returns_true(self):
        self.assertTrue(self._call())

    def test_missing_name_returns_false(self):
        self.assertFalse(self._call(name=''))

    def test_missing_cuit_returns_true(self):
        self.assertTrue(self._call(cuit=''))

    def test_missing_home_returns_false(self):
        self.assertFalse(self._call(home=''))

    def test_missing_phone_returns_true(self):
        self.assertTrue(self._call(phone=''))


class TestCustomerCuitValidation(unittest.TestCase):

    def setUp(self):
        self.ctrl = _make_ctrl()

    def _call(self, cuit):
        with patch("controllers.customer_controller.show_warning"):
            return self.ctrl._CustomerController__validate_supplier_cuit(cuit)

    def test_valid_cuit(self):
        self.assertTrue(self._call("20-12345678-1"))

    def test_invalid_no_dashes(self):
        self.assertFalse(self._call("20123456781"))

    def test_invalid_wrong_format(self):
        self.assertFalse(self._call("201-2345678-1"))

    def test_empty_string(self):
        self.assertFalse(self._call(""))


class TestCustomerPhoneValidation(unittest.TestCase):

    def setUp(self):
        self.ctrl = _make_ctrl()

    def _call(self, phone):
        with patch("controllers.customer_controller.show_warning"):
            return self.ctrl._CustomerController__validate_supplier_phone(phone)

    def test_valid_local_number(self):
        self.assertTrue(self._call("3514001234"))

    def test_valid_international(self):
        self.assertTrue(self._call("+543514001234"))

    def test_too_short(self):
        self.assertFalse(self._call("123"))

    def test_with_letters(self):
        self.assertFalse(self._call("351abc4001"))


class TestCustomerCVValidation(unittest.TestCase):

    def setUp(self):
        self.ctrl = _make_ctrl()

    def _call(self, cv):
        with patch("controllers.customer_controller.show_error"):
            return self.ctrl._CustomerController__validate_cv(cv)

    def test_empty_is_valid(self):
        self.assertTrue(self._call(""))

    def test_only_spaces_is_valid(self):
        self.assertTrue(self._call("   "))

    def test_valid_digits(self):
        self.assertTrue(self._call("1234"))

    def test_too_short(self):
        self.assertFalse(self._call("1"))

    def test_too_long(self):
        self.assertFalse(self._call("123456789"))

    def test_with_letters(self):
        self.assertFalse(self._call("12AB"))


class TestCustomerCUIGValidation(unittest.TestCase):

    def setUp(self):
        self.ctrl = _make_ctrl()

    def _call(self, cuig):
        with patch("controllers.customer_controller.show_error"):
            return self.ctrl._CustomerController__validate_cuig(cuig)

    def test_empty_is_valid(self):
        self.assertTrue(self._call(""))

    def test_valid_cuig(self):
        self.assertTrue(self._call("AB1234"))

    def test_valid_with_spaces_and_dashes(self):
        self.assertTrue(self._call("AB-12 34"))

    def test_invalid_no_letters_prefix(self):
        self.assertFalse(self._call("121234"))

    def test_invalid_too_short_digits(self):
        self.assertFalse(self._call("AB1"))


class TestCustomerRENSPAValidation(unittest.TestCase):

    def setUp(self):
        self.ctrl = _make_ctrl()

    def _call(self, renspa):
        with patch("controllers.customer_controller.show_error"):
            return self.ctrl._CustomerController__validate_renspa(renspa)

    def test_empty_is_valid(self):
        self.assertTrue(self._call(""))

    def test_valid_digits(self):
        self.assertTrue(self._call("123456789012"))

    def test_valid_with_dashes_and_slashes(self):
        self.assertTrue(self._call("12-3456/789012"))

    def test_too_short(self):
        self.assertFalse(self._call("12345"))

    def test_with_letters(self):
        self.assertFalse(self._call("12345678901A"))


if __name__ == "__main__":
    unittest.main()
