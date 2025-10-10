from typing import List
from utils.date_helper import DateHelper
from repositories.base_repository import BaseRepository
from models.transaction import BankTransaction, CreditTransaction
from models.investment import Investment


class TransactionRepository(BaseRepository):
    """Repositório para gerenciar operações de banco de dados relacionadas a transações."""

    def __init__(self):
        super().__init__()
        self.date_helper = DateHelper()

    def get_bank_transactions(self) -> List[BankTransaction]:
        """Retorna todas as transações bancárias como objetos BankTransaction."""
        query = """
            SELECT 
                bank_transactions.id,
                date,
                description,
                amount,
                categories.name AS category,
                operation_type
            FROM bank_transactions
            JOIN categories ON bank_transactions.category_id = categories.id
            WHERE description NOT IN ('Resgate RDB', 'Aplicação RDB', 'Aplicação em CDB')
            ORDER BY date DESC
        """
        rows = self.execute_query(query)
        return [
            BankTransaction(
                id_=row["id"],
                date=self.date_helper.format_date(row["date"]),
                description=row["description"],
                amount=row["amount"],
                category=row["category"],
                operation_type=row["operation_type"],
            )
            for row in rows
        ]

    def get_credit_transactions(self) -> List[CreditTransaction]:
        """Retorna todas as transações de crédito como objetos CreditTransaction."""
        query = """
            SELECT 
                credit_transactions.id,
                date,
                description,
                amount,
                categories.name AS category,
                status
            FROM credit_transactions
            JOIN categories ON credit_transactions.category_id = categories.id
            ORDER BY date DESC
        """
        rows = self.execute_query(query)
        return [
            CreditTransaction(
                id_=row["id"],
                date=self.date_helper.format_date(row["date"]),
                description=row["description"],
                amount=row["amount"],
                category=row["category"],
                status=row["status"],
            )
            for row in rows
        ]

    def get_investments(self) -> List[Investment]:
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
                rate_type
            FROM investments
            WHERE balance != 0
            ORDER BY date DESC
        """
        rows = self.execute_query(investment_query)
        return [
            Investment(
                investment_id=row["id"],
                name=row["name"],
                balance=row["balance"],
                type_=row["type"],
                subtype=row["subtype"],
                date=self.date_helper.format_date(row["date"]),
                due_date=self.date_helper.format_date(row["due_date"]),
                issuer=row["issuer"],
                rate_type=row["rate_type"],
            )
            for row in rows
        ]

    def get_bank_transaction_by_id(self, transaction_id: str) -> BankTransaction:
        """Retorna uma transação bancária específica pelo ID."""
        query = """
            SELECT 
                bank_transactions.id AS id,
                date,
                description,
                amount,
                categories.name AS category,
                operation_type
            FROM bank_transactions
            JOIN categories ON bank_transactions.category_id = categories.id
            WHERE bank_transactions.id = ?
        """
        result = self.execute_query(query, (transaction_id,))
        return BankTransaction(
            id_=result[0]["id"],
            date=self.date_helper.format_date(result[0]["date"]),
            description=result[0]["description"],
            amount=result[0]["amount"],
            category=result[0]["category"],
            operation_type=result[0]["operation_type"],
        )

    def get_credit_transaction_by_id(self, transaction_id: str) -> CreditTransaction:
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
        return CreditTransaction(
            id_=result[0]["id"],
            date=self.date_helper.format_date(result[0]["date"]),
            description=result[0]["description"],
            amount=result[0]["amount"],
            category=result[0]["category"],
            status=result[0]["status"],
        )

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
    ) -> List[BankTransaction]:
        """Retorna transações bancárias em um período específico."""
        bank_query = """
            SELECT 
                bank_transactions.id AS id,
                date,
                description,
                amount,
                categories.name AS category,
                operation_type
            FROM bank_transactions
            JOIN categories ON bank_transactions.category_id = categories.id
            WHERE date BETWEEN ? AND ?
            ORDER BY date DESC
        """
        rows = self.execute_query(bank_query, (start_date, end_date))
        return (
            [
                BankTransaction(
                    id_=row["id"],
                    date=self.date_helper.format_date(row["date"]),
                    description=row["description"],
                    amount=row["amount"],
                    category=row["category"],
                    operation_type=row["operation_type"],
                )
                for row in rows
            ]
            if rows
            else []
        )

    def get_all_credit_transactions_by_period(
        self, start_date: str, end_date: str
    ) -> List[CreditTransaction]:
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
        rows = self.execute_query(credit_query, (start_date, end_date))
        return (
            [
                CreditTransaction(
                    id_=row["id"],
                    date=self.date_helper.format_date(row["date"]),
                    description=row["description"],
                    amount=row["amount"],
                    category=row["category"],
                    status=row["status"],
                )
                for row in rows
            ]
            if rows
            else []
        )
