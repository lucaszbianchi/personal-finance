from datetime import date
from dateutil.relativedelta import relativedelta

from repositories.accounts_snapshot_repository import AccountsSnapshotRepository
from repositories.finance_history_repository import FinanceHistoryRepository
from repositories.investment_repository import InvestmentRepository
from repositories.user_goals_repository import UserGoalsRepository
from services.finance_summary_service import FinanceSummaryService


class NetWorthService:
    """Servico de patrimonio liquido e resultado parcial do mes."""

    def __init__(self):
        self.accounts_snapshot_repo = AccountsSnapshotRepository()
        self.investment_repo = InvestmentRepository()
        self.finance_history_repo = FinanceHistoryRepository()
        self.user_goals_repo = UserGoalsRepository()
        self.finance_summary_service = FinanceSummaryService()

    def get_net_worth(self) -> dict:
        """Retorna patrimonio atual (conta corrente + investimentos) e historico de 12 meses.

        - checking_balance: soma dos saldos do ultimo snapshot de contas BANK.
        - investments_total: soma dos saldos atuais da tabela investments.
        - net_worth: soma dos dois itens acima.
        - history: ultimos 12 meses de finance_history mapeados para {month, net_worth}.
        """
        bank_snapshots = self.accounts_snapshot_repo.get_latest_snapshot_by_type("BANK")
        checking_balance = round(
            sum(row.get("balance") or 0.0 for row in bank_snapshots), 2
        )

        investments = self.investment_repo.get_investments()
        investments_total = round(sum(inv.balance or 0.0 for inv in investments), 2)

        net_worth = round(checking_balance + investments_total, 2)

        cutoff = (date.today().replace(day=1) - relativedelta(months=11)).strftime("%Y-%m")
        all_history = self.finance_history_repo.get_all()
        history = sorted(
            [
                # total_cash = bank balance + investments at month-end snapshot
                {"month": e.month, "net_worth": round(e.total_cash or 0.0, 2)}
                for e in all_history
                if e.month >= cutoff and e.total_cash is not None
            ],
            key=lambda x: x["month"],
        )

        return {
            "checking_balance": checking_balance,
            "investments_total": investments_total,
            "net_worth": net_worth,
            "history": history,
        }

    def get_partial_result(self) -> dict:
        """Retorna resultado parcial do mes corrente vs meta de saldo.

        - income_so_far: receitas acumuladas no mes atual.
        - expenses_so_far: despesas acumuladas no mes atual.
        - partial_balance: income_so_far - expenses_so_far.
        - monthly_balance_goal: meta mensal de saldo (user_goals, category_id IS NULL).
        - goal_pct: percentual da meta atingido (None se meta nao configurada).
        """
        today = date.today()
        month_start = today.replace(day=1)
        start_date = month_start.strftime("%Y-%m-%d")
        end_date = (month_start + relativedelta(months=1)).strftime("%Y-%m-%d")

        income_so_far = round(
            self.finance_summary_service.get_income(start_date, end_date), 2
        )
        expenses_so_far = round(
            self.finance_summary_service.get_expenses(start_date, end_date), 2
        )
        partial_balance = round(income_so_far - expenses_so_far, 2)

        monthly_balance_goal = self.user_goals_repo.get_total_monthly_goal()
        goal_pct = None
        if monthly_balance_goal and monthly_balance_goal > 0:
            goal_pct = round(partial_balance / monthly_balance_goal * 100, 1)

        return {
            "income_so_far": income_so_far,
            "expenses_so_far": expenses_so_far,
            "partial_balance": partial_balance,
            "monthly_balance_goal": monthly_balance_goal,
            "goal_pct": goal_pct,
        }
