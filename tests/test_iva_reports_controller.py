import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import MagicMock
from controllers.iva_reports_controller import ReportsController


class TestGetMonthName(unittest.TestCase):

    def setUp(self):
        self.ctrl = ReportsController(MagicMock())

    def test_january(self):
        self.assertEqual(self.ctrl.get_month_name(1), "January")

    def test_june(self):
        self.assertEqual(self.ctrl.get_month_name(6), "June")

    def test_december(self):
        self.assertEqual(self.ctrl.get_month_name(12), "December")

    def test_all_months_returns_string(self):
        for i in range(1, 13):
            result = self.ctrl.get_month_name(i)
            self.assertIsInstance(result, str)
            self.assertTrue(len(result) > 0)

    def test_month_4_is_april(self):
        self.assertEqual(self.ctrl.get_month_name(4), "April")

    def test_month_9_is_september(self):
        self.assertEqual(self.ctrl.get_month_name(9), "September")


if __name__ == "__main__":
    unittest.main()
