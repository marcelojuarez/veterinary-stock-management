import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import tempfile
from decimal import Decimal
from unittest.mock import MagicMock
from db.database import Database
from models.sale import SalesModel


def make_test_db():
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp.close()
    db = Database(tmp.name)
    return db, tmp.name


def _make_model(db):
    movement_mock = MagicMock()
    fraction_mock = MagicMock()
    fraction_mock.get_config.return_value = {'unit': 'KG'}
    model = SalesModel(stock_movement_model=movement_mock, fraction_model=fraction_mock)
    model.db = db
    return model, movement_mock, fraction_mock


def _insert_customer(db, cid=1):
    db.execute_query(
        "INSERT INTO customer (id, name, cuit, home, iva_condition) VALUES (?, 'TEST', NULL, 'CITY', 'CF')",
        (cid,)
    )


def _insert_product(db, pid=1, name="PROD", iva="21.00", price="100.00", price_with_iva="121.00", qty=100):
    db.execute_query(
        "INSERT INTO stock (id, name, pack, list_price, discount, cost_price, profit, "
        "price, iva, price_with_iva, quantity) VALUES (?, ?, 'UNIT', '100', '0', '80', '20', ?, ?, ?, ?)",
        (pid, name, price, iva, price_with_iva, qty)
    )


def _insert_sale(db, sale_id, cliente_id, total, estado='paid'):
    db.execute_query(
        "INSERT INTO sales (id, date, total, cliente_id, estado) "
        "VALUES (?, '2026-05-10 10:00:00', ?, ?, ?)",
        (sale_id, str(total), cliente_id, estado)
    )


def _insert_sale_item(db, sale_id, product_id, quantity, price, subtotal, iva_rate, iva_amount):
    db.execute_query(
        "INSERT INTO sale_items (sale_id, product_id, quantity, price, subtotal, iva_rate, iva_amount) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (sale_id, product_id, str(quantity), str(price), str(subtotal), str(iva_rate), str(iva_amount))
    )


class TestGetTotalOfSaleItems(unittest.TestCase):

    def setUp(self):
        self.db, self.db_path = make_test_db()
        self.model, *_ = _make_model(self.db)
        _insert_customer(self.db)
        _insert_product(self.db)

    def tearDown(self):
        os.unlink(self.db_path)

    def test_single_item(self):
        _insert_sale(self.db, 1, 1, "121.00")
        _insert_sale_item(self.db, 1, 1, 1, "121.00", "121.00", "21.00", "21.00")
        self.assertEqual(self.model.get_total_of_sale_items(1), Decimal("121.00"))

    def test_multiple_items_summed(self):
        _insert_sale(self.db, 1, 1, "363.00")
        _insert_sale_item(self.db, 1, 1, 1, "121.00", "121.00", "21.00", "21.00")
        _insert_sale_item(self.db, 1, 1, 1, "121.00", "121.00", "21.00", "21.00")
        _insert_sale_item(self.db, 1, 1, 1, "121.00", "121.00", "21.00", "21.00")
        self.assertEqual(self.model.get_total_of_sale_items(1), Decimal("363.00"))

    def test_no_items_returns_zero(self):
        _insert_sale(self.db, 1, 1, "0.00")
        self.assertEqual(self.model.get_total_of_sale_items(1), Decimal("0.00"))


class TestUpdateSaleItem(unittest.TestCase):
    """
    Verifica el recálculo de precios al actualizar un ítem de venta.
    Cálculo esperado para 21% IVA, qty=2, new_price_with_iva=242:
      divisor              = 1.21
      price_without_iva    = 242 / 1.21 = 200.00
      subtotal_with_iva    = 242 * 2   = 484.00
      subtotal_without_iva = 200 * 2   = 400.00
      iva_amount           = 400 * 0.21 = 84.00
    """

    def setUp(self):
        self.db, self.db_path = make_test_db()
        self.model, *_ = _make_model(self.db)
        _insert_customer(self.db)
        _insert_product(self.db)
        _insert_sale(self.db, 1, 1, "121.00")
        # Original: qty=2, price=121, subtotal=242, iva_rate=21, iva_amount=42
        _insert_sale_item(self.db, 1, 1, 2, "121.00", "242.00", "21.00", "42.00")

    def tearDown(self):
        os.unlink(self.db_path)

    def _get_item(self):
        return self.db.fetch_one(
            "SELECT price, subtotal, iva_amount FROM sale_items WHERE sale_id = 1 AND product_id = 1"
        )

    def test_price_updated_correctly(self):
        self.model.update_sale_item(1, 1, Decimal("242.00"))
        row = self._get_item()
        self.assertEqual(Decimal(row[0]), Decimal("242.00"))

    def test_subtotal_with_iva_correct(self):
        self.model.update_sale_item(1, 1, Decimal("242.00"))
        row = self._get_item()
        self.assertEqual(Decimal(row[1]), Decimal("484.00"))

    def test_iva_amount_correct(self):
        self.model.update_sale_item(1, 1, Decimal("242.00"))
        row = self._get_item()
        self.assertEqual(Decimal(row[2]), Decimal("84.00"))

    def test_zero_iva_rate_item(self):
        # Product with 0% IVA: iva_amount must be 0
        _insert_product(self.db, pid=2, name="EXENTO", iva="0.00",
                         price="100.00", price_with_iva="100.00")
        _insert_sale(self.db, 2, 1, "100.00")
        _insert_sale_item(self.db, 2, 2, 1, "100.00", "100.00", "0.00", "0.00")
        self.model.update_sale_item(2, 2, Decimal("200.00"))
        row = self.db.fetch_one(
            "SELECT subtotal, iva_amount FROM sale_items WHERE sale_id = 2 AND product_id = 2"
        )
        self.assertEqual(Decimal(row[0]), Decimal("200.00"))
        self.assertEqual(Decimal(row[1]), Decimal("0.00"))

    def test_recalculate_sale_total_after_update(self):
        self.model.update_sale_item(1, 1, Decimal("242.00"))
        self.model.recalculate_sale_total(1)
        row = self.db.fetch_one("SELECT total FROM sales WHERE id = 1")
        self.assertEqual(Decimal(row[0]), Decimal("484.00"))


