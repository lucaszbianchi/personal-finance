"""
Repository para gerenciar operações de banco de dados relacionadas a investimentos.
"""

from typing import List, Dict, Any
from repositories.base_repository import BaseRepository
from models.investment import Investment
from utils.date_helper import DateHelper


class InvestmentRepository(BaseRepository):
    """Repositório para gerenciar operações de banco de dados relacionadas a investimentos."""

    def __init__(self, db_path: str = "finance.db"):
        super().__init__(db_path=db_path)
        self.date_helper = DateHelper()

    def get_investments(self) -> List[Investment]:
        """Retorna todos os investimentos ativos."""
        query = """
            SELECT
                id,
                name,
                type,
                subtype,
                amount,
                balance,
                date,
                due_date,
                issuer,
                rate_type
            FROM investments
            WHERE balance != 0
            ORDER BY date DESC
        """
        cursor = self.execute_query(query)
        return [
            Investment(
                investment_id=row["id"],
                name=row["name"],
                type_=row["type"],
                subtype=row["subtype"],
                amount=row["amount"],
                balance=row["balance"],
                date=self.date_helper.format_date(row["date"]),
                due_date=self.date_helper.format_date(row["due_date"]),
                issuer=row["issuer"],
                rate_type=row["rate_type"],
            )
            for row in cursor.fetchall()
        ]

    def get_investment_by_id(self, investment_id: str) -> Investment:
        """Retorna um investimento específico pelo ID."""
        query = """
            SELECT
                id,
                name,
                type,
                subtype,
                amount,
                balance,
                date,
                due_date,
                issuer,
                rate_type
            FROM investments
            WHERE id = ?
        """
        cursor = self.execute_query(query, (investment_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Investimento com ID {investment_id} não encontrado.")

        return Investment(
            investment_id=row["id"],
            name=row["name"],
            type_=row["type"],
            subtype=row["subtype"],
            amount=row["amount"],
            balance=row["balance"],
            date=self.date_helper.format_date(row["date"]),
            due_date=self.date_helper.format_date(row["due_date"]),
            issuer=row["issuer"],
            rate_type=row["rate_type"],
        )

    # Método de Upsert usando a nova funcionalidade do BaseRepository

    def upsert_investment(self, investment_data: dict) -> Dict[str, Any]:
        """
        Insere ou atualiza um investimento usando strategy smart_merge.
        Saldos são atualizados a cada sync.

        Args:
            investment_data: Dict com dados do investimento da API Pluggy

        Returns:
            Dict com resultado da operação
        """
        mapped_data = {
            "id": investment_data["id"],
            "name": investment_data.get("name"),
            "type": investment_data.get("type"),
            "subtype": investment_data.get("subtype"),
            "amount": investment_data.get("amount"),
            "balance": investment_data.get("balance"),
            "date": investment_data.get("date"),
            "due_date": investment_data.get("dueDate"),
            "issuer": investment_data.get("issuer"),
            "rate_type": investment_data.get("rateType"),
        }

        return self.upsert("investments", "id", mapped_data, strategy="smart_merge")

    # Métodos legacy para compatibilidade (podem ser removidos futuramente)

    def add_investment(self, investment: Investment) -> bool:
        """Adiciona um novo investimento (método legacy)."""
        investment_data = {
            "id": investment.investment_id,
            "name": investment.name,
            "type": investment.type,
            "subtype": investment.subtype,
            "amount": investment.amount,
            "balance": investment.balance,
            "date": investment.date,
            "due_date": investment.due_date,
            "issuer": investment.issuer,
            "rate_type": investment.rate_type,
        }

        result = self.upsert_investment(investment_data)
        # com smart_merge, "inserted" = novo; "updated" = já existia
        return result["action"] == "inserted"

    def update_investment_balance(
        self, investment_id: str, balance: float, date: str, due_date: str = None
    ) -> bool:
        """Atualiza saldo de um investimento (método legacy)."""
        query = (
            "UPDATE investments SET balance = ?, date = ?, due_date = ? WHERE id = ?"
        )
        cursor = self.execute_query(query, (balance, date, due_date, investment_id))
        return cursor.rowcount > 0
