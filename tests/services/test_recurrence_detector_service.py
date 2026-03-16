"""Tests for RecurrenceDetectorService."""

import unittest
from unittest.mock import MagicMock, patch

import services.recurrence_detector_service as svc_module


def _make_bank(description, amount, date, excluded=0):
    t = MagicMock()
    t.description = description
    t.amount = amount
    t.date = date
    t.excluded = excluded
    t.category_id = None
    return t


def _make_credit(description, amount, date, excluded=0):
    t = MagicMock()
    t.description = description
    t.amount = amount
    t.date = date
    t.excluded = excluded
    t.category_id = None
    return t


def _make_service():
    with patch("services.recurrence_detector_service.TransactionRepository"), \
         patch("services.recurrence_detector_service.RecurrentExpensesRepository"):
        svc = svc_module.RecurrenceDetectorService()
    svc.transaction_repo = MagicMock()
    svc.recurrence_repo = MagicMock()
    return svc


# Three dates spanning distinct months — enough for detection
_D1 = "2026-01-05"
_D2 = "2026-02-05"
_D3 = "2026-03-05"


class TestGroupTransactions(unittest.TestCase):

    # ── _group_transactions ──

    def test_bank_expense_included(self):
        svc = _make_service()
        svc.transaction_repo.get_bank_transactions.return_value = [
            _make_bank("Netflix", -50.0, _D1)
        ]
        svc.transaction_repo.get_credit_transactions.return_value = []
        groups = svc._group_transactions()
        self.assertIn("netflix", groups)

    def test_bank_income_excluded(self):
        svc = _make_service()
        svc.transaction_repo.get_bank_transactions.return_value = [
            _make_bank("Salario", 5000.0, _D1)
        ]
        svc.transaction_repo.get_credit_transactions.return_value = []
        groups = svc._group_transactions()
        self.assertEqual(groups, {})

    def test_bank_excluded_flag_skipped(self):
        svc = _make_service()
        svc.transaction_repo.get_bank_transactions.return_value = [
            _make_bank("Netflix", -50.0, _D1, excluded=1)
        ]
        svc.transaction_repo.get_credit_transactions.return_value = []
        groups = svc._group_transactions()
        self.assertEqual(groups, {})

    def test_credit_expense_included(self):
        svc = _make_service()
        svc.transaction_repo.get_bank_transactions.return_value = []
        svc.transaction_repo.get_credit_transactions.return_value = [
            _make_credit("Spotify", 25.0, _D1)
        ]
        groups = svc._group_transactions()
        self.assertIn("spotify", groups)

    def test_credit_excluded_flag_skipped(self):
        svc = _make_service()
        svc.transaction_repo.get_bank_transactions.return_value = []
        svc.transaction_repo.get_credit_transactions.return_value = [
            _make_credit("Spotify", 25.0, _D1, excluded=1)
        ]
        groups = svc._group_transactions()
        self.assertEqual(groups, {})

    def test_installment_credit_excluded(self):
        svc = _make_service()
        svc.transaction_repo.get_bank_transactions.return_value = []
        svc.transaction_repo.get_credit_transactions.return_value = [
            _make_credit("Netflix 2/6", 50.0, _D1)
        ]
        groups = svc._group_transactions()
        self.assertEqual(groups, {})

    def test_installment_bank_excluded(self):
        svc = _make_service()
        svc.transaction_repo.get_bank_transactions.return_value = [
            _make_bank("Compra 1/3", -200.0, _D1)
        ]
        svc.transaction_repo.get_credit_transactions.return_value = []
        groups = svc._group_transactions()
        self.assertEqual(groups, {})


class TestAnalyze(unittest.TestCase):

    # ── _analyze ──

    def _entries(self, dates, amount=50.0):
        return [
            {"date": d, "amount": amount, "category_id": None, "description": "Test"}
            for d in dates
        ]

    def test_monthly_detected(self):
        svc = _make_service()
        entries = self._entries([_D1, _D2, _D3])
        result = svc._analyze("test", entries)
        self.assertIsNotNone(result)
        self.assertEqual(result["frequency"], "monthly")

    def test_annual_detected(self):
        svc = _make_service()
        entries = self._entries(["2024-03-01", "2025-03-01", "2026-03-01"])
        result = svc._analyze("annual service", entries)
        self.assertIsNotNone(result)
        self.assertEqual(result["frequency"], "annual")

    def test_insufficient_months_returns_none(self):
        svc = _make_service()
        entries = self._entries([_D1, _D2])  # only 2 distinct months
        result = svc._analyze("test", entries)
        self.assertIsNone(result)

    def test_amount_variance_too_high_returns_none(self):
        svc = _make_service()
        entries = [
            {"date": _D1, "amount": 50.0, "category_id": None, "description": "Test"},
            {"date": _D2, "amount": 65.0, "category_id": None, "description": "Test"},
            {"date": _D3, "amount": 50.0, "category_id": None, "description": "Test"},
        ]
        result = svc._analyze("test", entries)
        self.assertIsNone(result)

    def test_amount_variance_ok(self):
        svc = _make_service()
        entries = [
            {"date": _D1, "amount": 50.0, "category_id": None, "description": "Test"},
            {"date": _D2, "amount": 55.0, "category_id": None, "description": "Test"},
            {"date": _D3, "amount": 50.0, "category_id": None, "description": "Test"},
        ]
        result = svc._analyze("test", entries)
        self.assertIsNotNone(result)

    def test_unknown_interval_returns_none(self):
        svc = _make_service()
        # ~60-day intervals → not weekly, monthly, or annual
        entries = self._entries(["2026-01-01", "2026-03-01", "2026-05-01"])
        result = svc._analyze("bimonthly", entries)
        self.assertIsNone(result)


