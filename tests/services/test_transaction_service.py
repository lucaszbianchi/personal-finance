import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch
from services.transaction_service import TransactionService


class TestTransactionService(unittest.TestCase):
    def setUp(self):
        with patch("services.transaction_service.TransactionRepository"), patch(
            "services.transaction_service.CategoryRepository"
        ), patch("services.transaction_service.PersonRepository"):
            self.service = TransactionService()

        self.mock_repo = MagicMock()
        self.mock_cat_repo = MagicMock()
        self.mock_person_repo = MagicMock()
        self.service.transaction_repository = self.mock_repo
        self.service.category_repository = self.mock_cat_repo
        self.service.person_repository = self.mock_person_repo

    def test_get_bank_transactions(self):
        self.mock_repo.get_bank_transactions.return_value = [MagicMock(), MagicMock()]
        result = self.service.get_bank_transactions()
        self.mock_repo.get_bank_transactions.assert_called()
        self.assertEqual(len(result), 2)

    def test_get_credit_transactions(self):
        self.mock_repo.get_credit_transactions.return_value = [MagicMock()]
        result = self.service.get_credit_transactions()
        self.mock_repo.get_credit_transactions.assert_called()
        self.assertEqual(len(result), 1)

    def test_get_investments(self):
        self.mock_repo.get_investments.return_value = [MagicMock()]
        result = self.service.get_investments()
        self.mock_repo.get_investments.assert_called()
        self.assertEqual(len(result), 1)

    def test_get_bank_transactions_by_period(self):
        mock_transaction = MagicMock(date="2025-01-15", category_id="cat1")
        self.mock_repo.get_bank_transactions.return_value = [mock_transaction]
        result = self.service.get_bank_transactions(
            start_date="2025-01-01", end_date="2025-01-31"
        )
        self.mock_repo.get_bank_transactions.assert_called_once()
        self.assertEqual(len(result), 1)

    def test_get_credit_transactions_by_period(self):
        mock_transaction = MagicMock(date="2025-01-15", category_id="cat1")
        self.mock_repo.get_credit_transactions.return_value = [mock_transaction]
        result = self.service.get_credit_transactions(
            start_date="2025-01-01", end_date="2025-01-31"
        )
        self.mock_repo.get_credit_transactions.assert_called_once()
        self.assertEqual(len(result), 1)

    def test_update_transaction_calls_repo(self):
        self.service.update_transaction("bank", "txid", "desc", "catid")
        self.mock_repo.update_bank_transaction.assert_called()

    def test_add_person_to_share_transaction(self):
        partners = {"p1": 50.0, "p2": 50.0}
        self.mock_repo.update_bank_transaction.return_value = True
        result = self.service.add_person_to_share_transaction("bank", "txid", partners)
        self.mock_repo.update_bank_transaction.assert_called_once()
        self.assertTrue(result)

    def test_settle_up_split(self):
        self.mock_repo.get_bank_transaction_by_id.return_value = MagicMock(
            payment_data={"payer": {"documentNumber": {"type": "CPF"}}}
        )
        self.service.settle_up_split("txid")
        self.mock_repo.get_bank_transaction_by_id.assert_called_with("txid")

    def test_add_category_to_settle_up_transaction(self):
        mock_transaction = MagicMock(split_info={"settle_up": True, "partner_id": "p1"})
        self.mock_repo.get_bank_transaction_by_id.return_value = mock_transaction
        self.mock_repo.update_bank_transaction.return_value = True
        result = self.service.add_category_to_settle_up_transaction("txid", "catid")
        self.mock_repo.update_bank_transaction.assert_called_once()
        self.assertTrue(result)

    def test_check_split_settle_up(self):
        mock_transaction = MagicMock(
            payment_data={
                "payer": {"documentNumber": {"type": "CPF", "value": "12345678901"}}
            },
            split_info={"settle_up": True, "partner_id": "p1"},
            transaction_id="txid",
            date=datetime.strptime("2025-01-01", "%Y-%m-%d"),
            amount=100.0,
            description="settle up",
            category_id="cat1",
        )
        self.mock_repo.get_bank_transactions.return_value = [mock_transaction]
        self.mock_person_repo.get_all_people.return_value = [
            MagicMock(id="p1", name="Partner 1")
        ]
        result = self.service.check_split_settle_up()
        self.assertIsInstance(result, list)
        self.mock_repo.get_bank_transactions.assert_called_once()


if __name__ == "__main__":
    unittest.main()
