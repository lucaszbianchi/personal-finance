import unittest
from unittest.mock import MagicMock, patch
from services.transaction_service import TransactionService
from models.transaction import BankTransaction, CreditTransaction, Investment


class TestTransactionService(unittest.TestCase):
    def setUp(self):
        self.mock_repo = MagicMock()
        self.mock_cat_repo = MagicMock()
        self.mock_person_repo = MagicMock()
        self.service = TransactionService()
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
        self.mock_repo.get_bank_transactions_by_period.return_value = [MagicMock()]
        result = self.service.get_bank_transactions_by_period(
            "2025-01-01", "2025-01-31"
        )
        self.mock_repo.get_bank_transactions_by_period.assert_called_with(
            "2025-01-01", "2025-01-31"
        )
        self.assertEqual(len(result), 1)

    def test_get_credit_transactions_by_period(self):
        self.mock_repo.get_credit_transactions_by_period.return_value = [MagicMock()]
        result = self.service.get_credit_transactions_by_period(
            "2025-01-01", "2025-01-31"
        )
        self.mock_repo.get_credit_transactions_by_period.assert_called_with(
            "2025-01-01", "2025-01-31"
        )
        self.assertEqual(len(result), 1)

    def test_update_transaction_calls_repo(self):
        self.service.update_transaction("bank", "txid", "desc", "catid")
        self.mock_repo.update_bank_transaction.assert_called()

    def test_add_person_to_share_transaction(self):
        self.service.add_person_to_share_transaction("bank", "txid", [{"id": "p1"}])
        self.mock_person_repo.update_person_split_info.assert_called()

    def test_settle_up_split(self):
        self.mock_repo.get_bank_transaction_by_id.return_value = MagicMock(
            payment_data={"payer": {"documentNumber": {"type": "CPF"}}}
        )
        self.service.settle_up_split("txid")
        self.mock_repo.get_bank_transaction_by_id.assert_called_with("txid")

    def test_add_category_to_settle_up_transaction(self):
        self.mock_repo.update_bank_transaction.return_value = True
        result = self.service.add_category_to_settle_up_transaction("txid", "catid")
        self.mock_repo.update_bank_transaction.assert_called_with(
            "txid", None, "catid", None
        )
        self.assertTrue(result)

    def test_check_split_settle_up(self):
        self.mock_repo.get_unlinked_transactions.return_value = [
            MagicMock(payment_data={"payer": {"documentNumber": {"type": "CPF"}}})
        ]
        self.service.check_split_settle_up()
        self.mock_repo.get_unlinked_transactions.assert_called()


if __name__ == "__main__":
    unittest.main()
