import unittest
from unittest.mock import MagicMock, patch


class TestOnboardingService(unittest.TestCase):
    def setUp(self):
        self.mock_settings_repo = MagicMock()
        self.mock_settings_repo.close = MagicMock()
        self.mock_pluggy_item_repo = MagicMock()
        self.mock_pluggy_item_repo.close = MagicMock()

        with patch(
            "services.onboarding_service.SettingsRepository",
            return_value=self.mock_settings_repo,
        ), patch(
            "services.onboarding_service.PluggyItemRepository",
            return_value=self.mock_pluggy_item_repo,
        ):
            from services.onboarding_service import OnboardingService

            self.service = OnboardingService()

    # ── get_status ──

    def test_status_all_complete(self):
        self.mock_settings_repo.get_value.side_effect = lambda key: {
            "pluggy_client_id": "id",
            "pluggy_client_secret": "secret",
        }.get(key)
        self.mock_pluggy_item_repo.get_items_by_role.return_value = [
            {"item_id": "item-1"}
        ]
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        self.mock_settings_repo.execute_query.return_value = mock_cursor

        result = self.service.get_status()

        self.assertTrue(result["has_credentials"])
        self.assertTrue(result["has_pluggy_items"])
        self.assertTrue(result["has_transactions"])
        self.assertTrue(result["has_history"])
        self.assertTrue(result["is_complete"])

    def test_status_empty_db(self):
        self.mock_settings_repo.get_value.return_value = None
        self.mock_pluggy_item_repo.get_items_by_role.return_value = []
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        self.mock_settings_repo.execute_query.return_value = mock_cursor

        result = self.service.get_status()

        self.assertFalse(result["has_credentials"])
        self.assertFalse(result["has_pluggy_items"])
        self.assertFalse(result["has_transactions"])
        self.assertFalse(result["has_history"])
        self.assertFalse(result["is_complete"])

    def test_status_partial_credentials_only(self):
        self.mock_settings_repo.get_value.side_effect = lambda key: {
            "pluggy_client_id": "id",
            "pluggy_client_secret": None,
        }.get(key)
        self.mock_pluggy_item_repo.get_items_by_role.return_value = []
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        self.mock_settings_repo.execute_query.return_value = mock_cursor

        result = self.service.get_status()

        self.assertFalse(result["has_credentials"])
        self.assertFalse(result["is_complete"])

    def test_status_has_transactions_from_credit(self):
        """has_transactions = True even if only credit_transactions exist."""
        self.mock_settings_repo.get_value.return_value = None
        self.mock_pluggy_item_repo.get_items_by_role.return_value = []

        call_count = 0

        def execute_side_effect(query, *args):
            nonlocal call_count
            mock_cursor = MagicMock()
            if "bank_transactions" in query:
                mock_cursor.fetchone.return_value = None
            elif "credit_transactions" in query:
                mock_cursor.fetchone.return_value = (1,)
            else:
                mock_cursor.fetchone.return_value = None
            call_count += 1
            return mock_cursor

        self.mock_settings_repo.execute_query.side_effect = execute_side_effect

        result = self.service.get_status()

        self.assertTrue(result["has_transactions"])

    # ── save_credentials ──

    def test_save_credentials_success(self):
        self.service.save_credentials("my-id", "my-secret", "Splitwise")

        calls = self.mock_settings_repo.set_value.call_args_list
        self.assertEqual(calls[0].args, ("pluggy_client_id", "my-id"))
        self.assertEqual(calls[1].args, ("pluggy_client_secret", "my-secret"))
        self.assertEqual(calls[2].args, ("splitwise_account_name", "Splitwise"))

    def test_save_credentials_without_splitwise(self):
        self.service.save_credentials("my-id", "my-secret")

        self.assertEqual(self.mock_settings_repo.set_value.call_count, 2)

    def test_save_credentials_raises_on_empty_client_id(self):
        with self.assertRaises(ValueError):
            self.service.save_credentials("", "secret")

    def test_save_credentials_raises_on_empty_client_secret(self):
        with self.assertRaises(ValueError):
            self.service.save_credentials("id", "")

    def test_save_credentials_raises_on_whitespace_only(self):
        with self.assertRaises(ValueError):
            self.service.save_credentials("  ", "secret")

    def test_save_credentials_strips_whitespace(self):
        self.service.save_credentials("  my-id  ", "  my-secret  ")

        calls = self.mock_settings_repo.set_value.call_args_list
        self.assertEqual(calls[0].args, ("pluggy_client_id", "my-id"))
        self.assertEqual(calls[1].args, ("pluggy_client_secret", "my-secret"))


if __name__ == "__main__":
    unittest.main()
