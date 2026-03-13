from typing import Dict, List
from repositories.base_repository import BaseRepository
from models.finance_history import FinanceHistory
import json


class FinanceHistoryRepository(BaseRepository):
    def __init__(self, db_path: str = "finance.db"):
        super().__init__(db_path=db_path)

    def dict_to_json(self, d: Dict) -> str:
        """Converte dicionário para JSON string"""
        return json.dumps(d)

    def json_to_dict(self, j: str) -> Dict:
        """Converte JSON string para dicionário"""
        return json.loads(j)

    def save_meal_allowance(self, month: str, meal_allowance: float) -> None:
        """Salva ou atualiza o valor do vale refeição para um determinado mês"""
        if meal_allowance is None:
            return
        existing = self.get_by_month(month)
        cursor = None
        if existing:
            cursor = self.execute_query(
                "UPDATE finance_history SET meal_allowance = ? WHERE month = ?",
                (meal_allowance, month),
            )
        else:
            cursor = self.execute_query(
                "INSERT INTO finance_history (month, meal_allowance) VALUES (?, ?)",
                (month, meal_allowance),
            )
        print(f"Rows affected: {cursor.rowcount}")

    def save_credit_card_info(
        self, month: str, current_bill: float, future_bill: float
    ) -> None:
        """Salva ou atualiza as informações de cartão de crédito para um determinado mês"""
        if current_bill is None or future_bill is None:
            return
        existing = self.get_by_month(month)
        if existing:
            self.execute_query(
                "UPDATE finance_history SET credit_card_bill = ?, credit_card_future_bill = ? WHERE month = ?",
                (current_bill, future_bill, month),
            )
        else:
            self.execute_query(
                "INSERT INTO finance_history (month, credit_card_bill, credit_card_future_bill) VALUES (?, ?, ?)",
                (month, current_bill, future_bill),
            )

    def save_net_worth(self, month: str, total_cash: float, investments: Dict) -> None:
        """Salva ou atualiza as informações de patrimônio líquido para um determinado mês"""
        if total_cash is None or investments is None:
            return
        existing = self.get_by_month(month)
        if existing:
            self.execute_query(
                "UPDATE finance_history SET total_cash = ?, investments = ? WHERE month = ?",
                (total_cash, json.dumps(investments), month),
            )
        else:
            self.execute_query(
                "INSERT INTO finance_history (month, total_cash, investments) VALUES (?, ?, ?)",
                (month, total_cash, json.dumps(investments)),
            )

    def save_cash_flow(self, month: str, income: float, expenses: float) -> None:
        """Salva ou atualiza as informações de fluxo de caixa (receitas e despesas) para um determinado mês"""
        if income is None or expenses is None:
            return
        existing = self.get_by_month(month)
        if existing:
            self.execute_query(
                "UPDATE finance_history SET income = ?, expenses = ? WHERE month = ?",
                (income, expenses, month),
            )
        else:
            self.execute_query(
                "INSERT INTO finance_history (month, income, expenses) VALUES (?, ?, ?)",
                (month, income, expenses),
            )

    def save_credit_card_bills(
        self, month: str, current_bill: float, future_bill: float
    ) -> None:
        """Salva as faturas de cartão calculadas automaticamente."""
        existing = self.get_by_month(month)
        if existing:
            self.execute_query(
                "UPDATE finance_history SET credit_card_bill = ?, credit_card_future_bill = ? WHERE month = ?",
                (current_bill, future_bill, month),
            )
        else:
            self.execute_query(
                "INSERT INTO finance_history (month, credit_card_bill, credit_card_future_bill) VALUES (?, ?, ?)",
                (month, current_bill, future_bill),
            )

    def calculate_and_save_risk_management(self, month: str) -> None:
        """Calcula e salva o indicador de gestão de risco baseado nos dados existentes do mês."""
        finance_data = self.get_by_month(month)
        if not finance_data:
            return

        total_fixed_costs = (finance_data.credit_card_bill or 0) + (finance_data.expenses or 0)
        available_cash = (finance_data.total_cash or 0) + (finance_data.meal_allowance or 0)
        investment_count = len(finance_data.investments) if finance_data.investments else 0
        income = finance_data.income or 0

        # Score de 0 a 100 com 3 componentes
        liquidity = (available_cash / total_fixed_costs * 50) if total_fixed_costs > 0 else 50
        diversification = min(investment_count * 10, 30)
        income_coverage = min((income / total_fixed_costs * 20), 20) if total_fixed_costs > 0 else 20
        risk_score = min(100, liquidity + diversification + income_coverage)

        self.execute_query(
            "UPDATE finance_history SET risk_management = ? WHERE month = ?",
            (risk_score, month),
        )

    def save(self, finance_history: FinanceHistory) -> None:
        """Método legado que salva todas as informações de uma vez"""
        self.save_meal_allowance(finance_history.month, finance_history.meal_allowance)
        self.save_credit_card_info(
            finance_history.month,
            finance_history.credit_card_bill,
            finance_history.credit_card_future_bill,
        )
        self.save_net_worth(
            finance_history.month,
            finance_history.total_cash,
            finance_history.investments,
        )
        self.save_cash_flow(
            finance_history.month, finance_history.income, finance_history.expenses
        )
        self.calculate_and_save_risk_management(finance_history.month)

    def get_by_month(self, month: str) -> FinanceHistory:
        cursor = self.execute_query(
            "SELECT month, meal_allowance, credit_card_bill, credit_card_future_bill, total_cash, investments, expenses, income, risk_management FROM finance_history WHERE month = ?",
            (month,),
        )
        row = cursor.fetchone()
        if row:
            return FinanceHistory(
                month=row[0],
                meal_allowance=row[1],
                credit_card_bill=row[2],
                credit_card_future_bill=row[3],
                total_cash=row[4],
                investments=json.loads(row[5]) if row[5] else {},
                expenses=row[6],
                income=row[7],
                risk_management=row[8],
            )
        return None

    def get_all(self) -> List[FinanceHistory]:
        """Retorna todo o histórico de patrimônio"""
        cursor = self.execute_query(
            "SELECT month, meal_allowance, credit_card_bill, credit_card_future_bill, total_cash, investments, expenses, income, risk_management FROM finance_history ORDER BY month DESC"
        )
        rows = cursor.fetchall()
        return [
            FinanceHistory(
                month=row[0],
                meal_allowance=row[1],
                credit_card_bill=row[2],
                credit_card_future_bill=row[3],
                total_cash=row[4],
                investments=json.loads(row[5]) if row[5] else {},
                expenses=row[6],
                income=row[7],
                risk_management=row[8],
            )
            for row in rows
        ]
