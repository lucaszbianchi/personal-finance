import unittest
from unittest.mock import MagicMock, patch
from services.finance_history_service import FinanceHistoryService
from models.finance_history import FinanceHistory


class TestFinanceHistoryService(unittest.TestCase):
    def setUp(self):
        self.mock_settings = MagicMock()
        self.mock_settings.get_meal_allowance.return_value = 0.0

        # Mock repositories
        with patch("services.finance_history_service.FinanceHistoryRepository"), \
             patch("services.finance_history_service.TransactionRepository"), \
             patch("services.finance_history_service.AccountsSnapshotRepository"), \
             patch("services.finance_history_service.InvestmentRepository"):
            self.service = FinanceHistoryService(settings_service=self.mock_settings)

        self.mock_repo = MagicMock()
        self.mock_txn_repo = MagicMock()
        self.mock_snapshot_repo = MagicMock()
        self.mock_investment_repo = MagicMock()
        self.service.finance_history_repository = self.mock_repo
        self.service.transaction_repository = self.mock_txn_repo
        self.service.accounts_snapshot_repo = self.mock_snapshot_repo
        self.service.investment_repo = self.mock_investment_repo
        # Default: no snapshots (so snapshot-based branches are skipped)
        self.mock_snapshot_repo.get_snapshot_for_month.return_value = []
        self.mock_repo.get_by_month.return_value = None

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


    def _patch_finance_summary(self, get_income=5000.0, get_expenses=3000.0, get_bank_expenses=2000.0, get_credit_expenses=1000.0):
        """Retorna (mock_inst, patcher) para FinanceSummaryService importado localmente."""
        import services.finance_summary_service as fss_mod
        mock_inst = MagicMock()
        mock_inst.get_income.return_value = get_income
        mock_inst.get_expenses.return_value = get_expenses
        mock_inst.get_bank_expenses.return_value = get_bank_expenses
        mock_inst.get_credit_expenses.return_value = get_credit_expenses
        patcher = patch.object(fss_mod, "FinanceSummaryService", return_value=mock_inst)
        return mock_inst, patcher

    def test_update_finance_history_from_sync_calls_all_steps(self):
        """update_finance_history_from_sync popula todos os campos (sem snapshot disponivel, usa bills fallback)."""
        mock_bill_repo = MagicMock()
        mock_bill_repo.get_current_and_future_bill.return_value = (800.0, 950.0)
        self.service.bill_repository = mock_bill_repo
        # No snapshots → falls back to bills for future_bill and skips total_cash
        self.mock_snapshot_repo.get_snapshot_for_month.return_value = []

        mock_inst, patcher = self._patch_finance_summary(5000.0, 3000.0, 2000.0, 1000.0)
        with patcher:
            self.service.update_finance_history_from_sync("2026-03")

        self.mock_repo.save_cash_flow.assert_called_once_with("2026-03", 5000.0, 3000.0, 2000.0, 1000.0)
        # current_bill call + fallback future_bill call
        self.assertEqual(mock_bill_repo.get_current_and_future_bill.call_count, 2)
        self.mock_repo.save_credit_card_bills.assert_called_once_with("2026-03", 800.0, 950.0)
        self.mock_repo.calculate_and_save_risk_management.assert_called_once_with("2026-03")

    def test_update_finance_history_from_sync_uses_credit_snapshot_for_future_bill(self):
        """credit_card_future_bill = credit_limit - available_credit quando snapshot disponivel."""
        mock_bill_repo = MagicMock()
        mock_bill_repo.get_current_and_future_bill.return_value = (800.0, 999.0)
        self.service.bill_repository = mock_bill_repo

        # Credit snapshot: limit=5000, available=3200 → outstanding=1800
        self.mock_snapshot_repo.get_snapshot_for_month.side_effect = lambda account_type, month: (
            [{"credit_limit": 5000.0, "available_credit": 3200.0}]
            if account_type == "CREDIT" else []
        )

        mock_inst, patcher = self._patch_finance_summary(5000.0, 3000.0, 2000.0, 1000.0)
        with patcher:
            self.service.update_finance_history_from_sync("2026-03")

        # future_bill = 5000 - 3200 = 1800, NOT 999 from bills
        self.mock_repo.save_credit_card_bills.assert_called_once_with("2026-03", 800.0, 1800.0)

    def test_update_finance_history_from_sync_saves_total_cash_from_bank_snapshot(self):
        """total_cash é computado a partir do snapshot bancário quando disponivel."""
        mock_bill_repo = MagicMock()
        mock_bill_repo.get_current_and_future_bill.return_value = (0.0, 0.0)
        self.service.bill_repository = mock_bill_repo
        # Entry has no total_cash yet
        self.mock_repo.get_by_month.return_value = None

        # Bank snapshot: balance = 10000
        self.mock_snapshot_repo.get_snapshot_for_month.side_effect = lambda account_type, month: (
            [{"balance": 10000.0}] if account_type == "BANK" else []
        )
        # Investments: 2000
        inv = MagicMock()
        inv.name = "CDB"
        inv.balance = 2000.0
        self.mock_investment_repo.get_investments.return_value = [inv]

        mock_inst, patcher = self._patch_finance_summary(5000.0, 3000.0, 2000.0, 1000.0)
        with patcher:
            self.service.update_finance_history_from_sync("2026-03")

        # total_cash = 10000 + 2000 = 12000
        self.mock_repo.save_net_worth.assert_called_once_with("2026-03", 12000.0, {"CDB": 2000.0})

    def test_update_finance_history_from_sync_skips_total_cash_if_already_set(self):
        """total_cash nao e sobrescrito se ja estiver definido."""
        mock_bill_repo = MagicMock()
        mock_bill_repo.get_current_and_future_bill.return_value = (0.0, 0.0)
        self.service.bill_repository = mock_bill_repo

        existing = MagicMock()
        existing.total_cash = 50000.0
        self.mock_repo.get_by_month.return_value = existing

        mock_inst, patcher = self._patch_finance_summary(5000.0, 3000.0, 2000.0, 1000.0)
        with patcher:
            self.service.update_finance_history_from_sync("2026-03")

        self.mock_repo.save_net_worth.assert_not_called()

    def test_update_finance_history_from_sync_december(self):
        """update_finance_history_from_sync trata dezembro corretamente (end_date = 2027-01-01)."""
        mock_bill_repo = MagicMock()
        mock_bill_repo.get_current_and_future_bill.return_value = (0.0, 0.0)
        self.service.bill_repository = mock_bill_repo

        mock_inst, patcher = self._patch_finance_summary(0.0, 0.0, 0.0, 0.0)
        with patcher:
            self.service.update_finance_history_from_sync("2026-12")

        mock_inst.get_income.assert_called_once_with("2026-12-01", "2027-01-01")
        mock_inst.get_expenses.assert_called_once_with("2026-12-01", "2027-01-01")


    # ── rebuild_all_months ──

    def test_rebuild_processes_all_distinct_months(self):
        months = ["2025-11", "2025-12", "2026-01"]
        self.mock_txn_repo.get_distinct_months.return_value = months
        self.mock_repo.get_all.return_value = []
        with patch.object(self.service, "update_finance_history_from_sync") as mock_sync:
            result = self.service.rebuild_all_months()
        self.assertEqual(result["months_processed"], 3)
        self.assertEqual(result["months"], months)
        self.assertEqual(mock_sync.call_count, 3)
        mock_sync.assert_any_call("2025-11")
        mock_sync.assert_any_call("2025-12")
        mock_sync.assert_any_call("2026-01")

    def test_rebuild_is_idempotent(self):
        months = ["2026-01", "2026-02"]
        self.mock_txn_repo.get_distinct_months.return_value = months
        self.mock_repo.get_all.return_value = []
        with patch.object(self.service, "update_finance_history_from_sync"):
            result1 = self.service.rebuild_all_months()
            result2 = self.service.rebuild_all_months()
        self.assertEqual(result1["months_processed"], 2)
        self.assertEqual(result2["months_processed"], 2)

    def test_rebuild_empty_db_returns_zero(self):
        self.mock_txn_repo.get_distinct_months.return_value = []
        with patch.object(self.service, "update_finance_history_from_sync") as mock_sync:
            result = self.service.rebuild_all_months()
        self.assertEqual(result, {"months_processed": 0, "months": []})
        mock_sync.assert_not_called()

    # ── _backfill_total_cash ──

    def _make_history_entry(self, month, income=None, expenses=None, bank_expenses=None, credit_expenses=None, total_cash=None):
        from models.finance_history import FinanceHistory
        return FinanceHistory(
            month=month, income=income, expenses=expenses,
            bank_expenses=bank_expenses, credit_expenses=credit_expenses,
            total_cash=total_cash, meal_allowance=None,
            credit_card_bill=None, credit_card_future_bill=None,
            investments=None, risk_management=None,
        )

    def test_backfill_total_cash_fills_backwards(self):
        """total_cash(fev) = total_cash(mar) - income(mar) + bank_expenses(mar) + credit_expenses(fev)"""
        months = ["2026-01", "2026-02", "2026-03"]
        self.mock_repo.get_all.return_value = [
            self._make_history_entry("2026-01", income=5000, expenses=4000, bank_expenses=2000, credit_expenses=2000),
            self._make_history_entry("2026-02", income=5000, expenses=3500, bank_expenses=2000, credit_expenses=1500),
            self._make_history_entry("2026-03", income=5000, expenses=4500, bank_expenses=3000, credit_expenses=1500, total_cash=50000),
        ]
        self.service._backfill_total_cash(months)
        # Feb = Mar_tc(50000) - Mar_income(5000) + Mar_bank(3000) + Feb_credit(1500) = 49500
        self.mock_repo.save_total_cash.assert_any_call("2026-02", 49500.0)
        # Jan = Feb_tc(49500) - Feb_income(5000) + Feb_bank(2000) + Jan_credit(2000) = 48500
        self.mock_repo.save_total_cash.assert_any_call("2026-01", 48500.0)

    def test_backfill_total_cash_no_anchor_does_nothing(self):
        months = ["2026-01", "2026-02"]
        self.mock_repo.get_all.return_value = [
            self._make_history_entry("2026-01", income=5000, expenses=4000),
            self._make_history_entry("2026-02", income=5000, expenses=3500),
        ]
        self.service._backfill_total_cash(months)
        self.mock_repo.save_total_cash.assert_not_called()

    def test_backfill_total_cash_skips_existing(self):
        """Months that already have total_cash are the anchor, not overwritten."""
        months = ["2026-01", "2026-02"]
        self.mock_repo.get_all.return_value = [
            self._make_history_entry("2026-01", income=5000, bank_expenses=2000, credit_expenses=500),
            self._make_history_entry("2026-02", income=5000, bank_expenses=2500, credit_expenses=1000, total_cash=40000),
        ]
        self.service._backfill_total_cash(months)
        # Jan = 40000 - 5000 + 2500 + 500 = 38000
        self.mock_repo.save_total_cash.assert_called_once_with("2026-01", 38000.0)


class TestFirstDayOfNextMonth(unittest.TestCase):
    def test_regular_month(self):
        from services.finance_history_service import _first_day_of_next_month
        self.assertEqual(_first_day_of_next_month("2026-03"), "2026-04-01")

    def test_december_wraps(self):
        from services.finance_history_service import _first_day_of_next_month
        self.assertEqual(_first_day_of_next_month("2026-12"), "2027-01-01")


if __name__ == "__main__":
    unittest.main()
