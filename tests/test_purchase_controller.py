import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import patch, MagicMock
from controllers.purchase_controller import PurchaseController


def _make_ctrl():
    ctrl = PurchaseController.__new__(PurchaseController)
    ctrl.supplier_model = MagicMock()
    ctrl.stock_model = MagicMock()
    ctrl.view = None
    return ctrl


# ─────────────────────────────────────────────────────────────────────────────
# is_valid_date
# ─────────────────────────────────────────────────────────────────────────────

class TestIsValidDate(unittest.TestCase):

    def test_valid_date(self):
        self.assertTrue(PurchaseController.is_valid_date("15/06/2024"))

    def test_invalid_format_iso(self):
        self.assertFalse(PurchaseController.is_valid_date("2024-06-15"))

    def test_invalid_format_us(self):
        self.assertFalse(PurchaseController.is_valid_date("06/15/2024"))

    def test_empty_string(self):
        self.assertFalse(PurchaseController.is_valid_date(""))

    def test_letters(self):
        self.assertFalse(PurchaseController.is_valid_date("ab/cd/efgh"))

    def test_valid_end_of_month(self):
        self.assertTrue(PurchaseController.is_valid_date("31/12/2023"))


# ─────────────────────────────────────────────────────────────────────────────
# is_int
# ─────────────────────────────────────────────────────────────────────────────

class TestIsInt(unittest.TestCase):

    def test_integer_string(self):
        self.assertTrue(PurchaseController.is_int("10"))

    def test_zero(self):
        self.assertTrue(PurchaseController.is_int("0"))

    def test_float_string(self):
        self.assertFalse(PurchaseController.is_int("10.5"))

    def test_letters(self):
        self.assertFalse(PurchaseController.is_int("abc"))

    def test_empty(self):
        self.assertFalse(PurchaseController.is_int(""))


# ─────────────────────────────────────────────────────────────────────────────
# validate_doc_data
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateDocData(unittest.TestCase):

    REMITO_BASE = {
        'receipt_id': 'R-001',
        'date': '15/06/2024',
        'expiration': '30/06/2024',
        'obs': 'Ninguna',
    }

    FACTURA_BASE = {
        'invoice_id': 'F-001',
        'date': '15/06/2024',
        'expiration': '30/06/2024',
        'pay_cond': 'CONTADO',
        'pay_period': '30',
    }

    def setUp(self):
        self.ctrl = _make_ctrl()

    def _call_remito(self, **overrides):
        data = dict(self.REMITO_BASE)
        data.update(overrides)
        with patch("controllers.purchase_controller.show_error"):
            return self.ctrl.validate_doc_data(data, 'REMITO')

    def _call_factura(self, **overrides):
        data = dict(self.FACTURA_BASE)
        data.update(overrides)
        with patch("controllers.purchase_controller.show_error"):
            return self.ctrl.validate_doc_data(data, 'FACTURA')

    def test_valid_remito(self):
        self.assertTrue(self._call_remito())

    def test_valid_factura(self):
        self.assertTrue(self._call_factura())

    def test_remito_missing_receipt_id(self):
        self.assertFalse(self._call_remito(receipt_id=''))

    def test_remito_missing_date(self):
        self.assertFalse(self._call_remito(date=''))

    def test_remito_invalid_date_format(self):
        self.assertFalse(self._call_remito(date='2024-06-15'))

    def test_remito_invalid_expiration_format(self):
        self.assertFalse(self._call_remito(expiration='2024-06-30'))

    def test_factura_missing_invoice_id(self):
        self.assertFalse(self._call_factura(invoice_id=''))

    def test_factura_missing_pay_cond(self):
        self.assertFalse(self._call_factura(pay_cond=''))

    def test_factura_invalid_date(self):
        self.assertFalse(self._call_factura(date='15-06-2024'))


# ─────────────────────────────────────────────────────────────────────────────
# validate_new_product_data
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateNewProductData(unittest.TestCase):

    BASE = {
        'Name': 'Ivermectina',
        'Package': '500ml',
        'ListPrice': '1500',
        'Profit': '20',
        'Stock': '10',
    }

    def setUp(self):
        self.ctrl = _make_ctrl()

    def _call(self, **overrides):
        data = dict(self.BASE)
        data.update(overrides)
        with patch("controllers.purchase_controller.show_warning"), \
             patch("controllers.purchase_controller.show_error"):
            return self.ctrl.validate_new_product_data(data)

    def test_valid_data(self):
        self.assertTrue(self._call())

    def test_missing_name(self):
        self.assertFalse(self._call(Name=''))

    def test_missing_package(self):
        self.assertFalse(self._call(Package=''))

    def test_missing_list_price(self):
        self.assertFalse(self._call(ListPrice=''))

    def test_non_numeric_price(self):
        self.assertFalse(self._call(ListPrice='abc'))

    def test_zero_price(self):
        self.assertFalse(self._call(ListPrice='0'))

    def test_negative_price(self):
        self.assertFalse(self._call(ListPrice='-100'))

    def test_non_numeric_profit(self):
        self.assertFalse(self._call(Profit='abc'))

    def test_negative_profit(self):
        self.assertFalse(self._call(Profit='-5'))

    def test_zero_profit_is_valid(self):
        self.assertTrue(self._call(Profit='0'))


# ─────────────────────────────────────────────────────────────────────────────
# validate_purchase_item_data
# ─────────────────────────────────────────────────────────────────────────────

class TestValidatePurchaseItemData(unittest.TestCase):

    BASE = {
        'Purchase_id': '1',
        'Product_id': '5',
        'Product_name': 'Ivermectina',
        'Pack': '500ml',
        'Qty': '10',
        'List_price': '1500',
        'Discount': '0',
        'Cost_price': '1200',
        'Iva_rate': '21',
        'Discount_amount': '0',
        'Subtotal': '12000',
        'Iva_amount': '2520',
        'Total': '14520',
    }

    def setUp(self):
        self.ctrl = _make_ctrl()

    def _call(self, **overrides):
        data = dict(self.BASE)
        data.update(overrides)
        with patch("controllers.purchase_controller.show_warning"), \
             patch("controllers.purchase_controller.show_error"):
            return self.ctrl.validate_purchase_item_data(data)

    def test_valid_data(self):
        self.assertTrue(self._call())

    def test_missing_product_name(self):
        self.assertFalse(self._call(Product_name=''))

    def test_non_integer_qty(self):
        self.assertFalse(self._call(Qty='10.5'))

    def test_zero_qty(self):
        self.assertFalse(self._call(Qty='0'))

    def test_negative_qty(self):
        self.assertFalse(self._call(Qty='-1'))

    def test_non_numeric_cost_price(self):
        self.assertFalse(self._call(Cost_price='abc'))

    def test_zero_cost_price(self):
        self.assertFalse(self._call(Cost_price='0'))

    def test_negative_cost_price(self):
        self.assertFalse(self._call(Cost_price='-100'))

    def test_discount_over_99(self):
        self.assertFalse(self._call(Discount='100'))

    def test_negative_discount(self):
        self.assertFalse(self._call(Discount='-1'))

    def test_discount_zero_is_valid(self):
        self.assertTrue(self._call(Discount='0'))

    def test_discount_99_is_valid(self):
        self.assertTrue(self._call(Discount='99'))

    def test_non_numeric_discount(self):
        self.assertFalse(self._call(Discount='abc'))


if __name__ == "__main__":
    unittest.main()
