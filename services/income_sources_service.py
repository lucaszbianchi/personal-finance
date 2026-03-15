import uuid
from datetime import date as _date

from repositories.income_sources_repository import IncomeSourcesRepository
from utils.date_helper import DateHelper as _DateHelper


class IncomeSourcesService:
    """Business logic for income sources CRUD, monthly view, and yearly view."""

    def __init__(self):
        self.repo = IncomeSourcesRepository()

    def get_all(self) -> list[dict]:
        return self.repo.get_all()

    def create(self, data: dict) -> dict:
        """Create a manual income source. Generates uuid and sets source='manual'."""
        record = {
            "id": str(uuid.uuid4()),
            "description": data.get("description"),
            "amount": data.get("amount"),
            "frequency": data.get("frequency"),
            "next_occurrence": data.get("next_occurrence"),
            "category_id": data.get("category_id"),
            "merchant_name": data.get("merchant_name"),
            "amount_min": data.get("amount_min"),
            "amount_max": data.get("amount_max"),
            "confidence": None,
            "source": "manual",
            "synced_at": _date.today().strftime("%Y-%m-%d"),
        }
        self.repo.upsert(record)
        return self.repo.get_by_id(record["id"])

    def update(self, id: str, data: dict) -> dict:
        """Update an income source. Raises ValueError if not found."""
        self.repo.update(id, data)
        return self.repo.get_by_id(id)

    def delete(self, id: str) -> None:
        """Delete an income source. Raises ValueError if not found."""
        self.repo.delete(id)

    def count_matching(
        self, merchant_name: str, amount_min=None, amount_max=None,
        next_occurrence=None, frequency=None,
    ) -> dict:
        """Return count of bank transactions (amount > 0) matching the given rules."""
        day = _DateHelper.day_of_month(next_occurrence) if frequency == "monthly" else None
        return {"count": self.repo.count_matching_transactions(merchant_name, amount_min, amount_max, day)}

    def get_detail(self, id: str) -> dict:
        """Return full detail for an income source: rules, linked transactions, timeline, metrics."""
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
            "source": record,
            "linked_transactions": txns,
            "timeline": self._build_match_timeline(txns),
            "metrics": self._compute_metrics(txns, record),
        }

    @staticmethod
    def _build_match_timeline(txns: list[dict]) -> list[dict]:
        return _DateHelper.build_match_timeline(txns)

    @staticmethod
    def _compute_metrics(txns: list[dict], record: dict) -> dict:
        return _DateHelper.compute_transaction_metrics(txns, "last_received_date")

    def get_monthly_view(self, month: str) -> dict:
        """Return income sources for the month and 12-month history.

        Each item's amount reflects actual transactions for that month when a
        merchant_name rule exists; falls back to the configured amount otherwise.
        """
        all_sources = self.repo.get_all()
        items = self._filter_items(all_sources, month)
        augmented = []
        for source in items:
            merchant = source.get("merchant_name") or ""
            if merchant:
                day = _DateHelper.day_of_month(source.get("next_occurrence")) if source.get("frequency") == "monthly" else None
                actual = self.repo.get_month_actual(
                    month, merchant, source.get("amount_min"), source.get("amount_max"), day
                )
                augmented.append({**source, "amount": round(actual, 2)})
            else:
                augmented.append(source)
        history = self._build_history(month, all_sources)
        total = round(sum(item["amount"] or 0 for item in augmented), 2)
        return {
            "sources": {"total": total, "items": augmented},
            "history": history,
        }

    def get_yearly_view(self, year: int) -> list[dict]:
        """Return income totals for each month of the given year.

        Past/current months use actual matched transaction sums.
        Future months use configured amounts as a projection.
        Sources without a merchant_name rule always use the configured amount.
        """
        all_sources = self.repo.get_all()
        current_month = _date.today().strftime("%Y-%m")

        monthly_actuals: dict[str, float] = {}
        for source in all_sources:
            merchant = source.get("merchant_name") or ""
            if not merchant:
                continue
            day = _DateHelper.day_of_month(source.get("next_occurrence")) if source.get("frequency") == "monthly" else None
            actuals = self.repo.get_monthly_actuals(
                year, merchant, source.get("amount_min"), source.get("amount_max"), day
            )
            for month, total in actuals.items():
                monthly_actuals[month] = monthly_actuals.get(month, 0.0) + total

        result = []
        for mon in range(1, 13):
            month_str = f"{year}-{mon:02d}"
            items = self._filter_items(all_sources, month_str)
            if month_str <= current_month:
                total = monthly_actuals.get(month_str, 0.0)
                # Sources without a matching rule contribute their configured amount
                for item in items:
                    if not item.get("merchant_name"):
                        total += item.get("amount") or 0
            else:
                total = sum(item.get("amount") or 0 for item in items)
            result.append({"month": month_str, "total": round(total, 2)})
        return result

    @staticmethod
    def _filter_items(rows: list[dict], month: str) -> list[dict]:
        """Filter income sources to those relevant for the given month."""
        month_mm = month[5:7]
        filtered = [
            r for r in rows
            if r.get("frequency") == "monthly"
            or (r.get("next_occurrence") or "")[5:7] == month_mm
        ]
        return sorted(
            filtered,
            key=lambda r: (r.get("next_occurrence") is None, r.get("next_occurrence") or ""),
        )

    def _build_history(self, current_month: str, all_sources: list[dict]) -> list[dict]:
        """Compute income totals for the last 12 months."""
        year, mon = map(int, current_month.split("-"))
        history = []
        for delta in range(11, -1, -1):
            m = mon - delta
            y = year
            while m <= 0:
                m += 12
                y -= 1
            month_str = f"{y}-{m:02d}"
            items = self._filter_items(all_sources, month_str)
            history.append({
                "month": month_str,
                "total": round(sum(item["amount"] or 0 for item in items), 2),
            })
        return history
