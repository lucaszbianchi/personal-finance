"""Tests for RecurrencesService"""

import unittest
from unittest.mock import MagicMock, patch

import services.recurrences_service as svc_module


def _make_service():
    with patch("services.recurrences_service.RecurrentExpensesRepository"), \
         patch("services.recurrences_service.TransactionRepository"):
        svc = svc_module.RecurrencesService()
    svc.repo = MagicMock()
    return svc


_MANUAL = {
    "id": "manual-1",
    "description": "Academia",
    "amount": 150.0,
    "frequency": "monthly",
    "next_occurrence": "2026-04-01",
    "category_id": None,
    "merchant_name": None,
    "amount_min": None,
    "amount_max": None,
    "confidence": None,
    "source": "manual",
    "is_unavoidable": 0,
    "synced_at": "2026-03-14 00:00:00",
}

_DETECTED = {**_MANUAL, "id": "detected-1", "source": "detected"}


class TestRecurrencesService(unittest.TestCase):

    # ── get_all ──

    def test_get_all_returns_list(self):
        svc = _make_service()
        svc.repo.get_all.return_value = [_MANUAL]
        result = svc.get_all()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "manual-1")

    # ── create ──

    def test_create_generates_uuid_and_sets_source(self):
        svc = _make_service()
        svc.repo.get_by_id.return_value = {**_MANUAL, "id": "some-uuid"}
        result = svc.create({"description": "Academia", "amount": 150.0, "frequency": "monthly"})
        svc.repo.upsert_recurrence.assert_called_once()
        call_data = svc.repo.upsert_recurrence.call_args[0][0]
        self.assertEqual(call_data["source"], "manual")
        self.assertEqual(len(call_data["id"]), 36)  # uuid4

    def test_create_is_unavoidable_false_by_default(self):
        svc = _make_service()
        svc.repo.get_by_id.return_value = _MANUAL
        svc.create({"description": "Test"})
        call_data = svc.repo.upsert_recurrence.call_args[0][0]
        self.assertEqual(call_data["is_unavoidable"], 0)

    def test_create_is_unavoidable_true_when_set(self):
        svc = _make_service()
        svc.repo.get_by_id.return_value = _MANUAL
        svc.create({"description": "Test", "is_unavoidable": True})
        call_data = svc.repo.upsert_recurrence.call_args[0][0]
        self.assertEqual(call_data["is_unavoidable"], 1)

    def test_create_passes_amount_min_max(self):
        svc = _make_service()
        svc.repo.get_by_id.return_value = _MANUAL
        svc.create({"description": "Test", "amount_min": 10.0, "amount_max": 100.0})
        call_data = svc.repo.upsert_recurrence.call_args[0][0]
        self.assertAlmostEqual(call_data["amount_min"], 10.0)
        self.assertAlmostEqual(call_data["amount_max"], 100.0)

    # ── update ──

    def test_update_calls_repo_update_and_returns_record(self):
        svc = _make_service()
        updated = {**_MANUAL, "amount": 200.0}
        svc.repo.get_by_id.return_value = updated
        result = svc.update("manual-1", {"amount": 200.0})
        svc.repo.update.assert_called_once_with("manual-1", {"amount": 200.0})
        self.assertEqual(result["amount"], 200.0)

    def test_update_not_found_raises(self):
        svc = _make_service()
        svc.repo.update.side_effect = ValueError("not found")
        with self.assertRaises(ValueError):
            svc.update("ghost", {"amount": 1.0})

    # ── delete ──

    def test_delete_manual_succeeds(self):
        svc = _make_service()
        svc.repo.delete.return_value = None
        svc.delete("manual-1")
        svc.repo.delete.assert_called_once_with("manual-1")

    def test_delete_detected_succeeds(self):
        svc = _make_service()
        svc.repo.delete.return_value = None
        svc.delete("detected-1")
        svc.repo.delete.assert_called_once_with("detected-1")

    def test_delete_not_found_raises(self):
        svc = _make_service()
        svc.repo.delete.side_effect = ValueError("not found")
        with self.assertRaises(ValueError):
            svc.delete("ghost")

    # ── toggle_unavoidable ──

    def test_toggle_unavoidable_flips_off_to_on(self):
        svc = _make_service()
        record = {**_MANUAL, "is_unavoidable": 0}
        updated = {**_MANUAL, "is_unavoidable": 1}
        svc.repo.get_by_id.side_effect = [record, updated]
        result = svc.toggle_unavoidable("manual-1")
        svc.repo.update.assert_called_once_with("manual-1", {"is_unavoidable": 1})
        self.assertEqual(result["is_unavoidable"], 1)

    def test_toggle_unavoidable_flips_on_to_off(self):
        svc = _make_service()
        record = {**_MANUAL, "is_unavoidable": 1}
        updated = {**_MANUAL, "is_unavoidable": 0}
        svc.repo.get_by_id.side_effect = [record, updated]
        result = svc.toggle_unavoidable("manual-1")
        svc.repo.update.assert_called_once_with("manual-1", {"is_unavoidable": 0})
        self.assertEqual(result["is_unavoidable"], 0)

    # ── _get_fixed_items ──

    def test_get_fixed_items_includes_monthly_always(self):
        svc = _make_service()
        monthly = {**_MANUAL, "frequency": "monthly", "next_occurrence": "2026-06-01"}
        svc.repo.get_all.return_value = [monthly]
        result = svc._get_fixed_items("2026-03")
        self.assertEqual(len(result), 1)

    def test_get_fixed_items_annual_matches_by_month_of_year(self):
        """Annual expense with next_occurrence='2027-02-09' must appear in any February."""
        svc = _make_service()
        annual = {**_MANUAL, "frequency": "annual", "next_occurrence": "2027-02-09"}
        svc.repo.get_all.return_value = [annual]
        self.assertEqual(len(svc._get_fixed_items("2026-02")), 1)
        self.assertEqual(len(svc._get_fixed_items("2025-02")), 1)
        self.assertEqual(len(svc._get_fixed_items("2026-03")), 0)

    def test_get_fixed_items_annual_excluded_in_wrong_month(self):
        svc = _make_service()
        annual = {**_MANUAL, "frequency": "annual", "next_occurrence": "2027-02-09"}
        svc.repo.get_all.return_value = [annual]
        self.assertEqual(len(svc._get_fixed_items("2026-01")), 0)
        self.assertEqual(len(svc._get_fixed_items("2026-03")), 0)

    def test_get_fixed_items_sorted_by_next_occurrence(self):
        svc = _make_service()
        a = {**_MANUAL, "id": "a", "next_occurrence": "2026-03-20"}
        b = {**_MANUAL, "id": "b", "next_occurrence": "2026-03-05"}
        c = {**_MANUAL, "id": "c", "next_occurrence": None}
        svc.repo.get_all.return_value = [a, c, b]
        result = svc._get_fixed_items("2026-03")
        self.assertEqual([r["id"] for r in result], ["b", "a", "c"])

    # ── count_matching ──

    def test_count_matching_delegates_to_repo(self):
        svc = _make_service()
        svc.repo.count_matching_transactions.return_value = 5
        result = svc.count_matching("netflix", amount_min=10.0)
        svc.repo.count_matching_transactions.assert_called_once_with("netflix", 10.0, None, None)
        self.assertEqual(result, {"count": 5})

    # ── get_detail ──

    def test_get_detail_shape(self):
        svc = _make_service()
        record = {**_MANUAL, "merchant_name": "netflix"}
        svc.repo.get_by_id.return_value = record
        svc.repo.get_matching_transactions.return_value = []
        result = svc.get_detail("manual-1")
        self.assertIn("recurrence", result)
        self.assertIn("linked_transactions", result)
        self.assertIn("timeline", result)
        self.assertIn("metrics", result)
        self.assertEqual(len(result["timeline"]), 12)

    def test_get_detail_timeline_marks_matched_months(self):
        svc = _make_service()
        record = {**_MANUAL, "merchant_name": "netflix"}
        svc.repo.get_by_id.return_value = record
        svc.repo.get_matching_transactions.return_value = [
            {"id": "t1", "description": "netflix", "amount": 55.9, "date": "2026-03-10"},
        ]
        result = svc.get_detail("manual-1")
        march_entry = next(e for e in result["timeline"] if e["month"] == "2026-03")
        self.assertTrue(march_entry["matched"])

    def test_get_detail_no_merchant_skips_txns(self):
        svc = _make_service()
        svc.repo.get_by_id.return_value = _MANUAL  # merchant_name is None
        result = svc.get_detail("manual-1")
        self.assertEqual(result["linked_transactions"], [])
        svc.repo.get_matching_transactions.assert_not_called()

    # ── get_monthly_view ──

    def test_get_monthly_view_shape(self):
        svc = _make_service()
        svc.repo.get_all.return_value = []
        with patch("services.recurrences_service.TransactionRepository") as MockTR, \
             patch("services.recurrences_service.BillRepository") as MockBR:
            mock_tr = MagicMock()
            mock_tr.execute_query.return_value.fetchall.return_value = []
            MockTR.return_value = mock_tr
            mock_br = MagicMock()
            mock_br.get_billing_period.return_value = None
            MockBR.return_value = mock_br
            result = svc.get_monthly_view("2026-03")

        self.assertIn("installments", result)
        self.assertIn("fixed_expenses", result)
        self.assertIn("history", result)
        self.assertIn("total", result["installments"])
        self.assertIn("items", result["installments"])
        self.assertEqual(len(result["history"]), 12)

    # ── _get_installment_items ──

    def _make_bill_repo_mock(self, period=None):
        mock_br = MagicMock()
        mock_br.get_billing_period.return_value = period
        return mock_br

    def test_get_installment_items_fallback_from_description(self):
        """Transactions with total_installments=NULL but X/Y in description are included."""
        svc = _make_service()
        mock_tr = MagicMock()
        mock_tr.execute_query.return_value.fetchall.return_value = [
            {
                "id": "t1",
                "description": "Andreia Antoniazzi Joi 2/10",
                "category_id": None,
                "amount": 150.0,
                "installment_number": None,
                "total_installments": None,
                "date": "2026-02-28",
            }
        ]
        items = svc._get_installment_items(mock_tr, self._make_bill_repo_mock(), "2026-03")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["installment_number"], 2)
        self.assertEqual(items[0]["total_installments"], 10)
        self.assertAlmostEqual(items[0]["pct_paid"], 0.2)

    def test_get_installment_items_excludes_non_installment(self):
        """Transactions without installment pattern and null total_installments are excluded."""
        svc = _make_service()
        mock_tr = MagicMock()
        mock_tr.execute_query.return_value.fetchall.return_value = [
            {
                "id": "t2",
                "description": "Compra normal",
                "category_id": None,
                "amount": 50.0,
                "installment_number": None,
                "total_installments": None,
                "date": "2026-03-10",
            }
        ]
        items = svc._get_installment_items(mock_tr, self._make_bill_repo_mock(), "2026-03")
        self.assertEqual(len(items), 0)

    def test_get_installment_items_uses_db_columns_when_populated(self):
        """Transactions with total_installments column set don't need description fallback."""
        svc = _make_service()
        mock_tr = MagicMock()
        mock_tr.execute_query.return_value.fetchall.return_value = [
            {
                "id": "t3",
                "description": "Netflix",
                "category_id": None,
                "amount": 45.9,
                "installment_number": 3,
                "total_installments": 6,
                "date": "2026-03-15",
            }
        ]
        items = svc._get_installment_items(mock_tr, self._make_bill_repo_mock(), "2026-03")
        self.assertEqual(len(items), 1)
        self.assertAlmostEqual(items[0]["pct_paid"], 0.5)

    def test_get_installment_items_uses_billing_period_when_available(self):
        """When billing period is available, exclusive/inclusive range query is used."""
        svc = _make_service()
        mock_tr = MagicMock()
        mock_tr.execute_query.return_value.fetchall.return_value = []
        mock_br = self._make_bill_repo_mock(period=("2026-02-09", "2026-03-09"))

        svc._get_installment_items(mock_tr, mock_br, "2026-03")

        call_args = mock_tr.execute_query.call_args
        query, params = call_args[0]
        self.assertIn("'-3 hours') >=", query)
        self.assertIn("'-3 hours') < ?", query)
        self.assertEqual(params, ("2026-02-09", "2026-03-09"))

    # ── get_yearly_view ──

    def _make_yearly_mocks(self, installment_rows, period=None):
        mock_tr = MagicMock()
        mock_tr.execute_query.return_value.fetchall.return_value = installment_rows
        mock_br = MagicMock()
        mock_br.get_billing_period.return_value = period
        return mock_tr, mock_br

    def test_get_yearly_view_returns_12_entries(self):
        svc = _make_service()
        svc.repo.get_all.return_value = []
        with patch("services.recurrences_service.TransactionRepository") as MockTR, \
             patch("services.recurrences_service.BillRepository") as MockBR, \
             patch("services.recurrences_service._date") as mock_date:
            mock_date.today.return_value.strftime.return_value = "2026-03"
            mock_tr, mock_br = self._make_yearly_mocks([])
            MockTR.return_value = mock_tr
            MockBR.return_value = mock_br
            result = svc.get_yearly_view(2026)

        self.assertEqual(len(result), 12)
        months = [r["month"] for r in result]
        self.assertEqual(months[0], "2026-01")
        self.assertEqual(months[-1], "2026-12")

    def test_get_yearly_view_past_months_not_projected(self):
        svc = _make_service()
        svc.repo.get_all.return_value = []
        with patch("services.recurrences_service.TransactionRepository") as MockTR, \
             patch("services.recurrences_service.BillRepository") as MockBR, \
             patch("services.recurrences_service._date") as mock_date:
            mock_date.today.return_value.strftime.return_value = "2026-06"
            mock_tr, mock_br = self._make_yearly_mocks([])
            MockTR.return_value = mock_tr
            MockBR.return_value = mock_br
            result = svc.get_yearly_view(2026)

        past = [r for r in result if r["month"] <= "2026-06"]
        future = [r for r in result if r["month"] > "2026-06"]
        self.assertTrue(all(not r["projected"] for r in past))
        self.assertTrue(all(r["projected"] for r in future))

    def test_get_yearly_view_projects_remaining_installments(self):
        """An installment at 2/12 has 10 remaining, so it appears in deltas 1-10."""
        svc = _make_service()
        svc.repo.get_all.return_value = []
        installment_row = {
            "id": "t1", "description": "Amazon 2/12", "category_id": None,
            "amount": 100.0, "installment_number": 2, "total_installments": 12,
            "date": "2026-03-15",
        }
        with patch("services.recurrences_service.TransactionRepository") as MockTR, \
             patch("services.recurrences_service.BillRepository") as MockBR, \
             patch("services.recurrences_service._date") as mock_date:
            mock_date.today.return_value.strftime.return_value = "2026-03"
            mock_tr, mock_br = self._make_yearly_mocks([installment_row])
            MockTR.return_value = mock_tr
            MockBR.return_value = mock_br
            result = svc.get_yearly_view(2026)

        # Apr (delta=1) through Dec (delta=9): remaining=10 >= delta -> all included
        future = [r for r in result if r["projected"]]
        self.assertEqual(len(future), 9)  # Apr-Dec
        self.assertTrue(all(r["installments"] == 100.0 for r in future))

    def test_get_yearly_view_drops_installment_when_exhausted(self):
        """An installment at 11/12 has 1 remaining; only delta=1 gets it."""
        svc = _make_service()
        svc.repo.get_all.return_value = []
        installment_row = {
            "id": "t1", "description": "Amazon 11/12", "category_id": None,
            "amount": 50.0, "installment_number": 11, "total_installments": 12,
            "date": "2026-03-15",
        }
        with patch("services.recurrences_service.TransactionRepository") as MockTR, \
             patch("services.recurrences_service.BillRepository") as MockBR, \
             patch("services.recurrences_service._date") as mock_date:
            mock_date.today.return_value.strftime.return_value = "2026-03"
            mock_tr, mock_br = self._make_yearly_mocks([installment_row])
            MockTR.return_value = mock_tr
            MockBR.return_value = mock_br
            result = svc.get_yearly_view(2026)

        april = next(r for r in result if r["month"] == "2026-04")
        may = next(r for r in result if r["month"] == "2026-05")
        self.assertEqual(april["installments"], 50.0)
        self.assertEqual(may["installments"], 0.0)

    def test_get_yearly_view_closes_repos(self):
        svc = _make_service()
        svc.repo.get_all.return_value = []
        with patch("services.recurrences_service.TransactionRepository") as MockTR, \
             patch("services.recurrences_service.BillRepository") as MockBR, \
             patch("services.recurrences_service._date") as mock_date:
            mock_date.today.return_value.strftime.return_value = "2026-03"
            mock_tr, mock_br = self._make_yearly_mocks([])
            MockTR.return_value = mock_tr
            MockBR.return_value = mock_br
            svc.get_yearly_view(2026)
            mock_tr.close.assert_called_once()
            mock_br.close.assert_called_once()

    # ── get_installments ──

    def test_get_installments_pct_paid_calculation(self):
        svc = _make_service()
        item = {
            "id": "t1", "description": "Test", "category_id": None,
            "amount": 100.0, "installment_number": 3, "total_installments": 12,
            "date": "2026-03-10", "pct_paid": round(3 / 12, 4),
        }
        with patch.object(svc, "_get_installment_items", return_value=[item]):
            with patch("services.recurrences_service.TransactionRepository") as MockTR:
                MockTR.return_value = MagicMock()
                result = svc.get_installments("2026-03")

        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result[0]["pct_paid"], 0.25)

    # ── _project_installments ──

    def test_project_installments_advances_installment_number(self):
        svc = _make_service()
        base = [{"id": "t1", "description": "TV 3/12", "category_id": None,
                 "amount": 100.0, "installment_number": 3, "total_installments": 12,
                 "date": "2026-03-10", "pct_paid": 0.25}]
        result = svc._project_installments(base, "2026-03", "2026-05")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["installment_number"], 5)
        self.assertAlmostEqual(result[0]["pct_paid"], round(5 / 12, 4))

    def test_project_installments_excludes_exhausted(self):
        svc = _make_service()
        base = [{"id": "t1", "description": "TV 11/12", "category_id": None,
                 "amount": 100.0, "installment_number": 11, "total_installments": 12,
                 "date": "2026-03-10", "pct_paid": round(11 / 12, 4)}]
        # delta=2: remaining=1 < 2, should be excluded
        result = svc._project_installments(base, "2026-03", "2026-05")
        self.assertEqual(len(result), 0)

    def test_project_installments_includes_last_installment(self):
        svc = _make_service()
        base = [{"id": "t1", "description": "TV 11/12", "category_id": None,
                 "amount": 100.0, "installment_number": 11, "total_installments": 12,
                 "date": "2026-03-10", "pct_paid": round(11 / 12, 4)}]
        # delta=1: remaining=1 >= 1, should be included as installment 12
        result = svc._project_installments(base, "2026-03", "2026-04")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["installment_number"], 12)

    def test_get_installments_future_month_uses_projection(self):
        svc = _make_service()
        base_item = {"id": "t1", "description": "TV 3/12", "category_id": None,
                     "amount": 100.0, "installment_number": 3, "total_installments": 12,
                     "date": "2026-03-10", "pct_paid": 0.25}
        with patch("services.recurrences_service.TransactionRepository") as MockTR, \
             patch("services.recurrences_service.BillRepository") as MockBR, \
             patch("services.recurrences_service._date") as mock_date:
            mock_date.today.return_value.strftime.return_value = "2026-03"
            mock_tr = MagicMock()
            mock_tr.execute_query.return_value.fetchall.return_value = [base_item]
            MockTR.return_value = mock_tr
            mock_br = MagicMock()
            mock_br.get_billing_period.return_value = None
            MockBR.return_value = mock_br
            with patch.object(svc, "_get_installment_items", return_value=[base_item]):
                result = svc.get_installments("2026-06")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["installment_number"], 6)

    def test_get_installments_closes_repos(self):
        svc = _make_service()
        with patch("services.recurrences_service.TransactionRepository") as MockTR, \
             patch("services.recurrences_service.BillRepository") as MockBR:
            mock_tr = MagicMock()
            mock_tr.execute_query.return_value.fetchall.return_value = []
            MockTR.return_value = mock_tr
            mock_br = MagicMock()
            mock_br.get_billing_period.return_value = None
            MockBR.return_value = mock_br
            svc.get_installments("2026-03")
            mock_tr.close.assert_called_once()
            mock_br.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
