from datetime import date

from dateutil.relativedelta import relativedelta

from repositories.accounts_snapshot_repository import AccountsSnapshotRepository
from repositories.category_repository import CategoryRepository
from repositories.finance_history_repository import FinanceHistoryRepository
from repositories.investment_repository import InvestmentRepository
from repositories.income_sources_repository import IncomeSourcesRepository
from repositories.recurrent_expenses_repository import RecurrentExpensesRepository
from repositories.transaction_repository import TransactionRepository
from services.finance_summary_service import FinanceSummaryService
from services.recurrences_service import RecurrencesService
from services.settings_service import SettingsService
from services.transaction_service import TransactionService

_VARIABLE_LOOKBACK_MONTHS = 6


class ProjectionService:
    """12-month net worth projection based on recurring income, fixed expenses, and installments."""

    def __init__(self):
        self.accounts_repo = AccountsSnapshotRepository()
        self.category_repo = CategoryRepository()
        self.finance_history_repo = FinanceHistoryRepository()
        self.investment_repo = InvestmentRepository()
        self.income_repo = IncomeSourcesRepository()
        self.recurrences_repo = RecurrentExpensesRepository()
        self.transaction_repo = TransactionRepository()
        self.recurrences_service = RecurrencesService()
        self.finance_summary = FinanceSummaryService()
        self.settings_service = SettingsService()
        self.transaction_service = TransactionService()

    def get_projection(self, months: int = 12) -> dict:
        """Return current net worth and month-by-month projection for the next N months.

        Each entry contains: month (YYYY-MM), net_worth, income, expenses, fixed, installments, necessary, optional.
        Fixed expenses vary per month to include applicable annual recurrences.
        Optional expenses use the user-defined monthly target from settings.
        """
        current_nw = self._get_current_net_worth()
        monthly_income = self._get_monthly_income()
        avg_necessary = self._get_avg_necessary_expenses()
        optional_target = self.settings_service.get_optional_expenses_target()
        installments_by_month = self._get_pending_installments_by_month(months)

        today = date.today()
        projection = []
        nw = current_nw

        for i in range(1, months + 1):
            month_date = today.replace(day=1) + relativedelta(months=i)
            month_key = month_date.strftime("%Y-%m")
            fixed_items = self.recurrences_service.get_fixed_expenses_for_month(month_key)
            monthly_fixed = round(sum(item.get("amount") or 0.0 for item in fixed_items), 2)
            installments = installments_by_month.get(month_key, 0.0)
            total_expenses = monthly_fixed + installments + avg_necessary + optional_target
            nw = round(nw + monthly_income - total_expenses, 2)
            projection.append(
                {
                    "month": month_key,
                    "net_worth": nw,
                    "income": round(monthly_income, 2),
                    "expenses": round(total_expenses, 2),
                    "fixed": monthly_fixed,
                    "installments": round(installments, 2),
                    "necessary": round(avg_necessary, 2),
                    "optional": round(optional_target, 2),
                }
            )

        return {
            "current_net_worth": round(current_nw, 2),
            "avg_necessary_expenses": round(avg_necessary, 2),
            "history": self._get_actual_history(),
            "projection": projection,
        }

    def _get_actual_history(self) -> list:
        """Return all historical months from finance_history with expense breakdown, oldest first.

        Fixed and installments come from recurrences_service (same data as Recorrencias screen).
        Necessary and optional are split from actual transactions by category classification.
        """
        next_month = (date.today().replace(day=1) + relativedelta(months=1)).strftime("%Y-%m")
        all_entries = self.finance_history_repo.get_all()
        bank_net_by_month = self.transaction_repo.get_bank_net_by_month()
        necessary_ids = self.category_repo.get_necessary_category_ids()
        optional_ids = self.category_repo.get_optional_category_ids()
        result = []
        for entry in sorted(all_entries, key=lambda x: x.month):
            if entry.month >= next_month:
                continue
            if entry.income is None and entry.expenses is None:
                continue
            fixed, installments, necessary, optional = self._get_expense_split_for_month(
                entry.month, necessary_ids, optional_ids
            )
            result.append({
                "month": entry.month,
                "income": round(entry.income or 0.0, 2),
                "expenses": round(entry.expenses or 0.0, 2),
                "fixed": fixed,
                "installments": installments,
                "necessary": necessary,
                "optional": optional,
                "net_worth": round(entry.total_cash, 2) if entry.total_cash is not None else None,
                # Needed for _backfill_net_worth formula
                "bank_net": bank_net_by_month.get(entry.month, 0.0),
            })
        return self._backfill_net_worth(result)

    @staticmethod
    def _backfill_net_worth(entries: list) -> list:
        """Fill missing net_worth values by working backwards from the most recent known value.

        Formula: net_worth(M) = net_worth(M+1) - bank_net(M+1)
        where bank_net is the sum of ALL bank transactions in month M+1 (including excluded ones).
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
            entries[i]["net_worth"] = round(nxt["net_worth"] - nxt["bank_net"], 2)

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
            "avg_necessary_expenses": round(self._get_avg_necessary_expenses(), 2),
            "avg_optional_expenses_historical": round(self._get_avg_optional_expenses_historical(), 2),
            "optional_expenses_target": round(self.settings_service.get_optional_expenses_target(), 2),
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

    def _get_expense_split_for_month(
        self,
        month_key: str,
        necessary_ids: set,
        optional_ids: set,
    ) -> tuple[float, float, float, float]:
        """Retorna (fixed_total, installments_total, necessary_variable, optional_variable) para um mês.

        fixed_total       = soma de todas as despesas fixas do mês
        installments_total = soma de todas as parcelas do mês
        necessary_variable = despesas em cats necessary − fixos necessary − parcelas necessary
        optional_variable  = despesas em cats optional  − fixos optional  − parcelas optional
        Transações sem categoria classificada não entram em necessary/optional.
        """
        start = f"{month_key}-01"
        month_date = date.fromisoformat(start)
        end = (month_date + relativedelta(months=1)).strftime("%Y-%m-%d")

        bank = self.transaction_service.get_bank_transactions(start_date=start, end_date=end)
        credit = self.transaction_service.get_credit_transactions(start_date=start, end_date=end)

        fixed_items = self.recurrences_service.get_fixed_expenses_for_month(month_key)
        installment_items = self.recurrences_service.get_installments(month_key)

        fixed_total = round(sum(item.get("amount") or 0.0 for item in fixed_items), 2)
        installments_total = round(sum(item.get("amount", 0.0) for item in installment_items), 2)

        necessary_fixed = sum(
            item.get("amount") or 0.0
            for item in fixed_items
            if item.get("category_id") in necessary_ids
        )
        optional_fixed = sum(
            item.get("amount") or 0.0
            for item in fixed_items
            if item.get("category_id") in optional_ids
        )
        necessary_installments = sum(
            item.get("amount", 0.0)
            for item in installment_items
            if item.get("category_id") in necessary_ids
        )
        optional_installments = sum(
            item.get("amount", 0.0)
            for item in installment_items
            if item.get("category_id") in optional_ids
        )

        def _is_expense(t) -> bool:
            return (
                not t.excluded
                and (
                    (t.transaction_type == "bank" and t.amount < 0)
                    or (t.transaction_type == "credit" and t.amount > 0)
                )
            )

        necessary_gross = sum(
            abs(t.amount) for t in bank + credit
            if _is_expense(t) and t.category_id in necessary_ids
        )
        optional_gross = sum(
            abs(t.amount) for t in bank + credit
            if _is_expense(t) and t.category_id in optional_ids
        )

        necessary_variable = max(0.0, necessary_gross - necessary_fixed - necessary_installments)
        optional_variable = max(0.0, optional_gross - optional_fixed - optional_installments)
        return fixed_total, installments_total, round(necessary_variable, 2), round(optional_variable, 2)

    def _compute_variable_averages(self) -> tuple[float, float]:
        """Returns (avg_necessary, avg_optional) over the last N months in a single pass.

        Fetches category IDs and transactions once per month, computing both averages
        together to avoid double-fetching when both values are needed (e.g. get_assumptions).
        """
        today = date.today()
        necessary_ids = self.category_repo.get_necessary_category_ids()
        optional_ids = self.category_repo.get_optional_category_ids()
        necessary_totals: list[float] = []
        optional_totals: list[float] = []

        for i in range(1, _VARIABLE_LOOKBACK_MONTHS + 1):
            month_key = (today.replace(day=1) - relativedelta(months=i)).strftime("%Y-%m")
            _, _, necessary, optional = self._get_expense_split_for_month(
                month_key, necessary_ids, optional_ids
            )
            if necessary > 0:
                necessary_totals.append(necessary)
            if optional > 0:
                optional_totals.append(optional)

        avg_n = sum(necessary_totals) / len(necessary_totals) if necessary_totals else 0.0
        avg_o = sum(optional_totals) / len(optional_totals) if optional_totals else 0.0
        return avg_n, avg_o

    def _get_avg_necessary_expenses(self) -> float:
        """Average monthly variable expenses from 'necessary' categories over the last N months."""
        return self._compute_variable_averages()[0]

    def _get_avg_optional_expenses_historical(self) -> float:
        """Average monthly expenses from 'optional' categories over the last N months.

        Used only as a historical reference in the optional expenses card.
        """
        return self._compute_variable_averages()[1]

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
