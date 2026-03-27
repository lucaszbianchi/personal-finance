"""Tests for ProjectionService"""

import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from services.projection_service import ProjectionService


def _make_service():
    with patch("services.projection_service.AccountsSnapshotRepository"), \
         patch("services.projection_service.CategoryRepository"), \
         patch("services.projection_service.FinanceHistoryRepository"), \
         patch("services.projection_service.InvestmentRepository"), \
         patch("services.projection_service.IncomeSourcesRepository"), \
         patch("services.projection_service.RecurrentExpensesRepository"), \
         patch("services.projection_service.TransactionRepository"), \
         patch("services.projection_service.RecurrencesService"), \
         patch("services.projection_service.FinanceSummaryService"), \
         patch("services.projection_service.SettingsService"), \
         patch("services.projection_service.TransactionService"):
        svc = ProjectionService()
    svc.accounts_repo = MagicMock()
    svc.category_repo = MagicMock()
    svc.category_repo.get_necessary_category_ids.return_value = set()
    svc.category_repo.get_optional_category_ids.return_value = set()
    svc.finance_history_repo = MagicMock()
    svc.finance_history_repo.get_all.return_value = []
    svc.investment_repo = MagicMock()
    svc.income_repo = MagicMock()
    svc.recurrences_repo = MagicMock()
    svc.transaction_repo = MagicMock()
    svc.transaction_repo.get_bank_net_by_month.return_value = {}
    svc.recurrences_service = MagicMock()
    svc.recurrences_service.get_installments.return_value = []
    svc.recurrences_service.get_fixed_expenses_for_month.return_value = []
    svc.finance_summary = MagicMock()
    svc.settings_service = MagicMock()
    svc.settings_service.get_optional_expenses_target.return_value = 0.0
    svc.transaction_service = MagicMock()
    svc.transaction_service.get_bank_transactions.return_value = []
    svc.transaction_service.get_credit_transactions.return_value = []
    return svc


def _make_investment(balance):
    inv = MagicMock()
    inv.balance = balance
    return inv


def _make_transaction(transaction_type, amount, category_id=None, excluded=False):
    t = MagicMock()
    t.transaction_type = transaction_type
    t.amount = amount
    t.category_id = category_id
    t.excluded = excluded
    return t


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