class TestRegisterSale(unittest.TestCase):
    """
    Verifica que register_sale inserta correctamente y calcula iva_amount.
    Se mockean StockMovementModel y FractionModel para aislar la lógica financiera.
    """

    def setUp(self):
        self.db, self.db_path = make_test_db()
        self.model, self.movement_mock, self.fraction_mock = _make_model(self.db)
        _insert_customer(self.db)
        _insert_product(self.db, pid=1, iva="21.00", price="100.00", price_with_iva="121.00", qty=50)

    def tearDown(self):
        os.unlink(self.db_path)

    def test_sale_inserted_in_db(self):
        sale_id = self.model.register_sale(
            total=Decimal("121.00"),
            items=[(1, "PROD", "UNIT", 1, Decimal("121.00"))],
            cliente_id=1,
            estado="paid"
        )
        row = self.db.fetch_one("SELECT id, total FROM sales WHERE id = ?", (sale_id,))
        self.assertIsNotNone(row)
        self.assertEqual(Decimal(row[1]), Decimal("121.00"))

    def test_iva_amount_calculated_from_price_with_iva(self):
        """
        price_with_iva=121, iva_rate=21% → iva_amount=21, subtotal=121.
        """
        sale_id = self.model.register_sale(
            total=Decimal("121.00"),
            items=[(1, "PROD", "UNIT", 1, Decimal("121.00"))],
            cliente_id=1,
            estado="paid"
        )
        row = self.db.fetch_one(
            "SELECT subtotal, iva_amount FROM sale_items WHERE sale_id = ?", (sale_id,)
        )
        self.assertEqual(Decimal(row[0]), Decimal("121.00"))
        self.assertEqual(Decimal(row[1]), Decimal("21.00"))

    def test_quantity_2_iva_calculation(self):
        """
        qty=2, price_with_iva=121, iva_rate=21% → subtotal=242, iva_amount=42.
        """
        sale_id = self.model.register_sale(
            total=Decimal("242.00"),
            items=[(1, "PROD", "UNIT", 2, Decimal("121.00"))],
            cliente_id=1,
            estado="paid"
        )
        row = self.db.fetch_one(
            "SELECT subtotal, iva_amount FROM sale_items WHERE sale_id = ?", (sale_id,)
        )
        self.assertEqual(Decimal(row[0]), Decimal("242.00"))
        self.assertEqual(Decimal(row[1]), Decimal("42.00"))

    def test_stock_decremented(self):
        self.model.register_sale(
            total=Decimal("121.00"),
            items=[(1, "PROD", "UNIT", 3, Decimal("121.00"))],
            cliente_id=1,
            estado="paid"
        )
        row = self.db.fetch_one("SELECT quantity FROM stock WHERE id = 1")
        self.assertEqual(row[0], 47)  # 50 - 3

    def test_stock_movement_registered(self):
        self.model.register_sale(
            total=Decimal("121.00"),
            items=[(1, "PROD", "UNIT", 1, Decimal("121.00"))],
            cliente_id=1,
            estado="paid"
        )
        self.movement_mock.register.assert_called_once()

    def test_retentions_saved(self):
        sale_id = self.model.register_sale(
            total=Decimal("121.00"),
            items=[(1, "PROD", "UNIT", 1, Decimal("121.00"))],
            cliente_id=1,
            estado="paid",
            retenciones={"IVA": Decimal("5.00"), "certificado": "CERT-001"}
        )
        row = self.db.fetch_one(
            "SELECT tax_type, amount FROM sale_retentions WHERE sale_id = ?", (sale_id,)
        )
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "IVA")
        self.assertEqual(Decimal(row[1]), Decimal("5.00"))

    def test_returns_sale_id(self):
        sale_id = self.model.register_sale(
            total=Decimal("121.00"),
            items=[(1, "PROD", "UNIT", 1, Decimal("121.00"))],
            cliente_id=1,
            estado="paid"
        )
        self.assertIsInstance(sale_id, int)
        self.assertGreater(sale_id, 0)


if __name__ == "__main__":
    unittest.main()
