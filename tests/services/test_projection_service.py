"""Tests for ProjectionService"""

import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from services.projection_service import ProjectionService


def _make_service():
    with patch("services.projection_service.AccountsSnapshotRepository"), \
         patch("services.projection_service.FinanceHistoryRepository"), \
         patch("services.projection_service.InvestmentRepository"), \
         patch("services.projection_service.IncomeSourcesRepository"), \
         patch("services.projection_service.RecurrentExpensesRepository"), \
         patch("services.projection_service.RecurrencesService"), \
         patch("services.projection_service.FinanceSummaryService"):
        svc = ProjectionService()
    svc.accounts_repo = MagicMock()
    svc.finance_history_repo = MagicMock()
    svc.finance_history_repo.get_all.return_value = []
    svc.investment_repo = MagicMock()
    svc.income_repo = MagicMock()
    svc.recurrences_repo = MagicMock()
    svc.recurrences_service = MagicMock()
    svc.finance_summary = MagicMock()
    return svc


def _make_investment(balance):
    inv = MagicMock()
    inv.balance = balance
    return inv


class TestGetCurrentNetWorth(unittest.TestCase):

    # ── _get_current_net_worth ──

    def test_sums_bank_snapshots_and_investments(self):
        svc = _make_service()
        svc.accounts_repo.get_latest_snapshot_by_type.return_value = [
            {"balance": 5000.0},
            {"balance": 3000.0},
        ]
        svc.investment_repo.get_investments.return_value = [
            _make_investment(10000.0),
            _make_investment(2500.0),
        ]
        result = svc._get_current_net_worth()
        self.assertAlmostEqual(result, 20500.0)

    def test_handles_none_balances(self):
        svc = _make_service()
        svc.accounts_repo.get_latest_snapshot_by_type.return_value = [
            {"balance": None},
            {"balance": 1000.0},
        ]
        svc.investment_repo.get_investments.return_value = [_make_investment(None)]
        result = svc._get_current_net_worth()
        self.assertAlmostEqual(result, 1000.0)


class TestGetMonthlyIncome(unittest.TestCase):

    # ── _get_monthly_income ──

    def test_only_monthly_frequency_summed(self):
        svc = _make_service()
        svc.income_repo.get_all.return_value = [
            {"description": "Salario", "amount": 5000.0, "frequency": "monthly"},
            {"description": "Freelance", "amount": 1000.0, "frequency": "monthly"},
            {"description": "Bonus", "amount": 3000.0, "frequency": "annual"},
        ]
        result = svc._get_monthly_income()
        self.assertAlmostEqual(result, 6000.0)

    def test_no_monthly_sources_returns_zero(self):
        svc = _make_service()
        svc.income_repo.get_all.return_value = [
            {"description": "Bonus", "amount": 3000.0, "frequency": "annual"},
        ]
        result = svc._get_monthly_income()
        self.assertAlmostEqual(result, 0.0)


class TestGetMonthlyFixedExpenses(unittest.TestCase):

    # ── _get_monthly_fixed_expenses ──

    def test_only_monthly_frequency_summed(self):
        svc = _make_service()
        svc.recurrences_repo.get_all.return_value = [
            {"description": "Aluguel", "amount": 3200.0, "frequency": "monthly"},
            {"description": "Academia", "amount": 100.0, "frequency": "monthly"},
            {"description": "IPTU", "amount": 600.0, "frequency": "annual"},
        ]
        result = svc._get_monthly_fixed_expenses()
        self.assertAlmostEqual(result, 3300.0)

    def test_no_monthly_recurrences_returns_zero(self):
        svc = _make_service()
        svc.recurrences_repo.get_all.return_value = []
        result = svc._get_monthly_fixed_expenses()
        self.assertAlmostEqual(result, 0.0)


