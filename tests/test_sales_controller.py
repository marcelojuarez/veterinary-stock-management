import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from decimal import Decimal
from unittest.mock import MagicMock
from controllers.sales_controller import SalesController


def _make_ctrl(items=None, fraction_model=None):
    ctrl = SalesController.__new__(SalesController)
    ctrl.sales_view = MagicMock()
    ctrl.sales_view.items_in_sale = items if items is not None else []
    ctrl.customer_model = MagicMock()
    ctrl.remito_model = MagicMock()
    ctrl.sales_model = MagicMock()
    ctrl.stock_model = MagicMock()
    ctrl.invoice_controller = MagicMock()
    ctrl.event_bus = MagicMock()
    ctrl.fraction_model = fraction_model
    return ctrl


# ─────────────────────────────────────────────────────────────────────────────
# _unpack_qty_price — static helper
# ─────────────────────────────────────────────────────────────────────────────

class TestUnpackQtyPrice(unittest.TestCase):

    def test_normal_item_len5(self):
        item = (1, "Prod", "500ml", 3, Decimal("100"))
        qty, price = SalesController._unpack_qty_price(item)
        self.assertEqual(qty, 3)
        self.assertEqual(price, Decimal("100"))

    def test_honorario_len6(self):
        item = (1, "Honorarios", "N/A", 1, Decimal("500"), "Consulta")
        qty, price = SalesController._unpack_qty_price(item)
        self.assertEqual(qty, 1)
        self.assertEqual(price, Decimal("500"))

    def test_fractional_len7(self):
        item = (1, "Prod", "KG", Decimal("2.5"), Decimal("200"), "FRAC. 2.5 KG", True)
        qty, price = SalesController._unpack_qty_price(item)
        self.assertEqual(qty, Decimal("2.5"))
        self.assertEqual(price, Decimal("200"))


# ─────────────────────────────────────────────────────────────────────────────
# add_product_to_sale — normal products
# ─────────────────────────────────────────────────────────────────────────────

class TestAddProductNormal(unittest.TestCase):

    def test_adds_new_product(self):
        ctrl = _make_ctrl()
        result = ctrl.add_product_to_sale(1, "Prod", "500ml", Decimal("100"), stock=10, qty_input="3")
        self.assertTrue(result)
        self.assertEqual(len(ctrl.sales_view.items_in_sale), 1)
        self.assertEqual(ctrl.sales_view.items_in_sale[0][3], 3)

    def test_accumulates_existing_product(self):
        existing = [(1, "Prod", "500ml", 2, Decimal("100"))]
        ctrl = _make_ctrl(items=existing)
        result = ctrl.add_product_to_sale(1, "Prod", "500ml", Decimal("100"), stock=10, qty_input="3")
        self.assertTrue(result)
        self.assertEqual(len(ctrl.sales_view.items_in_sale), 1)
        self.assertEqual(ctrl.sales_view.items_in_sale[0][3], 5)

    def test_insufficient_stock_returns_false(self):
        ctrl = _make_ctrl()
        result = ctrl.add_product_to_sale(1, "Prod", "500ml", Decimal("100"), stock=2, qty_input="5")
        self.assertFalse(result)
        ctrl.sales_view.show_warning.assert_called_once()

    def test_accumulate_exceeds_stock_returns_false(self):
        existing = [(1, "Prod", "500ml", 8, Decimal("100"))]
        ctrl = _make_ctrl(items=existing)
        result = ctrl.add_product_to_sale(1, "Prod", "500ml", Decimal("100"), stock=10, qty_input="5")
        self.assertFalse(result)
        ctrl.sales_view.show_warning.assert_called_once()

    def test_zero_quantity_returns_false(self):
        ctrl = _make_ctrl()
        result = ctrl.add_product_to_sale(1, "Prod", "500ml", Decimal("100"), stock=10, qty_input="0")
        self.assertFalse(result)

    def test_negative_quantity_returns_false(self):
        ctrl = _make_ctrl()
        result = ctrl.add_product_to_sale(1, "Prod", "500ml", Decimal("100"), stock=10, qty_input="-1")
        self.assertFalse(result)

    def test_non_numeric_quantity_returns_false(self):
        ctrl = _make_ctrl()
        result = ctrl.add_product_to_sale(1, "Prod", "500ml", Decimal("100"), stock=10, qty_input="abc")
        self.assertFalse(result)
        ctrl.sales_view.show_error.assert_called_once()

    def test_different_product_adds_new_line(self):
        existing = [(1, "Prod A", "500ml", 2, Decimal("100"))]
        ctrl = _make_ctrl(items=existing)
        result = ctrl.add_product_to_sale(2, "Prod B", "1L", Decimal("200"), stock=5, qty_input="1")
        self.assertTrue(result)
        self.assertEqual(len(ctrl.sales_view.items_in_sale), 2)


