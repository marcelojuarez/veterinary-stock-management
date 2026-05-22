import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import tempfile
from decimal import Decimal
from db.database import Database
from models.fraction import FractionModel


def make_test_db():
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp.close()
    db = Database(tmp.name)
    return db, tmp.name


def _make_model(db):
    return FractionModel(db_connection=db)


def _insert_product(db, pid=1, qty=10, name="ALIMENTO"):
    db.execute_query(
        "INSERT INTO stock (id, name, pack, list_price, discount, cost_price, profit, "
        "price, iva, price_with_iva, quantity) VALUES (?, ?, 'BOLSA', '100', '0', '80', "
        "'20', '100', '21', '121', ?)",
        (pid, name, qty)
    )


def _insert_open_fraction(db, product_id, remaining):
    db.execute_query(
        "INSERT INTO open_fractions (product_id, remaining, opened_at) VALUES (?, ?, '2026-01-01 00:00:00')",
        (product_id, float(remaining))
    )


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────────────────

class TestFractionConfig(unittest.TestCase):

    def setUp(self):
        self.db, self.db_path = make_test_db()
        _insert_product(self.db)
        self.model = _make_model(self.db)

    def tearDown(self):
        os.unlink(self.db_path)

    def test_get_config_none_when_not_configured(self):
        self.assertIsNone(self.model.get_config(1))

    def test_is_fractional_false_without_config(self):
        self.assertFalse(self.model.is_fractional(1))

    def test_set_config_creates_record(self):
        self.model.set_config(1, 'KG', 25.0, '10.00')
        cfg = self.model.get_config(1)
        self.assertIsNotNone(cfg)
        self.assertEqual(cfg['unit'], 'KG')
        self.assertEqual(cfg['qty_per_package'], Decimal('25'))
        self.assertEqual(cfg['fraction_price'], Decimal('10.00'))

    def test_is_fractional_true_after_set_config(self):
        self.model.set_config(1, 'KG', 25.0, '10.00')
        self.assertTrue(self.model.is_fractional(1))

    def test_set_config_updates_existing(self):
        self.model.set_config(1, 'KG', 25.0, '10.00')
        self.model.set_config(1, 'KG', 50.0, '8.00')
        cfg = self.model.get_config(1)
        self.assertEqual(cfg['qty_per_package'], Decimal('50'))
        self.assertEqual(cfg['fraction_price'], Decimal('8.00'))
        # Only one row in DB
        count = self.db.fetch_one("SELECT COUNT(*) FROM stock_fraction_config WHERE product_id = 1")
        self.assertEqual(count[0], 1)

    def test_remove_config(self):
        self.model.set_config(1, 'KG', 25.0, '10.00')
        self.model.remove_config(1)
        self.assertFalse(self.model.is_fractional(1))


# ─────────────────────────────────────────────────────────────────────────────
# STOCK DISPONIBLE
# ─────────────────────────────────────────────────────────────────────────────

