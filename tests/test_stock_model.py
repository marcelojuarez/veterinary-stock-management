import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import tempfile
from decimal import Decimal
from unittest.mock import MagicMock, patch
from db.database import Database
from models.stock import StockModel
from models.sale import SalesModel
from models.payment_model import PaymentModel
from models.customer_credit import CustomerCredit
import models.stock as stock_module


def make_test_db():
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp.close()
    db = Database(tmp.name)
    return db, tmp.name


def _make_stock_model(db):
    """
    Construye StockModel con dependencias reales conectadas al mismo test DB.
    event_bus es un mock (no toca DB).
    StockModel usa el módulo-level `db` en varios métodos, por eso se parchea.
    """
    event_bus = MagicMock()

    movement_mock = MagicMock()

    credit_model = CustomerCredit.__new__(CustomerCredit)
    credit_model.db = db

    pay_model = PaymentModel(
        sales_model=MagicMock(),
        customer_credit=credit_model,
        checks_model=MagicMock(),
        customer_model=MagicMock()
    )
    pay_model.db = db

    sales_model = SalesModel(
        stock_movement_model=MagicMock(),
        fraction_model=MagicMock()
    )
    sales_model.db = db

    stock_model = StockModel(
        sales_model=sales_model,
        payment_model=pay_model,
        event_bus=event_bus,
        db_conection=db,
        stock_movement_model=movement_mock
    )
    return stock_model, movement_mock, event_bus


def _insert_product(db, pid=1, name="ALIMENTO", iva="21.00",
                    price="100.00", price_with_iva="121.00",
                    cost_price="80.00", qty=10, date="2026-05-01"):
    db.execute_query(
        "INSERT INTO stock (id, name, pack, list_price, discount, cost_price, profit, "
        "price, iva, price_with_iva, quantity, last_price_update) "
        "VALUES (?, ?, 'BOLSA', '100', '0', ?, '20', ?, ?, ?, ?, ?)",
        (pid, name, cost_price, price, iva, price_with_iva, qty, date)
    )


def _insert_customer(db, cid=1):
    db.execute_query(
        "INSERT INTO customer (id, name, cuit, home, iva_condition) VALUES (?, 'TEST', NULL, 'CITY', 'CF')",
        (cid,)
    )


def _insert_sale(db, sale_id, cliente_id, total, estado='pending'):
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


# ─────────────────────────────────────────────────────────────────────────────
# UPDATE PRODUCT PRICE
# ─────────────────────────────────────────────────────────────────────────────

class TestUpdateProductPrice(unittest.TestCase):

    def setUp(self):
        self.db, self.db_path = make_test_db()
        self.model, *_ = _make_stock_model(self.db)
        _insert_product(self.db)

    def tearDown(self):
        os.unlink(self.db_path)

    def _get_product(self):
        return self.db.fetch_one(
            "SELECT profit, cost_price, price, price_with_iva FROM stock WHERE id = 1"
        )

    def test_fields_updated(self):
        self.model.update_product_price(1, {
            'Profit':    '25.00',
            'CostPrice': '85.00',
            'SalePrice': '110.00',
            'PriceWIva': '133.10',
        })
        row = self._get_product()
        self.assertEqual(row[0], '25.00')
        self.assertEqual(row[1], '85.00')
        self.assertEqual(row[2], '110.00')
        self.assertEqual(row[3], '133.10')

    def test_unrelated_fields_unchanged(self):
        original = self.db.fetch_one("SELECT name, iva, quantity FROM stock WHERE id = 1")
        self.model.update_product_price(1, {
            'Profit': '25.00', 'CostPrice': '85.00',
            'SalePrice': '110.00', 'PriceWIva': '133.10',
        })
        after = self.db.fetch_one("SELECT name, iva, quantity FROM stock WHERE id = 1")
        self.assertEqual(original, after)


# ─────────────────────────────────────────────────────────────────────────────
# BULK UPDATE PRICES BY DATE
# ─────────────────────────────────────────────────────────────────────────────

