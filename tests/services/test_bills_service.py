"""Tests for BillsService"""

import unittest
from datetime import date
from unittest.mock import MagicMock, call, patch

from services.bills_service import BillsService


def _make_service():
    with patch("services.bills_service.BillRepository"), \
         patch("services.bills_service.RecurrentExpensesRepository"), \
         patch("services.bills_service.TransactionRepository"):
        svc = BillsService()
    svc.bill_repo = MagicMock()
    svc.recurrence_repo = MagicMock()
    svc.transaction_repo = MagicMock()
    return svc


def _make_row(
    id="tx-1",
    description="Compra",
    amount=100.0,
    category_id=None,
    installment_number=None,
    total_installments=None,
    date_str="2026-02-15T12:00:00.000Z",
):
    return {
        "id": id,
        "description": description,
        "amount": amount,
        "category_id": category_id,
        "installment_number": installment_number,
        "total_installments": total_installments,
        "date": date_str,
    }


def _cursor_returning(rows):
    cursor = MagicMock()
    cursor.fetchall.return_value = rows
    return cursor


class TestBillsServiceClassify(unittest.TestCase):

    # ── _classify ──

    def test_classify_installment_db_columns(self):
        row = _make_row(installment_number=3, total_installments=6)
        self.assertEqual(BillsService._classify(row, []), "installment")

    def test_classify_installment_description(self):
        row = _make_row(description="Compra 2/10")
        self.assertEqual(BillsService._classify(row, []), "installment")

    def test_classify_recurrent(self):
        row = _make_row(description="NETFLIX *STREAMING")
        self.assertEqual(BillsService._classify(row, ["netflix"]), "recurrent")

    def test_classify_one_off(self):
        row = _make_row(description="Restaurante X")
        self.assertEqual(BillsService._classify(row, ["netflix"]), "one_off")

    def test_classify_installment_priority(self):
        # matches both installment pattern and merchant name — installment wins
        row = _make_row(description="NETFLIX 1/12")
        self.assertEqual(BillsService._classify(row, ["netflix"]), "installment")


