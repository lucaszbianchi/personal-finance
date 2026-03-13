"""Testes para SpendingPaceService"""

import unittest
from unittest.mock import MagicMock, patch

from services.spending_pace_service import SpendingPaceService


def _make_bank(amount, date_str="2026-03-05", excluded=0):
    t = MagicMock()
    t.transaction_type = "bank"
    t.amount = amount
    t.date = date_str
    t.excluded = excluded
    return t


def _make_credit(amount, date_str="2026-03-10", excluded=0):
    t = MagicMock()
    t.transaction_type = "credit"
    t.amount = amount
    t.date = date_str
    t.excluded = excluded
    return t


def _make_history(month, expenses):
    h = MagicMock()
    h.month = month
    h.expenses = expenses
    return h


def _make_service(bank_cur=None, credit_cur=None, bank_prev=None, credit_prev=None,
                  history=None, goal=None):
    """Build a SpendingPaceService with all external calls mocked."""
    with patch("services.spending_pace_service.FinanceSummaryService"), \
         patch("services.spending_pace_service.FinanceHistoryRepository"), \
         patch("services.spending_pace_service.UserGoalsRepository"):
        svc = SpendingPaceService()

    mock_ts = MagicMock()
    mock_ts.get_bank_transactions.side_effect = [
        bank_cur or [],
        bank_prev or [],
    ]
    mock_ts.get_credit_transactions.side_effect = [
        credit_cur or [],
        credit_prev or [],
    ]
    svc._summary = MagicMock()
    svc._summary.transaction_service = mock_ts

    mock_history_repo = MagicMock()
    mock_history_repo.get_all.return_value = history or []
    svc._history_repo = mock_history_repo

    mock_goals_repo = MagicMock()
    mock_goals_repo.get_total_monthly_goal.return_value = goal
    svc._goals_repo = mock_goals_repo

    return svc


