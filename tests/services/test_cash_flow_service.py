"""Testes para CashFlowService"""

import unittest
from unittest.mock import MagicMock, patch
from services.cash_flow_service import (
    CashFlowService,
    _generate_months,
    _prev_month,
    _delta_pct,
    _sum_values,
    _month_date_range,
)


class TestCashFlowHelpers(unittest.TestCase):

    # ── _generate_months ──────────────────────────────────────────────────────

    def test_generate_months_3_window(self):
        result = _generate_months("2026-03", 3)
        self.assertEqual(result, ["2026-01", "2026-02", "2026-03"])

    def test_generate_months_6_window(self):
        result = _generate_months("2026-03", 6)
        self.assertEqual(result, ["2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03"])

    def test_generate_months_wraps_year(self):
        result = _generate_months("2026-01", 3)
        self.assertEqual(result, ["2025-11", "2025-12", "2026-01"])

    # ── _prev_month ───────────────────────────────────────────────────────────

    def test_prev_month_normal(self):
        self.assertEqual(_prev_month("2026-03"), "2026-02")

    def test_prev_month_wraps_year(self):
        self.assertEqual(_prev_month("2026-01"), "2025-12")

    # ── _month_date_range ─────────────────────────────────────────────────────

    def test_month_date_range_basic(self):
        start, end = _month_date_range("2026-03")
        self.assertEqual(start, "2026-03-01")
        self.assertEqual(end, "2026-04-01")

    def test_month_date_range_december(self):
        start, end = _month_date_range("2025-12")
        self.assertEqual(start, "2025-12-01")
        self.assertEqual(end, "2026-01-01")

    # ── _delta_pct ────────────────────────────────────────────────────────────

    def test_delta_pct_positive(self):
        self.assertEqual(_delta_pct(110.0, 100.0), 10.0)

    def test_delta_pct_negative(self):
        self.assertEqual(_delta_pct(90.0, 100.0), -10.0)

    def test_delta_pct_none_when_previous_zero(self):
        self.assertIsNone(_delta_pct(100.0, 0.0))

    def test_delta_pct_none_when_current_none(self):
        self.assertIsNone(_delta_pct(None, 100.0))

    def test_delta_pct_none_when_previous_none(self):
        self.assertIsNone(_delta_pct(100.0, None))

    # ── _sum_values ───────────────────────────────────────────────────────────

    def test_sum_values_basic(self):
        entries = [{"month": "2026-01", "value": 100.0}, {"month": "2026-02", "value": 200.0}]
        self.assertEqual(_sum_values(entries), 300.0)

    def test_sum_values_skips_none(self):
        entries = [{"month": "2026-01", "value": None}, {"month": "2026-02", "value": 200.0}]
        self.assertEqual(_sum_values(entries), 200.0)

    def test_sum_values_all_none_returns_none(self):
        entries = [{"month": "2026-01", "value": None}]
        self.assertIsNone(_sum_values(entries))