class TestBillsServiceGetMonthly(unittest.TestCase):

    # ── get_monthly ──

    def test_get_monthly_shape(self):
        svc = _make_service()
        svc.bill_repo.get_billing_period.return_value = ("2026-01-20", "2026-02-18")
        svc.bill_repo.get_bill_metadata.return_value = {"payment_date": "2026-02-10"}
        svc.transaction_repo.execute_query.return_value = _cursor_returning([])
        svc.recurrence_repo.get_all.return_value = []

        result = svc.get_monthly("2026-02")

        for key in ("month", "total", "installments", "recurrent", "one_off",
                    "is_open", "payment_date", "transactions", "is_projected"):
            self.assertIn(key, result)

    def test_get_monthly_totals(self):
        svc = _make_service()
        svc.bill_repo.get_billing_period.return_value = ("2026-01-20", "2026-02-18")
        svc.bill_repo.get_bill_metadata.return_value = {}
        svc.transaction_repo.execute_query.return_value = _cursor_returning([
            _make_row(id="a", amount=50.0, total_installments=3, installment_number=1),
            _make_row(id="b", description="NETFLIX", amount=30.0),
            _make_row(id="c", description="Jantar", amount=20.0),
        ])
        svc.recurrence_repo.get_all.return_value = [{"merchant_name": "Netflix"}]

        result = svc.get_monthly("2026-02")

        self.assertAlmostEqual(result["total"], 100.0)
        self.assertAlmostEqual(result["installments"], 50.0)
        self.assertAlmostEqual(result["recurrent"], 30.0)
        self.assertAlmostEqual(result["one_off"], 20.0)
        self.assertFalse(result["is_projected"])

    def test_get_monthly_uses_billing_period(self):
        svc = _make_service()
        svc.bill_repo.get_billing_period.return_value = ("2026-01-20", "2026-02-18")
        svc.bill_repo.get_bill_metadata.return_value = {}
        svc.transaction_repo.execute_query.return_value = _cursor_returning([])
        svc.recurrence_repo.get_all.return_value = []

        svc.get_monthly("2026-02")

        call_args = svc.transaction_repo.execute_query.call_args
        sql, params = call_args[0]
        self.assertIn(">=", sql)
        self.assertIn("< ?", sql)
        self.assertEqual(params, ("2026-01-20", "2026-02-18"))

    def test_get_monthly_no_billing_period(self):
        svc = _make_service()
        svc.bill_repo.get_billing_period.return_value = None
        svc.bill_repo.get_bill_metadata.return_value = {}
        svc.transaction_repo.execute_query.return_value = _cursor_returning([])
        svc.recurrence_repo.get_all.return_value = []

        svc.get_monthly("2026-02")

        call_args = svc.transaction_repo.execute_query.call_args
        params = call_args[0][1]
        self.assertEqual(params, ("2026-02%",))

    def test_get_monthly_transactions_have_classification(self):
        svc = _make_service()
        svc.bill_repo.get_billing_period.return_value = None
        svc.bill_repo.get_bill_metadata.return_value = {}
        svc.transaction_repo.execute_query.return_value = _cursor_returning(
            [_make_row(id="x", amount=10.0)]
        )
        svc.recurrence_repo.get_all.return_value = []

        result = svc.get_monthly("2026-02")

        self.assertEqual(len(result["transactions"]), 1)
        self.assertIn("classification", result["transactions"][0])

    def test_get_monthly_empty(self):
        svc = _make_service()
        svc.bill_repo.get_billing_period.return_value = None
        svc.bill_repo.get_bill_metadata.return_value = {}
        svc.transaction_repo.execute_query.return_value = _cursor_returning([])
        svc.recurrence_repo.get_all.return_value = []

        result = svc.get_monthly("2026-02")

        self.assertEqual(result["total"], 0.0)
        self.assertEqual(result["transactions"], [])

    def test_get_monthly_is_open_true_when_today_before_close(self):
        svc = _make_service()
        # close_date far in the future
        svc.bill_repo.get_billing_period.return_value = ("2026-02-18", "2099-12-31")
        svc.bill_repo.get_bill_metadata.return_value = {}
        svc.transaction_repo.execute_query.return_value = _cursor_returning([])
        svc.recurrence_repo.get_all.return_value = []

        result = svc.get_monthly("2026-02")

        self.assertTrue(result["is_open"])

    def test_get_monthly_is_open_false_when_today_after_close(self):
        svc = _make_service()
        # close_date in the past
        svc.bill_repo.get_billing_period.return_value = ("2026-01-01", "2026-01-18")
        svc.bill_repo.get_bill_metadata.return_value = {}
        svc.transaction_repo.execute_query.return_value = _cursor_returning([])
        svc.recurrence_repo.get_all.return_value = []

        result = svc.get_monthly("2026-01")

        self.assertFalse(result["is_open"])

    def test_get_monthly_is_open_none_when_no_period(self):
        svc = _make_service()
        svc.bill_repo.get_billing_period.return_value = None
        svc.bill_repo.get_bill_metadata.return_value = {}
        svc.transaction_repo.execute_query.return_value = _cursor_returning([])
        svc.recurrence_repo.get_all.return_value = []

        result = svc.get_monthly("2026-02")

        self.assertIsNone(result["is_open"])


