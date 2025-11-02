from typing import Dict, Optional


class FinanceHistory:
    def __init__(
        self,
        month: str,
        meal_allowance: Optional[float],
        credit_card_bill: Optional[float],
        credit_card_future_bill: Optional[float],
        total_cash: Optional[float],
        investments: Optional[Dict[str, float]],
        expenses: Optional[float],
        income: Optional[float],
        risk_management: Optional[float],
    ):
        self.month = month
        self.meal_allowance = meal_allowance
        self.credit_card_bill = credit_card_bill
        self.credit_card_future_bill = credit_card_future_bill
        self.total_cash = total_cash
        self.investments = investments or {}
        self.expenses = expenses
        self.income = income
        self.risk_management = risk_management
