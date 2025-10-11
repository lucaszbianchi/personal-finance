from typing import List, Optional
import json
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
                category_id,
                operation_type
            FROM bank_transactions
            WHERE description NOT IN ('Resgate RDB', 'Aplicação RDB', 'Aplicação em CDB')
            ORDER BY date DESC
        """
        rows = self.execute_query(query)
        return [
            BankTransaction(
                transaction_id=row["id"],
                date=self.date_helper.format_date(row["date"]),
                description=row["description"],
                amount=row["amount"],
                category_id=row["category_id"],
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
                category_id,
                status
            FROM credit_transactions
            ORDER BY date DESC
        """
        rows = self.execute_query(query)
        return [
            CreditTransaction(
                transaction_id=row["id"],
                date=self.date_helper.format_date(row["date"]),
                description=row["description"],
                amount=row["amount"],
                category_id=row["category_id"],
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
                category_id,
                operation_type
            FROM bank_transactions
            WHERE bank_transactions.id = ?
        """
        result = self.execute_query(query, (transaction_id,))
        return BankTransaction(
            transaction_id=result[0]["id"],
            date=self.date_helper.format_date(result[0]["date"]),
            description=result[0]["description"],
            amount=result[0]["amount"],
            category_id=result[0]["category_id"],
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
                category_id,
                status
            FROM credit_transactions
            WHERE credit_transactions.id = ?
        """
        result = self.execute_query(query, (transaction_id,))
        return CreditTransaction(
            transaction_id=result[0]["id"],
            date=self.date_helper.format_date(result[0]["date"]),
            description=result[0]["description"],
            amount=result[0]["amount"],
            category_id=result[0]["category_id"],
            status=result[0]["status"],
        )

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
                category_id,
                operation_type,
                split_info,
                payment_data
            FROM bank_transactions
            WHERE date BETWEEN ? AND ?
            AND description NOT IN ('Resgate RDB', 'Aplicação RDB', 'Aplicação em CDB')
            ORDER BY date DESC
        """
        rows = self.execute_query(bank_query, (start_date, end_date))
        return (
            [
                BankTransaction(
                    transaction_id=row["id"],
                    date=self.date_helper.format_date(row["date"]),
                    description=row["description"],
                    amount=row["amount"],
                    category_id=row["category_id"],
                    operation_type=row["operation_type"],
                    split_info=json.loads(row["split_info"]),
                    payment_data=json.loads(row["payment_data"]),
                )
                for row in rows
            ]
            if rows
            else []
        )

    def get_credit_transactions_by_period(
        self, start_date: str, end_date: str
    ) -> List[CreditTransaction]:
        """Retorna transações de cartão de crédito em um período específico."""
        credit_query = """
            SELECT 
                credit_transactions.id AS id,
                date,
                description,
                amount,
                category_id,
                status
            FROM credit_transactions
            WHERE date BETWEEN ? AND ?
            ORDER BY date DESC
        """
        rows = self.execute_query(credit_query, (start_date, end_date))
        return (
            [
                CreditTransaction(
                    transaction_id=row["id"],
                    date=self.date_helper.format_date(row["date"]),
                    description=row["description"],
                    amount=row["amount"],
                    category_id=row["category_id"],
                    status=row["status"],
                )
                for row in rows
            ]
            if rows
            else []
        )

    def add_bank_transaction(self, bank_transaction: BankTransaction) -> bool:
        """Adiciona uma nova transação bancária."""
        query = """
                INSERT OR IGNORE INTO bank_transactions
                (id, date, description, amount, category_id, type, operation_type, payment_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
        values = (
            bank_transaction.transaction_id,
            bank_transaction.date,
            bank_transaction.description,
            bank_transaction.amount,
            bank_transaction.category_id,
            bank_transaction.type_,
            bank_transaction.operation_type,
            json.dumps(bank_transaction.payment_data),
        )

        result = self.execute_update(query, values)
        return result > 0

    def add_credit_transaction(self, credit_transaction: CreditTransaction) -> bool:
        """Adiciona uma nova transação de cartão de crédito."""
        query = """
                INSERT OR IGNORE INTO credit_transactions
                (id, date, description, amount, category_id, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """
        values = (
            credit_transaction.transaction_id,
            credit_transaction.date,
            credit_transaction.description,
            credit_transaction.amount,
            credit_transaction.category_id,
            credit_transaction.status,
        )

        result = self.execute_update(query, values)
        return result > 0

    def update_bank_transaction(
        self,
        transaction_id: str,
        description: Optional[str],
        category: Optional[str],
        split_info: Optional[dict],
    ) -> bool:
        """Atualiza uma transação bancária existente."""
        if split_info:
            query = """
                UPDATE bank_transactions
                SET split_info = ?
                WHERE id = ?
            """
            values = (
                json.dumps(split_info),
                transaction_id,
            )

            result = self.execute_update(query, values)
            return result > 0
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
        description: Optional[str],
        category: Optional[str],
        split_info: Optional[dict],
    ) -> bool:
        """Atualiza uma transação de cartão de crédito existente."""

        if split_info:
            query = """
                UPDATE credit_transactions
                SET split_info = ?
                WHERE id = ?
            """
            values = (
                json.dumps(split_info),
                transaction_id,
            )

            result = self.execute_update(query, values)
            return result > 0
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
