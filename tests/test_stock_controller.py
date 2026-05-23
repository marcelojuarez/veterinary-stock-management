import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import MagicMock
from controllers.stock_controller import StockController


def _make_ctrl():
    ctrl = StockController.__new__(StockController)
    ctrl.stock_model = MagicMock()
    ctrl.supplier_model = MagicMock()
    ctrl.payment_model = MagicMock()
    ctrl.event_bus = MagicMock()
    ctrl.view = MagicMock()
    ctrl.all_products = []
    return ctrl


class TestUpdateProductField(unittest.TestCase):

    def setUp(self):
        self.ctrl = _make_ctrl()

    def test_name_field_mapped_and_uppercased(self):
        result = self.ctrl.update_product_field(1, 'Name', 'ivermectina')
        self.assertTrue(result)
        self.ctrl.stock_model.update_field.assert_called_once_with('name', 'IVERMECTINA', 1)

    def test_package_field_mapped_and_uppercased(self):
        result = self.ctrl.update_product_field(1, 'Package', '500ml')
        self.assertTrue(result)
        self.ctrl.stock_model.update_field.assert_called_once_with('pack', '500ML', 1)

    def test_unknown_field_returns_false(self):
        result = self.ctrl.update_product_field(1, 'Price', '999')
        self.assertFalse(result)
        self.ctrl.stock_model.update_field.assert_not_called()

    def test_empty_field_returns_false(self):
        result = self.ctrl.update_product_field(1, '', 'value')
        self.assertFalse(result)
        self.ctrl.stock_model.update_field.assert_not_called()

    def test_value_is_uppercased_before_saving(self):
        self.ctrl.update_product_field(5, 'Name', 'producto')
        args = self.ctrl.stock_model.update_field.call_args[0]
        self.assertEqual(args[1], 'PRODUCTO')

    def test_correct_product_id_passed(self):
        self.ctrl.update_product_field(42, 'Name', 'Test')
        args = self.ctrl.stock_model.update_field.call_args[0]
        self.assertEqual(args[2], 42)


if __name__ == "__main__":
    unittest.main()
