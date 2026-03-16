from datetime import date as _date

from repositories.bill_repository import BillRepository
from repositories.recurrent_expenses_repository import RecurrentExpensesRepository
from repositories.transaction_repository import TransactionRepository
from utils.installment_helper import INSTALLMENT_RE

_TX_FIELDS = (
    "id, description, category_id, amount, installment_number, total_installments, date"
)


class BillsService:
    def __init__(self):
        self.bill_repo = BillRepository()
        self.recurrence_repo = RecurrentExpensesRepository()
        self.transaction_repo = TransactionRepository()

    def get_monthly(self, month: str) -> dict:
        """Return bill breakdown for the given month (YYYY-MM).

        Future months return projections (installments + recurrences only).
        Past/current months return actual credit transactions, classified.
        """
        today = _date.today()
        current_month = today.strftime("%Y-%m")

        if month > current_month:
            return self._get_projected_monthly(month)

        period = self.bill_repo.get_billing_period(month)
        rows = [dict(r) for r in self._fetch_transactions(period, month).fetchall()]

        merchant_names = [
            r["merchant_name"].lower()
            for r in self.recurrence_repo.get_all()
            if r.get("merchant_name")
        ]

        transactions = []
        totals = {"installment": 0.0, "recurrent": 0.0, "one_off": 0.0}
        for row in rows:
            classification = self._classify(row, merchant_names)
            totals[classification] += row["amount"]
            transactions.append(
                {
                    "id": row["id"],
                    "description": row.get("description"),
                    "amount": row["amount"],
                    "date": row["date"],
                    "category_id": row.get("category_id"),
                    "classification": classification,
                }
            )

        # is_open: True only while the billing period is still accepting purchases
        is_open = None
        if period:
            _, close_date = period
            is_open = today.isoformat() < close_date

        metadata = self.bill_repo.get_bill_metadata(month)

        return {
            "month": month,
            "total": round(sum(totals.values()), 2),
            "installments": round(totals["installment"], 2),
            "recurrent": round(totals["recurrent"], 2),
            "one_off": round(totals["one_off"], 2),
            "is_open": is_open,
            "payment_date": metadata.get("payment_date"),
            "transactions": transactions,
            "is_projected": False,
        }

    def _get_projected_monthly(self, month: str) -> dict:
        """Return projected bill for a future month (installments + recurrences only)."""
        today = _date.today()
        current_month = today.strftime("%Y-%m")

        period = self.bill_repo.get_billing_period(current_month)
        current_rows = [
            dict(r) for r in self._fetch_transactions(period, current_month).fetchall()
        ]

        cy, cm = map(int, current_month.split("-"))
        ty, tm = map(int, month.split("-"))
        delta = (ty - cy) * 12 + (tm - cm)

        installment_txns = self._project_installments(current_rows, delta, month)
        recurrent_txns = self._project_recurrences(month)

        all_txns = installment_txns + recurrent_txns
        installments_total = round(sum(t["amount"] for t in installment_txns), 2)
        recurrent_total = round(sum(t["amount"] for t in recurrent_txns), 2)

        return {
            "month": month,
            "total": round(installments_total + recurrent_total, 2),
            "installments": installments_total,
            "recurrent": recurrent_total,
            "one_off": 0.0,
            "is_open": None,
            "payment_date": None,
            "transactions": all_txns,
            "is_projected": True,
        }

    def _fetch_transactions(self, period, month: str):
        if period:
            start_incl, end_excl = period
            return self.transaction_repo.execute_query(
                f"""
                SELECT {_TX_FIELDS}
                FROM credit_transactions
                WHERE excluded = 0
                  AND date(substr(date, 1, 19), '-3 hours') >= ?
                  AND date(substr(date, 1, 19), '-3 hours') < ?
                ORDER BY date
                """,
                (start_incl, end_excl),
            )
        return self.transaction_repo.execute_query(
            f"""
            SELECT {_TX_FIELDS}
            FROM credit_transactions
            WHERE excluded = 0
              AND date(substr(date, 1, 19), '-3 hours') LIKE ?
            ORDER BY date
            """,
            (f"{month}%",),
        )

    @staticmethod
    def _project_installments(
        current_rows: list[dict], delta: int, month: str
    ) -> list[dict]:
        result = []
        for row in current_rows:
            total = row.get("total_installments") or 0
            num = row.get("installment_number") or 0
            desc = row.get("description") or ""

            if not (total > 1 and num > 0):
                m = INSTALLMENT_RE.search(desc)
                if not m:
                    continue
                num = num or int(m.group(1))
                total = int(m.group(2))

            if (total - num) >= delta:
                result.append(
                    {
                        "id": row["id"],
                        "description": desc,
                        "amount": row["amount"],
                        "date": None,
                        "category_id": row.get("category_id"),
                        "classification": "installment",
                    }
                )
        return result

    def _project_recurrences(self, month: str) -> list[dict]:
        """Return recurrences relevant to the given month that originate from credit transactions.

        Only includes recurrences with account_type='credit'. 'both', 'bank', and NULL
        entries are excluded — NULL/manual entries cannot be confidently assigned to the
        credit card bill without a confirmed credit transaction match.
        """
        month_mm = month[5:7]
        result = []
        for rec in self.recurrence_repo.get_all():
            if rec.get("account_type") != "credit":
                continue
            freq = rec.get("frequency")
            next_occ = rec.get("next_occurrence") or ""
            if freq != "monthly" and next_occ[5:7] != month_mm:
                continue
            amount = rec.get("amount") or 0
            if amount > 0:
                result.append(
                    {
                        "id": rec["id"],
                        "description": rec.get("description"),
                        "amount": amount,
                        "date": None,
                        "category_id": rec.get("category_id"),
                        "classification": "recurrent",
                    }
                )
        return result

    @staticmethod
    def _classify(row: dict, merchant_names: list[str]) -> str:
        total = row.get("total_installments") or 0
        num = row.get("installment_number") or 0
        desc = row.get("description") or ""
        if (total > 1 and num > 0) or INSTALLMENT_RE.search(desc):
            return "installment"
        if any(m in desc.lower() for m in merchant_names):
            return "recurrent"
        return "one_off"

    def get_history(self, months: int = 12) -> list[dict]:
        """Return bill totals computed from transactions for last N months (ASC).

        Uses the same billing-period logic as get_monthly() for consistency with
        the header total shown on the Bills page. Fetches all billing periods in
        one query to avoid N+1 database calls.
        """
        today = _date.today()
        month_strs = []
        for delta in range(months - 1, -1, -1):
            m = today.month - delta
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            month_strs.append(f"{y}-{m:02d}")

        periods = self.bill_repo.get_billing_periods_bulk(month_strs)
        results = []
        for month_str in month_strs:
            period = periods[month_str]
            if period:
                start, end = period
                row = self.transaction_repo.execute_query(
                    "SELECT COALESCE(SUM(amount), 0) FROM credit_transactions"
                    " WHERE excluded = 0"
                    " AND date(substr(date, 1, 19), '-3 hours') >= ?"
                    " AND date(substr(date, 1, 19), '-3 hours') < ?",
                    (start, end),
                ).fetchone()
            else:
                row = self.transaction_repo.execute_query(
                    "SELECT COALESCE(SUM(amount), 0) FROM credit_transactions"
                    " WHERE excluded = 0"
                    " AND date(substr(date, 1, 19), '-3 hours') LIKE ?",
                    (f"{month_str}%",),
                ).fetchone()
            results.append({"month": month_str, "total": round(float(row[0] or 0), 2)})
        return results
