from typing import List, Optional
from repositories.person_repository import PersonRepository
from repositories.splitwise_repository import SplitwiseRepository
from models.splitwise import Splitwise


class SplitwiseService:
    def __init__(self):
        self.splitwise_repository = SplitwiseRepository()
        self.person_repository = PersonRepository()

    def get_all_splitwise(self) -> List[Splitwise]:
        """Retorna todas as transações do Splitwise."""
        return self.splitwise_repository.get_all_splitwise()

    def get_splitwise_by_id(self, splitwise_id: str) -> Optional[Splitwise]:
        """Retorna uma transação específica do Splitwise pelo ID."""
        return self.splitwise_repository.get_splitwise_by_id(splitwise_id)

    def get_splitwise_by_transaction(self, transaction_id: str) -> Optional[Splitwise]:
        """Retorna a transação do Splitwise vinculada a uma transação específica."""
        return self.splitwise_repository.get_splitwise_by_transaction_id(transaction_id)

    def link_transaction_to_splitwise(self, splitwise_id: str, transaction_id: str):
        """Vincula uma transação ao splitwise"""
        splitwise = self.splitwise_repository.get_splitwise_by_id(splitwise_id)
        if not splitwise:
            raise ValueError("Splitwise não encontrado")
        return self.splitwise_repository.set_transaction_to_splitwise(
            splitwise_id, transaction_id
        )

    def get_unsettled_splitwise(self) -> List[Splitwise]:
        """Retorna splitwise sem transação vinculada."""
        return self.splitwise_repository.get_unsettled_splitwise()

    def get_splitwise_summary(self) -> dict:
        """Retorna um resumo das transações do Splitwise."""
        splitwise_entries = self.splitwise_repository.get_all_splitwise()

        summary = {
            "total_entries": len(splitwise_entries),
            "total_amount": sum(entry.amount for entry in splitwise_entries),
            "settled": {
                "count": len([e for e in splitwise_entries if e.transaction_id]),
                "amount": sum(e.amount for e in splitwise_entries if e.transaction_id),
            },
            "unsettled": {
                "count": len([e for e in splitwise_entries if not e.transaction_id]),
                "amount": sum(
                    e.amount for e in splitwise_entries if not e.transaction_id
                ),
            },
        }

        return summary

    def update_splitwise(
        self, splitwise_id: str, category_id: str, transaction_id: str
    ):
        """Atualiza um registro do Splitwise."""
        splitwise = self.splitwise_repository.get_splitwise_by_id(splitwise_id)
        if not splitwise:
            raise ValueError("Splitwise não encontrado")
        return self.splitwise_repository.update_splitwise(
            splitwise_id, category_id, transaction_id
        )

    def category_in_use(self, category_id: str) -> bool:
        """Verifica se uma categoria está em uso no Splitwise."""
        return self.splitwise_repository.category_in_use(category_id)
