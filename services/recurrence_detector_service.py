import hashlib
import statistics
from datetime import datetime, timedelta

from repositories.recurrent_expenses_repository import RecurrentExpensesRepository
from repositories.transaction_repository import TransactionRepository
from utils.installment_helper import INSTALLMENT_RE as _INSTALLMENT_RE

_WEEKLY_MAX = 10
_MONTHLY_MIN = 25
_MONTHLY_MAX = 40
_ANNUAL_MIN = 350
_ANNUAL_MAX = 380
_MIN_DISTINCT_MONTHS = 3
_AMOUNT_VARIANCE_MAX = 10.0


class RecurrenceDetectorService:
    """Detect recurring expenses from transaction history and store them."""

    def __init__(self):
        self.transaction_repo = TransactionRepository()
        self.recurrence_repo = RecurrentExpensesRepository()

    def close(self) -> None:
        self.transaction_repo.close()
        self.recurrence_repo.close()

    def detect_and_store(self) -> int:
        """Run detection algorithm and upsert results. Returns count of upserted records.

        Skips detection entirely if the table already has entries — preserves any
        edits or deletions the user made after the first auto-detection run.
        """
        if self.recurrence_repo.has_any():
            return 0
        grouped = self._group_transactions()
        count = 0
        for description, entries in grouped.items():
            record = self._analyze(description, entries)
            if record is None:
                continue
            self.recurrence_repo.upsert_recurrence(record)
            count += 1
        return count

    @staticmethod
    def _is_installment(description: str) -> bool:
        return bool(_INSTALLMENT_RE.search(description))

    def _group_transactions(self) -> dict:
        """Return transactions grouped by normalized description."""
        bank_rows = self.transaction_repo.get_bank_transactions()
        credit_rows = self.transaction_repo.get_credit_transactions()

        groups: dict[str, list] = {}
        for t in bank_rows:
            if t.excluded or t.amount is None or t.amount >= 0:
                continue
            desc = t.description or ""
            if self._is_installment(desc):
                continue
            key = desc.strip().lower()
            if not key:
                continue
            groups.setdefault(key, []).append({
                "date": t.date,
                "amount": abs(t.amount),
                "category_id": getattr(t, "category_id", None),
                "description": t.description,
                "source_type": "bank",
            })

        for t in credit_rows:
            if t.excluded or t.amount is None or t.amount <= 0:
                continue
            desc = t.description or ""
            if self._is_installment(desc):
                continue
            key = desc.strip().lower()
            if not key:
                continue
            groups.setdefault(key, []).append({
                "date": t.date,
                "amount": t.amount,
                "category_id": getattr(t, "category_id", None),
                "description": t.description,
                "source_type": "credit",
            })

        return groups

    def _analyze(self, normalized_description: str, entries: list) -> dict | None:
        """Analyze a group of transactions for recurrence pattern. Returns record or None."""
        dates = sorted(set(e["date"][:10] for e in entries))
        months = set(d[:7] for d in dates)
        if len(months) < _MIN_DISTINCT_MONTHS:
            return None

        parsed_dates = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
        intervals = [
            (parsed_dates[i + 1] - parsed_dates[i]).days
            for i in range(len(parsed_dates) - 1)
        ]
        if not intervals:
            return None

        amounts = [e["amount"] for e in entries]
        if max(amounts) - min(amounts) > _AMOUNT_VARIANCE_MAX:
            return None

        median_interval = statistics.median(intervals)
        if median_interval < _WEEKLY_MAX:
            frequency = "weekly"
        elif _MONTHLY_MIN <= median_interval <= _MONTHLY_MAX:
            frequency = "monthly"
        elif _ANNUAL_MIN <= median_interval <= _ANNUAL_MAX:
            frequency = "annual"
        else:
            return None

        std_dev = statistics.stdev(intervals) if len(intervals) > 1 else 0.0
        mean_interval = statistics.mean(intervals)
        regularity = max(0.0, min(1.0, 1.0 - (std_dev / mean_interval if mean_interval else 0)))

        avg_amount = round(statistics.mean(amounts), 2)

        last_date = parsed_dates[-1]
        next_occurrence = (last_date + timedelta(days=int(median_interval))).strftime("%Y-%m-%d")

        category_ids = [e["category_id"] for e in entries if e["category_id"]]
        category_id = max(set(category_ids), key=category_ids.count) if category_ids else None

        original_description = entries[0]["description"]
        stable_id = hashlib.sha1(normalized_description.encode()).hexdigest()[:16]
        synced_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        has_credit = any(e.get("source_type") == "credit" for e in entries)
        has_bank = any(e.get("source_type") == "bank" for e in entries)
        if has_credit and has_bank:
            account_type = "both"
        elif has_credit:
            account_type = "credit"
        elif has_bank:
            account_type = "bank"
        else:
            account_type = None

        return {
            "id": stable_id,
            "description": original_description,
            "amount": avg_amount,
            "frequency": frequency,
            "next_occurrence": next_occurrence,
            "category_id": category_id,
            "merchant_name": None,
            "confidence": round(regularity, 4),
            "source": "detected",
            "is_unavoidable": 0,
            "synced_at": synced_at,
            "account_type": account_type,
        }
