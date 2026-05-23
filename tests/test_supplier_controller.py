import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import patch, MagicMock
from controllers.supplier_controller import SupplierController


def _make_ctrl():
    ctrl = SupplierController.__new__(SupplierController)
    ctrl.model = MagicMock()
    ctrl.view = None
    ctrl.info_view = None
    ctrl.event_bus = MagicMock()
    return ctrl


# ─────────────────────────────────────────────────────────────────────────────
# __validate_supplier_cuit
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateSupplierCuit(unittest.TestCase):

    def setUp(self):
        self.ctrl = _make_ctrl()

    def _call(self, cuit):
        with patch("controllers.supplier_controller.show_warning"):
            return self.ctrl._SupplierController__validate_supplier_cuit(cuit)

    def test_valid_cuit(self):
        self.assertTrue(self._call("20-12345678-1"))

    def test_valid_cuit_different_prefix(self):
        self.assertTrue(self._call("30-98765432-9"))

    def test_invalid_no_dashes(self):
        self.assertFalse(self._call("20123456781"))

    def test_invalid_wrong_segment_lengths(self):
        self.assertFalse(self._call("201-2345678-1"))

    def test_invalid_letters(self):
        self.assertFalse(self._call("AB-12345678-1"))

    def test_empty_string(self):
        self.assertFalse(self._call(""))


# ─────────────────────────────────────────────────────────────────────────────
# __validate_supplier_email
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateSupplierEmail(unittest.TestCase):

    def setUp(self):
        self.ctrl = _make_ctrl()

    def _call(self, email):
        with patch("controllers.supplier_controller.show_warning"):
            return self.ctrl._SupplierController__validate_supplier_email(email)

    def test_valid_email(self):
        self.assertTrue(self._call("proveedor@empresa.com"))

    def test_dash_is_valid(self):
        self.assertTrue(self._call("-"))

    def test_missing_at(self):
        self.assertFalse(self._call("proveedorempresa.com"))

    def test_missing_domain(self):
        self.assertFalse(self._call("proveedor@"))

    def test_empty_string(self):
        self.assertFalse(self._call(""))

    def test_spaces_only(self):
        self.assertFalse(self._call("   "))


# ─────────────────────────────────────────────────────────────────────────────
# __validate_supplier_phone
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateSupplierPhone(unittest.TestCase):

    def setUp(self):
        self.ctrl = _make_ctrl()

    def _call(self, phone):
        with patch("controllers.supplier_controller.show_warning"):
            return self.ctrl._SupplierController__validate_supplier_phone(phone)

    def test_valid_local_phone(self):
        self.assertTrue(self._call("3514001234"))

    def test_valid_with_plus(self):
        self.assertTrue(self._call("+543514001234"))

    def test_dash_is_valid(self):
        self.assertTrue(self._call("-"))

    def test_too_short(self):
        self.assertFalse(self._call("123456"))

    def test_with_letters(self):
        self.assertFalse(self._call("351abc0001"))

    def test_empty_string(self):
        self.assertFalse(self._call(""))


# ─────────────────────────────────────────────────────────────────────────────
# __validate_supplier_name
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateSupplierName(unittest.TestCase):

    def setUp(self):
        self.ctrl = _make_ctrl()

    def _call(self, name):
        with patch("controllers.supplier_controller.show_warning"):
            return self.ctrl._SupplierController__validate_supplier_name(name)

    def test_valid_name(self):
        self.assertTrue(self._call("Proveedor SA"))

    def test_single_char_invalid(self):
        self.assertFalse(self._call("A"))

    def test_exactly_2_chars_valid(self):
        self.assertTrue(self._call("AB"))

    def test_name_over_100_chars_invalid(self):
        self.assertFalse(self._call("A" * 101))

    def test_exactly_100_chars_valid(self):
        self.assertTrue(self._call("A" * 100))

    def test_empty_string_invalid(self):
        self.assertFalse(self._call(""))


# ─────────────────────────────────────────────────────────────────────────────
# __validate_supplier_address
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateSupplierAddress(unittest.TestCase):

    def setUp(self):
        self.ctrl = _make_ctrl()

    def _call(self, address):
        with patch("controllers.supplier_controller.show_warning"):
            return self.ctrl._SupplierController__validate_supplier_address(address)

    def test_valid_address(self):
        self.assertTrue(self._call("Av. Corrientes 1234"))

    def test_dash_is_valid(self):
        self.assertTrue(self._call("-"))

    def test_too_short(self):
        self.assertFalse(self._call("AB"))

    def test_exactly_5_chars_valid(self):
        self.assertTrue(self._call("Calle"))

    def test_over_150_chars_invalid(self):
        self.assertFalse(self._call("A" * 151))

    def test_exactly_150_chars_valid(self):
        self.assertTrue(self._call("A" * 150))


# ─────────────────────────────────────────────────────────────────────────────
# validate_existing_address
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateExistingAddress(unittest.TestCase):

    def setUp(self):
        self.ctrl = _make_ctrl()

    def test_address_not_found_returns_true(self):
        self.ctrl.model.core.find_supplier_by_address.return_value = None
        with patch("controllers.supplier_controller.show_warning"):
            result = self.ctrl.validate_existing_address(None, "Av. Siempre Viva 742", "Springfield")
        self.assertTrue(result)

    def test_same_supplier_editing_returns_true(self):
        existing = (5, "20-12345678-1", "Proveedor SA")
        self.ctrl.model.core.find_supplier_by_address.return_value = existing
        with patch("controllers.supplier_controller.show_warning"):
            result = self.ctrl.validate_existing_address(5, "Av. Siempre Viva 742", "Springfield")
        self.assertTrue(result)

    def test_different_supplier_same_address_returns_false(self):
        existing = (7, "20-12345678-1", "Otro Proveedor")
        self.ctrl.model.core.find_supplier_by_address.return_value = existing
        with patch("controllers.supplier_controller.show_warning"):
            result = self.ctrl.validate_existing_address(5, "Av. Siempre Viva 742", "Springfield")
        self.assertFalse(result)

    def test_new_supplier_duplicate_address_returns_false(self):
        existing = (7, "20-12345678-1", "Otro Proveedor")
        self.ctrl.model.core.find_supplier_by_address.return_value = existing
        with patch("controllers.supplier_controller.show_warning"):
            result = self.ctrl.validate_existing_address(None, "Av. Siempre Viva 742", "Springfield")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