class TestAvailableStock(unittest.TestCase):

    def setUp(self):
        self.db, self.db_path = make_test_db()
        _insert_product(self.db, pid=1, qty=4)
        self.model = _make_model(self.db)
        self.model.set_config(1, 'KG', 25.0, '10.00')

    def tearDown(self):
        os.unlink(self.db_path)

    def test_total_available_in_open_empty(self):
        self.assertEqual(self.model.total_available_in_open(1), Decimal('0'))

    def test_total_available_in_open_single(self):
        _insert_open_fraction(self.db, 1, Decimal('10'))
        self.assertEqual(self.model.total_available_in_open(1), Decimal('10'))

    def test_total_available_in_open_multiple(self):
        _insert_open_fraction(self.db, 1, Decimal('10'))
        _insert_open_fraction(self.db, 1, Decimal('7.5'))
        self.assertEqual(self.model.total_available_in_open(1), Decimal('17.5'))

    def test_get_available_stock_info_returns_empty_without_config(self):
        _insert_product(self.db, pid=2, qty=5, name="SIN CONFIG")
        info = self.model.get_available_stock_info(2)
        self.assertEqual(info, {})

    def test_get_available_stock_info_no_open_fractions(self):
        # 4 bolsas cerradas * 25 kg = 100 kg disponibles
        info = self.model.get_available_stock_info(1)
        self.assertEqual(info['closed_packages'], 4)
        self.assertEqual(info['open_remaining'], Decimal('0'))
        self.assertEqual(info['total_units'], Decimal('100'))

    def test_get_available_stock_info_with_open_fractions(self):
        # 4 bolsas * 25 = 100 + 7 abierto = 107 kg
        _insert_open_fraction(self.db, 1, Decimal('7'))
        info = self.model.get_available_stock_info(1)
        self.assertEqual(info['open_remaining'], Decimal('7'))
        self.assertEqual(info['total_units'], Decimal('107'))

    def test_has_enough_stock_true(self):
        self.assertTrue(self.model.has_enough_stock(1, Decimal('50')))

    def test_has_enough_stock_false(self):
        self.assertFalse(self.model.has_enough_stock(1, Decimal('200')))

    def test_has_enough_stock_exact(self):
        # 4 * 25 = 100, pedir exactamente 100 debe ser suficiente
        self.assertTrue(self.model.has_enough_stock(1, Decimal('100')))

    def test_has_enough_stock_false_no_config(self):
        _insert_product(self.db, pid=2, qty=100, name="SIN CONFIG")
        self.assertFalse(self.model.has_enough_stock(2, Decimal('1')))


# ─────────────────────────────────────────────────────────────────────────────
# DESCUENTO FIFO
# ─────────────────────────────────────────────────────────────────────────────