class TestSpendingPaceService(unittest.TestCase):

    def _run(self, month, bank_cur=None, credit_cur=None, bank_prev=None, credit_prev=None,
             history=None, goal=None):
        """Helper: creates service with all external calls mocked, calls get_spending_pace."""
        svc = _make_service(bank_cur, credit_cur, bank_prev, credit_prev, history, goal)
        return svc.get_spending_pace(month)

    # ── 1. Series length == last day of month ────────────────────────────────

    def test_series_length_march(self):
        result = self._run("2026-03")
        self.assertEqual(len(result["daily_series"]), 31)

    def test_series_length_february_non_leap(self):
        result = self._run("2026-02")
        self.assertEqual(len(result["daily_series"]), 28)

    def test_series_length_april(self):
        result = self._run("2026-04")
        self.assertEqual(len(result["daily_series"]), 30)

    # ── 2. Cumulative values are monotonically non-decreasing ─────────────────

    def test_cumulative_monotonic(self):
        txns = [
            _make_bank(-100.0, "2026-03-01"),
            _make_bank(-50.0, "2026-03-15"),
            _make_bank(-200.0, "2026-03-28"),
        ]
        result = self._run("2026-03", bank_cur=txns)
        amounts = [e["cumulative_amount"] for e in result["daily_series"]]
        for i in range(1, len(amounts)):
            self.assertGreaterEqual(amounts[i], amounts[i - 1])

    # ── 3. Bank income excluded from series ───────────────────────────────────

    def test_bank_income_excluded(self):
        txns = [
            _make_bank(5000.0, "2026-03-05"),   # income — should be ignored
            _make_bank(-100.0, "2026-03-05"),   # expense — should be counted
        ]
        result = self._run("2026-03", bank_cur=txns)
        final = result["daily_series"][-1]["cumulative_amount"]
        self.assertAlmostEqual(final, 100.0)

    # ── 4. Excluded transactions not counted ─────────────────────────────────

    def test_excluded_transactions_not_counted(self):
        txns = [
            _make_bank(-300.0, "2026-03-01", excluded=1),
            _make_bank(-100.0, "2026-03-01", excluded=0),
        ]
        result = self._run("2026-03", bank_cur=txns)
        final = result["daily_series"][-1]["cumulative_amount"]
        self.assertAlmostEqual(final, 100.0)

    def test_excluded_credit_not_counted(self):
        txns = [
            _make_credit(500.0, "2026-03-10", excluded=1),
            _make_credit(80.0, "2026-03-10", excluded=0),
        ]
        result = self._run("2026-03", credit_cur=txns)
        final = result["daily_series"][-1]["cumulative_amount"]
        self.assertAlmostEqual(final, 80.0)

    # ── 5. monthly_goal from repo / None when unset ───────────────────────────

    def test_monthly_goal_returned(self):
        result = self._run("2026-03", goal=3000.0)
        self.assertEqual(result["monthly_goal"], 3000.0)

    def test_monthly_goal_none_when_unset(self):
        result = self._run("2026-03", goal=None)
        self.assertIsNone(result["monthly_goal"])

    # ── 6. monthly_avg uses last 6 months, excludes current month ─────────────

    def test_monthly_avg_last_6(self):
        history = [
            _make_history("2026-02", 2000.0),
            _make_history("2026-01", 1800.0),
            _make_history("2025-12", 2200.0),
            _make_history("2025-11", 1900.0),
            _make_history("2025-10", 2100.0),
            _make_history("2025-09", 1700.0),
            _make_history("2025-08", 9999.0),  # 7th — should be excluded
        ]
        result = self._run("2026-03", history=history)
        expected = round((2000 + 1800 + 2200 + 1900 + 2100 + 1700) / 6, 2)
        self.assertAlmostEqual(result["monthly_avg"], expected)

    def test_monthly_avg_excludes_current_month(self):
        history = [
            _make_history("2026-03", 9999.0),  # current month — must be excluded
            _make_history("2026-02", 1000.0),
        ]
        result = self._run("2026-03", history=history)
        self.assertAlmostEqual(result["monthly_avg"], 1000.0)

    # ── 7. monthly_avg is None when no history ────────────────────────────────

    def test_monthly_avg_none_when_no_history(self):
        result = self._run("2026-03", history=[])
        self.assertIsNone(result["monthly_avg"])

    def test_monthly_avg_none_when_all_history_in_future(self):
        history = [_make_history("2026-04", 1500.0)]
        result = self._run("2026-03", history=history)
        self.assertIsNone(result["monthly_avg"])

    # ── 8. Previous month alignment when Feb precedes March ───────────────────

    def test_prev_month_feb_padded_to_march_length(self):
        """Feb (28 days) preceding March (31 days): prev series padded to length 31."""
        prev_txns = [_make_bank(-500.0, "2026-02-28")]
        result = self._run("2026-03", bank_prev=prev_txns)
        series = result["daily_series"]
        self.assertEqual(len(series), 31)
        # Days 29-31 should carry the final Feb cumulative value
        self.assertAlmostEqual(series[27]["prev_month_cumulative"], 500.0)  # day 28
        self.assertAlmostEqual(series[28]["prev_month_cumulative"], 500.0)  # day 29 padded
        self.assertAlmostEqual(series[30]["prev_month_cumulative"], 500.0)  # day 31 padded

    def test_prev_month_longer_truncated(self):
        """March (31d) preceding April (30d): prev series truncated to length 30."""
        prev_txns = [_make_bank(-200.0, "2026-03-31")]
        result = self._run("2026-04", bank_prev=prev_txns)
        series = result["daily_series"]
        self.assertEqual(len(series), 30)
        # Day 31 of prev month should not appear
        days = [e["day"] for e in series]
        self.assertNotIn(31, days)

    # ── 9. unavoidable_avg is always None ────────────────────────────────────

    def test_unavoidable_avg_always_none(self):
        result = self._run("2026-03")
        self.assertIsNone(result["unavoidable_avg"])

    # ── Structural checks ─────────────────────────────────────────────────────

    def test_day_field_starts_at_1(self):
        result = self._run("2026-03")
        self.assertEqual(result["daily_series"][0]["day"], 1)

    def test_day_field_ends_at_last_day(self):
        result = self._run("2026-03")
        self.assertEqual(result["daily_series"][-1]["day"], 31)

    def test_result_keys_present(self):
        result = self._run("2026-03")
        self.assertIn("daily_series", result)
        self.assertIn("monthly_goal", result)
        self.assertIn("monthly_avg", result)
        self.assertIn("unavoidable_avg", result)

    def test_day_entry_keys_present(self):
        result = self._run("2026-03")
        entry = result["daily_series"][0]
        self.assertIn("day", entry)
        self.assertIn("cumulative_amount", entry)
        self.assertIn("prev_month_cumulative", entry)


if __name__ == "__main__":
    unittest.main()
