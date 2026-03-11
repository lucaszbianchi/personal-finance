from typing import List, Dict, Any
from repositories.investment_repository import InvestmentRepository
from repositories.finance_history_repository import FinanceHistoryRepository
from models.investment import Investment


class InvestmentService:
    def __init__(self):
        self.investment_repository = InvestmentRepository()
        self.finance_history_repository = FinanceHistoryRepository()

    def get_investments(self) -> List[Investment]:
        try:
            return self.investment_repository.get_investments()
        finally:
            self.investment_repository.close()

    def get_investment_history(self) -> List[Dict[str, Any]]:
        try:
            investments = self.investment_repository.get_investments()
            name_to_type = {i.name: i.type for i in investments}

            entries = self.finance_history_repository.get_all()
            result = []
            for entry in entries:
                if not entry.investments:
                    continue
                by_type: dict = {}
                for name, balance in entry.investments.items():
                    inv_type = name_to_type.get(name, "OTHER")
                    by_type.setdefault(inv_type, 0.0)
                    by_type[inv_type] += balance
                result.append({
                    "month": entry.month,
                    "investments": entry.investments,
                    "by_type": by_type,
                    "total": sum(entry.investments.values()),
                })
            return result
        finally:
            self.investment_repository.close()
            self.finance_history_repository.close()
