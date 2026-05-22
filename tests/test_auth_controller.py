import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import patch, MagicMock
from controllers.auth_controller import validate_data


class TestAuthControllerValidateData(unittest.TestCase):

    def _patch(self, user_row=None, password_valid=False):
        mock_user_instance = MagicMock()
        mock_user_instance.get_user_by_username.return_value = user_row
        mock_user_class = MagicMock(return_value=mock_user_instance)
        return (
            patch("controllers.auth_controller.User", mock_user_class),
            patch("controllers.auth_controller.validate_password", return_value=password_valid),
            patch("controllers.auth_controller.messagebox"),
        )

    def test_user_not_found_returns_false(self):
        p1, p2, p3 = self._patch(user_row=None)
        with p1, p2, p3 as mock_mb:
            result = validate_data("unknown", "pass")
        self.assertFalse(result)
        mock_mb.showwarning.assert_called_once()

    def test_wrong_password_returns_false(self):
        fake_user = ("admin", "hash_stored")  # user[1] is the hash
        p1, p2, p3 = self._patch(user_row=fake_user, password_valid=False)
        with p1, p2, p3 as mock_mb:
            result = validate_data("admin", "wrong")
        self.assertFalse(result)
        mock_mb.showwarning.assert_called_once()

    def test_correct_credentials_returns_true(self):
        fake_user = ("admin", "hash_stored")  # user[1] is the hash
        p1, p2, p3 = self._patch(user_row=fake_user, password_valid=True)
        with p1, p2, p3:
            result = validate_data("admin", "correct")
        self.assertTrue(result)

    def test_empty_username_shows_warning_if_not_found(self):
        p1, p2, p3 = self._patch(user_row=None)
        with p1, p2, p3 as mock_mb:
            result = validate_data("", "pass")
        self.assertFalse(result)
        mock_mb.showwarning.assert_called_once()


if __name__ == "__main__":
    unittest.main()
