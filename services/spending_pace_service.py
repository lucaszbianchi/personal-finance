import calendar
from typing import Optional
from dateutil.relativedelta import relativedelta
from datetime import date

from services.finance_summary_service import FinanceSummaryService
from repositories.finance_history_repository import FinanceHistoryRepository
from repositories.user_goals_repository import UserGoalsRepository


class SpendingPaceService:
    def __init__(self):
        self._summary = FinanceSummaryService()
        self._history_repo = FinanceHistoryRepository()
        self._goals_repo = UserGoalsRepository()

    def _daily_cumulative(self, transactions: list, last_day: int) -> list[float]:
        """Build a cumulative expense series for days 1..last_day."""
        daily_totals: dict[int, float] = {}
        for t in transactions:
            if not FinanceSummaryService._is_expense(t) or getattr(t, "excluded", 0):
                continue
            date_str = t.date.split("\n")[0]  # "YYYY-MM-DD"
            day = date.fromisoformat(date_str).day
            daily_totals[day] = daily_totals.get(day, 0.0) + abs(t.amount)

        cumulative = []
        running = 0.0
        for d in range(1, last_day + 1):
            running += daily_totals.get(d, 0.0)
            cumulative.append(running)
        return cumulative

    def get_spending_pace(self, month: str) -> dict:
        """
        Returns daily cumulative expense series for the requested month alongside
        the previous month's series, a monthly spending goal, and a 6-month avg.

        Args:
            month: "YYYY-MM"

        Returns:
            {
                "daily_series": [{"day": int, "cumulative_amount": float,
                                   "prev_month_cumulative": float}, ...],
                "monthly_goal": float | None,
                "monthly_avg": float | None,
                "unavoidable_avg": None,
            }
        """
        year, mo = int(month[:4]), int(month[5:7])
        current_first = date(year, mo, 1)
        last_day_current = calendar.monthrange(year, mo)[1]

        prev_first = current_first - relativedelta(months=1)
        last_day_prev = calendar.monthrange(prev_first.year, prev_first.month)[1]

        # Date range strings (end is exclusive — first day of next month)
        cur_start = current_first.strftime("%Y-%m-%d")
        cur_end = (current_first + relativedelta(months=1)).strftime("%Y-%m-%d")
        prev_start = prev_first.strftime("%Y-%m-%d")
        prev_end = current_first.strftime("%Y-%m-%d")

        # Fetch transactions for both months
        cur_bank = self._summary.transaction_service.get_bank_transactions(cur_start, cur_end)
        cur_credit = self._summary.transaction_service.get_credit_transactions(cur_start, cur_end)
        prev_bank = self._summary.transaction_service.get_bank_transactions(prev_start, prev_end)
        prev_credit = self._summary.transaction_service.get_credit_transactions(prev_start, prev_end)

        cur_cumul = self._daily_cumulative(cur_bank + cur_credit, last_day_current)

        # Build prev cumulative aligned to last_day_current length
        prev_cumul_raw = self._daily_cumulative(prev_bank + prev_credit, last_day_prev)
        if last_day_prev >= last_day_current:
            prev_cumul = prev_cumul_raw[:last_day_current]
        else:
            # Pad shorter month by repeating final value
            final_val = prev_cumul_raw[-1] if prev_cumul_raw else 0.0
            prev_cumul = prev_cumul_raw + [final_val] * (last_day_current - last_day_prev)

        daily_series = [
            {
                "day": d + 1,
                "cumulative_amount": round(cur_cumul[d], 2),
                "prev_month_cumulative": round(prev_cumul[d], 2),
            }
            for d in range(last_day_current)
        ]

        # 6-month historical average (excludes current month)
        monthly_avg: Optional[float] = None
        all_history = self._history_repo.get_all()  # sorted DESC
        past = [
            e.expenses
            for e in all_history
            if e.month < month and e.expenses is not None
        ][:6]
        if past:
            monthly_avg = round(sum(past) / len(past), 2)

        # Monthly goal
        monthly_goal = self._goals_repo.get_total_monthly_goal()

        return {
            "daily_series": daily_series,
            "monthly_goal": monthly_goal,
            "monthly_avg": monthly_avg,
            "unavoidable_avg": None,
        }
