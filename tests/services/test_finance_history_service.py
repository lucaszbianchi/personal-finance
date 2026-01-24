import unittest
from unittest.mock import MagicMock, patch
from services.finance_history_service import FinanceHistoryService
from models.finance_history import FinanceHistory


class TestFinanceHistoryService(unittest.TestCase):
    def setUp(self):
        # Mock repositories
        with patch("services.finance_history_service.FinanceHistoryRepository"), patch(
            "services.finance_history_service.TransactionRepository"
        ):
            self.service = FinanceHistoryService()

        self.mock_repo = MagicMock()
        self.mock_txn_repo = MagicMock()
        self.service.finance_history_repository = self.mock_repo
        self.service.transaction_repository = self.mock_txn_repo

    def test_update_meal_allowance_calls_repo(self):
        self.mock_repo.get_all.return_value = []
        self.service.update_meal_allowance(month="11/25", value=100)
        self.mock_repo.save_meal_allowance.assert_called_with("11/25", 100)

    def test_update_credit_card_info_calls_repo(self):
        self.mock_repo.get_all.return_value = []
        self.service.update_credit_card_info(
            month="11/25", current_bill=500, future_bill=600
        )
        self.mock_repo.save_credit_card_info.assert_called_with("11/25", 500, 600)

    def test_update_finance_history_net_worth_aggregates_investments(self):
        # Simula investimentos
        investment = MagicMock()
        investment.name = "Tesouro"
        investment.balance = 1000
        self.mock_txn_repo.get_investments.return_value = [investment]
        self.mock_txn_repo.get_bank_transactions.return_value = []
        self.mock_repo.get_all.return_value = []
        self.service.update_finance_history_net_worth("11/25", 500)
        self.mock_repo.save_net_worth.assert_called_with(
            "11/25", 500, {"Tesouro": 1000}
        )

    def test_update_cash_flow_calls_repo_and_risk(self):
        self.mock_repo.get_all.return_value = []
        self.service.update_cash_flow(month="11/25", income=2000, expenses=1500)
        self.mock_repo.save_cash_flow.assert_called_with("11/25", 2000, 1500)
        self.mock_repo.calculate_and_save_risk_management.assert_called_with("11/25")

    def test_get_net_worth_history_formats(self):
        history = [
            FinanceHistory(
                month="11/25",
                meal_allowance=100,
                credit_card_bill=200,
                credit_card_future_bill=300,
                total_cash=400,
                investments={"Tesouro": 500},
                expenses=600,
                income=700,
                risk_management=80,
            )
        ]
        self.mock_repo.get_all.return_value = history
        result = self.service.get_net_worth_history()
        self.assertIn("11/25", result)
        self.assertEqual(result["11/25"]["meal_allowance"], 100)
        self.assertEqual(result["11/25"]["credit_card_bill"], 200)
        self.assertEqual(result["11/25"]["credit_card_future_bill"], 300)
        self.assertEqual(result["11/25"]["total_cash"], 400)
        self.assertEqual(result["11/25"]["investments"], {"Tesouro": 500})
        self.assertEqual(result["11/25"]["expenses"], 600)
        self.assertEqual(result["11/25"]["income"], 700)
        self.assertEqual(result["11/25"]["risk_management"], 80)


if __name__ == "__main__":
    unittest.main()