class TestGetExpenseSplitForMonth(unittest.TestCase):

    # ── _get_expense_split_for_month ──

    def test_splits_necessary_and_optional_transactions(self):
        svc = _make_service()
        necessary_id = "cat_food"
        optional_id = "cat_clothes"
        svc.category_repo.get_necessary_category_ids.return_value = {necessary_id}
        svc.category_repo.get_optional_category_ids.return_value = {optional_id}
        svc.transaction_service.get_bank_transactions.return_value = [
            _make_transaction("bank", -500.0, category_id=necessary_id),
            _make_transaction("bank", -200.0, category_id=optional_id),
        ]
        svc.transaction_service.get_credit_transactions.return_value = []
        necessary, optional = svc._get_expense_split_for_month(
            "2025-10", {necessary_id}, {optional_id}
        )
        self.assertAlmostEqual(necessary, 500.0)
        self.assertAlmostEqual(optional, 200.0)

    def test_deducts_fixed_recurrences_per_category(self):
        svc = _make_service()
        necessary_id = "cat_rent"
        optional_id = "cat_leisure"
        svc.recurrences_service.get_fixed_expenses_for_month.return_value = [
            {"description": "Aluguel", "amount": 1000.0, "category_id": necessary_id},
            {"description": "Netflix", "amount": 50.0, "category_id": optional_id},
        ]
        svc.recurrences_service.get_installments.return_value = []
        svc.transaction_service.get_bank_transactions.return_value = [
            _make_transaction("bank", -1500.0, category_id=necessary_id),
            _make_transaction("bank", -80.0, category_id=optional_id),
        ]
        svc.transaction_service.get_credit_transactions.return_value = []
        necessary, optional = svc._get_expense_split_for_month(
            "2025-10", {necessary_id}, {optional_id}
        )
        # necessary_gross(1500) - fixed(1000) - installments(0) = 500
        self.assertAlmostEqual(necessary, 500.0)
        # optional_gross(80) - fixed(50) - installments(0) = 30
        self.assertAlmostEqual(optional, 30.0)

    def test_unclassified_transactions_ignored(self):
        svc = _make_service()
        necessary_id = "cat_food"
        svc.transaction_service.get_bank_transactions.return_value = [
            _make_transaction("bank", -500.0, category_id=necessary_id),
            _make_transaction("bank", -300.0, category_id="cat_uncategorized"),
        ]
        svc.transaction_service.get_credit_transactions.return_value = []
        necessary, optional = svc._get_expense_split_for_month(
            "2025-10", {necessary_id}, set()
        )
        # Only necessary is counted; uncategorized is ignored
        self.assertAlmostEqual(necessary, 500.0)
        self.assertAlmostEqual(optional, 0.0)

    def test_result_never_negative(self):
        svc = _make_service()
        necessary_id = "cat_rent"
        svc.recurrences_service.get_fixed_expenses_for_month.return_value = [
            {"description": "Aluguel", "amount": 2000.0, "category_id": necessary_id},
        ]
        svc.transaction_service.get_bank_transactions.return_value = [
            _make_transaction("bank", -1000.0, category_id=necessary_id),
        ]
        svc.transaction_service.get_credit_transactions.return_value = []
        necessary, optional = svc._get_expense_split_for_month(
            "2025-10", {necessary_id}, set()
        )
        # necessary_gross(1000) - fixed(2000) = -1000 → clamped to 0
        self.assertAlmostEqual(necessary, 0.0)
        self.assertAlmostEqual(optional, 0.0)

    def test_excluded_transactions_ignored(self):
        svc = _make_service()
        necessary_id = "cat_food"
        svc.transaction_service.get_bank_transactions.return_value = [
            _make_transaction("bank", -500.0, category_id=necessary_id, excluded=True),
        ]
        svc.transaction_service.get_credit_transactions.return_value = []
        necessary, optional = svc._get_expense_split_for_month(
            "2025-10", {necessary_id}, set()
        )
        self.assertAlmostEqual(necessary, 0.0)


class TestGetAvgNecessaryExpenses(unittest.TestCase):

    # ── _get_avg_necessary_expenses ──

    def test_averages_necessary_transactions_only(self):
        svc = _make_service()
        necessary_id = "cat_food"
        optional_id = "cat_clothes"
        svc.category_repo.get_necessary_category_ids.return_value = {necessary_id}
        svc.category_repo.get_optional_category_ids.return_value = {optional_id}
        # Necessary bank expense (-500) + optional bank expense (-200): only necessary counted
        svc.transaction_service.get_bank_transactions.return_value = [
            _make_transaction("bank", -500.0, category_id=necessary_id),
            _make_transaction("bank", -200.0, category_id=optional_id),
        ]
        svc.transaction_service.get_credit_transactions.return_value = []
        result = svc._get_avg_necessary_expenses()
        self.assertAlmostEqual(result, 500.0)

    def test_deducts_necessary_fixed_recurrences(self):
        svc = _make_service()
        necessary_id = "cat_rent"
        svc.category_repo.get_necessary_category_ids.return_value = {necessary_id}
        # Fixed recurrence in necessary category
        svc.recurrences_service.get_fixed_expenses_for_month.return_value = [
            {"description": "Aluguel", "amount": 1000.0, "category_id": necessary_id},
        ]
        svc.transaction_service.get_bank_transactions.return_value = [
            _make_transaction("bank", -1500.0, category_id=necessary_id),
        ]
        svc.transaction_service.get_credit_transactions.return_value = []
        # necessary_expenses(1500) - necessary_fixed(1000) - installments(0) = 500
        result = svc._get_avg_necessary_expenses()
        self.assertAlmostEqual(result, 500.0)

    def test_excludes_months_with_zero_or_negative_result(self):
        svc = _make_service()
        necessary_id = "cat_food"
        svc.category_repo.get_necessary_category_ids.return_value = {necessary_id}
        svc.recurrences_service.get_fixed_expenses_for_month.return_value = [
            {"description": "Conta", "amount": 2000.0, "category_id": necessary_id},
        ]
        # necessary_expenses(1500) < necessary_fixed(2000) → negative → excluded
        svc.transaction_service.get_bank_transactions.return_value = [
            _make_transaction("bank", -1500.0, category_id=necessary_id),
        ]
        svc.transaction_service.get_credit_transactions.return_value = []
        result = svc._get_avg_necessary_expenses()
        self.assertAlmostEqual(result, 0.0)

    def test_returns_zero_when_no_necessary_categories(self):
        svc = _make_service()
        svc.category_repo.get_necessary_category_ids.return_value = set()
        svc.transaction_service.get_bank_transactions.return_value = [
            _make_transaction("bank", -1000.0, category_id="cat_optional"),
        ]
        svc.transaction_service.get_credit_transactions.return_value = []
        result = svc._get_avg_necessary_expenses()
        self.assertAlmostEqual(result, 0.0)

    def test_credit_transactions_in_necessary_categories_counted(self):
        svc = _make_service()
        necessary_id = "cat_food"
        svc.category_repo.get_necessary_category_ids.return_value = {necessary_id}
        svc.transaction_service.get_bank_transactions.return_value = []
        # Credit transaction with positive amount = expense
        svc.transaction_service.get_credit_transactions.return_value = [
            _make_transaction("credit", 300.0, category_id=necessary_id),
        ]
        result = svc._get_avg_necessary_expenses()
        self.assertAlmostEqual(result, 300.0)


