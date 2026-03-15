"""Testes para BillRepository"""

import json
import unittest
from repositories.bill_repository import BillRepository


class TestBillRepository(unittest.TestCase):
    def setUp(self):
        self.repo = BillRepository(db_path=":memory:")
        self.repo.execute_query(
            """
            CREATE TABLE bills (
                id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                due_date TEXT,
                open_date TEXT,
                close_date TEXT,
                total_amount REAL,
                total_amount_currency_code TEXT,
                minimum_payment_amount REAL,
                allows_installments INTEGER DEFAULT 0,
                finance_charges TEXT
            )
            """
        )
        self.repo.execute_query(
            """
            CREATE TABLE credit_transactions (
                id TEXT PRIMARY KEY,
                date TEXT,
                description TEXT,
                amount REAL,
                excluded INTEGER DEFAULT 0
            )
            """
        )

    def tearDown(self):
        self.repo.close()

    # ------------------------------------------------------------------
    # upsert_bill
    # ------------------------------------------------------------------

    def test_upsert_bill_insert_new(self):
        bill_data = {
            "id": "bill-1",
            "dueDate": "2026-04-10",
            "totalAmount": 1500.0,
            "totalAmountCurrencyCode": "BRL",
            "minimumPaymentAmount": 150.0,
            "allowsInstallments": True,
            "financeCharges": None,
        }
        result = self.repo.upsert_bill(bill_data, "account-1")

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "inserted")

        bills = self.repo.get_all_bills()
        self.assertEqual(len(bills), 1)
        self.assertEqual(bills[0]["id"], "bill-1")
        self.assertEqual(bills[0]["account_id"], "account-1")
        self.assertEqual(bills[0]["total_amount"], 1500.0)
        self.assertEqual(bills[0]["allows_installments"], 1)

    def test_upsert_bill_derives_close_date_from_due_date(self):
        """close_date is derived as due_date - 7 days when API does not return it."""
        self.repo.upsert_bill(
            {"id": "bill-1", "dueDate": "2026-04-10", "totalAmount": 1000.0, "financeCharges": None},
            "account-1",
        )
        bills = self.repo.get_all_bills()
        self.assertEqual(bills[0]["close_date"], "2026-04-03")
        self.assertIsNone(bills[0]["open_date"])

    def test_upsert_bill_existing_updated(self):
        """smart_merge updates mutable fields on re-sync."""
        bill_data = {
            "id": "bill-1",
            "dueDate": "2026-04-10",
            "totalAmount": 1000.0,
            "financeCharges": None,
        }
        self.repo.upsert_bill(bill_data, "account-1")
        bill_data["totalAmount"] = 1200.0
        result = self.repo.upsert_bill(bill_data, "account-1")
        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "updated")

    def test_upsert_bill_allows_installments_false(self):
        bill_data = {
            "id": "bill-2",
            "dueDate": "2026-05-10",
            "totalAmount": 500.0,
            "totalAmountCurrencyCode": "BRL",
            "minimumPaymentAmount": 50.0,
            "allowsInstallments": False,
            "financeCharges": None,
        }
        self.repo.upsert_bill(bill_data, "account-1")

        bills = self.repo.get_all_bills()
        self.assertEqual(bills[0]["allows_installments"], 0)

    def test_upsert_bill_with_finance_charges(self):
        charges = [{"type": "INTEREST", "amount": 25.50}]
        bill_data = {
            "id": "bill-3",
            "dueDate": "2026-06-10",
            "totalAmount": 800.0,
            "totalAmountCurrencyCode": "BRL",
            "minimumPaymentAmount": 80.0,
            "allowsInstallments": False,
            "financeCharges": charges,
        }
        self.repo.upsert_bill(bill_data, "account-2")

        bills = self.repo.get_all_bills()
        self.assertEqual(bills[0]["finance_charges"], charges)

    def test_upsert_bill_without_optional_fields(self):
        bill_data = {"id": "bill-4"}
        result = self.repo.upsert_bill(bill_data, "account-1")

        self.assertTrue(result["success"])
        bills = self.repo.get_all_bills()
        self.assertIsNone(bills[0]["due_date"])
        self.assertIsNone(bills[0]["total_amount"])
        self.assertIsNone(bills[0]["finance_charges"])

    # ------------------------------------------------------------------
    # get_all_bills
    # ------------------------------------------------------------------

    def test_get_all_bills_empty(self):
        self.assertEqual(self.repo.get_all_bills(), [])

    def test_get_all_bills_ordered_by_due_date_desc(self):
        for bill_id, due_date in [("b1", "2026-03-01"), ("b2", "2026-05-01"), ("b3", "2026-04-01")]:
            self.repo.upsert_bill(
                {"id": bill_id, "dueDate": due_date, "totalAmount": 100.0, "financeCharges": None},
                "account-1",
            )

        bills = self.repo.get_all_bills()
        due_dates = [b["due_date"] for b in bills]
        self.assertEqual(due_dates, ["2026-05-01", "2026-04-01", "2026-03-01"])

    def test_get_all_bills_finance_charges_none_stays_none(self):
        self.repo.upsert_bill(
            {"id": "b1", "dueDate": "2026-03-01", "totalAmount": 100.0, "financeCharges": None},
            "account-1",
        )
        bills = self.repo.get_all_bills()
        self.assertIsNone(bills[0]["finance_charges"])

    # ------------------------------------------------------------------
    # get_current_and_future_bill
    # ------------------------------------------------------------------

    def test_get_current_and_future_bill_returns_sums(self):
        """Retorna (soma do mês atual, soma do mês seguinte)."""
        self.repo.upsert_bill(
            {"id": "b-cur-1", "dueDate": "2026-03-05", "totalAmount": 500.0, "financeCharges": None},
            "account-1",
        )
        self.repo.upsert_bill(
            {"id": "b-cur-2", "dueDate": "2026-03-20", "totalAmount": 300.0, "financeCharges": None},
            "account-1",
        )
        self.repo.upsert_bill(
            {"id": "b-fut-1", "dueDate": "2026-04-10", "totalAmount": 700.0, "financeCharges": None},
            "account-1",
        )

        current, future = self.repo.get_current_and_future_bill("2026-03")

        self.assertAlmostEqual(current, 800.0)
        self.assertAlmostEqual(future, 700.0)

    def test_get_current_and_future_bill_december_wraps_to_january(self):
        """Em dezembro o mês seguinte deve ser janeiro do ano seguinte."""
        self.repo.upsert_bill(
            {"id": "b-dec", "dueDate": "2026-12-15", "totalAmount": 400.0, "financeCharges": None},
            "account-1",
        )
        self.repo.upsert_bill(
            {"id": "b-jan", "dueDate": "2027-01-10", "totalAmount": 200.0, "financeCharges": None},
            "account-1",
        )

        current, future = self.repo.get_current_and_future_bill("2026-12")

        self.assertAlmostEqual(current, 400.0)
        self.assertAlmostEqual(future, 200.0)

    def test_get_current_and_future_bill_empty_returns_zeros(self):
        """Sem faturas no período retorna (0.0, 0.0)."""
        current, future = self.repo.get_current_and_future_bill("2026-03")
        self.assertEqual(current, 0.0)
        self.assertEqual(future, 0.0)


    # ------------------------------------------------------------------
    # get_billing_period
    # ------------------------------------------------------------------

    def _insert_due(self, bill_id, due_date):
        self.repo.upsert_bill(
            {"id": bill_id, "dueDate": due_date, "totalAmount": 100.0, "financeCharges": None},
            "account-1",
        )

    def test_get_billing_period_primary_path_overlap(self):
        """Primary: returns open/close dates of bill whose period overlaps month M."""
        self.repo.execute_query(
            """INSERT INTO bills (id, account_id, due_date, open_date, close_date, total_amount)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("b1", "account-1", "2026-04-08", "2026-02-28", "2026-04-01", 500.0),
        )
        start, end = self.repo.get_billing_period("2026-03")
        self.assertEqual(start, "2026-02-28")
        self.assertEqual(end, "2026-04-01")

    def test_get_billing_period_primary_open_date_inclusive_for_feb28(self):
        """open_date 2026-02-28 is returned as start so Feb 28 transactions are included."""
        self.repo.execute_query(
            """INSERT INTO bills (id, account_id, due_date, open_date, close_date, total_amount)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("b1", "account-1", "2026-04-08", "2026-02-28", "2026-04-01", 500.0),
        )
        start, end = self.repo.get_billing_period("2026-03")
        # start is inclusive: callers must use >= start to include transactions on this date
        self.assertEqual(start, "2026-02-28")

    def test_get_billing_period_primary_excludes_non_overlapping_bill(self):
        """A bill that closed before month M started does not match."""
        self.repo.execute_query(
            """INSERT INTO bills (id, account_id, due_date, open_date, close_date, total_amount)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("b1", "account-1", "2026-02-08", "2025-12-31", "2026-01-31", 500.0),
        )
        # January bill doesn't overlap March → falls through to fallback
        # Fallback end = first_of_next = "2026-04-01" (exclusive close_date convention)
        start, end = self.repo.get_billing_period("2026-03")
        self.assertEqual(start, "2026-01-31")
        self.assertEqual(end, "2026-04-01")

    def test_get_billing_period_primary_takes_precedence_over_fallback(self):
        """When open_date/close_date overlap month M, they are used instead of the fallback."""
        # Overlapping bill (primary path)
        self.repo.execute_query(
            """INSERT INTO bills (id, account_id, due_date, open_date, close_date, total_amount)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("b1", "account-1", "2026-04-08", "2026-02-28", "2026-04-01", 500.0),
        )
        # Previous bill that would be chosen by fallback (close_date before March)
        self.repo.execute_query(
            """INSERT INTO bills (id, account_id, due_date, open_date, close_date, total_amount)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("b0", "account-1", "2026-03-09", None, "2026-01-31", 500.0),
        )
        start, end = self.repo.get_billing_period("2026-03")
        # Primary wins: returns b1's open/close, not fallback's (2026-01-31, 2026-03-31)
        self.assertEqual(start, "2026-02-28")
        self.assertEqual(end, "2026-04-01")

    def test_get_billing_period_fallback_uses_previous_close_date(self):
        """Fallback: when no overlapping bill, uses previous bill's close_date as open_date."""
        # February bill closed on 2026-02-28 (after recalculate_close_dates)
        # March bill not in DB yet (in-progress period)
        self.repo.execute_query(
            """INSERT INTO bills (id, account_id, due_date, open_date, close_date, total_amount)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("b1", "account-1", "2026-03-09", None, "2026-02-28", 500.0),
        )
        start, end = self.repo.get_billing_period("2026-03")
        self.assertEqual(start, "2026-02-28")  # previous bill's close_date (inclusive)
        self.assertEqual(end, "2026-04-01")    # first of next month (exclusive)

    def test_get_billing_period_handles_timestamp_format(self):
        """due_date stored as full ISO timestamp does not break the query."""
        self.repo.execute_query(
            """INSERT INTO bills (id, account_id, due_date, open_date, close_date, total_amount)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("b1", "account-1", "2026-04-08T00:00:00.000Z", "2026-02-28", "2026-04-01", 100.0),
        )
        start, end = self.repo.get_billing_period("2026-03")
        self.assertEqual(start, "2026-02-28")
        self.assertEqual(end, "2026-04-01")

    def test_get_billing_period_returns_none_empty_table(self):
        self.assertIsNone(self.repo.get_billing_period("2026-03"))

    def test_get_billing_period_returns_none_no_previous_close(self):
        """Returns None when there is no previous bill close_date to anchor the period."""
        # Only a future bill exists (its close_date is after March starts)
        self._insert_due("b1", "2026-05-09")  # close_date = 2026-05-02, after 2026-03-01
        self.assertIsNone(self.repo.get_billing_period("2026-03"))

    # ------------------------------------------------------------------
    # recalculate_close_dates
    # ------------------------------------------------------------------

    def _insert_credit_txn(self, txn_id, date_str, description):
        self.repo.execute_query(
            "INSERT INTO credit_transactions (id, date, description, amount) VALUES (?, ?, ?, ?)",
            (txn_id, date_str, description, 100.0),
        )

    def test_recalculate_uses_last_installment_midnight_transaction(self):
        """close_date is set to the date of the last midnight installment in the window."""
        self._insert_due("b1", "2026-03-09")
        # Midnight installment on 2026-02-28 → close_date should be 2026-02-28
        self._insert_credit_txn("t1", "2026-02-28T03:00:00.000Z", "Produto 2/6")
        self._insert_credit_txn("t2", "2026-02-15T14:23:11.001Z", "Produto 1/6")

        self.repo.recalculate_close_dates("account-1")

        bills = self.repo.get_all_bills()
        self.assertEqual(bills[0]["close_date"], "2026-02-28")

    def test_recalculate_fallback_when_no_installment_transaction(self):
        """Falls back to due_date - 7 days when no qualifying transaction is found."""
        self._insert_due("b1", "2026-03-09")

        self.repo.recalculate_close_dates("account-1")

        bills = self.repo.get_all_bills()
        self.assertEqual(bills[0]["close_date"], "2026-03-02")

    def test_recalculate_sets_open_date_from_previous_close(self):
        """open_date of bill N = close_date of bill N-1."""
        self._insert_due("b1", "2026-02-09")
        self._insert_due("b2", "2026-03-09")
        self._insert_credit_txn("t1", "2026-01-31T03:00:00.000Z", "Item 1/3")
        self._insert_credit_txn("t2", "2026-02-28T03:00:00.000Z", "Item 2/3")

        self.repo.recalculate_close_dates("account-1")

        bills = {b["id"]: b for b in self.repo.get_all_bills()}
        self.assertEqual(bills["b1"]["close_date"], "2026-01-31")
        self.assertIsNone(bills["b1"]["open_date"])
        self.assertEqual(bills["b2"]["close_date"], "2026-02-28")
        self.assertEqual(bills["b2"]["open_date"], "2026-01-31")

    def test_recalculate_ignores_non_midnight_installments(self):
        """Transactions with specific times (not midnight) are not used as close_date."""
        self._insert_due("b1", "2026-03-09")
        self._insert_credit_txn("t1", "2026-02-20T14:23:11.001Z", "Item 1/6")

        self.repo.recalculate_close_dates("account-1")

        bills = self.repo.get_all_bills()
        self.assertEqual(bills[0]["close_date"], "2026-03-02")  # fallback


if __name__ == "__main__":
    unittest.main()