# ─────────────────────────────────────────────────────────────────────────────
# add_product_to_sale — fractional products
# ─────────────────────────────────────────────────────────────────────────────

class TestAddProductFractional(unittest.TestCase):

    def _make_fraction_model(self, has_stock=True, total_units=10):
        fm = MagicMock()
        fm.has_enough_stock.return_value = has_stock
        fm.get_available_stock_info.return_value = {'total_units': total_units}
        return fm

    def test_fractional_adds_item_with_label(self):
        fm = self._make_fraction_model(has_stock=True)
        ctrl = _make_ctrl(fraction_model=fm)
        result = ctrl.add_product_to_sale(
            1, "Prod", "KG", Decimal("50"), stock=0,
            qty_input="2.5", is_fractional=True, unit="KG"
        )
        self.assertTrue(result)
        item = ctrl.sales_view.items_in_sale[0]
        self.assertEqual(len(item), 7)
        self.assertTrue(item[6])
        self.assertIn("FRAC.", item[5])
        self.assertIn("KG", item[5])

    def test_fractional_insufficient_stock_returns_false(self):
        fm = self._make_fraction_model(has_stock=False)
        ctrl = _make_ctrl(fraction_model=fm)
        result = ctrl.add_product_to_sale(
            1, "Prod", "KG", Decimal("50"), stock=0,
            qty_input="5", is_fractional=True, unit="KG"
        )
        self.assertFalse(result)
        ctrl.sales_view.show_warning.assert_called_once()

    def test_fractional_zero_qty_returns_false(self):
        fm = self._make_fraction_model(has_stock=True)
        ctrl = _make_ctrl(fraction_model=fm)
        result = ctrl.add_product_to_sale(
            1, "Prod", "KG", Decimal("50"), stock=0,
            qty_input="0", is_fractional=True, unit="KG"
        )
        self.assertFalse(result)

    def test_fractional_does_not_accumulate_with_existing(self):
        """Two fractional sales of the same product create independent lines."""
        existing = [(1, "Prod", "KG", Decimal("2.5"), Decimal("50"), "FRAC. 2.5 KG", True)]
        fm = self._make_fraction_model(has_stock=True)
        ctrl = _make_ctrl(items=existing, fraction_model=fm)
        result = ctrl.add_product_to_sale(
            1, "Prod", "KG", Decimal("50"), stock=0,
            qty_input="1.5", is_fractional=True, unit="KG"
        )
        self.assertTrue(result)
        self.assertEqual(len(ctrl.sales_view.items_in_sale), 2)

    def test_fractional_uses_decimal_quantity(self):
        fm = self._make_fraction_model(has_stock=True)
        ctrl = _make_ctrl(fraction_model=fm)
        ctrl.add_product_to_sale(
            1, "Prod", "KG", Decimal("50"), stock=0,
            qty_input="3.75", is_fractional=True, unit="KG"
        )
        item = ctrl.sales_view.items_in_sale[0]
        self.assertEqual(item[3], Decimal("3.75"))


if __name__ == "__main__":
    unittest.main()