class TestGetPendingInstallmentsByMonth(unittest.TestCase):

    # ── _get_pending_installments_by_month ──

    def test_projects_remaining_installments_correctly(self):
        svc = _make_service()
        # First future month has installments, second does not
        svc.recurrences_service.get_installments.side_effect = lambda month: (
            [{"amount": 500.0}, {"amount": 300.0}] if month == _next_month(1) else []
        )
        result = svc._get_pending_installments_by_month(3)
        self.assertIn(_next_month(1), result)
        self.assertAlmostEqual(result[_next_month(1)], 800.0)
        self.assertNotIn(_next_month(2), result)

    def test_installments_beyond_window_ignored(self):
        svc = _make_service()
        # Only 3 months projected, 4th+ ignored because get_installments is only called 3 times
        svc.recurrences_service.get_installments.return_value = [{"amount": 200.0}]
        result = svc._get_pending_installments_by_month(3)
        self.assertEqual(len(result), 3)

    def test_empty_installments_returns_empty_dict(self):
        svc = _make_service()
        svc.recurrences_service.get_installments.return_value = []
        result = svc._get_pending_installments_by_month(12)
        self.assertEqual(result, {})

    def test_months_with_zero_total_excluded(self):
        svc = _make_service()
        svc.recurrences_service.get_installments.return_value = [{"amount": 0.0}]
        result = svc._get_pending_installments_by_month(3)
        self.assertEqual(result, {})


class TestGetAvgVariableExpenses(unittest.TestCase):

    # ── _get_avg_variable_expenses ──

    def test_averages_variable_over_lookback_months(self):
        svc = _make_service()
        svc.recurrences_repo.get_all.return_value = [
            {"description": "Aluguel", "amount": 1000.0, "frequency": "monthly"},
        ]
        # total=3000, fixed=1000, installments=500 → variable=1500 each month
        svc.finance_summary.get_expenses.return_value = 3000.0
        svc.recurrences_service.get_installments.return_value = [{"amount": 500.0}]
        result = svc._get_avg_variable_expenses()
        self.assertAlmostEqual(result, 1500.0)

    def test_excludes_months_with_zero_or_negative_variable(self):
        svc = _make_service()
        svc.recurrences_repo.get_all.return_value = [
            {"description": "Aluguel", "amount": 2000.0, "frequency": "monthly"},
        ]
        # total=1500 < fixed=2000 → variable negative, excluded
        svc.finance_summary.get_expenses.return_value = 1500.0
        svc.recurrences_service.get_installments.return_value = []
        result = svc._get_avg_variable_expenses()
        self.assertAlmostEqual(result, 0.0)

    def test_returns_zero_when_no_data(self):
        svc = _make_service()
        svc.recurrences_repo.get_all.return_value = []
        svc.finance_summary.get_expenses.return_value = 0.0
        svc.recurrences_service.get_installments.return_value = []
        result = svc._get_avg_variable_expenses()
        self.assertAlmostEqual(result, 0.0)