class TestCashFlowService(unittest.TestCase):

    def setUp(self):
        with patch("services.cash_flow_service.FinanceSummaryService"):
            self.service = CashFlowService()

        self.mock_summary = MagicMock()
        self.service.summary_service = self.mock_summary
        self.mock_summary.get_income.return_value = 0.0
        self.mock_summary.get_expenses.return_value = 0.0
        self.mock_summary.get_category_expenses_by_parent.return_value = []

    # ── get_cash_flow — window structure ──────────────────────────────────────

    def test_current_months_window_3(self):
        result = self.service.get_cash_flow(3, "2026-03")
        self.assertEqual(result["current_window"]["months"], ["2026-01", "2026-02", "2026-03"])

    def test_previous_months_window_3(self):
        result = self.service.get_cash_flow(3, "2026-03")
        self.assertEqual(result["previous_window"]["months"], ["2025-10", "2025-11", "2025-12"])

    def test_current_months_window_6(self):
        result = self.service.get_cash_flow(6, "2026-03")
        self.assertEqual(
            result["current_window"]["months"],
            ["2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03"],
        )

    def test_previous_months_window_6(self):
        result = self.service.get_cash_flow(6, "2026-03")
        self.assertEqual(
            result["previous_window"]["months"],
            ["2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09"],
        )

    # ── get_cash_flow — period_total ──────────────────────────────────────────

    def test_period_total_sums_net_balance(self):
        self.mock_summary.get_income.return_value = 8000.0
        self.mock_summary.get_expenses.return_value = 5000.0
        result = self.service.get_cash_flow(3, "2026-03")
        # each month: 8000 - 5000 = 3000; 3 months = 9000
        self.assertEqual(result["current_window"]["period_total"], 9000.0)

    def test_previous_period_total_sums_net_balance(self):
        self.mock_summary.get_income.return_value = 7000.0
        self.mock_summary.get_expenses.return_value = 4500.0
        result = self.service.get_cash_flow(3, "2026-03")
        self.assertEqual(result["previous_window"]["period_total"], 7500.0)

    # ── get_cash_flow — delta_pct ─────────────────────────────────────────────

    def test_delta_pct_positive_growth(self):
        def income_side(start, end):
            return 11000.0 if start >= "2026-01-01" else 10000.0

        def expenses_side(start, end):
            return 6000.0

        self.mock_summary.get_income.side_effect = income_side
        self.mock_summary.get_expenses.side_effect = expenses_side
        result = self.service.get_cash_flow(3, "2026-03")
        # current net per month: 5000, total 15000
        # previous net per month: 4000, total 12000
        # delta = (15000 - 12000) / 12000 * 100 = 25.0
        self.assertEqual(result["previous_window"]["delta_pct"], 25.0)

    def test_delta_pct_none_when_previous_zero(self):
        def income_side(start, end):
            return 8000.0 if start >= "2026-01-01" else 0.0

        def expenses_side(start, end):
            return 0.0 if start < "2026-01-01" else 5000.0

        self.mock_summary.get_income.side_effect = income_side
        self.mock_summary.get_expenses.side_effect = expenses_side
        result = self.service.get_cash_flow(3, "2026-03")
        self.assertIsNone(result["previous_window"]["delta_pct"])

    # ── get_cash_flow — net balance and income values ─────────────────────────

    def test_net_balance_is_income_minus_expenses(self):
        self.mock_summary.get_income.return_value = 8000.0
        self.mock_summary.get_expenses.return_value = 5000.0
        result = self.service.get_cash_flow(3, "2026-03")
        for entry in result["current_window"]["net_balance"]:
            self.assertEqual(entry["value"], 3000.0)

    def test_income_values_populated(self):
        self.mock_summary.get_income.return_value = 8000.0
        self.mock_summary.get_expenses.return_value = 5000.0
        result = self.service.get_cash_flow(3, "2026-03")
        for entry in result["current_window"]["income"]:
            self.assertEqual(entry["value"], 8000.0)

    # ── get_cash_flow — category expenses ─────────────────────────────────────

    def test_category_expenses_called_per_current_month(self):
        self.service.get_cash_flow(3, "2026-03")
        self.assertEqual(self.mock_summary.get_category_expenses_by_parent.call_count, 3)

    def test_category_expenses_not_called_for_previous_window(self):
        self.service.get_cash_flow(6, "2026-03")
        # only called for current window (6 months)
        self.assertEqual(self.mock_summary.get_category_expenses_by_parent.call_count, 6)

    def test_category_expenses_mapped_to_description(self):
        self.mock_summary.get_category_expenses_by_parent.return_value = [
            {"id": "cat1", "description": "Alimentacao", "total": 800.0}
        ]
        result = self.service.get_cash_flow(3, "2026-03")
        for entry in result["current_window"]["expenses_by_category"]:
            self.assertIn("Alimentacao", entry["categories"])
            self.assertEqual(entry["categories"]["Alimentacao"], 800.0)

    def test_correct_date_range_passed_to_summary(self):
        self.service.get_cash_flow(3, "2026-03")
        self.mock_summary.get_income.assert_any_call("2026-03-01", "2026-04-01")
        self.mock_summary.get_income.assert_any_call("2026-01-01", "2026-02-01")


if __name__ == "__main__":
    unittest.main()
