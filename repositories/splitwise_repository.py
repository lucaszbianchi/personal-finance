from typing import List, Optional
from utils.date_helper import DateHelper
from repositories.base_repository import BaseRepository
from models.splitwise import Splitwise
from models.transaction import Transaction


class SplitwiseRepository(BaseRepository):
    """Repositório para gerenciar operações de banco de dados relacionadas ao Splitwise."""

    def __init__(self, db_path: str = "finance.db"):
        super().__init__(db_path=db_path)
        self.date_helper = DateHelper()

    def get_all_splitwise(self) -> List[Splitwise]:
        """Retorna todas as transações do Splitwise."""
        query = """
            SELECT id, amount, date, description, category_id, transaction_id FROM splitwise ORDER BY date DESC
        """
        cursor = self.execute_query(query)
        splitwise_list = []
        for row in cursor.fetchall():
            splitwise = Splitwise(
                splitwise_id=row["id"],
                amount=row["amount"],
                date=self.date_helper.format_date(row["date"]),
                description=row["description"],
                category_id=row["category_id"],
                transaction_id=row["transaction_id"],
            )
            splitwise_list.append(splitwise)
        return splitwise_list

    def get_splitwise_by_transaction_id(
        self, transaction_id: str
    ) -> Optional[Splitwise]:
        """Retorna uma transação do Splitwise que contém a transação especificada."""
        query = "SELECT id, amount, date, description, category_id, transaction_id FROM splitwise WHERE transaction_id = ?"
        cursor = self.execute_query(query, (transaction_id,))
        row = cursor.fetchone()
        if row:
            return Splitwise(
                splitwise_id=row["id"],
                amount=row["amount"],
                date=self.date_helper.format_date(row["date"]),
                description=row["description"],
                category_id=row["category_id"],
                transaction_id=row["transaction_id"],
            )
        return None

    def get_splitwise_by_id(self, splitwise_id: str) -> Optional[Splitwise]:
        """Retorna uma transação do Splitwise pelo ID."""
        query = "SELECT id, amount, date, description, category_id, transaction_id FROM splitwise WHERE id = ?"
        cursor = self.execute_query(query, (splitwise_id,))
        row = cursor.fetchone()
        if row:
            return Splitwise(
                splitwise_id=row["id"],
                amount=row["amount"],
                date=self.date_helper.format_date(row["date"]),
                description=row["description"],
                category_id=row["category_id"],
                transaction_id=row["transaction_id"],
            )
        return None

    def update_splitwise(
        self, splitwise_id, category_id, transaction: str | None
    ) -> None:
        """Atualiza uma transação do Splitwise."""
        query = """
            UPDATE splitwise
            SET category_id = ?, transaction_id = ?
            WHERE id = ?
        """
        if transaction is None:
            transaction = ""
        values = (category_id, transaction, splitwise_id)
        self.execute_query(query, values)

    def set_transaction_to_splitwise(
        self, splitwise_id: str, transaction: Transaction
    ) -> bool:
        """Define as transações para uma entrada do Splitwise."""
        category_id = transaction.category_id
        self.update_splitwise(splitwise_id, category_id, transaction.transaction_id)
        return True

    def category_in_use(self, category_id: str) -> bool:
        """Verifica se uma categoria está em uso no Splitwise."""
        query = "SELECT COUNT(*) as count FROM splitwise WHERE category_id = ?"
        cursor = self.execute_query(query, (category_id,))
        row = cursor.fetchone()
        return row and row["count"] > 0

    def get_unsettled_splitwise(self) -> List[Splitwise]:
        """Retorna todos os splitwise que não estão quitados (faltam transações vinculadas)."""
        query = "SELECT id, amount, date, description, category_id, transaction_id FROM splitwise"
        cursor = self.execute_query(query)
        unsettled = []
        for row in cursor.fetchall():
            # Considera quitado se há pelo menos uma transação vinculada
            if not row["transaction_id"]:
                unsettled.append(
                    Splitwise(
                        splitwise_id=row["id"],
                        amount=row["amount"],
                        date=self.date_helper.format_date(row["date"]),
                        description=row["description"],
                        category_id=row["category_id"],
                        transaction_id=row["transaction_id"],
                    )
                )
        return unsettled
