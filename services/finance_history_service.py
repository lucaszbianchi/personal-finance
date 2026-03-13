from typing import Any, Dict, List, Optional
from datetime import datetime, date
from repositories.finance_history_repository import FinanceHistoryRepository
from repositories.transaction_repository import TransactionRepository
from repositories.bill_repository import BillRepository
from models.finance_history import FinanceHistory
from services.settings_service import SettingsService


def _first_day_of_next_month(month: str) -> str:
    """Returns YYYY-MM-DD for the first day of the month after `month` (YYYY-MM)."""
    year, mon = int(month[:4]), int(month[5:7])
    if mon == 12:
        return f"{year + 1}-01-01"
    return f"{year}-{mon + 1:02d}-01"


class FinanceHistoryService:
    def __init__(self, settings_service: SettingsService = None):
        self.finance_history_repository = FinanceHistoryRepository()
        self.transaction_repository = TransactionRepository()
        self.bill_repository = BillRepository()
        self.settings_service = settings_service or SettingsService()

    def update_meal_allowance(
        self, month: Optional[str] = None, value: Optional[float] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Atualiza o valor do vale refeição"""
        if month is None:
            month = datetime.now().strftime("%Y-%m")
        if value is None:
            value = float(input("Digite o valor atual do vale refeição: "))

        self.finance_history_repository.save_meal_allowance(month, value)
        return self._format_net_worth_history(self.finance_history_repository.get_all())

    def update_credit_card_info(
        self,
        month: Optional[str] = None,
        current_bill: Optional[float] = None,
        future_bill: Optional[float] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Atualiza as informações de cartão de crédito"""
        if month is None:
            month = datetime.now().strftime("%Y-%m")
        if current_bill is None:
            current_bill = float(input("Digite o valor da fatura atual do cartão: "))
        if future_bill is None:
            future_bill = float(input("Digite o valor da fatura futura do cartão: "))

        self.finance_history_repository.save_credit_card_info(
            month, current_bill, future_bill
        )
        return self._format_net_worth_history(self.finance_history_repository.get_all())

    def update_finance_history_from_sync(self, month: str) -> None:
        """Calcula e persiste income, expenses, credit_card_bill e risk_management após o sync."""
        from services.finance_summary_service import FinanceSummaryService

        start_date = f"{month}-01"
        end_date = _first_day_of_next_month(month)

        finance_summary = FinanceSummaryService()
        income = finance_summary.get_income(start_date, end_date)
        expenses = finance_summary.get_expenses(start_date, end_date)
        self.finance_history_repository.save_cash_flow(month, income, expenses)

        current_bill, future_bill = self.bill_repository.get_current_and_future_bill(month)
        self.finance_history_repository.save_credit_card_bills(month, current_bill, future_bill)

        self.finance_history_repository.calculate_and_save_risk_management(month)

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

        # Carry-forward: propaga meal_allowance da setting se o mês ainda não tem valor
        meal_value = self.settings_service.get_meal_allowance()
        if meal_value:
            entry = self.finance_history_repository.get_by_month(month)
            if entry and entry.meal_allowance is None:
                self.finance_history_repository.save_meal_allowance(month, meal_value)

        return self._format_net_worth_history(self.finance_history_repository.get_all())

    def update_all(self) -> Dict[str, Dict[str, Any]]:
        """Atualiza todas as informações financeiras de uma vez"""
        month = datetime.now().strftime("%Y-%m")

        # Atualiza vale refeição
        meal_allowance = float(input("Digite o valor atual do vale refeição: "))
        self.finance_history_repository.save_meal_allowance(month, meal_allowance)

        # Atualiza cartão de crédito
        current_bill = float(input("Digite o valor da fatura atual do cartão: "))
        future_bill = float(input("Digite o valor da fatura futura do cartão: "))
        self.finance_history_repository.save_credit_card_info(
            month, current_bill, future_bill
        )

        # Atualiza patrimônio
        investments_list = self.transaction_repository.get_investments()
        investments = {}
        for inv in investments_list:
            if inv.name not in investments:
                investments[inv.name] = 0.0
            investments[inv.name] += inv.balance
        bank_account = float(input("Digite o saldo atual da conta bancária: "))
        total_cash = bank_account + sum(investments.values())
        self.finance_history_repository.save_net_worth(month, total_cash, investments)

        # Atualiza fluxo de caixa
        income = float(input("Digite o total de receitas do mês: "))
        expenses = float(input("Digite o total de despesas do mês: "))
        self.finance_history_repository.save_cash_flow(month, income, expenses)

        # Calcula e atualiza o risco
        self.finance_history_repository.calculate_and_save_risk_management(month)

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
                "meal_allowance": entry.meal_allowance,
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