class TestDeductFractionalStock(unittest.TestCase):
    """
    Escenarios del algoritmo FIFO de descuento fraccionado.
    """

    def setUp(self):
        self.db, self.db_path = make_test_db()
        self.model = _make_model(self.db)

    def tearDown(self):
        os.unlink(self.db_path)

    def _deduct(self, product_id, quantity):
        """Helper: obtiene conn, deduce, hace commit y cierra conn."""
        conn = self.db.get_connection()
        self.model.deduct_fractional_stock(product_id, quantity, conn, commit=True)
        conn.close()

    def _qty(self, product_id):
        return self.db.fetch_one("SELECT quantity FROM stock WHERE id = ?", (product_id,))[0]

    def _open_fracs(self, product_id):
        rows = self.db.fetch_all(
            "SELECT remaining FROM open_fractions WHERE product_id = ? ORDER BY opened_at ASC",
            (product_id,)
        )
        return [Decimal(str(r[0])) for r in rows]

    def test_raises_if_no_config(self):
        _insert_product(self.db, pid=1, qty=10)
        conn = self.db.get_connection()
        with self.assertRaises(ValueError):
            self.model.deduct_fractional_stock(1, Decimal('3'), conn, commit=False)
        conn.close()

    def test_raises_if_insufficient_stock(self):
        _insert_product(self.db, pid=1, qty=1)
        self.model.set_config(1, 'KG', 25.0, '10.00')
        # 1 bolsa * 25 = 25 kg, pedir 30 debe fallar
        conn = self.db.get_connection()
        with self.assertRaises(ValueError):
            self.model.deduct_fractional_stock(1, Decimal('30'), conn, commit=False)
        conn.close()

    def test_deduct_from_existing_open_fraction(self):
        """
        Hay 10 kg abiertos, se venden 3 kg.
        Resultado: remaining=7, stock sin cambios.
        """
        _insert_product(self.db, pid=1, qty=5)
        self.model.set_config(1, 'KG', 25.0, '10.00')
        _insert_open_fraction(self.db, 1, Decimal('10'))

        self._deduct(1, Decimal('3'))

        self.assertEqual(self._open_fracs(1), [Decimal('7')])
        self.assertEqual(self._qty(1), 5)  # no se abrió bolsa nueva

    def test_open_new_package_when_no_open_fractions(self):
        """
        No hay bolsas abiertas, se venden 3 kg de bolsas de 25 kg.
        Resultado: stock.quantity -= 1, open_fraction con remaining=22.
        """
        _insert_product(self.db, pid=1, qty=5)
        self.model.set_config(1, 'KG', 25.0, '10.00')

        self._deduct(1, Decimal('3'))

        self.assertEqual(self._qty(1), 4)  # se abrió una bolsa
        fracs = self._open_fracs(1)
        self.assertEqual(len(fracs), 1)
        self.assertEqual(fracs[0], Decimal('22'))  # 25 - 3 = 22

    def test_exact_package_consumption_leaves_zero(self):
        """
        Se venden exactamente 25 kg (= 1 bolsa entera).
        remaining=0, stock.quantity -= 1.
        """
        _insert_product(self.db, pid=1, qty=3)
        self.model.set_config(1, 'KG', 25.0, '10.00')

        self._deduct(1, Decimal('25'))

        self.assertEqual(self._qty(1), 2)
        fracs = self._open_fracs(1)
        self.assertEqual(len(fracs), 1)
        self.assertEqual(fracs[0], Decimal('0'))

    def test_span_across_multiple_open_fractions(self):
        """
        2 bolsas abiertas: [5 kg, 8 kg]. Se venden 7 kg.
        FIFO: consume 5 de la primera → remaining=0, consume 2 de la segunda → remaining=6.
        """
        _insert_product(self.db, pid=1, qty=5)
        self.model.set_config(1, 'KG', 25.0, '10.00')
        _insert_open_fraction(self.db, 1, Decimal('5'))
        _insert_open_fraction(self.db, 1, Decimal('8'))

        self._deduct(1, Decimal('7'))

        fracs = self._open_fracs(1)
        self.assertEqual(fracs[0], Decimal('0'))  # primera vaciada
        self.assertEqual(fracs[1], Decimal('6'))  # segunda con 6 restantes
        self.assertEqual(self._qty(1), 5)          # no se abrió bolsa nueva

    def test_open_multiple_packages_when_needed(self):
        """
        Sin bolsas abiertas, se venden 60 kg de bolsas de 25 kg.
        Necesita abrir 3 bolsas: [0, 0, 15] → stock.quantity -= 3.
        """
        _insert_product(self.db, pid=1, qty=5)
        self.model.set_config(1, 'KG', 25.0, '10.00')

        self._deduct(1, Decimal('60'))

        self.assertEqual(self._qty(1), 2)  # 5 - 3 = 2
        fracs = self._open_fracs(1)
        self.assertEqual(len(fracs), 3)
        self.assertEqual(fracs[0], Decimal('0'))
        self.assertEqual(fracs[1], Decimal('0'))
        self.assertEqual(fracs[2], Decimal('15'))  # 75 - 60 = 15

    def test_open_fraction_exhausted_then_new_package(self):
        """
        Hay 3 kg abiertos, se venden 10 kg.
        Consume 3 kg de abierta → 7 kg restantes se toman de bolsa nueva (25 kg).
        remaining=[0, 18], stock.quantity -= 1.
        """
        _insert_product(self.db, pid=1, qty=5)
        self.model.set_config(1, 'KG', 25.0, '10.00')
        _insert_open_fraction(self.db, 1, Decimal('3'))

        self._deduct(1, Decimal('10'))

        self.assertEqual(self._qty(1), 4)  # una bolsa cerrada abierta
        fracs = self._open_fracs(1)
        self.assertEqual(fracs[0], Decimal('0'))   # la original vaciada
        self.assertEqual(fracs[1], Decimal('18'))  # 25 - 7 = 18 en la nueva


if __name__ == "__main__":
    unittest.main()
