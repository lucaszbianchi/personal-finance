from typing import List
from repositories.transaction_repository import TransactionRepository
from repositories.category_repository import CategoryRepository
from repositories.finance_history_repository import FinanceHistoryRepository
from services.transaction_service import TransactionService


class FinanceSummaryService:
    """
    Serviço para cálculo de resumo financeiro, considerando regras de negócio do projeto.

    Regras de classificação:
    - Receita: bank_transactions com amount > 0 e excluded = 0
    - Gasto:   bank_transactions com amount < 0 e excluded = 0
             + credit_transactions com amount > 0 e excluded = 0
    """

    def __init__(self):
        self.transaction_service = TransactionService()
        self.transaction_repository = TransactionRepository()
        self.category_repository = CategoryRepository()

    @staticmethod
    def _is_income(t) -> bool:
        return t.transaction_type == "bank" and t.amount > 0 and not t.excluded

    @staticmethod
    def _is_expense(t) -> bool:
        if t.transaction_type == "bank":
            return t.amount < 0 and not t.excluded
        if t.transaction_type == "credit":
            return t.amount > 0 and not t.excluded
        return False

    def get_income(self, start_date: str, end_date: str) -> float:
        """Calcula as receitas em um determinado período."""
        transactions = self.transaction_service.get_bank_transactions(
            start_date=start_date, end_date=end_date
        )
        return sum(t.amount for t in transactions if self._is_income(t))

    def get_expenses(self, start_date: str, end_date: str) -> float:
        """Calcula as despesas em um determinado período."""
        bank = self.transaction_service.get_bank_transactions(
            start_date=start_date, end_date=end_date
        )
        credit = self.transaction_service.get_credit_transactions(
            start_date=start_date, end_date=end_date
        )
        return sum(abs(t.amount) for t in bank + credit if self._is_expense(t))

    def get_bank_expenses(self, start_date: str, end_date: str) -> float:
        """Calcula apenas as despesas bancárias (bank_transactions negativas) no período."""
        bank = self.transaction_service.get_bank_transactions(
            start_date=start_date, end_date=end_date
        )
        return sum(abs(t.amount) for t in bank if self._is_expense(t))

    def get_credit_expenses(self, start_date: str, end_date: str) -> float:
        """Calcula apenas as despesas de crédito (credit_transactions positivas) no período."""
        credit = self.transaction_service.get_credit_transactions(
            start_date=start_date, end_date=end_date
        )
        return sum(abs(t.amount) for t in credit if self._is_expense(t))

    def get_investment_value(self) -> float:
        """Calcula o valor total investido."""
        investments = self.transaction_repository.get_investments()
        total_investment = sum(inv.balance for inv in investments)
        return total_investment

    def get_category_expenses(self, start_date: str, end_date: str) -> List[dict]:
        """Calcula as despesas por categoria em um determinado período."""
        bank = self.transaction_service.get_bank_transactions(
            start_date=start_date, end_date=end_date
        )
        credit = self.transaction_service.get_credit_transactions(
            start_date=start_date, end_date=end_date
        )
        category_expenses: dict = {}
        for t in bank + credit:
            if not self._is_expense(t):
                continue
            cat_id = t.category_id
            if cat_id not in category_expenses:
                category_expenses[cat_id] = 0
            category_expenses[cat_id] += abs(t.amount)

        categories_result = []
        for cat_id, total in category_expenses.items():
            category = self.category_repository.get_category_by_id(cat_id)
            if category:
                categories_result.append(
                    {
                        "id": category.id,
                        "description": category.description,
                        "total": total,
                    }
                )

        return sorted(categories_result, key=lambda x: x["total"], reverse=True)

    def _resolve_root_category(self, category_id: str):
        """Walks up the parent chain to find the root (parentless) category."""
        cat = self.category_repository.get_category_by_id(category_id)
        if cat is None:
            return None
        visited = set()
        while cat.parent_id and cat.parent_id != cat.id:
            if cat.id in visited:
                break  # guard against cycles
            visited.add(cat.id)
            parent = self.category_repository.get_category_by_id(cat.parent_id)
            if parent is None:
                break
            cat = parent
        return cat

    def get_category_expenses_by_parent(self, start_date: str, end_date: str) -> List[dict]:
        """Calcula despesas agregadas por categoria pai (root), somando os filhos."""
        raw = self.get_category_expenses(start_date, end_date)
        parent_totals: dict = {}
        for item in raw:
            root = self._resolve_root_category(item["id"])
            if root is None:
                continue
            if root.id not in parent_totals:
                parent_totals[root.id] = {"id": root.id, "description": root.description, "total": 0.0}
            parent_totals[root.id]["total"] += item["total"]

        result = [
            {"id": v["id"], "description": v["description"], "total": round(v["total"], 2)}
            for v in parent_totals.values()
        ]
        return sorted(result, key=lambda x: x["total"], reverse=True)

    def get_history_data(self, month: str, cutoff: str) -> tuple:
        """Retorna (current_entry, all_history) do finance_history para o mês e cutoff dados."""
        repo = FinanceHistoryRepository()
        try:
            current_entry = repo.get_by_month(month)
            all_history = repo.get_all()
        finally:
            repo.close()
        return current_entry, all_history

    def get_full_summary(self, start_date: str, end_date: str) -> dict:
        """Retorna um resumo financeiro completo do período."""
        income = self.get_income(start_date, end_date)
        expenses = self.get_expenses(start_date, end_date)
        investment_value = self.get_investment_value()
        category_expenses = self.get_category_expenses(start_date, end_date)

        return {
            "period": {"start_date": start_date, "end_date": end_date},
            "totals": {
                "income": income,
                "expenses": expenses,
                "balance": income - expenses,
                "investments": investment_value,
            },
            "expenses_by_category": category_expenses,
        }


if __name__ == "__main__":
    service = FinanceSummaryService()
