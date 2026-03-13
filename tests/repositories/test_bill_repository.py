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
                total_amount REAL,
                total_amount_currency_code TEXT,
                minimum_payment_amount REAL,
                allows_installments INTEGER DEFAULT 0,
                finance_charges TEXT
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

    def test_upsert_bill_existing_ignored(self):
        """upsert usa INSERT OR IGNORE — registro existente não é sobrescrito."""
        bill_data = {
            "id": "bill-1",
            "dueDate": "2026-04-10",
            "totalAmount": 1000.0,
            "totalAmountCurrencyCode": "BRL",
            "minimumPaymentAmount": 100.0,
            "allowsInstallments": False,
            "financeCharges": None,
        }
        self.repo.upsert_bill(bill_data, "account-1")

        bill_data["totalAmount"] = 1200.0
        result = self.repo.upsert_bill(bill_data, "account-1")

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "ignored")
        # Valor original preservado
        bills = self.repo.get_all_bills()
        self.assertEqual(len(bills), 1)
        self.assertEqual(bills[0]["total_amount"], 1000.0)

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


if __name__ == "__main__":
    unittest.main()