class TestGetAvgOptionalExpensesHistorical(unittest.TestCase):

    # ── _get_avg_optional_expenses_historical ──

    def test_only_optional_transactions_counted(self):
        svc = _make_service()
        necessary_id = "cat_food"
        optional_id = "cat_clothes"
        svc.category_repo.get_necessary_category_ids.return_value = {necessary_id}
        svc.category_repo.get_optional_category_ids.return_value = {optional_id}
        svc.transaction_service.get_bank_transactions.return_value = [
            _make_transaction("bank", -500.0, category_id=necessary_id),
            _make_transaction("bank", -200.0, category_id=optional_id),
        ]
        svc.transaction_service.get_credit_transactions.return_value = []
        result = svc._get_avg_optional_expenses_historical()
        # Only optional_id transactions counted
        self.assertAlmostEqual(result, 200.0)

    def test_returns_zero_when_no_optional_categories(self):
        svc = _make_service()
        svc.category_repo.get_necessary_category_ids.return_value = set()
        svc.category_repo.get_optional_category_ids.return_value = set()
        svc.transaction_service.get_bank_transactions.return_value = [
            _make_transaction("bank", -1000.0, category_id="cat_unclassified"),
        ]
        svc.transaction_service.get_credit_transactions.return_value = []
        result = svc._get_avg_optional_expenses_historical()
        self.assertAlmostEqual(result, 0.0)

    def test_excludes_months_with_zero_optional(self):
        svc = _make_service()
        svc.category_repo.get_necessary_category_ids.return_value = set()
        svc.category_repo.get_optional_category_ids.return_value = {"cat_optional"}
        # Transactions in unclassified category only → optional_expenses = 0 for all months
        svc.transaction_service.get_bank_transactions.return_value = [
            _make_transaction("bank", -1000.0, category_id="cat_unclassified"),
        ]
        svc.transaction_service.get_credit_transactions.return_value = []
        result = svc._get_avg_optional_expenses_historical()
        self.assertAlmostEqual(result, 0.0)


