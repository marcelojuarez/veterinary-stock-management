import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from decimal import Decimal
from unittest.mock import patch
from controllers.payment_controller import PaymentController


class TestIsDecimal(unittest.TestCase):
    """PaymentController._is_decimal — wraps string_to_2_dec."""

    def test_valid_decimal(self):
        self.assertTrue(PaymentController._is_decimal("10.50"))

    def test_valid_decimal_with_comma(self):
        self.assertTrue(PaymentController._is_decimal("10,50"))

    def test_zero(self):
        self.assertTrue(PaymentController._is_decimal("0"))

    def test_empty_string(self):
        self.assertFalse(PaymentController._is_decimal(""))

    def test_letters(self):
        self.assertFalse(PaymentController._is_decimal("abc"))

    def test_letters_mixed(self):
        self.assertFalse(PaymentController._is_decimal("12abc"))

    def test_large_value(self):
        self.assertTrue(PaymentController._is_decimal("999999.99"))


class TestIsStr(unittest.TestCase):
    """PaymentController._is_str — must be non-empty string after strip."""

    def test_valid_string(self):
        self.assertTrue(PaymentController._is_str("Banco Nacion"))

    def test_empty_string(self):
        self.assertFalse(PaymentController._is_str(""))

    def test_only_spaces(self):
        self.assertFalse(PaymentController._is_str("   "))

    def test_integer_not_a_string(self):
        self.assertFalse(PaymentController._is_str(123))

    def test_none_not_a_string(self):
        self.assertFalse(PaymentController._is_str(None))

    def test_single_char(self):
        self.assertTrue(PaymentController._is_str("X"))


class TestIsInt(unittest.TestCase):
    """PaymentController._is_int."""

    def test_integer_string(self):
        self.assertTrue(PaymentController._is_int("5"))

    def test_zero(self):
        self.assertTrue(PaymentController._is_int("0"))

    def test_float_string(self):
        self.assertFalse(PaymentController._is_int("5.5"))

    def test_letters(self):
        self.assertFalse(PaymentController._is_int("abc"))

    def test_empty(self):
        self.assertFalse(PaymentController._is_int(""))


class TestValidateDebt(unittest.TestCase):
    """PaymentController.validate_debt — show_warning mocked so no tkinter needed."""

    def _make_controller(self):
        ctrl = PaymentController.__new__(PaymentController)
        return ctrl

    def test_amount_equal_to_debt_ok(self):
        ctrl = self._make_controller()
        self.assertTrue(ctrl.validate_debt(Decimal("500.00"), Decimal("500.00"), False))

    def test_amount_less_than_debt_ok(self):
        ctrl = self._make_controller()
        self.assertTrue(ctrl.validate_debt(Decimal("300.00"), Decimal("500.00"), False))

    def test_amount_greater_than_debt_returns_false(self):
        ctrl = self._make_controller()
        with patch("controllers.payment_controller.show_warning") as mock_warn:
            result = ctrl.validate_debt(Decimal("600.00"), Decimal("500.00"), False)
        self.assertFalse(result)
        mock_warn.assert_called_once()

    def test_warning_message_uses_total_prefix_when_total_debt(self):
        ctrl = self._make_controller()
        with patch("controllers.payment_controller.show_warning") as mock_warn:
            ctrl.validate_debt(Decimal("999.00"), Decimal("500.00"), total_debt=True)
        call_args = mock_warn.call_args[0][0]
        self.assertIn("deuda Total", call_args)

    def test_warning_message_uses_compra_prefix_when_not_total_debt(self):
        ctrl = self._make_controller()
        with patch("controllers.payment_controller.show_warning") as mock_warn:
            ctrl.validate_debt(Decimal("999.00"), Decimal("500.00"), total_debt=False)
        call_args = mock_warn.call_args[0][0]
        self.assertIn("compra", call_args)


class TestValidateData(unittest.TestCase):
    """
    PaymentController.validate_data — static method, show_warning/show_error mocked.
    Tests the field-presence and type validations for supplier payments.
    """

    BASE_DATA = {
        'amount':         "500.00",
        'method':         "EFECTIVO",
        'receipt_number': "R-001",
        'observation':    "",
        'operation_num':  "",
        'origin':         "",
        'destination':    "",
        'check_number':   "",
        'bank':           "",
    }

    def _valid_data(self, **overrides):
        data = dict(self.BASE_DATA)
        data.update(overrides)
        return data

    def test_valid_efectivo_passes(self):
        with patch("controllers.payment_controller.show_warning"), \
             patch("controllers.payment_controller.show_error"):
            self.assertTrue(PaymentController.validate_data(self._valid_data()))

    def test_missing_amount_fails(self):
        with patch("controllers.payment_controller.show_warning") as mock_warn:
            result = PaymentController.validate_data(self._valid_data(amount=""))
        self.assertFalse(result)
        mock_warn.assert_called_once()

    def test_missing_method_fails(self):
        with patch("controllers.payment_controller.show_warning") as mock_warn:
            result = PaymentController.validate_data(self._valid_data(method=""))
        self.assertFalse(result)
        mock_warn.assert_called_once()

    def test_missing_receipt_number_fails(self):
        with patch("controllers.payment_controller.show_warning") as mock_warn:
            result = PaymentController.validate_data(self._valid_data(receipt_number=""))
        self.assertFalse(result)
        mock_warn.assert_called_once()

    def test_non_numeric_amount_fails(self):
        with patch("controllers.payment_controller.show_error") as mock_err:
            result = PaymentController.validate_data(self._valid_data(amount="abc"))
        self.assertFalse(result)
        mock_err.assert_called_once()

    def test_zero_amount_fails(self):
        with patch("controllers.payment_controller.show_error") as mock_err:
            result = PaymentController.validate_data(self._valid_data(amount="0"))
        self.assertFalse(result)
        mock_err.assert_called_once()

    def test_negative_amount_fails(self):
        with patch("controllers.payment_controller.show_error"):
            result = PaymentController.validate_data(self._valid_data(amount="-100"))
        self.assertFalse(result)

    def test_transferencia_requires_operation_num(self):
        with patch("controllers.payment_controller.show_warning") as mock_warn:
            result = PaymentController.validate_data(self._valid_data(
                method="TRANSFERENCIA",
                operation_num="",
                origin="CBU123",
                destination="CBU456"
            ))
        self.assertFalse(result)
        mock_warn.assert_called_once()

    def test_transferencia_complete_passes(self):
        with patch("controllers.payment_controller.show_warning"), \
             patch("controllers.payment_controller.show_error"):
            result = PaymentController.validate_data(self._valid_data(
                method="TRANSFERENCIA",
                operation_num="OP-001",
                origin="CBU123",
                destination="CBU456"
            ))
        self.assertTrue(result)

    def test_cheque_requires_number_and_bank(self):
        with patch("controllers.payment_controller.show_warning") as mock_warn:
            result = PaymentController.validate_data(self._valid_data(
                method="CHEQUE",
                check_number="",
                bank="Nacion"
            ))
        self.assertFalse(result)
        mock_warn.assert_called_once()

    def test_cheque_complete_passes(self):
        with patch("controllers.payment_controller.show_warning"), \
             patch("controllers.payment_controller.show_error"):
            result = PaymentController.validate_data(self._valid_data(
                method="CHEQUE",
                check_number="1234",
                bank="Galicia"
            ))
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
