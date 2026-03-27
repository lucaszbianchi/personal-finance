import uuid
from datetime import datetime, date as _date

from repositories.bill_repository import BillRepository
from repositories.recurrent_expenses_repository import RecurrentExpensesRepository
from repositories.transaction_repository import TransactionRepository
from utils.date_helper import DateHelper as _DateHelper
from utils.installment_helper import INSTALLMENT_RE as _INSTALLMENT_RE


class RecurrencesService:
    """Business logic for recurrences CRUD, monthly view, and installments."""

    def __init__(self):
        self.repo = RecurrentExpensesRepository()

    def get_all(self) -> list[dict]:
        return self.repo.get_all()

    def create(self, data: dict) -> dict:
        """Create a manual recurrence. Generates uuid and sets source='manual'."""
        merchant = data.get("merchant_name")
        record = {
            "id": str(uuid.uuid4()),
            "description": data.get("description"),
            "amount": data.get("amount"),
            "frequency": data.get("frequency"),
            "next_occurrence": data.get("next_occurrence"),
            "category_id": data.get("category_id"),
            "merchant_name": merchant,
            "amount_min": data.get("amount_min"),
            "amount_max": data.get("amount_max"),
            "confidence": None,
            "source": "manual",
            "is_unavoidable": 1 if data.get("is_unavoidable") else 0,
            "synced_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "account_type": self._resolve_account_type(merchant),
        }
        self.repo.upsert_recurrence(record)
        return self.repo.get_by_id(record["id"])

    def update(self, id: str, data: dict) -> dict:
        """Update a recurrence. Raises ValueError if not found."""
        if "merchant_name" in data:
            data = {**data, "account_type": self._resolve_account_type(data["merchant_name"])}
        self.repo.update(id, data)
        return self.repo.get_by_id(id)

    def _resolve_account_type(self, merchant_name: str | None) -> str | None:
        """Return 'credit' if merchant_name matches a credit transaction, else None."""
        if not merchant_name:
            return None
        return "credit" if self.repo.has_matching_credit_transaction(merchant_name) else None

    def delete(self, id: str) -> None:
        """Delete a recurrence. Raises ValueError if not found."""
        self.repo.delete(id)

    def toggle_unavoidable(self, id: str) -> dict:
        """Flip is_unavoidable flag for a recurrence."""
        record = self.repo.get_by_id(id)
        new_value = 0 if record.get("is_unavoidable") else 1
        self.repo.update(id, {"is_unavoidable": new_value})
        return self.repo.get_by_id(id)

    def count_matching(
        self, merchant_name: str, amount_min=None, amount_max=None,
        next_occurrence=None, frequency=None,
    ) -> dict:
        """Return count of transactions matching the given rules."""
        day = _DateHelper.day_of_month(next_occurrence) if frequency == "monthly" else None
        return {"count": self.repo.count_matching_transactions(merchant_name, amount_min, amount_max, day)}

    def get_detail(self, id: str) -> dict:
        """Return full detail for a recurrence: rules, linked transactions, timeline, metrics."""
        record = self.repo.get_by_id(id)
        merchant = record.get("merchant_name") or ""
        day = _DateHelper.day_of_month(record.get("next_occurrence")) if record.get("frequency") == "monthly" else None
        txns = (
            self.repo.get_matching_transactions(
                merchant, record.get("amount_min"), record.get("amount_max"), day
            )
            if merchant
            else []
        )
        return {
            "recurrence": record,
            "linked_transactions": txns,
            "timeline": self._build_match_timeline(txns),
            "metrics": self._compute_metrics(txns, record),
        }

    @staticmethod
    def _build_match_timeline(txns: list[dict]) -> list[dict]:
        return _DateHelper.build_match_timeline(txns)

    @staticmethod
    def _compute_metrics(txns: list[dict], record: dict) -> dict:
        return _DateHelper.compute_transaction_metrics(txns, "last_payment_date")

    def get_monthly_view(self, month: str) -> dict:
        """Return installments, fixed expenses, and 12-month history for a given month."""
        transaction_repo = TransactionRepository()
        bill_repo = BillRepository()
        try:
            all_recurrences = self.repo.get_all()
            installment_items = self._get_installment_items(transaction_repo, bill_repo, month)
            fixed_items = self._filter_fixed_items(all_recurrences, month)
            history = self._build_history(transaction_repo, bill_repo, month, all_recurrences)
        finally:
            transaction_repo.close()
            bill_repo.close()

        installments_total = round(sum(item["amount"] for item in installment_items), 2)
        fixed_total = round(sum(item["amount"] for item in fixed_items), 2)

        return {
            "installments": {"total": installments_total, "items": installment_items},
            "fixed_expenses": {"total": fixed_total, "items": fixed_items},
            "history": history,
        }



    def get_installments(self, month: str) -> list[dict]:
        """Return installments for the given month.

        Past/current months query actual credit transactions.
        Future months project from the current month's installments.
        """
        transaction_repo = TransactionRepository()
        bill_repo = BillRepository()
        try:
            current_month = _date.today().strftime("%Y-%m")
            if month <= current_month:
                return self._get_installment_items(transaction_repo, bill_repo, month)
            base = self._get_installment_items(transaction_repo, bill_repo, current_month)
            return self._project_installments(base, current_month, month)
        finally:
            transaction_repo.close()
            bill_repo.close()

    @staticmethod
    def _project_installments(base: list[dict], current_month: str, target_month: str) -> list[dict]:
        """Return projected installments for target_month based on current_month's items."""
        cy, cm = map(int, current_month.split("-"))
        ty, tm = map(int, target_month.split("-"))
        delta = (ty - cy) * 12 + (tm - cm)
        result = []
        for item in base:
            total = item.get("total_installments") or 0
            num = item.get("installment_number") or 0
            if total - num >= delta:
                projected_num = num + delta
                result.append({
                    **item,
                    "installment_number": projected_num,
                    "pct_paid": round(projected_num / total, 4) if total else 0.0,
                })
        return result

    # ── private helpers ──

    def _get_installment_items(
        self, repo: TransactionRepository, bill_repo: BillRepository, month: str
    ) -> list[dict]:
        period = bill_repo.get_billing_period(month)
        if period:
            start_incl, end_excl = period
            cursor = repo.execute_query(
                """
                SELECT id, description, category_id, amount, installment_number,
                       total_installments, date
                FROM credit_transactions
                WHERE excluded = 0
                  AND date(substr(date, 1, 19), '-3 hours') >= ?
                  AND date(substr(date, 1, 19), '-3 hours') < ?
                ORDER BY date
                """,
                (start_incl, end_excl),
            )
        else:
            cursor = repo.execute_query(
                """
                SELECT id, description, category_id, amount, installment_number,
                       total_installments, date
                FROM credit_transactions
                WHERE excluded = 0
                  AND date(substr(date, 1, 19), '-3 hours') LIKE ?
                ORDER BY date
                """,
                (f"{month}%",),
            )
        rows = cursor.fetchall()
        items = []
        for row in rows:
            row_dict = dict(row)
            total = row_dict.get("total_installments")
            inst_num = row_dict.get("installment_number") or 0
            if not total or total <= 1:
                match = _INSTALLMENT_RE.search(row_dict.get("description", "") or "")
                if not match:
                    continue
                inst_num = inst_num or int(match.group(1))
                total = int(match.group(2))
                row_dict["installment_number"] = inst_num
                row_dict["total_installments"] = total
            row_dict["pct_paid"] = round(inst_num / total, 4) if total else 0.0
            items.append(row_dict)
        return items

    def get_fixed_expenses_for_month(self, month_key: str) -> list[dict]:
        """Retorna lista de despesas fixas aplicáveis ao mês informado.

        Inclui recorrências mensais (sempre) e anuais/semanais cujo mês-do-ano
        coincide com month_key. Mesmo dado exibido na tela de Recorrências.
        """
        return self._filter_fixed_items(self.repo.get_all(), month_key)

    @staticmethod
    def _filter_fixed_items(rows: list[dict], month: str) -> list[dict]:
        """Filter a pre-fetched list of recurrences to those relevant for the given month."""
        month_mm = month[5:7]
        filtered = [
            r for r in rows
            if r.get("frequency") == "monthly"
            or (r.get("next_occurrence") or "")[5:7] == month_mm
        ]
        return sorted(filtered, key=lambda r: (r.get("next_occurrence") is None, r.get("next_occurrence") or ""))

    def get_yearly_view(self, year: int) -> list[dict]:
        """Return installment and fixed totals for each month of the given year.

        Past and current months use actual transaction data.
        Future months are projected from active installments in the current month
        (remaining = total_installments - installment_number) and all monthly
        fixed expenses.
        """
        current_month = _date.today().strftime("%Y-%m")
        cy, cm = map(int, current_month.split("-"))

        transaction_repo = TransactionRepository()
        bill_repo = BillRepository()
        try:
            projection_base = self._get_installment_items(transaction_repo, bill_repo, current_month)
            all_recurrences = self.repo.get_all()
            result = []
            for mon in range(1, 13):
                month_str = f"{year}-{mon:02d}"
                fixed_items = self._filter_fixed_items(all_recurrences, month_str)
                fixed_total = round(sum(i["amount"] for i in fixed_items), 2)

                if month_str <= current_month:
                    inst_items = self._get_installment_items(transaction_repo, bill_repo, month_str)
                    result.append({
                        "month": month_str,
                        "installments": round(sum(i["amount"] for i in inst_items), 2),
                        "fixed": fixed_total,
                        "projected": False,
                    })
                else:
                    delta = (year - cy) * 12 + (mon - cm)
                    projected_inst = round(sum(
                        item["amount"]
                        for item in projection_base
                        if (item.get("total_installments") or 0) - (item.get("installment_number") or 0) >= delta
                    ), 2)
                    result.append({
                        "month": month_str,
                        "installments": projected_inst,
                        "fixed": fixed_total,
                        "projected": True,
                    })
            return result
        finally:
            transaction_repo.close()
            bill_repo.close()

    def _build_history(
        self,
        repo: TransactionRepository,
        bill_repo: BillRepository,
        current_month: str,
        all_recurrences: list[dict],
    ) -> list[dict]:
        """Compute installment and fixed totals for the last 12 months."""
        year, mon = map(int, current_month.split("-"))
        history = []
        for delta in range(11, -1, -1):
            m = mon - delta
            y = year
            while m <= 0:
                m += 12
                y -= 1
            month_str = f"{y}-{m:02d}"
            inst_items = self._get_installment_items(repo, bill_repo, month_str)
            fixed_items = self._filter_fixed_items(all_recurrences, month_str)
            history.append({
                "month": month_str,
                "installments": round(sum(i["amount"] for i in inst_items), 2),
                "fixed": round(sum(i["amount"] for i in fixed_items), 2),
            })
        return history