class TestGetProjection(unittest.TestCase):

    # ── get_projection ──

    def _setup_service(self, current_nw=10000.0, income=3000.0, fixed=1000.0, necessary=500.0, optional_target=0.0):
        svc = _make_service()
        svc.accounts_repo.get_latest_snapshot_by_type.return_value = [{"balance": current_nw}]
        svc.investment_repo.get_investments.return_value = []
        svc.income_repo.get_all.return_value = [
            {"description": "Salario", "amount": income, "frequency": "monthly"},
        ]
        svc.recurrences_service.get_fixed_expenses_for_month.return_value = [
            {"description": "Aluguel", "amount": fixed, "category_id": None},
        ]
        svc.recurrences_service.get_installments.return_value = []
        svc._get_avg_necessary_expenses = MagicMock(return_value=necessary)
        svc.settings_service.get_optional_expenses_target.return_value = optional_target
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
        # income=3000, fixed=1000, necessary=500, optional_target=0 → delta = 3000 - 1500 = +1500
        svc = self._setup_service(current_nw=10000.0, income=3000.0, fixed=1000.0, necessary=500.0)
        result = svc.get_projection(months=3)
        projection = result["projection"]
        self.assertAlmostEqual(result["current_net_worth"], 10000.0)
        self.assertAlmostEqual(projection[0]["net_worth"], 11500.0)
        self.assertAlmostEqual(projection[1]["net_worth"], 13000.0)
        self.assertAlmostEqual(projection[2]["net_worth"], 14500.0)

    def test_projection_entries_include_required_fields(self):
        svc = self._setup_service(current_nw=10000.0, income=5000.0, fixed=1500.0, necessary=500.0)
        result = svc.get_projection(months=2)
        for entry in result["projection"]:
            self.assertIn("fixed", entry)
            self.assertIn("installments", entry)
            self.assertIn("necessary", entry)
            self.assertIn("optional", entry)
        self.assertAlmostEqual(result["projection"][0]["fixed"], 1500.0)
        self.assertAlmostEqual(result["projection"][0]["installments"], 0.0)
        self.assertAlmostEqual(result["projection"][0]["necessary"], 500.0)

    def test_optional_included_in_expenses(self):
        svc = self._setup_service(income=5000.0, fixed=1000.0, necessary=500.0, optional_target=300.0)
        result = svc.get_projection(months=1)
        entry = result["projection"][0]
        # expenses = fixed(1000) + installments(0) + necessary(500) + optional(300) = 1800
        self.assertAlmostEqual(entry["expenses"], 1800.0)
        self.assertAlmostEqual(entry["optional"], 300.0)

    def test_installments_reduce_net_worth_in_correct_month(self):
        svc = _make_service()
        svc.accounts_repo.get_latest_snapshot_by_type.return_value = [{"balance": 10000.0}]
        svc.investment_repo.get_investments.return_value = []
        svc.income_repo.get_all.return_value = [
            {"description": "Salario", "amount": 3000.0, "frequency": "monthly"},
        ]
        svc.recurrences_service.get_fixed_expenses_for_month.return_value = []
        svc._get_avg_necessary_expenses = MagicMock(return_value=0.0)
        svc.settings_service.get_optional_expenses_target.return_value = 0.0

        next_month_key = _next_month(1)
        svc.recurrences_service.get_installments.side_effect = lambda month: (
            [{"amount": 500.0}] if month == next_month_key else []
        )

        result = svc.get_projection(months=12)
        first_entry = next(e for e in result["projection"] if e["month"] == next_month_key)
        # expenses = fixed(0) + installments(500) + necessary(0) + optional(0)
        self.assertAlmostEqual(first_entry["expenses"], 500.0)
        self.assertAlmostEqual(first_entry["installments"], 500.0)

    def test_current_net_worth_in_response(self):
        svc = self._setup_service(current_nw=50000.0)
        result = svc.get_projection(months=1)
        self.assertAlmostEqual(result["current_net_worth"], 50000.0)

    def test_response_has_avg_necessary_expenses(self):
        svc = self._setup_service(necessary=800.0, optional_target=200.0)
        result = svc.get_projection(months=1)
        self.assertIn("avg_necessary_expenses", result)
        self.assertNotIn("optional_expenses_target", result)
        self.assertAlmostEqual(result["avg_necessary_expenses"], 800.0)
        self.assertAlmostEqual(result["projection"][0]["optional"], 200.0)

    def test_annual_recurrence_applied_in_matching_month(self):
        """Annual fixed expense only appears in its designated month."""
        svc = _make_service()
        svc.accounts_repo.get_latest_snapshot_by_type.return_value = [{"balance": 10000.0}]
        svc.investment_repo.get_investments.return_value = []
        svc.income_repo.get_all.return_value = [
            {"description": "Salario", "amount": 3000.0, "frequency": "monthly"},
        ]
        target_month = _next_month(2)
        svc.recurrences_service.get_fixed_expenses_for_month.side_effect = lambda month: (
            [{"description": "IPTU", "amount": 600.0, "category_id": None}]
            if month == target_month else []
        )
        svc._get_avg_necessary_expenses = MagicMock(return_value=0.0)
        svc.settings_service.get_optional_expenses_target.return_value = 0.0

        result = svc.get_projection(months=12)
        entry_with_annual = next(e for e in result["projection"] if e["month"] == target_month)
        entry_without = next(e for e in result["projection"] if e["month"] == _next_month(1))
        self.assertAlmostEqual(entry_with_annual["fixed"], 600.0)
        self.assertAlmostEqual(entry_without["fixed"], 0.0)


