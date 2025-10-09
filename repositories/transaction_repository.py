from typing import List, Dict, Any
from repositories.base_repository import BaseRepository


class TransactionRepository(BaseRepository):
    """Repositório para gerenciar operações de banco de dados relacionadas a transações."""

    def get_bank_transactions(self) -> List[Dict[str, Any]]:
        """Retorna todas as transações bancárias."""
        bank_query = """
            SELECT 
                bank_transactions.id AS id,
                date,
                description,
                amount,
                categories.name AS category,
                operationType
            FROM bank_transactions
            JOIN categories ON bank_transactions.category_id = categories.id
            WHERE description NOT IN ('Resgate RDB', 'Aplicação RDB', 'Aplicação em CDB')
            ORDER BY date DESC
        """
        bank_transactions = self.execute_query(bank_query)
        return bank_transactions

    def get_credit_transactions(self) -> List[Dict[str, Any]]:
        """Retorna todas as transações de cartão de crédito."""
        credit_query = """
            SELECT 
                credit_transactions.id AS id,
                date,
                description,
                amount,
                categories.name AS category,
                status
            FROM credit_transactions
            JOIN categories ON credit_transactions.category_id = categories.id
            ORDER BY date DESC
        """
        credit_transactions = self.execute_query(credit_query)
        return credit_transactions

    def get_investments(self) -> List[Dict[str, Any]]:
        """Retorna todas as transações de investimentos."""
        investment_query = """
            SELECT 
                id,
                name,
                balance,
                type,
                subtype,
                date,
                due_date,
                issuer,
                rateType
            FROM investments
            WHERE balance != 0
            ORDER BY date DESC
        """
        investment_transactions = self.execute_query(investment_query)
        return investment_transactions

    def get_bank_transaction_by_id(self, transaction_id: str) -> Dict[str, Any]:
        """Retorna uma transação bancária específica pelo ID."""
        query = """
            SELECT 
                bank_transactions.id AS id,
                date,
                description,
                amount,
                categories.name AS category,
                operationType
            FROM bank_transactions
            JOIN categories ON bank_transactions.category_id = categories.id
            WHERE bank_transactions.id = ?
        """
        result = self.execute_query(query, (transaction_id,))
        return result[0] if result else None

    def get_credit_transaction_by_id(self, transaction_id: str) -> Dict[str, Any]:
        """Retorna uma transação de cartão de crédito específica pelo ID."""
        query = """
            SELECT 
                credit_transactions.id AS id,
                date,
                description,
                amount,
                categories.name AS category,
                status
            FROM credit_transactions
            JOIN categories ON credit_transactions.category_id = categories.id
            WHERE credit_transactions.id = ?
        """
        result = self.execute_query(query, (transaction_id,))
        return result[0] if result else None

    def update_bank_transaction(
        self,
        transaction_id: str,
        description: str,
        category: str = None,
    ) -> bool:
        """Atualiza uma transação bancária existente."""
        query = """
            UPDATE bank_transactions
            SET description = ?, category_id = (
                SELECT id FROM categories WHERE name = ?
            )
            WHERE id = ?
        """
        values = (
            description,
            category,
            transaction_id,
        )

        result = self.execute_update(query, values)
        return result > 0

    def update_credit_transaction(
        self,
        transaction_id: str,
        description: str,
        category: str = None,
    ) -> bool:
        """Atualiza uma transação de cartão de crédito existente."""
        query = """
            UPDATE credit_transactions
            SET description = ?, category_id = (
                SELECT id FROM categories WHERE name = ?
            )
            WHERE id = ?
        """
        values = (
            description,
            category,
            transaction_id,
        )

        result = self.execute_update(query, values)
        return result > 0

    def get_bank_transactions_by_period(
        self, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """Retorna transações bancárias em um período específico."""
        bank_query = """
            SELECT 
                bank_transactions.id AS id,
                date,
                description,
                amount,
                categories.name AS category,
                operationType
            FROM bank_transactions
            JOIN categories ON bank_transactions.category_id = categories.id
            WHERE date BETWEEN ? AND ?
            ORDER BY date DESC
        """
        bank_transactions = self.execute_query(bank_query, (start_date, end_date))
        return bank_transactions

    def get_all_credit_transactions_by_period(
        self, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """Retorna transações de cartão de crédito em um período específico."""
        credit_query = """
            SELECT 
                credit_transactions.id AS id,
                date,
                description,
                amount,
                categories.name AS category,
                status
            FROM credit_transactions
            JOIN categories ON credit_transactions.category_id = categories.id
            WHERE date BETWEEN ? AND ?
            ORDER BY date DESC
        """
        credit_transactions = self.execute_query(credit_query, (start_date, end_date))
        return credit_transactions