class TestBillsServiceProjected(unittest.TestCase):

    # ── get_monthly (future/projected) ──

    def test_get_monthly_future_is_projected(self):
        svc = _make_service()
        svc.bill_repo.get_billing_period.return_value = None
        svc.transaction_repo.execute_query.return_value = _cursor_returning([])
        svc.recurrence_repo.get_all.return_value = []

        result = svc.get_monthly("2099-01")

        self.assertTrue(result["is_projected"])
        self.assertIsNone(result["is_open"])

    def test_get_monthly_future_no_one_off(self):
        svc = _make_service()
        svc.bill_repo.get_billing_period.return_value = None
        svc.transaction_repo.execute_query.return_value = _cursor_returning([])
        svc.recurrence_repo.get_all.return_value = []

        result = svc.get_monthly("2099-01")

        self.assertEqual(result["one_off"], 0.0)

    def test_get_monthly_future_projects_installments(self):
        svc = _make_service()
        # Current month has an installment 2/10 — should still appear 1 month ahead
        svc.bill_repo.get_billing_period.return_value = None
        svc.transaction_repo.execute_query.return_value = _cursor_returning([
            _make_row(id="inst", amount=100.0, installment_number=2, total_installments=10),
        ])
        svc.recurrence_repo.get_all.return_value = []

        # One month in the future relative to today
        today = date.today()
        m = today.month + 1
        y = today.year
        if m > 12:
            m = 1
            y += 1
        future = f"{y}-{m:02d}"

        result = svc.get_monthly(future)

        self.assertTrue(result["is_projected"])
        self.assertEqual(len(result["transactions"]), 1)
        self.assertEqual(result["transactions"][0]["classification"], "installment")
        self.assertAlmostEqual(result["installments"], 100.0)

    def test_get_monthly_future_expired_installment_excluded(self):
        svc = _make_service()
        # installment 10/10 — no remaining installments in the future
        svc.bill_repo.get_billing_period.return_value = None
        svc.transaction_repo.execute_query.return_value = _cursor_returning([
            _make_row(id="inst", amount=100.0, installment_number=10, total_installments=10),
        ])
        svc.recurrence_repo.get_all.return_value = []

        result = svc.get_monthly("2099-01")

        self.assertEqual(result["installments"], 0.0)
        self.assertEqual(result["transactions"], [])

    def test_get_monthly_future_includes_credit_recurrences(self):
        svc = _make_service()
        svc.bill_repo.get_billing_period.return_value = None
        svc.transaction_repo.execute_query.return_value = _cursor_returning([])
        svc.recurrence_repo.get_all.return_value = [
            {
                "id": "rec-1", "description": "Streaming", "amount": 45.0,
                "frequency": "monthly", "next_occurrence": None,
                "category_id": None, "merchant_name": "Netflix",
                "account_type": "credit",
            }
        ]

        result = svc.get_monthly("2099-01")

        self.assertEqual(len(result["transactions"]), 1)
        self.assertEqual(result["transactions"][0]["classification"], "recurrent")
        self.assertAlmostEqual(result["recurrent"], 45.0)

    def test_get_monthly_future_excludes_bank_recurrences(self):
        svc = _make_service()
        svc.bill_repo.get_billing_period.return_value = None
        svc.transaction_repo.execute_query.return_value = _cursor_returning([])
        svc.recurrence_repo.get_all.return_value = [
            {
                "id": "rec-bank", "description": "Aluguel", "amount": 1500.0,
                "frequency": "monthly", "next_occurrence": None,
                "category_id": None, "merchant_name": None,
                "account_type": "bank",
            }
        ]

        result = svc.get_monthly("2099-01")

        self.assertEqual(result["recurrent"], 0.0)
        self.assertEqual(result["transactions"], [])

    def test_get_monthly_future_excludes_null_account_type_recurrences(self):
        """Only explicit account_type='credit' recurrences appear in bill projections."""
        svc = _make_service()
        svc.bill_repo.get_billing_period.return_value = None
        svc.transaction_repo.execute_query.return_value = _cursor_returning([])
        svc.recurrence_repo.get_all.return_value = [
            {
                "id": "rec-manual", "description": "Plano", "amount": 30.0,
                "frequency": "monthly", "next_occurrence": None,
                "category_id": None, "merchant_name": None,
                "account_type": None,
            }
        ]

        result = svc.get_monthly("2099-01")

        self.assertEqual(result["recurrent"], 0.0)
        self.assertEqual(result["transactions"], [])


class TestBillsServiceGetHistory(unittest.TestCase):

    # ── get_history ──

    def test_get_history_asc_order(self):
        svc = _make_service()
        svc.bill_repo.get_billing_periods_bulk.side_effect = lambda months: {m: None for m in months}
        svc.transaction_repo.execute_query.return_value.fetchone.return_value = (100.0,)

        result = svc.get_history(months=3)

        self.assertEqual(len(result), 3)
        # Result must be in ascending order (oldest month first)
        self.assertLessEqual(result[0]["month"], result[1]["month"])
        self.assertLessEqual(result[1]["month"], result[2]["month"])

    def test_get_history_uses_transaction_sum(self):
        """get_history must NOT call bill_repo.get_history — it queries transactions directly."""
        svc = _make_service()
        svc.bill_repo.get_billing_periods_bulk.side_effect = lambda months: {m: None for m in months}
        svc.transaction_repo.execute_query.return_value.fetchone.return_value = (250.0,)

        result = svc.get_history(months=1)

        svc.bill_repo.get_history.assert_not_called()
        self.assertEqual(result[0]["total"], 250.0)

    def test_get_history_uses_billing_period_when_available(self):
        svc = _make_service()
        svc.bill_repo.get_billing_periods_bulk.side_effect = (
            lambda months: {m: ("2026-01-20", "2026-02-18") for m in months}
        )
        svc.transaction_repo.execute_query.return_value.fetchone.return_value = (300.0,)

        result = svc.get_history(months=1)

        call_args = svc.transaction_repo.execute_query.call_args
        sql, params = call_args[0]
        self.assertIn(">=", sql)
        self.assertEqual(params, ("2026-01-20", "2026-02-18"))
        self.assertEqual(result[0]["total"], 300.0)

    def test_get_history_calls_bulk_once(self):
        """get_billing_periods_bulk must be called exactly once regardless of month count."""
        svc = _make_service()
        svc.bill_repo.get_billing_periods_bulk.side_effect = lambda months: {m: None for m in months}
        svc.transaction_repo.execute_query.return_value.fetchone.return_value = (0.0,)

        svc.get_history(months=12)

        svc.bill_repo.get_billing_periods_bulk.assert_called_once()


if __name__ == "__main__":
    unittest.main()