class TestGetAssumptions(unittest.TestCase):

    # ── get_assumptions ──

    def test_returns_correct_structure(self):
        svc = _make_service()
        svc.income_repo.get_all.return_value = [
            {"description": "Salario", "amount": 5000.0, "frequency": "monthly"},
            {"description": "Bonus", "amount": 2000.0, "frequency": "annual"},
        ]
        svc.recurrences_repo.get_all.return_value = [
            {"description": "Aluguel", "amount": 3200.0, "frequency": "monthly", "category_id": None},
        ]
        svc.recurrences_service.get_installments.return_value = []
        svc.transaction_service.get_bank_transactions.return_value = []
        svc.transaction_service.get_credit_transactions.return_value = []
        svc.settings_service.get_optional_expenses_target.return_value = 400.0

        result = svc.get_assumptions()

        self.assertIn("income_sources", result)
        self.assertIn("fixed_expenses", result)
        self.assertIn("installments_by_month", result)
        self.assertIn("avg_necessary_expenses", result)
        self.assertIn("avg_optional_expenses_historical", result)
        self.assertIn("optional_expenses_target", result)
        self.assertEqual(len(result["income_sources"]), 1)
        self.assertEqual(result["income_sources"][0]["description"], "Salario")
        self.assertEqual(len(result["fixed_expenses"]), 1)
        self.assertEqual(result["fixed_expenses"][0]["description"], "Aluguel")
        self.assertIsInstance(result["installments_by_month"], list)
        self.assertIsInstance(result["avg_necessary_expenses"], float)
        self.assertIsInstance(result["avg_optional_expenses_historical"], float)
        self.assertAlmostEqual(result["optional_expenses_target"], 400.0)