class TestGetProjection(unittest.TestCase):

    # ── get_projection ──

    def _setup_service(self, current_nw=10000.0, income=3000.0, fixed=1000.0, variable=500.0):
        svc = _make_service()
        svc.accounts_repo.get_latest_snapshot_by_type.return_value = [{"balance": current_nw}]
        svc.investment_repo.get_investments.return_value = []
        svc.income_repo.get_all.return_value = [
            {"description": "Salario", "amount": income, "frequency": "monthly"},
        ]
        svc.recurrences_repo.get_all.return_value = [
            {"description": "Aluguel", "amount": fixed, "frequency": "monthly"},
        ]
        svc.recurrences_service.get_installments.return_value = []
        # variable avg = total(2500) - fixed(1000) - installments(0) = 1500... just mock directly
        svc.finance_summary.get_expenses.return_value = fixed + variable
        return svc

    def test_default_12_months_returned(self):
        svc = self._setup_service()
        result = svc.get_projection()
        self.assertEqual(len(result["projection"]), 12)

    def test_custom_months_param_respected(self):
        svc = self._setup_service()
        result = svc.get_projection(months=6)
        self.assertEqual(len(result["projection"]), 6)

    def test_net_worth_accumulates_correctly(self):
        # fixed=1000, variable avg derived from finance_summary returning 1500 total
        # so variable = 1500 - 1000 = 500, monthly delta = 3000 - (1000 + 500) = +1500
        svc = self._setup_service(current_nw=10000.0, income=3000.0, fixed=1000.0, variable=500.0)
        result = svc.get_projection(months=3)
        projection = result["projection"]
        self.assertAlmostEqual(result["current_net_worth"], 10000.0)
        self.assertAlmostEqual(projection[0]["net_worth"], 11500.0)
        self.assertAlmostEqual(projection[1]["net_worth"], 13000.0)
        self.assertAlmostEqual(projection[2]["net_worth"], 14500.0)

    def test_projection_entries_include_fixed_and_installments(self):
        svc = self._setup_service(current_nw=10000.0, income=5000.0, fixed=1500.0, variable=500.0)
        result = svc.get_projection(months=2)
        for entry in result["projection"]:
            self.assertIn("fixed", entry)
            self.assertIn("installments", entry)
            self.assertIn("variable", entry)
        self.assertAlmostEqual(result["projection"][0]["fixed"], 1500.0)
        self.assertAlmostEqual(result["projection"][0]["installments"], 0.0)

    def test_installments_reduce_net_worth_in_correct_month(self):
        svc = _make_service()
        svc.accounts_repo.get_latest_snapshot_by_type.return_value = [{"balance": 10000.0}]
        svc.investment_repo.get_investments.return_value = []
        svc.income_repo.get_all.return_value = [
            {"description": "Salario", "amount": 3000.0, "frequency": "monthly"},
        ]
        svc.recurrences_repo.get_all.return_value = []
        svc.finance_summary.get_expenses.return_value = 0.0

        next_month_key = _next_month(1)
        # get_installments used for both past lookback (returns []) and future projection
        svc.recurrences_service.get_installments.side_effect = lambda month: (
            [{"amount": 500.0}] if month == next_month_key else []
        )

        result = svc.get_projection(months=12)
        first_entry = next(e for e in result["projection"] if e["month"] == next_month_key)
        # expenses = fixed(0) + installments(500) + variable(0)
        self.assertAlmostEqual(first_entry["expenses"], 500.0)
        self.assertAlmostEqual(first_entry["installments"], 500.0)

    def test_current_net_worth_in_response(self):
        svc = self._setup_service(current_nw=50000.0)
        result = svc.get_projection(months=1)
        self.assertAlmostEqual(result["current_net_worth"], 50000.0)


class TestGetAssumptions(unittest.TestCase):

    # ── get_assumptions ──

    def test_returns_correct_structure(self):
        svc = _make_service()
        svc.income_repo.get_all.return_value = [
            {"description": "Salario", "amount": 5000.0, "frequency": "monthly"},
            {"description": "Bonus", "amount": 2000.0, "frequency": "annual"},
        ]
        svc.recurrences_repo.get_all.return_value = [
            {"description": "Aluguel", "amount": 3200.0, "frequency": "monthly"},
        ]
        svc.recurrences_service.get_installments.return_value = []
        svc.finance_summary.get_expenses.return_value = 0.0

        result = svc.get_assumptions()

        self.assertIn("income_sources", result)
        self.assertIn("fixed_expenses", result)
        self.assertIn("installments_by_month", result)
        self.assertIn("avg_variable_expenses", result)
        self.assertEqual(len(result["income_sources"]), 1)
        self.assertEqual(result["income_sources"][0]["description"], "Salario")
        self.assertEqual(len(result["fixed_expenses"]), 1)
        self.assertEqual(result["fixed_expenses"][0]["description"], "Aluguel")
        self.assertIsInstance(result["installments_by_month"], list)
        self.assertIsInstance(result["avg_variable_expenses"], float)


