import unittest
from unittest.mock import MagicMock, patch
from services.finance_history_service import FinanceHistoryService
from models.finance_history import FinanceHistory


class TestFinanceHistoryService(unittest.TestCase):
    def setUp(self):
        self.mock_settings = MagicMock()
        self.mock_settings.get_meal_allowance.return_value = 0.0

        # Mock repositories
        with patch("services.finance_history_service.FinanceHistoryRepository"), patch(
            "services.finance_history_service.TransactionRepository"
        ):
            self.service = FinanceHistoryService(settings_service=self.mock_settings)

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
            "11/25", 1500.0, {"Tesouro": 1000}
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

    def test_update_meal_allowance_uses_current_month_when_none(self):
        """Cobre o branch month=None (linha 18)"""
        self.mock_repo.get_all.return_value = []
        with patch("services.finance_history_service.datetime") as mock_dt:
            mock_dt.now.return_value.strftime.return_value = "2026-03"
            self.service.update_meal_allowance(value=200.0)
        self.mock_repo.save_meal_allowance.assert_called_once_with("2026-03", 200.0)

    def test_update_meal_allowance_prompts_when_value_none(self):
        """Cobre o branch value=None (linha 20)"""
        self.mock_repo.get_all.return_value = []
        with patch("builtins.input", return_value="150.0"):
            self.service.update_meal_allowance(month="2026-03")
        self.mock_repo.save_meal_allowance.assert_called_once_with("2026-03", 150.0)

    def test_update_credit_card_info_uses_current_month_when_none(self):
        """Cobre o branch month=None (linha 33)"""
        self.mock_repo.get_all.return_value = []
        with patch("services.finance_history_service.datetime") as mock_dt:
            mock_dt.now.return_value.strftime.return_value = "2026-03"
            self.service.update_credit_card_info(current_bill=400.0, future_bill=500.0)
        self.mock_repo.save_credit_card_info.assert_called_once_with("2026-03", 400.0, 500.0)

    def test_update_credit_card_info_prompts_when_bills_none(self):
        """Cobre os branches current_bill=None e future_bill=None (linhas 35-37)"""
        self.mock_repo.get_all.return_value = []
        with patch("builtins.input", side_effect=["400.0", "500.0"]):
            self.service.update_credit_card_info(month="2026-03")
        self.mock_repo.save_credit_card_info.assert_called_once_with("2026-03", 400.0, 500.0)

    def test_update_net_worth_aggregates_and_prompts(self):
        """Cobre update_net_worth (linhas 46-58): agrega investimentos e usa input()"""
        inv1 = MagicMock()
        inv1.name = "Tesouro"
        inv1.balance = 1000.0
        inv2 = MagicMock()
        inv2.name = "Tesouro"
        inv2.balance = 500.0
        inv3 = MagicMock()
        inv3.name = "CDB"
        inv3.balance = 2000.0
        self.mock_txn_repo.get_investments.return_value = [inv1, inv2, inv3]
        self.mock_repo.get_all.return_value = []

        with patch("services.finance_history_service.datetime") as mock_dt, \
             patch("builtins.input", return_value="300.0"):
            mock_dt.now.return_value.strftime.return_value = "2026-03"
            self.service.update_net_worth()

        expected_investments = {"Tesouro": 1500.0, "CDB": 2000.0}
        expected_total = 300.0 + 3500.0
        self.mock_repo.save_net_worth.assert_called_once_with(
            "2026-03", expected_total, expected_investments
        )

    def test_update_net_worth_no_investments(self):
        """Cobre update_net_worth sem investimentos"""
        self.mock_txn_repo.get_investments.return_value = []
        self.mock_repo.get_all.return_value = []

        with patch("services.finance_history_service.datetime") as mock_dt, \
             patch("builtins.input", return_value="1000.0"):
            mock_dt.now.return_value.strftime.return_value = "2026-03"
            self.service.update_net_worth()

        self.mock_repo.save_net_worth.assert_called_once_with("2026-03", 1000.0, {})

    def test_update_cash_flow_uses_current_month_when_none(self):
        """Cobre o branch month=None em update_cash_flow (linha 68)"""
        self.mock_repo.get_all.return_value = []
        with patch("services.finance_history_service.datetime") as mock_dt:
            mock_dt.now.return_value.strftime.return_value = "2026-03"
            self.service.update_cash_flow(income=3000.0, expenses=2000.0)
        self.mock_repo.save_cash_flow.assert_called_once_with("2026-03", 3000.0, 2000.0)

    def test_update_cash_flow_prompts_when_none(self):
        """Cobre os branches income=None e expenses=None (linhas 70-72)"""
        self.mock_repo.get_all.return_value = []
        with patch("builtins.input", side_effect=["3000.0", "2000.0"]):
            self.service.update_cash_flow(month="2026-03")
        self.mock_repo.save_cash_flow.assert_called_once_with("2026-03", 3000.0, 2000.0)
        self.mock_repo.calculate_and_save_risk_management.assert_called_once_with("2026-03")

    def test_update_finance_history_net_worth_aggregates_duplicate_names(self):
        """Cobre linhas 86-88: agrega investimentos com nomes duplicados"""
        inv1 = MagicMock()
        inv1.name = "CDB"
        inv1.balance = 1000.0
        inv2 = MagicMock()
        inv2.name = "CDB"
        inv2.balance = 500.0
        self.mock_txn_repo.get_investments.return_value = [inv1, inv2]
        self.mock_repo.get_all.return_value = []

        self.service.update_finance_history_net_worth("2026-03", 200.0)

        self.mock_repo.save_net_worth.assert_called_once_with(
            "2026-03", 1700.0, {"CDB": 1500.0}
        )

    def test_update_all_calls_all_repos(self):
        """Cobre update_all (linhas 96-128): todos os prompts e chamadas de repositório"""
        inv = MagicMock()
        inv.name = "Tesouro"
        inv.balance = 2000.0
        self.mock_txn_repo.get_investments.return_value = [inv]
        self.mock_repo.get_all.return_value = []

        inputs = ["100.0", "400.0", "500.0", "1000.0", "3000.0", "2000.0"]
        with patch("services.finance_history_service.datetime") as mock_dt, \
             patch("builtins.input", side_effect=inputs):
            mock_dt.now.return_value.strftime.return_value = "2026-03"
            result = self.service.update_all()

        self.mock_repo.save_meal_allowance.assert_called_once_with("2026-03", 100.0)
        self.mock_repo.save_credit_card_info.assert_called_once_with("2026-03", 400.0, 500.0)
        self.mock_repo.save_net_worth.assert_called_once_with(
            "2026-03", 3000.0, {"Tesouro": 2000.0}
        )
        self.mock_repo.save_cash_flow.assert_called_once_with("2026-03", 3000.0, 2000.0)
        self.mock_repo.calculate_and_save_risk_management.assert_called_once_with("2026-03")
        self.assertIsInstance(result, dict)

    def test_update_all_no_investments(self):
        """Cobre update_all sem investimentos"""
        self.mock_txn_repo.get_investments.return_value = []
        self.mock_repo.get_all.return_value = []

        inputs = ["100.0", "400.0", "500.0", "800.0", "3000.0", "2000.0"]
        with patch("services.finance_history_service.datetime") as mock_dt, \
             patch("builtins.input", side_effect=inputs):
            mock_dt.now.return_value.strftime.return_value = "2026-03"
            self.service.update_all()

        self.mock_repo.save_net_worth.assert_called_once_with("2026-03", 800.0, {})


if __name__ == "__main__":
    unittest.main()
