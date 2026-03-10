import json
from typing import List, Optional
from utils.date_helper import DateHelper
from repositories.base_repository import BaseRepository
from models.splitwise import Splitwise
from models.transaction import Transaction
from models.transaction import BankTransaction
from models.transaction import CreditTransaction


class SplitwiseRepository(BaseRepository):
    """Repositório para gerenciar operações de banco de dados relacionadas ao Splitwise."""

    def __init__(self, db_path: str = "finance.db"):
        super().__init__(db_path=db_path)
        self.date_helper = DateHelper()

    def get_all_splitwise(self) -> List[Splitwise]:
        """Retorna todas as transações do Splitwise válidas (excluindo as inválidas)."""
        query = """
            SELECT id, amount, date, description, category_id, transaction_id, is_invalid
            FROM splitwise
            WHERE is_invalid = 0
            ORDER BY date DESC
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
                is_invalid=bool(row["is_invalid"]),
            )
            splitwise_list.append(splitwise)
        return splitwise_list

    def get_splitwise_by_transaction_id(
        self, transaction_id: str
    ) -> Optional[Splitwise]:
        """Retorna uma transação do Splitwise que contém a transação especificada."""
        query = "SELECT id, amount, date, description, category_id, transaction_id, is_invalid FROM splitwise WHERE transaction_id = ?"
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
                is_invalid=bool(row["is_invalid"]),
            )
        return None

    def get_splitwise_by_id(self, splitwise_id: str) -> Optional[Splitwise]:
        """Retorna uma transação do Splitwise pelo ID."""
        query = "SELECT id, amount, date, description, category_id, transaction_id, is_invalid FROM splitwise WHERE id = ?"
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
                is_invalid=bool(row["is_invalid"]),
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
        """Retorna todos os splitwise válidos que não estão quitados (faltam transações vinculadas)."""
        query = "SELECT id, amount, date, description, category_id, transaction_id, is_invalid FROM splitwise WHERE is_invalid = 0"
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
                        is_invalid=bool(row["is_invalid"]),
                    )
                )
        return unsettled

    # Método de Upsert usando a nova funcionalidade do BaseRepository

    def upsert_splitwise_transaction(self, transaction_data: dict) -> dict:
        """
        Insere ou atualiza uma transação Splitwise usando strategy smart_merge.
        Transações Splitwise podem ser alteradas, então usa upsert inteligente.

        Args:
            transaction_data: Dict com dados da transação da API Pluggy

        Returns:
            Dict com resultado da operação
        """
        # Mapeia dados da API para schema do banco
        mapped_data = {
            "id": transaction_data["id"],
            "date": transaction_data["date"],
            "description": transaction_data.get("description"),
            "amount": transaction_data.get("amount"),
            "category_id": transaction_data.get("categoryId"),
            "transaction_id": None,  # Inicialmente vazio, será preenchido por lógica de negócio
        }

        # Transações Splitwise podem ter alterações nos dados básicos
        # Mantém transaction_id se já existir para não quebrar vinculações
        update_fields = ["date", "description", "amount", "category_id"]

        result = self.upsert(
            "splitwise",
            "id",
            mapped_data,
        )

        # Processa lógica de negócio adicional
        self._process_category_creation(transaction_data)

        return result

    def _process_category_creation(self, transaction_data: dict) -> None:
        """
        Cria categoria automaticamente se não existir.
        Mantém a lógica existente de fetch_data.py.
        """
        category_id = transaction_data.get("categoryId")
        category_name = transaction_data.get("category")

        if category_id and category_name:
            category_data = {"id": category_id, "description": category_name}

            # Usa insert_only para categorias (não devem ser alteradas automaticamente)
            self.upsert("categories", "id", category_data)

    def get_bank_transactions_by_date(self, date_str: str) -> list:
        """Retorna transações bancárias de uma data específica."""
        query = """
            SELECT
                id, date, description, amount, category_id,
                operation_type, split_info, payment_data
            FROM bank_transactions
            WHERE DATE(date) = DATE(?)
            AND description NOT IN ('Resgate RDB', 'Aplicação RDB', 'Aplicação em CDB')
            ORDER BY date DESC
        """
        cursor = self.execute_query(query, (date_str,))
        transactions = []
        for row in cursor.fetchall():
            transaction = BankTransaction(
                transaction_id=row["id"],
                date=self.date_helper.format_date(row["date"]),
                description=row["description"],
                amount=row["amount"],
                category_id=row["category_id"],
                operation_type=row["operation_type"],
                split_info=json.loads(row["split_info"]) if row["split_info"] else None,
                payment_data=(
                    json.loads(row["payment_data"]) if row["payment_data"] else None
                ),
            )
            transactions.append(transaction)
        return transactions

    def get_credit_transactions_by_date(self, date_str: str) -> list:
        """Retorna transações de cartão de crédito de uma data específica."""
        query = """
            SELECT
                id, date, description, amount, category_id,
                split_info, status
            FROM credit_transactions
            WHERE DATE(date) = DATE(?)
            ORDER BY date DESC
        """
        cursor = self.execute_query(query, (date_str,))
        transactions = []
        for row in cursor.fetchall():
            transaction = CreditTransaction(
                transaction_id=row["id"],
                date=self.date_helper.format_date(row["date"]),
                description=row["description"],
                amount=row["amount"],
                category_id=row["category_id"],
                split_info=json.loads(row["split_info"]) if row["split_info"] else None,
                status=row["status"],
            )
            transactions.append(transaction)
        return transactions

    def update_match_type(self, splitwise_id: str, match_type: str) -> None:
        """Atualiza o campo match_type de uma entrada do Splitwise."""
        query = "UPDATE splitwise SET match_type = ? WHERE id = ?"
        self.execute_query(query, (match_type, splitwise_id))

    def mark_splitwise_invalid(self, splitwise_id: str) -> bool:
        """Marca um item do Splitwise como inválido."""
        try:
            query = "UPDATE splitwise SET is_invalid = 1 WHERE id = ?"
            cursor = self.execute_query(query, (splitwise_id,))
            return cursor.rowcount > 0
        except Exception:
            return False

    def mark_splitwise_valid(self, splitwise_id: str) -> bool:
        """Marca um item do Splitwise como válido."""
        try:
            query = "UPDATE splitwise SET is_invalid = 0 WHERE id = ?"
            cursor = self.execute_query(query, (splitwise_id,))
            return cursor.rowcount > 0
        except Exception:
            return False

    def update_splitwise_content(self, splitwise_id: str, date: str, amount: float) -> bool:
        """Atualiza data e valor de um item do Splitwise."""
        try:
            query = "UPDATE splitwise SET date = ?, amount = ? WHERE id = ?"
            cursor = self.execute_query(query, (date, amount, splitwise_id))
            return cursor.rowcount > 0
        except Exception:
            return False

    def get_all_splitwise_including_invalid(self) -> List[Splitwise]:
        """Retorna todas as transações do Splitwise, incluindo as inválidas (para administração)."""
        query = """
            SELECT id, amount, date, description, category_id, transaction_id, is_invalid
            FROM splitwise
            ORDER BY date DESC
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
                is_invalid=bool(row["is_invalid"]),
            )
            splitwise_list.append(splitwise)
        return splitwise_list

    def create_splitwise(self, splitwise: Splitwise) -> Splitwise:
        """
        Cria uma nova entrada do Splitwise no banco de dados.

        Args:
            splitwise: Objeto Splitwise com os dados da nova entrada

        Returns:
            Splitwise: A entrada criada com ID atualizado

        Raises:
            ValueError: Se a entrada já existe ou dados são inválidos
        """
        if not splitwise.splitwise_id:
            raise ValueError("ID da entrada do Splitwise é obrigatório")
        if not splitwise.description:
            raise ValueError("Descrição é obrigatória")
        if splitwise.amount is None:
            raise ValueError("Valor é obrigatório")

        # Verifica se já existe uma entrada com o mesmo ID
        existing_splitwise = self.get_splitwise_by_id(splitwise.splitwise_id)
        if existing_splitwise:
            raise ValueError(f"Entrada do Splitwise com ID {splitwise.splitwise_id} já existe")

        # Converte a data para string no formato correto se for datetime
        date_str = splitwise.date
        if hasattr(splitwise.date, 'strftime'):
            date_str = splitwise.date.strftime('%Y-%m-%d')

        # Usa upsert com strategy insert_only para garantir que não sobrescreva
        splitwise_data = {
            "id": splitwise.splitwise_id,
            "amount": splitwise.amount,
            "date": date_str,
            "description": splitwise.description,
            "category_id": splitwise.category_id,
            "transaction_id": splitwise.transaction_id,
            "is_invalid": 1 if splitwise.is_invalid else 0
        }

        result = self.upsert("splitwise", "id", splitwise_data)

        if result["success"] and result["action"] == "inserted":
            return splitwise
        else:
            raise ValueError(f"Falha ao criar entrada do Splitwise: {result.get('error', 'Erro desconhecido')}")

    def delete_splitwise(self, splitwise_id: str) -> bool:
        """
        Deleta uma entrada do Splitwise do banco de dados.

        Args:
            splitwise_id: ID da entrada a ser deletada

        Returns:
            bool: True se a entrada foi deletada com sucesso

        Raises:
            ValueError: Se a entrada não existe ou está vinculada a transações
        """
        if not splitwise_id:
            raise ValueError("ID da entrada do Splitwise é obrigatório")

        # Verifica se a entrada existe
        splitwise = self.get_splitwise_by_id(splitwise_id)
        if not splitwise:
            raise ValueError(f"Entrada do Splitwise com ID {splitwise_id} não encontrada")

        # Verifica se a entrada está vinculada a alguma transação
        # Se estiver vinculada, não deve ser deletada para manter integridade
        if splitwise.transaction_id:
            raise ValueError(f"Não é possível deletar entrada do Splitwise '{splitwise.description}'. Ela está vinculada à transação {splitwise.transaction_id}.")

        # Deleta a entrada
        query = "DELETE FROM splitwise WHERE id = ?"
        cursor = self.execute_query(query, (splitwise_id,))
        return cursor.rowcount > 0