class TestAnalyzeAccountType(unittest.TestCase):

    # ── _analyze account_type ──

    def _entries(self, dates, source_type, amount=50.0):
        return [
            {"date": d, "amount": amount, "category_id": None,
             "description": "Test", "source_type": source_type}
            for d in dates
        ]

    def test_credit_only_entries_set_account_type_credit(self):
        svc = _make_service()
        entries = self._entries([_D1, _D2, _D3], "credit")
        result = svc._analyze("test", entries)
        self.assertEqual(result["account_type"], "credit")

    def test_bank_only_entries_set_account_type_bank(self):
        svc = _make_service()
        entries = self._entries([_D1, _D2, _D3], "bank")
        result = svc._analyze("test", entries)
        self.assertEqual(result["account_type"], "bank")

    def test_mixed_entries_set_account_type_both(self):
        svc = _make_service()
        entries = (
            self._entries([_D1, _D2], "credit") +
            self._entries([_D3], "bank")
        )
        result = svc._analyze("test", entries)
        self.assertEqual(result["account_type"], "both")

    def test_no_source_type_sets_account_type_none(self):
        svc = _make_service()
        entries = [
            {"date": d, "amount": 50.0, "category_id": None, "description": "Test"}
            for d in [_D1, _D2, _D3]
        ]
        result = svc._analyze("test", entries)
        self.assertIsNone(result["account_type"])


class TestGroupTransactionsSourceType(unittest.TestCase):

    # ── source_type tagging ──

    def test_bank_entries_tagged_bank(self):
        svc = _make_service()
        svc.transaction_repo.get_bank_transactions.return_value = [
            _make_bank("Netflix", -50.0, _D1)
        ]
        svc.transaction_repo.get_credit_transactions.return_value = []
        groups = svc._group_transactions()
        self.assertEqual(groups["netflix"][0]["source_type"], "bank")

    def test_credit_entries_tagged_credit(self):
        svc = _make_service()
        svc.transaction_repo.get_bank_transactions.return_value = []
        svc.transaction_repo.get_credit_transactions.return_value = [
            _make_credit("Spotify", 25.0, _D1)
        ]
        groups = svc._group_transactions()
        self.assertEqual(groups["spotify"][0]["source_type"], "credit")


class TestDetectAndStore(unittest.TestCase):

    # ── detect_and_store ──

    def _monthly_entries(self, description, amount=50.0):
        return [
            {"date": d, "amount": amount, "category_id": None, "description": description}
            for d in [_D1, _D2, _D3]
        ]

    def test_detect_and_store_returns_count(self):
        svc = _make_service()
        svc.recurrence_repo.has_any.return_value = False
        svc.transaction_repo.get_bank_transactions.return_value = []
        svc.transaction_repo.get_credit_transactions.return_value = []

        groups = {
            "netflix": self._monthly_entries("Netflix"),
            "spotify": self._monthly_entries("Spotify"),
        }
        with patch.object(svc, "_group_transactions", return_value=groups):
            count = svc.detect_and_store()

        self.assertEqual(count, 2)
        self.assertEqual(svc.recurrence_repo.upsert_recurrence.call_count, 2)

    def test_detect_and_store_skips_invalid(self):
        svc = _make_service()
        svc.recurrence_repo.has_any.return_value = False
        groups = {
            "netflix": self._monthly_entries("Netflix"),
            "rare": [
                {"date": _D1, "amount": 50.0, "category_id": None, "description": "Rare"},
                {"date": _D2, "amount": 50.0, "category_id": None, "description": "Rare"},
            ],
        }
        with patch.object(svc, "_group_transactions", return_value=groups):
            count = svc.detect_and_store()

        self.assertEqual(count, 1)
        self.assertEqual(svc.recurrence_repo.upsert_recurrence.call_count, 1)

    def test_detect_and_store_skips_when_table_not_empty(self):
        svc = _make_service()
        svc.recurrence_repo.has_any.return_value = True

        count = svc.detect_and_store()

        self.assertEqual(count, 0)
        svc.recurrence_repo.upsert_recurrence.assert_not_called()


if __name__ == "__main__":
    unittest.main()
