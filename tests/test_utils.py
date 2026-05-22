import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from decimal import Decimal
from utils.utils import norm_to_2_dec, string_to_2_dec, flex_dec, format_currency


class TestNormTo2Dec(unittest.TestCase):
    def test_rounds_up(self):
        self.assertEqual(norm_to_2_dec(Decimal("1.235")), Decimal("1.24"))

    def test_rounds_down(self):
        self.assertEqual(norm_to_2_dec(Decimal("1.234")), Decimal("1.23"))

    def test_already_2_decimals(self):
        self.assertEqual(norm_to_2_dec(Decimal("1.00")), Decimal("1.00"))

    def test_integer(self):
        self.assertEqual(norm_to_2_dec(Decimal("5")), Decimal("5.00"))

    def test_string_input(self):
        self.assertEqual(norm_to_2_dec("3.145"), Decimal("3.15"))

    def test_zero(self):
        self.assertEqual(norm_to_2_dec(Decimal("0")), Decimal("0.00"))


class TestStringTo2Dec(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(string_to_2_dec("10.50"), Decimal("10.50"))

    def test_comma_separator(self):
        self.assertEqual(string_to_2_dec("10,50"), Decimal("10.50"))

    def test_empty_string(self):
        self.assertIsNone(string_to_2_dec(""))

    def test_non_numeric(self):
        self.assertIsNone(string_to_2_dec("abc"))

    def test_zero(self):
        self.assertEqual(string_to_2_dec("0"), Decimal("0.00"))

    def test_rounds_up(self):
        self.assertEqual(string_to_2_dec("1.995"), Decimal("2.00"))

    def test_large_value(self):
        self.assertEqual(string_to_2_dec("999999.99"), Decimal("999999.99"))


class TestFlexDec(unittest.TestCase):
    def test_2_decimals_preserved(self):
        self.assertEqual(flex_dec("10.50"), Decimal("10.50"))

    def test_4_decimals_preserved(self):
        self.assertEqual(flex_dec("1.2345"), Decimal("1.2345"))

    def test_more_than_4_rounds(self):
        self.assertEqual(flex_dec("1.23456"), Decimal("1.2346"))

    def test_trailing_zeros_stripped_to_2(self):
        self.assertEqual(flex_dec("5.0000"), Decimal("5.00"))

    def test_3_significant_decimals(self):
        self.assertEqual(flex_dec("1.230"), Decimal("1.23"))


class TestFormatCurrency(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(format_currency(Decimal("1234.56")), "1.234,56")

    def test_millions(self):
        self.assertEqual(format_currency(Decimal("1000000.00")), "1.000.000,00")

    def test_zero(self):
        self.assertEqual(format_currency(Decimal("0")), "0,00")

    def test_small_value(self):
        self.assertEqual(format_currency(Decimal("0.01")), "0,01")


if __name__ == "__main__":
    unittest.main()