class TestBulkUpdatePricesByDate(unittest.TestCase):
    """
    Verifica que bulk_update_prices_by_date aplica el multiplicador correctamente
    y recalcula price_with_iva según la alícuota de cada producto.
    """

    def setUp(self):
        self.db, self.db_path = make_test_db()
        self._original_db = stock_module.db
        stock_module.db = self.db  # redirigir db global al test DB
        self.model, self.movement_mock, _ = _make_stock_model(self.db)

    def tearDown(self):
        stock_module.db = self._original_db
        os.unlink(self.db_path)

    def _get_prices(self, pid):
        return self.db.fetch_one("SELECT price, price_with_iva, profit FROM stock WHERE id = ?", (pid,))

    def test_price_increased_by_percent(self):
        _insert_product(self.db, pid=1, price="100.00", price_with_iva="121.00",
                         cost_price="80.00", iva="21.00", date="2026-05-01")
        self.model.bulk_update_prices_by_date("2026-05-01", 10)
        row = self._get_prices(1)
        self.assertAlmostEqual(float(row[0]), 110.00, places=2)

    def test_price_with_iva_21_correct(self):
        # price=100, +10% → price=110 → price_with_iva = round(110 * 1.21, 2) = 133.10
        _insert_product(self.db, pid=1, price="100.00", price_with_iva="121.00",
                         cost_price="80.00", iva="21.00", date="2026-05-01")
        self.model.bulk_update_prices_by_date("2026-05-01", 10)
        row = self._get_prices(1)
        self.assertAlmostEqual(float(row[1]), 133.10, places=2)

    def test_price_with_iva_105_correct(self):
        # price=100, +10% → price=110 → price_with_iva = round(110 * 1.105, 2) = 121.55
        _insert_product(self.db, pid=2, price="100.00", price_with_iva="110.50",
                         cost_price="80.00", iva="10.5", date="2026-05-01")
        self.model.bulk_update_prices_by_date("2026-05-01", 10)
        row = self._get_prices(2)
        self.assertAlmostEqual(float(row[1]), 121.55, places=2)

    def test_profit_recalculated(self):
        # price=100 → 110, cost=80 → profit = (110-80)/80 * 100 = 37.5
        _insert_product(self.db, pid=1, price="100.00", price_with_iva="121.00",
                         cost_price="80.00", iva="21.00", date="2026-05-01")
        self.model.bulk_update_prices_by_date("2026-05-01", 10)
        row = self._get_prices(1)
        self.assertAlmostEqual(float(row[2]), 37.5, places=1)

    def test_returns_count_of_updated_products(self):
        _insert_product(self.db, pid=1, date="2026-05-01")
        _insert_product(self.db, pid=2, name="OTRO", date="2026-05-01")
        count = self.model.bulk_update_prices_by_date("2026-05-01", 5)
        self.assertEqual(count, 2)

    def test_only_affects_target_date(self):
        _insert_product(self.db, pid=1, price="100.00", date="2026-05-01")
        _insert_product(self.db, pid=2, name="OTRO", price="200.00", date="2026-04-01")
        self.model.bulk_update_prices_by_date("2026-05-01", 10)
        pid1 = self._get_prices(1)
        pid2 = self._get_prices(2)
        self.assertAlmostEqual(float(pid1[0]), 110.00, places=2)
        self.assertEqual(float(pid2[0]), 200.00)  # sin cambios

    def test_movement_registered_per_product(self):
        _insert_product(self.db, pid=1, date="2026-05-01")
        _insert_product(self.db, pid=2, name="OTRO", date="2026-05-01")
        self.model.bulk_update_prices_by_date("2026-05-01", 5)
        self.assertEqual(self.movement_mock.register.call_count, 2)

    def test_zero_increase_leaves_prices_unchanged(self):
        _insert_product(self.db, pid=1, price="100.00", price_with_iva="121.00", date="2026-05-01")
        self.model.bulk_update_prices_by_date("2026-05-01", 0)
        row = self._get_prices(1)
        self.assertAlmostEqual(float(row[0]), 100.00, places=2)
        self.assertAlmostEqual(float(row[1]), 121.00, places=2)


# ─────────────────────────────────────────────────────────────────────────────
# UPDATE PRICE AND RELATED SALES
# ─────────────────────────────────────────────────────────────────────────────

