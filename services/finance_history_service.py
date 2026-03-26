from typing import Any, Dict, List, Optional
from datetime import datetime, date
from repositories.accounts_snapshot_repository import AccountsSnapshotRepository
from repositories.finance_history_repository import FinanceHistoryRepository
from repositories.investment_repository import InvestmentRepository
from repositories.transaction_repository import TransactionRepository
from repositories.bill_repository import BillRepository
from models.finance_history import FinanceHistory


def _first_day_of_next_month(month: str) -> str:
    """Returns YYYY-MM-DD for the first day of the month after `month` (YYYY-MM)."""
    year, mon = int(month[:4]), int(month[5:7])
    if mon == 12:
        return f"{year + 1}-01-01"
    return f"{year}-{mon + 1:02d}-01"


class FinanceHistoryService:
    def __init__(self):
        self.finance_history_repository = FinanceHistoryRepository()
        self.transaction_repository = TransactionRepository()
        self.bill_repository = BillRepository()
        self.accounts_snapshot_repo = AccountsSnapshotRepository()
        self.investment_repo = InvestmentRepository()

    def update_finance_history_from_sync(self, month: str) -> None:
        """Popula todos os campos de finance_history para o mês informado."""
        from services.finance_summary_service import FinanceSummaryService

        start_date = f"{month}-01"
        end_date = _first_day_of_next_month(month)

        # Income and expenses split by type
        finance_summary = FinanceSummaryService()
        income = finance_summary.get_income(start_date, end_date)
        expenses = finance_summary.get_expenses(start_date, end_date)
        bank_expenses = finance_summary.get_bank_expenses(start_date, end_date)
        credit_expenses = finance_summary.get_credit_expenses(start_date, end_date)
        self.finance_history_repository.save_cash_flow(month, income, expenses, bank_expenses, credit_expenses)

        # Credit card bill (actual bill due this month)
        current_bill, _ = self.bill_repository.get_current_and_future_bill(month)

        # Future bill: outstanding balance on card = credit_limit - available_credit
        credit_snaps = self.accounts_snapshot_repo.get_snapshot_for_month("CREDIT", month)
        if credit_snaps:
            future_bill = round(
                sum(
                    (row.get("credit_limit") or 0.0) - (row.get("available_credit") or 0.0)
                    for row in credit_snaps
                ),
                2,
            )
        else:
            # Fallback when no credit snapshot exists for this month
            _, future_bill = self.bill_repository.get_current_and_future_bill(month)

        self.finance_history_repository.save_credit_card_bills(month, current_bill, future_bill)

        # total_cash and investments: from bank snapshot (only if not already set)
        entry = self.finance_history_repository.get_by_month(month)
        if entry is None or entry.total_cash is None:
            bank_snaps = self.accounts_snapshot_repo.get_snapshot_for_month("BANK", month)
            if bank_snaps:
                bank_balance = sum(row.get("balance") or 0.0 for row in bank_snaps)
                investments = self.investment_repo.get_investments()
                inv_dict: dict = {}
                for inv in investments:
                    inv_dict[inv.name] = inv_dict.get(inv.name, 0.0) + (inv.balance or 0.0)
                total_cash = round(bank_balance + sum(inv_dict.values()), 2)
                self.finance_history_repository.save_net_worth(month, total_cash, inv_dict)

        self.finance_history_repository.calculate_and_save_risk_management(month)

    def rebuild_all_months(self) -> dict:
        """Backfill finance_history for every month that has transaction data.

        Calls update_finance_history_from_sync() for each distinct month, then
        force-recalculates total_cash from bank snapshots (ignoring existing values),
        clears total_cash for months without snapshots, and backfills them using:
          total_cash(M) = total_cash(M+1) - sum_of_all_bank_transactions(M+1)
        Idempotent — safe to run multiple times.
        Returns {"months_processed": N, "months": ["2025-04", ...]}.
        """
        months = self.transaction_repository.get_distinct_months()
        months_with_snapshot = set()

        for month in months:
            self.update_finance_history_from_sync(month)
            # Force-recalculate total_cash from snapshot regardless of existing value
            bank_snaps = self.accounts_snapshot_repo.get_snapshot_for_month("BANK", month)
            if bank_snaps:
                bank_balance = sum(row.get("balance") or 0.0 for row in bank_snaps)
                investments = self.investment_repo.get_investments()
                inv_dict: dict = {}
                for inv in investments:
                    inv_dict[inv.name] = inv_dict.get(inv.name, 0.0) + (inv.balance or 0.0)
                total_cash = round(bank_balance + sum(inv_dict.values()), 2)
                self.finance_history_repository.save_net_worth(month, total_cash, inv_dict)
                months_with_snapshot.add(month)

        # Clear total_cash for months without snapshots so backfill can recompute them
        for month in months:
            if month not in months_with_snapshot:
                self.finance_history_repository.save_total_cash(month, None)

        self._backfill_total_cash(months)
        return {"months_processed": len(months), "months": months}

    def _backfill_total_cash(self, months: list) -> None:
        """Fill total_cash backwards from the most recent anchor using net bank transaction flow.

        Formula: total_cash(M) = total_cash(M+1) - sum_of_all_bank_transactions(M+1)
        Sums ALL bank transactions in each month (including excluded ones such as investment
        applications and credit card bill payments) to capture the true change in bank balance.
        """
        if not months:
            return

        bank_net = self.transaction_repository.get_bank_net_by_month()
        sorted_months = sorted(months)
        all_entries = {e.month: e for e in self.finance_history_repository.get_all()}

        # Find the most recent month that already has total_cash (anchor)
        anchor_idx = None
        for i in range(len(sorted_months) - 1, -1, -1):
            entry = all_entries.get(sorted_months[i])
            if entry and entry.total_cash is not None:
                anchor_idx = i
                break

        if anchor_idx is None:
            return

        for i in range(anchor_idx - 1, -1, -1):
            curr_month = sorted_months[i]
            next_month = sorted_months[i + 1]
            curr = all_entries.get(curr_month)
            nxt = all_entries.get(next_month)

            if curr is None or nxt is None or nxt.total_cash is None:
                break

            # Respect intermediate anchors — don't overwrite months with real snapshot data
            if curr.total_cash is not None:
                continue

            net_next = bank_net.get(next_month, 0.0)
            total_cash = round(nxt.total_cash - net_next, 2)
            self.finance_history_repository.save_total_cash(curr_month, total_cash)
            # Update local cache so subsequent iterations use the computed value
            curr.total_cash = total_cash

    def update_net_worth(self) -> Dict[str, Dict[str, Any]]:
        """Atualiza as informações de patrimônio líquido"""
        month = datetime.now().strftime("%Y-%m")
        investments_list = self.transaction_repository.get_investments()
        investments = {}
        for inv in investments_list:
            if inv.name not in investments:
                investments[inv.name] = 0.0
            investments[inv.name] += inv.balance

        bank_account = float(input("Digite o saldo atual da conta bancária: "))
        total_cash = bank_account + sum(investments.values())

        self.finance_history_repository.save_net_worth(month, total_cash, investments)
        return self._format_net_worth_history(self.finance_history_repository.get_all())

    def update_cash_flow(
        self,
        month: Optional[str] = None,
        income: Optional[float] = None,
        expenses: Optional[float] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Atualiza as informações de fluxo de caixa"""
        if month is None:
            month = datetime.now().strftime("%Y-%m")
        if income is None:
            income = float(input("Digite o total de receitas do mês: "))
        if expenses is None:
            expenses = float(input("Digite o total de despesas do mês: "))

        self.finance_history_repository.save_cash_flow(month, income, expenses)
        # Após atualizar o fluxo de caixa, recalcula o risco
        self.finance_history_repository.calculate_and_save_risk_management(month)
        return self._format_net_worth_history(self.finance_history_repository.get_all())

    def update_finance_history_net_worth(
        self, month: str, bank_account: float
    ) -> Dict[str, Dict[str, Any]]:
        """Atualiza patrimônio líquido de forma programática."""
        investments_list = self.transaction_repository.get_investments()
        investments = {}
        for inv in investments_list:
            if inv.name not in investments:
                investments[inv.name] = 0.0
            investments[inv.name] += inv.balance

        total_cash = bank_account + sum(investments.values())
        self.finance_history_repository.save_net_worth(month, total_cash, investments)
        return self._format_net_worth_history(self.finance_history_repository.get_all())

    def get_net_worth_history(self) -> Dict[str, Dict[str, Any]]:
        """Retorna o histórico de patrimônio"""
        history = self.finance_history_repository.get_all()
        return self._format_net_worth_history(history)

    def _format_net_worth_history(
        self, history: List[FinanceHistory]
    ) -> Dict[str, Dict[str, Any]]:
        """Formata o histórico de patrimônio para o formato esperado pela API"""
        return {
            entry.month: {
                "credit_card_bill": entry.credit_card_bill,
                "credit_card_future_bill": entry.credit_card_future_bill,
                "total_cash": entry.total_cash,
                "investments": entry.investments,
                "expenses": entry.expenses,
                "income": entry.income,
                "risk_management": entry.risk_management,
            }
            for entry in history
        }
