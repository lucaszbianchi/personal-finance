from typing import List, Dict

from flask import jsonify

from helpers.query_db import QueryDB
from helpers.format_helpers import FormatHelpers


class FinanceSummaryService:
    """
    Serviço para cálculo de resumo financeiro, considerando regras de negócio do projeto.
    """

    query_db = QueryDB()
    format_date = FormatHelpers().format_date

    def get_bank_transactions(self) -> List[Dict]:
        """
        Returns a list of bank transactions excluding specific descriptions.
        """

        data = self.query_db.execute(
            "SELECT id, description, amount, date, category, operationType FROM bank_transactions WHERE description NOT IN ('Resgate RDB', 'Aplicação RDB') ORDER BY date DESC"
        )
        for row in data:
            row["date"] = self.format_date(row["date"])
        return jsonify(data)

    def get_credit_transactions(self) -> List[Dict]:

        data = self.query_db.execute(
            "SELECT id, description, amount, date, category, status FROM credit_transactions ORDER BY date DESC"
        )
        for row in data:
            row["date"] = self.format_date(row["date"])
        return jsonify(data)

    def get_investments(self) -> List[Dict]:

        data = self.query_db.execute(
            "SELECT id, name, amount, date, rate, type, subtype FROM investments WHERE amount != 0 ORDER BY date DESC"
        )
        for row in data:
            row["date"] = self.format_date(row["date"])
        return jsonify(data)