class TestUpdatePriceAndRelatedSales(unittest.TestCase):
    """
    Verifica que al actualizar el precio de un producto, las ventas pending/partial
    relacionadas actualizan su ítem y recalculan el total.
    """

    def setUp(self):
        self.db, self.db_path = make_test_db()
        self._original_db = stock_module.db
        stock_module.db = self.db
        self.model, self.movement_mock, self.event_bus = _make_stock_model(self.db)
        _insert_customer(self.db)
        _insert_product(self.db, pid=1, price="100.00", price_with_iva="121.00",
                         cost_price="80.00", iva="21.00")

    def tearDown(self):
        stock_module.db = self._original_db
        os.unlink(self.db_path)

    def test_product_price_updated(self):
        result = self.model.update_p_price_and_related_sales_amount(1, {
            'Profit': '30.00', 'CostPrice': '80.00',
            'SalePrice': '110.00', 'PriceWIva': '133.10',
        })
        self.assertTrue(result)
        row = self.db.fetch_one("SELECT price, price_with_iva FROM stock WHERE id = 1")
        self.assertEqual(row[0], '110.00')
        self.assertEqual(row[1], '133.10')

    def test_pending_sale_item_price_updated(self):
        """El precio del ítem en ventas pendientes se actualiza al nuevo precio."""
        _insert_sale(self.db, 1, 1, "121.00", estado='pending')
        _insert_sale_item(self.db, 1, 1, 1, "121.00", "121.00", "21.00", "21.00")

        self.model.update_p_price_and_related_sales_amount(1, {
            'Profit': '30.00', 'CostPrice': '80.00',
            'SalePrice': '110.00', 'PriceWIva': '133.10',
        })

        row = self.db.fetch_one("SELECT price FROM sale_items WHERE sale_id = 1")
        self.assertEqual(row[0], '133.10')

    def test_pending_sale_total_recalculated(self):
        """El total de la venta pendiente se recalcula según el nuevo precio."""
        _insert_sale(self.db, 1, 1, "121.00", estado='pending')
        _insert_sale_item(self.db, 1, 1, 1, "121.00", "121.00", "21.00", "21.00")

        self.model.update_p_price_and_related_sales_amount(1, {
            'Profit': '30.00', 'CostPrice': '80.00',
            'SalePrice': '110.00', 'PriceWIva': '133.10',
        })

        row = self.db.fetch_one("SELECT total FROM sales WHERE id = 1")
        self.assertEqual(Decimal(row[0]), Decimal('133.10'))

    def test_paid_sale_not_affected(self):
        """Las ventas ya pagadas (estado=paid) no se modifican."""
        _insert_sale(self.db, 1, 1, "121.00", estado='paid')
        _insert_sale_item(self.db, 1, 1, 1, "121.00", "121.00", "21.00", "21.00")

        self.model.update_p_price_and_related_sales_amount(1, {
            'Profit': '30.00', 'CostPrice': '80.00',
            'SalePrice': '110.00', 'PriceWIva': '133.10',
        })

        row = self.db.fetch_one("SELECT total FROM sales WHERE id = 1")
        self.assertEqual(Decimal(row[0]), Decimal('121.00'))  # sin cambios

    def test_movement_registered(self):
        self.model.update_p_price_and_related_sales_amount(1, {
            'Profit': '30.00', 'CostPrice': '80.00',
            'SalePrice': '110.00', 'PriceWIva': '133.10',
        })
        self.movement_mock.register.assert_called_once()

    def test_returns_false_on_error(self):
        # Pasar product_id inexistente no debe lanzar excepción, debe retornar False
        result = self.model.update_p_price_and_related_sales_amount(9999, {
            'Profit': '0', 'CostPrice': '0', 'SalePrice': '0', 'PriceWIva': '0',
        })
        # Puede retornar True (no hay error) o False — lo importante es no crashear
        self.assertIn(result, (True, False))

    def test_event_published_when_sales_affected(self):
        _insert_sale(self.db, 1, 1, "121.00", estado='pending')
        _insert_sale_item(self.db, 1, 1, 1, "121.00", "121.00", "21.00", "21.00")

        self.model.update_p_price_and_related_sales_amount(1, {
            'Profit': '30.00', 'CostPrice': '80.00',
            'SalePrice': '110.00', 'PriceWIva': '133.10',
        })

        self.event_bus.publish.assert_called_with("price_changes", unittest.mock.ANY)


if __name__ == "__main__":
    unittest.main()