class TestGetActualHistory(unittest.TestCase):

    # ── _get_actual_history ──

    def _make_entry(self, month, income, expenses, total_cash=None, bank_expenses=None, credit_expenses=None):
        from models.finance_history import FinanceHistory
        return FinanceHistory(
            month=month, income=income, expenses=expenses,
            total_cash=total_cash, meal_allowance=None,
            credit_card_bill=None, credit_card_future_bill=None,
            investments=None, risk_management=None,
            bank_expenses=bank_expenses, credit_expenses=credit_expenses,
        )

    def test_returns_all_past_months(self):
        svc = _make_service()
        svc.finance_history_repo.get_all.return_value = [
            self._make_entry("2025-10", 5000.0, 3000.0),
            self._make_entry("2025-11", 5000.0, 3200.0),
        ]
        svc.recurrences_repo.get_all.return_value = []
        svc.recurrences_service.get_installments.return_value = []
        result = svc._get_actual_history()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["month"], "2025-10")
        self.assertEqual(result[1]["month"], "2025-11")

    def test_includes_current_month_excludes_future(self):
        svc = _make_service()
        current = date.today().strftime("%Y-%m")
        future = _next_month(1)
        svc.finance_history_repo.get_all.return_value = [
            self._make_entry(current, 5000.0, 3000.0),
            self._make_entry(future, 5000.0, 3000.0),
        ]
        svc.recurrences_repo.get_all.return_value = []
        svc.recurrences_service.get_installments.return_value = []
        result = svc._get_actual_history()
        # Current month is included (in-progress data); only future is excluded
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["month"], current)

    def test_skips_entries_with_no_income_and_no_expenses(self):
        svc = _make_service()
        svc.finance_history_repo.get_all.return_value = [
            self._make_entry("2025-10", None, None),
            self._make_entry("2025-11", 5000.0, 3000.0),
        ]
        svc.recurrences_repo.get_all.return_value = []
        svc.recurrences_service.get_installments.return_value = []
        result = svc._get_actual_history()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["month"], "2025-11")

    def test_expense_breakdown_sums_to_total(self):
        svc = _make_service()
        svc.finance_history_repo.get_all.return_value = [
            self._make_entry("2025-10", 5000.0, 4000.0),
        ]
        svc.recurrences_repo.get_all.return_value = [
            {"description": "Aluguel", "amount": 1500.0, "frequency": "monthly"},
        ]
        svc.recurrences_service.get_installments.return_value = [{"amount": 600.0}]
        result = svc._get_actual_history()
        entry = result[0]
        self.assertAlmostEqual(entry["fixed"] + entry["installments"] + entry["variable"], 4000.0)
        self.assertAlmostEqual(entry["fixed"], 1500.0)
        self.assertAlmostEqual(entry["installments"], 600.0)
        self.assertAlmostEqual(entry["variable"], 1900.0)

    def test_variable_never_negative_when_fixed_exceeds_expenses(self):
        svc = _make_service()
        svc.finance_history_repo.get_all.return_value = [
            self._make_entry("2025-10", 2000.0, 1000.0),
        ]
        svc.recurrences_repo.get_all.return_value = [
            {"description": "Aluguel", "amount": 3000.0, "frequency": "monthly"},
        ]
        svc.recurrences_service.get_installments.return_value = []
        result = svc._get_actual_history()
        entry = result[0]
        self.assertGreaterEqual(entry["variable"], 0.0)
        self.assertGreaterEqual(entry["installments"], 0.0)
        self.assertAlmostEqual(entry["fixed"] + entry["installments"] + entry["variable"], 1000.0)

    def test_net_worth_included_when_present(self):
        svc = _make_service()
        svc.finance_history_repo.get_all.return_value = [
            self._make_entry("2025-10", 5000.0, 3000.0, total_cash=45000.0),
        ]
        svc.recurrences_repo.get_all.return_value = []
        svc.recurrences_service.get_installments.return_value = []
        result = svc._get_actual_history()
        self.assertAlmostEqual(result[0]["net_worth"], 45000.0)

    def test_net_worth_is_none_when_not_set(self):
        svc = _make_service()
        svc.finance_history_repo.get_all.return_value = [
            self._make_entry("2025-10", 5000.0, 3000.0, total_cash=None),
        ]
        svc.recurrences_repo.get_all.return_value = []
        svc.recurrences_service.get_installments.return_value = []
        result = svc._get_actual_history()
        self.assertIsNone(result[0]["net_worth"])

    def test_empty_history_returns_empty_list(self):
        svc = _make_service()
        svc.finance_history_repo.get_all.return_value = []
        result = svc._get_actual_history()
        self.assertEqual(result, [])

    def _entry(self, month, income, expenses, bank_expenses=None, credit_expenses=0.0, net_worth=None):
        """Helper to build a history entry dict for backfill tests."""
        return {
            "month": month,
            "income": income,
            "expenses": expenses,
            "bank_expenses": bank_expenses if bank_expenses is not None else expenses,
            "credit_expenses": credit_expenses,
            "net_worth": net_worth,
        }

    def test_backfill_fills_missing_net_worth_backwards(self):
        # Formula: total_cash(M) = total_cash(M+1) - income(M+1) + bank_expenses(M+1) + credit_expenses(M)
        # M=Oct: bank=2500, credit=1500, income=5000
        # M=Nov: bank=2000, credit=1500, income=5000
        # M=Dec: nw=50000 (anchor), bank=3000, income=5000
        entries = [
            self._entry("2025-10", income=5000.0, expenses=4000.0, bank_expenses=2500.0, credit_expenses=1500.0),
            self._entry("2025-11", income=5000.0, expenses=3500.0, bank_expenses=2000.0, credit_expenses=1500.0),
            self._entry("2025-12", income=5000.0, expenses=4500.0, bank_expenses=3000.0, credit_expenses=0.0, net_worth=50000.0),
        ]
        result = ProjectionService._backfill_net_worth(entries)
        # Nov = Dec_nw(50000) - Dec_income(5000) + Dec_bank(3000) + Nov_credit(1500) = 49500
        self.assertAlmostEqual(result[1]["net_worth"], 49500.0)
        # Oct = Nov_nw(49500) - Nov_income(5000) + Nov_bank(2000) + Oct_credit(1500) = 48000
        self.assertAlmostEqual(result[0]["net_worth"], 48000.0)

    def test_backfill_no_anchor_returns_entries_unchanged(self):
        entries = [
            self._entry("2025-10", income=5000.0, expenses=4000.0),
            self._entry("2025-11", income=5000.0, expenses=3500.0),
        ]
        result = ProjectionService._backfill_net_worth(entries)
        self.assertIsNone(result[0]["net_worth"])
        self.assertIsNone(result[1]["net_worth"])

    def test_backfill_all_present_unchanged(self):
        entries = [
            self._entry("2025-10", income=5000.0, expenses=4000.0, net_worth=45000.0),
            self._entry("2025-11", income=5000.0, expenses=3500.0, net_worth=48500.0),
        ]
        result = ProjectionService._backfill_net_worth(entries)
        self.assertAlmostEqual(result[0]["net_worth"], 45000.0)
        self.assertAlmostEqual(result[1]["net_worth"], 48500.0)

    def test_backfill_anchor_in_middle_only_fills_before(self):
        # Anchor at index 1; index 0 should be filled, index 2 stays null
        # Nov_nw=48500, Nov_bank=2000, Nov_income=5000; Oct_credit=1500
        # Oct = 48500 - 5000 + 2000 + 1500 = 47000
        entries = [
            self._entry("2025-10", income=5000.0, expenses=4000.0, bank_expenses=2500.0, credit_expenses=1500.0),
            self._entry("2025-11", income=5000.0, expenses=3500.0, bank_expenses=2000.0, credit_expenses=1000.0, net_worth=48500.0),
            self._entry("2025-12", income=5000.0, expenses=4500.0, bank_expenses=3000.0, credit_expenses=0.0),
        ]
        result = ProjectionService._backfill_net_worth(entries)
        # Oct = Nov_nw(48500) - Nov_income(5000) + Nov_bank(2000) + Oct_credit(1500) = 47000
        self.assertAlmostEqual(result[0]["net_worth"], 47000.0)
        # Dec is after the anchor, stays null
        self.assertIsNone(result[2]["net_worth"])

    def test_get_projection_includes_history_key(self):
        svc = _make_service()
        svc.accounts_repo.get_latest_snapshot_by_type.return_value = [{"balance": 10000.0}]
        svc.investment_repo.get_investments.return_value = []
        svc.income_repo.get_all.return_value = []
        svc.recurrences_repo.get_all.return_value = []
        svc.recurrences_service.get_installments.return_value = []
        svc.finance_summary.get_expenses.return_value = 0.0
        result = svc.get_projection(months=1)
        self.assertIn("history", result)
        self.assertIsInstance(result["history"], list)


# ── helpers ──

def _next_month(delta: int) -> str:
    from dateutil.relativedelta import relativedelta
    today = date.today()
    return (today.replace(day=1) + relativedelta(months=delta)).strftime("%Y-%m")


if __name__ == "__main__":
    unittest.main()
