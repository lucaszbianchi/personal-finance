import unittest
from unittest.mock import MagicMock, patch

from services.pluggy_insights_service import PluggyInsightsService


class TestPluggyInsightsService(unittest.TestCase):
    def setUp(self):
        self.service = PluggyInsightsService(api_key="test-key")
        self.service.repo = MagicMock()

    def test_store_book_calls_upsert_book_summary(self):
        data = {
            "book": {
                "bankAccount": {"balance": 1000},
                "creditCard": {"balance": -500},
                "categories": [{"category": "food", "transactionType": "DEBIT"}],
            }
        }
        self.service.store_book("item-1", "2025-01", data)
        self.service.repo.upsert_book_summary.assert_called_once()
        args = self.service.repo.upsert_book_summary.call_args
        self.assertEqual(args[0][0], "item-1")

    def test_store_book_ignores_categories(self):
        """After removal, categories in API response are ignored."""
        data = {
            "book": {
                "bankAccount": {},
                "creditCard": {},
                "categories": [{"category": "food"}],
            }
        }
        self.service.store_book("item-1", "2025-01", data)
        # upsert_book_category should not exist or not be called
        self.assertFalse(
            hasattr(self.service.repo, "upsert_book_category")
            and self.service.repo.upsert_book_category.called
        )

    def test_store_book_empty_book(self):
        self.service.store_book("item-1", "2025-01", {})
        self.service.repo.upsert_book_summary.assert_called_once()


if __name__ == "__main__":
    unittest.main()
