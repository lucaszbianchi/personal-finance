from typing import List
from repositories.transaction_repository import TransactionRepository
from repositories.person_repository import PersonRepository
from repositories.category_repository import CategoryRepository
from repositories.splitwise_repository import SplitwiseRepository
from services.transaction_service import TransactionService


class FinanceSummaryService:
    """
    Serviço para cálculo de resumo financeiro, considerando regras de negócio do projeto.
    """

    def __init__(self):
        self.transaction_service = TransactionService()
        self.transaction_repository = TransactionRepository()
        self.person_repository = PersonRepository()
        self.category_repository = CategoryRepository()
        self.splitwise_repository = SplitwiseRepository()

    def get_income(self, start_date: str, end_date: str) -> float:
        """Calcula as receitas em um determinado período."""
        transactions = self.transaction_service.get_bank_transactions(
            start_date=start_date, end_date=end_date
        )
        income_transactions = [
            t for t in transactions if t.amount > 0 and not t.split_info
        ]
        income = sum(t.amount for t in income_transactions)
        return income

    def get_expenses(self, start_date: str, end_date: str) -> float:
        """Calcula as despesas em um determinado período."""
        bank_transactions = self.transaction_service.get_bank_transactions(
            start_date=start_date, end_date=end_date
        )
        credit_transactions = self.transaction_service.get_credit_transactions(
            start_date=start_date, end_date=end_date
        )
        transactions = bank_transactions + credit_transactions

        expenses = 0
        splited_expenses = 0

        for t in transactions:
            if t.split_info and t.split_info.get("partners", []):
                splited_expenses += sum(
                    partner["share"] for partner in t.split_info["partners"]
                )
            splitwise_reference = (
                self.splitwise_repository.get_splitwise_by_transaction_id(
                    t.transaction_id
                )
            )
            if splitwise_reference:
                splited_expenses += splitwise_reference.amount
            if (t.transaction_type == "bank" and t.amount < 0) or (
                t.transaction_type == "credit" and t.amount > 0
            ):
                expenses += abs(t.amount)

        expense = expenses - splited_expenses
        return expense

    def get_investment_value(self) -> float:
        """Calcula o valor total investido."""
        investments = self.transaction_repository.get_investments()
        total_investment = sum(inv.balance for inv in investments)
        return total_investment

    def get_category_expenses(self, start_date: str, end_date: str) -> List[dict]:
        """Calcula as despesas por categoria em um determinado período."""
        bank_transactions = self.transaction_service.get_bank_transactions(
            start_date=start_date, end_date=end_date
        )
        credit_transactions = self.transaction_service.get_credit_transactions(
            start_date=start_date, end_date=end_date
        )
        transactions = bank_transactions + credit_transactions
        category_expenses = {}
        for t in transactions:
            # Pagamentos de despesas compartilhadas são descontadas no cálculo
            if t.split_info and t.split_info.get("partners", []):
                category_id = t.split_info.get("category")
                if category_id:
                    if category_id not in category_expenses:
                        category_expenses[category_id] = 0
                    category_expenses[category_id] -= sum(
                        partner["share"] for partner in t.split_info["partners"]
                    )
            splitwise_reference = (
                self.splitwise_repository.get_splitwise_by_transaction_id(
                    t.transaction_id
                )
            )
            if splitwise_reference:
                category_id = splitwise_reference.category_id
                if category_id:
                    if category_id not in category_expenses:
                        category_expenses[category_id] = 0
                    category_expenses[category_id] -= splitwise_reference.amount
            if (t.transaction_type == "bank" and t.amount < 0) or (
                t.transaction_type == "credit" and t.amount > 0
            ):
                category_id = t.category_id
                if category_id not in category_expenses:
                    category_expenses[category_id] = 0
                category_expenses[category_id] += abs(t.amount)

        categories_result = []
        for cat, total in category_expenses.items():
            category = self.category_repository.get_category_by_id(cat)
            if category:  # Só adiciona se a categoria existe
                categories_result.append(
                    {
                        "id": category.id,
                        "description": category.description,
                        "total": total,
                    }
                )

        return sorted(categories_result, key=lambda x: abs(x["total"]), reverse=True)

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
