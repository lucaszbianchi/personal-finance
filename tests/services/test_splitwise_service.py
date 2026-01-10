import unittest
from unittest.mock import MagicMock
from services.splitwise_service import SplitwiseService


class TestSplitwiseService(unittest.TestCase):
    def setUp(self):
        self.mock_repo = MagicMock()
        self.service = SplitwiseService()
        self.service.splitwise_repository = self.mock_repo

    def test_get_all_splitwise(self):
        self.mock_repo.get_all_splitwise.return_value = [MagicMock(), MagicMock()]
        result = self.service.get_all_splitwise()
        self.mock_repo.get_all_splitwise.assert_called()
        self.assertEqual(len(result), 2)

    def test_update_splitwise_calls_repo(self):
        self.service.update_splitwise("sid", "catid", "txid")
        self.mock_repo.update_splitwise.assert_called_with("sid", "catid", "txid")

    def test_link_transaction_to_splitwise(self):
        txn = MagicMock()
        self.service.link_transaction_to_splitwise("sid", txn)
        self.mock_repo.set_transaction_to_splitwise.assert_called_with("sid", txn)

    def test_category_in_use(self):
        self.mock_repo.category_in_use.return_value = True
        result = self.service.category_in_use("catid")
        self.mock_repo.category_in_use.assert_called_with("catid")
        self.assertTrue(result)

    def test_get_unsettled_splitwise(self):
        self.mock_repo.get_unsettled_splitwise.return_value = [MagicMock()]
        result = self.service.get_unsettled_splitwise()
        self.mock_repo.get_unsettled_splitwise.assert_called()
        self.assertEqual(len(result), 1)


if __name__ == "__main__":
    unittest.main()
