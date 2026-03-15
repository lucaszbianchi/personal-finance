"""Tests for IncomeSourcesService"""

import unittest
from unittest.mock import MagicMock, patch

import services.income_sources_service as svc_module


def _make_service():
    with patch("services.income_sources_service.IncomeSourcesRepository"):
        svc = svc_module.IncomeSourcesService()
    svc.repo = MagicMock()
    return svc


_MANUAL = {
    "id": "inc-1",
    "description": "Salario",
    "amount": 4800.0,
    "frequency": "monthly",
    "next_occurrence": "2026-04-05",
    "category_id": None,
    "merchant_name": None,
    "amount_min": None,
    "amount_max": None,
    "confidence": None,
    "source": "manual",
    "synced_at": "2026-03-01",
}


class TestIncomeSourcesService(unittest.TestCase):

    # ── get_all ──

    def test_get_all_returns_list(self):
        svc = _make_service()
        svc.repo.get_all.return_value = [_MANUAL]
        result = svc.get_all()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "inc-1")

    # ── create ──

    def test_create_generates_uuid_and_sets_source(self):
        svc = _make_service()
        svc.repo.get_by_id.return_value = {**_MANUAL, "id": "some-uuid"}
        svc.create({"description": "Salario", "amount": 4800.0, "frequency": "monthly"})
        svc.repo.upsert.assert_called_once()
        call_data = svc.repo.upsert.call_args[0][0]
        self.assertEqual(call_data["source"], "manual")
        self.assertEqual(len(call_data["id"]), 36)  # uuid4

    def test_create_passes_all_fields(self):
        svc = _make_service()
        svc.repo.get_by_id.return_value = _MANUAL
        svc.create({
            "description": "Freelance",
            "amount": 2000.0,
            "frequency": "monthly",
            "merchant_name": "cliente",
            "amount_min": 1500.0,
            "amount_max": 2500.0,
        })
        call_data = svc.repo.upsert.call_args[0][0]
        self.assertEqual(call_data["merchant_name"], "cliente")
        self.assertAlmostEqual(call_data["amount_min"], 1500.0)
        self.assertAlmostEqual(call_data["amount_max"], 2500.0)

    def test_create_confidence_is_none(self):
        svc = _make_service()
        svc.repo.get_by_id.return_value = _MANUAL
        svc.create({"description": "Test"})
        call_data = svc.repo.upsert.call_args[0][0]
        self.assertIsNone(call_data["confidence"])

    # ── update ──

    def test_update_calls_repo_and_returns_record(self):
        svc = _make_service()
        updated = {**_MANUAL, "amount": 5200.0}
        svc.repo.get_by_id.return_value = updated
        result = svc.update("inc-1", {"amount": 5200.0})
        svc.repo.update.assert_called_once_with("inc-1", {"amount": 5200.0})
        self.assertEqual(result["amount"], 5200.0)

    def test_update_not_found_raises(self):
        svc = _make_service()
        svc.repo.update.side_effect = ValueError("not found")
        with self.assertRaises(ValueError):
            svc.update("ghost", {"amount": 1.0})

    # ── delete ──

    def test_delete_delegates_to_repo(self):
        svc = _make_service()
        svc.delete("inc-1")
        svc.repo.delete.assert_called_once_with("inc-1")

    def test_delete_not_found_raises(self):
        svc = _make_service()
        svc.repo.delete.side_effect = ValueError("not found")
        with self.assertRaises(ValueError):
            svc.delete("ghost")

    # ── get_detail ──

    def test_get_detail_shape(self):
        svc = _make_service()
        record = {**_MANUAL, "merchant_name": "salario"}
        svc.repo.get_by_id.return_value = record
        svc.repo.get_matching_transactions.return_value = []
        result = svc.get_detail("inc-1")
        self.assertIn("source", result)
        self.assertIn("linked_transactions", result)
        self.assertIn("timeline", result)
        self.assertIn("metrics", result)
        self.assertEqual(len(result["timeline"]), 12)

    def test_get_detail_no_merchant_skips_txns(self):
        svc = _make_service()
        svc.repo.get_by_id.return_value = _MANUAL  # merchant_name is None
        result = svc.get_detail("inc-1")
        self.assertEqual(result["linked_transactions"], [])
        svc.repo.get_matching_transactions.assert_not_called()

    def test_get_detail_timeline_marks_matched_months(self):
        svc = _make_service()
        record = {**_MANUAL, "merchant_name": "salario"}
        svc.repo.get_by_id.return_value = record
        svc.repo.get_matching_transactions.return_value = [
            {"id": "t1", "description": "salario", "amount": 4800.0, "date": "2026-03-05"},
        ]
        result = svc.get_detail("inc-1")
        march_entry = next(e for e in result["timeline"] if e["month"] == "2026-03")
        self.assertTrue(march_entry["matched"])

    def test_get_detail_metrics_shape(self):
        svc = _make_service()
        record = {**_MANUAL, "merchant_name": "salario"}
        svc.repo.get_by_id.return_value = record
        svc.repo.get_matching_transactions.return_value = [
            {"id": "t1", "description": "salario", "amount": 4800.0, "date": "2026-03-05"},
        ]
        result = svc.get_detail("inc-1")
        metrics = result["metrics"]
        self.assertIn("last_amount", metrics)
        self.assertIn("avg_amount", metrics)
        self.assertIn("total_this_year", metrics)
        self.assertIn("last_received_date", metrics)
        self.assertAlmostEqual(metrics["last_amount"], 4800.0)

    # ── count_matching ──

    def test_count_matching_returns_dict(self):
        svc = _make_service()
        svc.repo.count_matching_transactions.return_value = 3
        result = svc.count_matching("empresa xyz", amount_min=4000.0)
        svc.repo.count_matching_transactions.assert_called_once_with("empresa xyz", 4000.0, None, None)
        self.assertEqual(result, {"count": 3})

    def test_count_matching_with_monthly_passes_day(self):
        svc = _make_service()
        svc.repo.count_matching_transactions.return_value = 2
        svc.count_matching("salario", next_occurrence="2026-03-05", frequency="monthly")
        svc.repo.count_matching_transactions.assert_called_once_with("salario", None, None, 5)

    def test_count_matching_non_monthly_ignores_day(self):
        svc = _make_service()
        svc.repo.count_matching_transactions.return_value = 1
        svc.count_matching("bonus", next_occurrence="2026-12-25", frequency="annual")
        svc.repo.count_matching_transactions.assert_called_once_with("bonus", None, None, None)

    # ── _filter_items ──

    def test_filter_items_includes_monthly_always(self):
        svc = _make_service()
        monthly = {**_MANUAL, "frequency": "monthly", "next_occurrence": "2026-06-05"}
        result = svc._filter_items([monthly], "2026-03")
        self.assertEqual(len(result), 1)

    def test_filter_items_annual_matches_by_month_of_year(self):
        svc = _make_service()
        annual = {**_MANUAL, "frequency": "annual", "next_occurrence": "2027-03-01"}
        result_march = svc._filter_items([annual], "2026-03")
        result_april = svc._filter_items([annual], "2026-04")
        self.assertEqual(len(result_march), 1)
        self.assertEqual(len(result_april), 0)

    def test_filter_items_sorted_by_next_occurrence(self):
        svc = _make_service()
        a = {**_MANUAL, "id": "a", "next_occurrence": "2026-03-20"}
        b = {**_MANUAL, "id": "b", "next_occurrence": "2026-03-05"}
        c = {**_MANUAL, "id": "c", "next_occurrence": None}
        result = svc._filter_items([a, c, b], "2026-03")
        self.assertEqual([r["id"] for r in result], ["b", "a", "c"])

    # ── get_monthly_view ──

    def test_get_monthly_view_shape(self):
        svc = _make_service()
        svc.repo.get_all.return_value = []
        result = svc.get_monthly_view("2026-03")
        self.assertIn("sources", result)
        self.assertIn("history", result)
        self.assertIn("total", result["sources"])
        self.assertIn("items", result["sources"])
        self.assertEqual(len(result["history"]), 12)

    def test_get_monthly_view_calculates_total(self):
        svc = _make_service()
        source = {**_MANUAL, "frequency": "monthly", "amount": 4800.0}
        svc.repo.get_all.return_value = [source]
        result = svc.get_monthly_view("2026-03")
        self.assertAlmostEqual(result["sources"]["total"], 4800.0)

    def test_get_monthly_view_history_has_12_entries(self):
        svc = _make_service()
        svc.repo.get_all.return_value = []
        result = svc.get_monthly_view("2026-03")
        self.assertEqual(len(result["history"]), 12)

    # ── get_yearly_view ──

    def test_get_yearly_view_returns_12_entries(self):
        svc = _make_service()
        svc.repo.get_all.return_value = []
        svc.repo.get_monthly_actuals.return_value = {}
        result = svc.get_yearly_view(2026)
        self.assertEqual(len(result), 12)
        self.assertEqual(result[0]["month"], "2026-01")
        self.assertEqual(result[-1]["month"], "2026-12")

    def test_get_yearly_view_past_month_uses_actuals(self):
        """Past months reflect actual transaction sums, not configured amount."""
        svc = _make_service()
        source = {**_MANUAL, "frequency": "monthly", "amount": 4800.0, "merchant_name": "empresa"}
        svc.repo.get_all.return_value = [source]
        # Simulate actual transaction total of 4950 in March 2026
        svc.repo.get_monthly_actuals.return_value = {"2026-03": 4950.0}
        result = svc.get_yearly_view(2026)
        march = next(r for r in result if r["month"] == "2026-03")
        self.assertAlmostEqual(march["total"], 4950.0)

    def test_get_yearly_view_future_month_uses_configured_amount(self):
        """Future months use the configured amount as projection."""
        svc = _make_service()
        source = {**_MANUAL, "frequency": "monthly", "amount": 4800.0, "merchant_name": "empresa"}
        svc.repo.get_all.return_value = [source]
        svc.repo.get_monthly_actuals.return_value = {}
        result = svc.get_yearly_view(2026)
        # Any month beyond current_month (2026-03 in test context) uses configured amount
        future = [r for r in result if r["month"] > "2026-03"]
        self.assertTrue(all(r["total"] == 4800.0 for r in future))

    def test_get_yearly_view_no_merchant_always_uses_configured_amount(self):
        """Sources without merchant_name use configured amount regardless of month."""
        svc = _make_service()
        source = {**_MANUAL, "frequency": "monthly", "amount": 4800.0}  # no merchant_name
        svc.repo.get_all.return_value = [source]
        svc.repo.get_monthly_actuals.return_value = {}
        result = svc.get_yearly_view(2026)
        self.assertTrue(all(r["total"] == 4800.0 for r in result))
        svc.repo.get_monthly_actuals.assert_not_called()

    def test_get_yearly_view_annual_source_appears_once(self):
        svc = _make_service()
        source = {**_MANUAL, "frequency": "annual", "next_occurrence": "2026-12-25", "amount": 1200.0}
        svc.repo.get_all.return_value = [source]
        svc.repo.get_monthly_actuals.return_value = {}
        result = svc.get_yearly_view(2026)
        december = next(r for r in result if r["month"] == "2026-12")
        other_months = [r for r in result if r["month"] != "2026-12"]
        self.assertAlmostEqual(december["total"], 1200.0)
        self.assertTrue(all(r["total"] == 0.0 for r in other_months))


if __name__ == "__main__":
    unittest.main()
