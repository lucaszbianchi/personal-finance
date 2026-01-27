import unittest
from unittest.mock import MagicMock, patch
from services.category_service import CategoryService


class TestCategoryService(unittest.TestCase):
    def setUp(self):
        with patch("services.category_service.CategoryRepository"), patch(
            "services.category_service.TransactionRepository"
        ), patch("services.category_service.SplitwiseRepository"):
            self.service = CategoryService()

        self.mock_repo = MagicMock()
        self.mock_transaction_repo = MagicMock()
        self.mock_splitwise_repo = MagicMock()
        self.service.category_repo = self.mock_repo
        self.service.transaction_repo = self.mock_transaction_repo
        self.service.splitwise_repo = self.mock_splitwise_repo

    def test_get_all_categories(self):
        self.mock_repo.get_all_categories.return_value = [
            MagicMock(name="cat1"),
            MagicMock(name="cat2"),
        ]
        result = self.service.get_all_categories()
        self.mock_repo.get_all_categories.assert_called()
        self.assertEqual(len(result), 2)

    def test_create_category_calls_repo(self):
        self.mock_repo.get_category_by_name.return_value = None
        self.service.create_category("Test")
        self.mock_repo.create_category.assert_called_with("Test")

    def test_edit_category_calls_repo(self):
        self.service.edit_category("Old", "New")
        self.mock_repo.update_category.assert_called_with("Old", "New")

    def test_delete_category_calls_repo(self):
        mock_category = MagicMock()
        mock_category.id = "123"  # Set a proper string ID
        self.mock_repo.get_category_by_name.return_value = mock_category
        self.mock_transaction_repo.category_in_use.return_value = False
        self.mock_splitwise_repo.category_in_use.return_value = False
        self.mock_repo.delete_category.return_value = True

        result = self.service.delete_category("category")

        self.mock_repo.get_category_by_name.assert_called_with("category")
        self.mock_transaction_repo.category_in_use.assert_called_with("123")
        self.mock_splitwise_repo.category_in_use.assert_called_with("123")
        self.mock_repo.delete_category.assert_called_with("123")
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
