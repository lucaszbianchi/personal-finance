import json
from datetime import date, timedelta
from repositories.base_repository import BaseRepository


class BillRepository(BaseRepository):
    """Repositório para gerenciar faturas de cartão de crédito."""

    def upsert_bill(self, bill_data: dict, account_id: str) -> dict:
        """Insere ou atualiza uma fatura.

        close_date is initially derived as due_date - 7 days.
        Call recalculate_close_dates() after transaction sync for accurate values.
        """
        finance_charges = bill_data.get("financeCharges")
        due_date_raw = (bill_data.get("dueDate") or "")[:10]
        close_date = bill_data.get("closeDate") or (
            (date.fromisoformat(due_date_raw) - timedelta(days=7)).isoformat()
            if due_date_raw else None
        )
        payment_date_raw = (bill_data.get("paymentDate") or "")[:10]
        mapped_data = {
            "id": bill_data["id"],
            "account_id": account_id,
            "due_date": bill_data.get("dueDate"),
            "open_date": bill_data.get("openDate"),
            "close_date": close_date,
            "total_amount": bill_data.get("totalAmount"),
            "total_amount_currency_code": bill_data.get("totalAmountCurrencyCode"),
            "minimum_payment_amount": bill_data.get("minimumPaymentAmount"),
            "allows_installments": 1 if bill_data.get("allowsInstallments") else 0,
            "finance_charges": (
                json.dumps(finance_charges, ensure_ascii=False)
                if finance_charges is not None
                else None
            ),
            "is_open": 1 if bill_data.get("isOpen") else 0,
            "payment_date": payment_date_raw or None,
            "total_amount_paid": bill_data.get("totalAmountPaid"),
        }
        return self.upsert("bills", "id", mapped_data, strategy="smart_merge")

    def recalculate_close_dates(self, account_id: str) -> int:
        """Recalculates close_date and open_date for all bills of an account.

        close_date = date of the last installment transaction (description contains '/'
        and time is a synthetic midnight marker '%:00:00.000Z') within the billing window.
        Falls back to due_date - 7 days when no such transaction is found.
        open_date = close_date of the previous bill.

        Returns the number of bills updated.
        """
        rows = self.execute_query(
            "SELECT id, due_date FROM bills WHERE account_id = ? ORDER BY due_date",
            (account_id,),
        ).fetchall()

        updated = 0
        prev_close: str | None = None

        for row in rows:
            due_date_str = row["due_date"][:10]
            due_dt = date.fromisoformat(due_date_str)
            window_start = prev_close or (due_dt - timedelta(days=40)).isoformat()

            result = self.execute_query(
                """
                SELECT MAX(date(substr(date, 1, 19), '-3 hours')) AS last_date
                FROM credit_transactions
                WHERE description LIKE '%/%'
                  AND date LIKE '%:00:00.000Z'
                  AND date(substr(date, 1, 19), '-3 hours') > ?
                  AND date(substr(date, 1, 19), '-3 hours') <= ?
                """,
                (window_start, due_date_str),
            ).fetchone()

            last_installment_date = result[0] if result and result[0] else None
            close_date = last_installment_date or (due_dt - timedelta(days=7)).isoformat()
            open_date = prev_close

            self.execute_query(
                "UPDATE bills SET close_date = ?, open_date = ? WHERE id = ?",
                (close_date, open_date, row["id"]),
            )
            updated += 1
            prev_close = close_date

        return updated

    def recalculate_all_close_dates(self) -> int:
        """Runs recalculate_close_dates for every account that has bills."""
        account_rows = self.execute_query(
            "SELECT DISTINCT account_id FROM bills"
        ).fetchall()
        return sum(self.recalculate_close_dates(row["account_id"]) for row in account_rows)

    def get_current_and_future_bill(self, month: str) -> tuple[float, float]:
        """Returns (current_bill, future_bill) totals for the given month and next month."""
        from datetime import datetime, date
        year, mon = int(month[:4]), int(month[5:7])
        # current: due_date in this month
        current_row = self.execute_query(
            "SELECT COALESCE(SUM(total_amount), 0) FROM bills WHERE strftime('%Y-%m', due_date) = ?",
            (month,),
        ).fetchone()
        # future: due_date in next month
        if mon == 12:
            next_month = f"{year + 1}-01"
        else:
            next_month = f"{year}-{mon + 1:02d}"
        future_row = self.execute_query(
            "SELECT COALESCE(SUM(total_amount), 0) FROM bills WHERE strftime('%Y-%m', due_date) = ?",
            (next_month,),
        ).fetchone()
        return float(current_row[0] or 0), float(future_row[0] or 0)

    def get_billing_period(self, month: str) -> tuple[str, str] | None:
        """Returns (open_date, close_date) for the billing period of the given month.

        open_date is inclusive: transactions ON open_date belong to this bill.
        close_date is exclusive: the last included day is close_date - 1.

        Primary: finds the bill whose recalculated (open_date, close_date) overlaps month M.
        Fallback: the previous bill's close_date becomes the open_date for an in-progress
                  period (bill not yet created by the bank); end = last day of month M.

        Returns None if no billing data is available.
        """
        year, mon = int(month[:4]), int(month[5:7])
        first_of_month = month + "-01"
        first_of_next = (
            f"{year + 1}-01-01" if mon == 12 else f"{year}-{mon + 1:02d}-01"
        )

        # Primary: bill whose close_date falls within month M.
        # close_date is exclusive (last included day = close_date - 1), so a bill
        # with close_date = first_of_next (e.g. "2026-04-01") is still a March bill.
        row = self.execute_query(
            """
            SELECT open_date, close_date
            FROM bills
            WHERE open_date IS NOT NULL
              AND close_date IS NOT NULL
              AND close_date > ?
              AND close_date <= ?
            ORDER BY close_date ASC
            LIMIT 1
            """,
            (first_of_month, first_of_next),
        ).fetchone()

        if row:
            return (row["open_date"], row["close_date"])

        # Fallback: use the latest previous bill's close_date as the open_date for
        # an in-progress period (e.g. current month when the bill hasn't closed yet)
        prev = self.execute_query(
            """
            SELECT close_date
            FROM bills
            WHERE close_date IS NOT NULL
              AND close_date < ?
            ORDER BY close_date DESC
            LIMIT 1
            """,
            (first_of_month,),
        ).fetchone()

        if prev:
            return (prev["close_date"], first_of_next)

        return None

    def get_billing_periods_bulk(self, months: list[str]) -> dict[str, tuple[str, str] | None]:
        """Return {month: (open_date, close_date) | None} for each requested month.

        Applies the same primary/fallback logic as get_billing_period() but fetches
        all bills in a single query, eliminating per-month round-trips.
        """
        if not months:
            return {}
        rows = self.execute_query(
            "SELECT open_date, close_date FROM bills WHERE close_date IS NOT NULL ORDER BY close_date ASC"
        ).fetchall()

        result = {}
        for month in months:
            year, mon = int(month[:4]), int(month[5:7])
            first_of_month = month + "-01"
            first_of_next = f"{year + 1}-01-01" if mon == 12 else f"{year}-{mon + 1:02d}-01"

            period = None
            for row in rows:
                if row["open_date"] and row["close_date"] > first_of_month and row["close_date"] <= first_of_next:
                    period = (row["open_date"], row["close_date"])
                    break

            if period is None:
                prev_close = None
                for row in rows:
                    if row["close_date"] < first_of_month:
                        prev_close = row["close_date"]
                if prev_close:
                    period = (prev_close, first_of_next)

            result[month] = period
        return result

    def get_bill_metadata(self, month: str) -> dict:
        """Returns is_open and payment_date for the most recent bill in the given month."""
        row = self.execute_query(
            """
            SELECT is_open, payment_date
            FROM bills
            WHERE strftime('%Y-%m', due_date) = ?
            ORDER BY due_date DESC LIMIT 1
            """,
            (month,),
        ).fetchone()
        if not row:
            return {}
        return {
            "is_open": bool(row["is_open"]) if row["is_open"] is not None else None,
            "payment_date": row["payment_date"],
        }

    def get_all_bills(self) -> list:
        """Retorna todas as faturas."""
        cursor = self.execute_query("SELECT * FROM bills ORDER BY due_date DESC")
        rows = cursor.fetchall()
        result = []
        for row in rows:
            bill = dict(row)
            if bill.get("finance_charges"):
                bill["finance_charges"] = json.loads(bill["finance_charges"])
            result.append(bill)
        return result