class TestGetActualHistory(unittest.TestCase):

    # ── _get_actual_history ──

    def _make_entry(self, month, income, expenses, total_cash=None, bank_expenses=None, credit_expenses=None):
        from models.finance_history import FinanceHistory
        return FinanceHistory(
            month=month, income=income, expenses=expenses,
            total_cash=total_cash,
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
        result = svc._get_actual_history()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["month"], "2025-11")

    def test_history_entry_has_necessary_and_optional_fields(self):
        svc = _make_service()
        necessary_id = "cat_food"
        optional_id = "cat_leisure"
        svc.category_repo.get_necessary_category_ids.return_value = {necessary_id}
        svc.category_repo.get_optional_category_ids.return_value = {optional_id}
        svc.finance_history_repo.get_all.return_value = [
            self._make_entry("2025-10", 5000.0, 4000.0),
        ]
        svc.recurrences_service.get_fixed_expenses_for_month.return_value = [
            {"description": "Aluguel", "amount": 1500.0, "category_id": None},
        ]
        svc.transaction_service.get_bank_transactions.return_value = [
            _make_transaction("bank", -800.0, category_id=necessary_id),
            _make_transaction("bank", -300.0, category_id=optional_id),
        ]
        result = svc._get_actual_history()
        entry = result[0]
        self.assertIn("necessary", entry)
        self.assertIn("optional", entry)
        self.assertNotIn("variable", entry)
        self.assertAlmostEqual(entry["necessary"], 800.0)
        self.assertAlmostEqual(entry["optional"], 300.0)

    def test_fixed_comes_from_recurrences_service(self):
        svc = _make_service()
        svc.finance_history_repo.get_all.return_value = [
            self._make_entry("2025-10", 5000.0, 4000.0),
        ]
        svc.recurrences_service.get_fixed_expenses_for_month.return_value = [
            {"description": "Aluguel", "amount": 1500.0, "category_id": None},
            {"description": "IPTU", "amount": 600.0, "category_id": None},
        ]
        result = svc._get_actual_history()
        # fixed = sum of fixed_items, not capped at expenses
        self.assertAlmostEqual(result[0]["fixed"], 2100.0)

    def test_installments_from_recurrences_service(self):
        svc = _make_service()
        svc.finance_history_repo.get_all.return_value = [
            self._make_entry("2025-10", 5000.0, 4000.0),
        ]
        svc.recurrences_service.get_installments.return_value = [
            {"amount": 300.0, "category_id": None},
            {"amount": 200.0, "category_id": None},
        ]
        result = svc._get_actual_history()
        self.assertAlmostEqual(result[0]["installments"], 500.0)

    def test_net_worth_included_when_present(self):
        svc = _make_service()
        svc.finance_history_repo.get_all.return_value = [
            self._make_entry("2025-10", 5000.0, 3000.0, total_cash=45000.0),
        ]
        result = svc._get_actual_history()
        self.assertAlmostEqual(result[0]["net_worth"], 45000.0)

    def test_net_worth_is_none_when_not_set(self):
        svc = _make_service()
        svc.finance_history_repo.get_all.return_value = [
            self._make_entry("2025-10", 5000.0, 3000.0, total_cash=None),
        ]
        result = svc._get_actual_history()
        self.assertIsNone(result[0]["net_worth"])

    def test_empty_history_returns_empty_list(self):
        svc = _make_service()
        svc.finance_history_repo.get_all.return_value = []
        result = svc._get_actual_history()
        self.assertEqual(result, [])

    def _entry(self, month, income, expenses, bank_net=0.0, net_worth=None):
        """Helper to build a history entry dict for backfill tests."""
        return {
            "month": month,
            "income": income,
            "expenses": expenses,
            "bank_net": bank_net,
            "net_worth": net_worth,
        }

    def test_backfill_fills_missing_net_worth_backwards(self):
        # Formula: net_worth(M) = net_worth(M+1) - bank_net(M+1)
        # M=Dec: nw=50000 (anchor), bank_net=+2000
        # M=Nov: bank_net=-1500
        entries = [
            self._entry("2025-10", income=5000.0, expenses=4000.0, bank_net=500.0),
            self._entry("2025-11", income=5000.0, expenses=3500.0, bank_net=-1500.0),
            self._entry("2025-12", income=5000.0, expenses=4500.0, bank_net=2000.0, net_worth=50000.0),
        ]
        result = ProjectionService._backfill_net_worth(entries)
        # Nov = Dec_nw(50000) - Dec_bank_net(2000) = 48000
        self.assertAlmostEqual(result[1]["net_worth"], 48000.0)
        # Oct = Nov_nw(48000) - Nov_bank_net(-1500) = 49500
        self.assertAlmostEqual(result[0]["net_worth"], 49500.0)

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
        # Anchor at index 1 (Nov); index 0 should be filled, index 2 stays null
        # Nov_nw=48500, Nov_bank_net=-3000
        # Oct = 48500 - (-3000) = 51500
        entries = [
            self._entry("2025-10", income=5000.0, expenses=4000.0, bank_net=1000.0),
            self._entry("2025-11", income=5000.0, expenses=3500.0, bank_net=-3000.0, net_worth=48500.0),
            self._entry("2025-12", income=5000.0, expenses=4500.0, bank_net=2000.0),
        ]
        result = ProjectionService._backfill_net_worth(entries)
        # Oct = Nov_nw(48500) - Nov_bank_net(-3000) = 51500
        self.assertAlmostEqual(result[0]["net_worth"], 51500.0)
        # Dec is after the anchor, stays null
        self.assertIsNone(result[2]["net_worth"])

    def test_get_projection_includes_history_key(self):
        svc = _make_service()
        svc.accounts_repo.get_latest_snapshot_by_type.return_value = [{"balance": 10000.0}]
        svc.investment_repo.get_investments.return_value = []
        svc.income_repo.get_all.return_value = []
        svc.recurrences_service.get_fixed_expenses_for_month.return_value = []
        svc.recurrences_service.get_installments.return_value = []
        svc._get_avg_necessary_expenses = MagicMock(return_value=0.0)
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
