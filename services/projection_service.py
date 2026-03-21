from datetime import date

from dateutil.relativedelta import relativedelta

from repositories.accounts_snapshot_repository import AccountsSnapshotRepository
from repositories.finance_history_repository import FinanceHistoryRepository
from repositories.investment_repository import InvestmentRepository
from repositories.income_sources_repository import IncomeSourcesRepository
from repositories.recurrent_expenses_repository import RecurrentExpensesRepository
from services.finance_summary_service import FinanceSummaryService
from services.recurrences_service import RecurrencesService

_VARIABLE_LOOKBACK_MONTHS = 6


class ProjectionService:
    """12-month net worth projection based on recurring income, fixed expenses, and installments."""

    def __init__(self):
        self.accounts_repo = AccountsSnapshotRepository()
        self.finance_history_repo = FinanceHistoryRepository()
        self.investment_repo = InvestmentRepository()
        self.income_repo = IncomeSourcesRepository()
        self.recurrences_repo = RecurrentExpensesRepository()
        self.recurrences_service = RecurrencesService()
        self.finance_summary = FinanceSummaryService()

    def get_projection(self, months: int = 12) -> dict:
        """Return current net worth and month-by-month projection for the next N months.

        Each entry contains: month (YYYY-MM), net_worth, income, expenses, fixed, installments, variable.
        """
        current_nw = self._get_current_net_worth()
        monthly_income = self._get_monthly_income()
        monthly_fixed = self._get_monthly_fixed_expenses()
        avg_variable = self._get_avg_variable_expenses()
        installments_by_month = self._get_pending_installments_by_month(months)

        today = date.today()
        projection = []
        nw = current_nw

        for i in range(1, months + 1):
            month_date = today.replace(day=1) + relativedelta(months=i)
            month_key = month_date.strftime("%Y-%m")
            installments = installments_by_month.get(month_key, 0.0)
            total_expenses = monthly_fixed + installments + avg_variable
            nw = round(nw + monthly_income - total_expenses, 2)
            projection.append(
                {
                    "month": month_key,
                    "net_worth": nw,
                    "income": round(monthly_income, 2),
                    "expenses": round(total_expenses, 2),
                    "fixed": round(monthly_fixed, 2),
                    "installments": round(installments, 2),
                    "variable": round(avg_variable, 2),
                }
            )

        return {
            "current_net_worth": round(current_nw, 2),
            "avg_variable_expenses": round(avg_variable, 2),
            "history": self._get_actual_history(),
            "projection": projection,
        }

    def _get_actual_history(self) -> list:
        """Return all historical months from finance_history with expense breakdown, oldest first.

        Variable expenses are the actual values (total - fixed - installments).
        Fixed and installments are capped so they never exceed actual expenses.
        """
        current_month = date.today().strftime("%Y-%m")
        next_month = (date.today().replace(day=1) + relativedelta(months=1)).strftime("%Y-%m")
        monthly_fixed = self._get_monthly_fixed_expenses()
        all_entries = self.finance_history_repo.get_all()
        result = []
        for entry in sorted(all_entries, key=lambda x: x.month):
            if entry.month >= next_month:
                continue
            if entry.income is None and entry.expenses is None:
                continue
            expenses = entry.expenses or 0.0
            installments_items = self.recurrences_service.get_installments(entry.month)
            installments_total = round(
                sum(item.get("amount", 0.0) for item in installments_items), 2
            )
            # Distribute expenses: fixed takes priority, then installments, remainder is variable
            remaining = round(expenses, 2)
            fixed = round(min(monthly_fixed, remaining), 2)
            remaining = round(remaining - fixed, 2)
            installments = round(min(installments_total, remaining), 2)
            variable = round(remaining - installments, 2)
            result.append({
                "month": entry.month,
                "income": round(entry.income or 0.0, 2),
                "expenses": round(expenses, 2),
                "fixed": fixed,
                "installments": installments,
                "variable": variable,
                "net_worth": round(entry.total_cash, 2) if entry.total_cash is not None else None,
                # Needed for _backfill_net_worth formula; fall back to combined expenses when not split
                "bank_expenses": round(entry.bank_expenses, 2) if entry.bank_expenses is not None else round(expenses, 2),
                "credit_expenses": round(entry.credit_expenses or 0.0, 2),
            })
        return self._backfill_net_worth(result)

    @staticmethod
    def _backfill_net_worth(entries: list) -> list:
        """Fill missing net_worth values by working backwards from the most recent known value.

        Formula: total_cash(M) = total_cash(M+1) - income(M+1) + bank_expenses(M+1) + credit_expenses(M)
        Entries must be sorted oldest-first. Only the most recent anchor is used.
        """
        anchor_idx = None
        for i in range(len(entries) - 1, -1, -1):
            if entries[i]["net_worth"] is not None:
                anchor_idx = i
                break

        if anchor_idx is None:
            return entries

        for i in range(anchor_idx - 1, -1, -1):
            if entries[i]["net_worth"] is not None:
                break  # Stop at the next existing anchor
            nxt = entries[i + 1]
            entries[i]["net_worth"] = round(
                nxt["net_worth"] - nxt["income"] + nxt["bank_expenses"] + entries[i]["credit_expenses"], 2
            )

        return entries

    def get_assumptions(self) -> dict:
        """Return the raw assumptions used in the projection for display purposes."""
        income_sources = [
            {"description": s.get("description"), "amount": s.get("amount") or 0.0}
            for s in self.income_repo.get_all()
            if (s.get("frequency") or "").upper() == "MONTHLY"
        ]
        fixed_expenses = [
            {"description": r.get("description"), "amount": r.get("amount") or 0.0}
            for r in self.recurrences_repo.get_all()
            if (r.get("frequency") or "").upper() == "MONTHLY"
        ]
        installments_by_month = self._get_pending_installments_by_month(12)
        installments_list = sorted(
            [{"month": k, "total": round(v, 2)} for k, v in installments_by_month.items()],
            key=lambda x: x["month"],
        )
        return {
            "income_sources": income_sources,
            "fixed_expenses": fixed_expenses,
            "installments_by_month": installments_list,
            "avg_variable_expenses": round(self._get_avg_variable_expenses(), 2),
        }

    def _get_current_net_worth(self) -> float:
        """Sum of latest BANK snapshot balances plus current investment balances."""
        bank_snapshots = self.accounts_repo.get_latest_snapshot_by_type("BANK")
        checking_balance = sum(row.get("balance") or 0.0 for row in bank_snapshots)

        investments = self.investment_repo.get_investments()
        investments_total = sum(inv.balance or 0.0 for inv in investments)

        return checking_balance + investments_total

    def _get_monthly_income(self) -> float:
        """Sum of income_sources amounts where frequency is MONTHLY."""
        return sum(
            s.get("amount") or 0.0
            for s in self.income_repo.get_all()
            if (s.get("frequency") or "").upper() == "MONTHLY"
        )

    def _get_monthly_fixed_expenses(self) -> float:
        """Sum of recurrent_expenses amounts where frequency is MONTHLY."""
        return sum(
            r.get("amount") or 0.0
            for r in self.recurrences_repo.get_all()
            if (r.get("frequency") or "").upper() == "MONTHLY"
        )

    def _get_avg_variable_expenses(self) -> float:
        """Average monthly variable expenses over the last N complete months.

        Variable = total_expenses - fixed_recurrences - installments.
        Only months with a positive variable total are included in the average,
        to avoid skewing from months with incomplete data.
        """
        today = date.today()
        monthly_fixed = self._get_monthly_fixed_expenses()
        totals = []

        for i in range(1, _VARIABLE_LOOKBACK_MONTHS + 1):
            month_date = today.replace(day=1) - relativedelta(months=i)
            month_key = month_date.strftime("%Y-%m")
            start = month_date.strftime("%Y-%m-%d")
            end = (month_date + relativedelta(months=1)).strftime("%Y-%m-%d")

            total_expenses = self.finance_summary.get_expenses(start, end)
            installments = sum(
                item.get("amount", 0.0)
                for item in self.recurrences_service.get_installments(month_key)
            )
            variable = total_expenses - monthly_fixed - installments
            if variable > 0:
                totals.append(variable)

        return sum(totals) / len(totals) if totals else 0.0

    def _get_pending_installments_by_month(self, months: int) -> dict:
        """Return {YYYY-MM: total_amount} for pending installments within the projection window.

        Delegates to RecurrencesService.get_installments() which uses the same billing-period
        aware logic as the Recorrencias page, including regex-detected installments.
        """
        today = date.today()
        result: dict[str, float] = {}

        for i in range(1, months + 1):
            month_date = today.replace(day=1) + relativedelta(months=i)
            month_key = month_date.strftime("%Y-%m")
            items = self.recurrences_service.get_installments(month_key)
            total = round(sum(item.get("amount", 0.0) for item in items), 2)
            if total > 0:
                result[month_key] = total

        return result
