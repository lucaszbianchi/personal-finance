from datetime import date
from services.finance_summary_service import FinanceSummaryService


def current_ym() -> str:
    today = date.today()
    return f"{today.year:04d}-{today.month:02d}"


def _generate_months(end_month: str, count: int) -> list:
    """Generate `count` months ending at end_month (inclusive), oldest first."""
    year, month = int(end_month[:4]), int(end_month[5:7])
    months = []
    for i in range(count - 1, -1, -1):
        m = month - i
        y = year
        while m <= 0:
            m += 12
            y -= 1
        months.append(f"{y:04d}-{m:02d}")
    return months


def _prev_month(ym: str) -> str:
    year, month = int(ym[:4]), int(ym[5:7])
    month -= 1
    if month == 0:
        month = 12
        year -= 1
    return f"{year:04d}-{month:02d}"


def _month_date_range(ym: str) -> tuple:
    """Return (start_date, end_date) as YYYY-MM-DD strings for a month."""
    year, month = int(ym[:4]), int(ym[5:7])
    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_month = 1
        next_year += 1
    return f"{year:04d}-{month:02d}-01", f"{next_year:04d}-{next_month:02d}-01"


def _sum_values(entries: list):
    values = [e["value"] for e in entries if e["value"] is not None]
    return round(sum(values), 2) if values else None


def _delta_pct(current, previous):
    if current is None or previous is None or previous == 0:
        return None
    return round((current - previous) / abs(previous) * 100, 1)


class CashFlowService:
    def __init__(self):
        self.summary_service = FinanceSummaryService()

    def get_cash_flow(self, window: int, end_month: str) -> dict:
        current_months = _generate_months(end_month, window)
        prev_end = _prev_month(current_months[0])
        previous_months = _generate_months(prev_end, window)

        current_net_balance, current_income, current_expenses_by_category = (
            self._build_window(current_months, include_categories=True)
        )
        prev_net_balance, prev_income, _ = self._build_window(previous_months, include_categories=False)

        current_period_total = _sum_values(current_net_balance)
        prev_period_total = _sum_values(prev_net_balance)
        delta_pct = _delta_pct(current_period_total, prev_period_total)

        return {
            "current_window": {
                "months": current_months,
                "net_balance": current_net_balance,
                "expenses_by_category": current_expenses_by_category,
                "income": current_income,
                "period_total": current_period_total,
            },
            "previous_window": {
                "months": previous_months,
                "net_balance": prev_net_balance,
                "income": prev_income,
                "period_total": prev_period_total,
                "delta_pct": delta_pct,
            },
        }

    def _build_window(self, months: list, include_categories: bool) -> tuple:
        net_balance = []
        income_list = []
        expenses_by_category = []

        for month in months:
            start_date, end_date = _month_date_range(month)
            income = round(self.summary_service.get_income(start_date, end_date), 2)
            expenses = round(self.summary_service.get_expenses(start_date, end_date), 2)
            net = round(income - expenses, 2)

            net_balance.append({"month": month, "value": net})
            income_list.append({"month": month, "value": income})

            if include_categories:
                cats = self.summary_service.get_category_expenses_by_parent(start_date, end_date)
                cats_dict = {c["description"]: round(c["total"], 2) for c in cats}
                expenses_by_category.append({"month": month, "categories": cats_dict})

        return net_balance, income_list, expenses_by_category
