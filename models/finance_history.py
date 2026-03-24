from typing import Dict, Optional


class FinanceHistory:
    def __init__(
        self,
        month: str,
        credit_card_bill: Optional[float],
        credit_card_future_bill: Optional[float],
        total_cash: Optional[float],
        investments: Optional[Dict[str, float]],
        expenses: Optional[float],
        income: Optional[float],
        risk_management: Optional[float],
        bank_expenses: Optional[float] = None,
        credit_expenses: Optional[float] = None,
    ):
        self.month = month
        self.credit_card_bill = credit_card_bill
        self.credit_card_future_bill = credit_card_future_bill
        self.total_cash = total_cash
        self.investments = investments or {}
        self.expenses = expenses
        self.income = income
        self.risk_management = risk_management
        self.bank_expenses = bank_expenses
        self.credit_expenses = credit_expenses

