import unittest
from repositories.finance_history_repository import FinanceHistoryRepository


class TestFinanceHistoryRepository(unittest.TestCase):
    def setUp(self):
        self.repo = FinanceHistoryRepository(db_path=":memory:")
        self.month = "2099-01"
        # Cria tabela
        self.repo.execute_query(
            """
            CREATE TABLE finance_history (
                month TEXT PRIMARY KEY,
                meal_allowance REAL,
                credit_card_bill REAL,
                credit_card_future_bill REAL,
                total_cash REAL,
                investments TEXT,
                income REAL,
                expenses REAL,
                risk_management TEXT
            )
            """
        )
        self.repo.save_meal_allowance(self.month, 0)  # Limpa mês de teste

    def test_save_and_get_meal_allowance(self):
        self.repo.save_meal_allowance(self.month, 123.45)
        history = self.repo.get_by_month(self.month)
        self.assertIsNotNone(history)
        self.assertEqual(history.meal_allowance, 123.45)

    def test_save_and_get_credit_card_info(self):
        self.repo.save_credit_card_info(self.month, 1000, 2000)
        history = self.repo.get_by_month(self.month)
        self.assertEqual(history.credit_card_bill, 1000)
        self.assertEqual(history.credit_card_future_bill, 2000)

    def test_save_and_get_net_worth(self):
        investments = {"A": 500, "B": 500}
        self.repo.save_net_worth(self.month, 1000, investments)
        history = self.repo.get_by_month(self.month)
        self.assertEqual(history.total_cash, 1000)
        self.assertEqual(history.investments, investments)

    def test_save_and_get_cash_flow(self):
        self.repo.save_cash_flow(self.month, 5000, 3000)
        history = self.repo.get_by_month(self.month)
        self.assertEqual(history.income, 5000)
        self.assertEqual(history.expenses, 3000)

    def test_calculate_risk_management(self):
        self.repo.save_meal_allowance(self.month, 100)
        self.repo.save_credit_card_info(self.month, 100, 100)
        self.repo.save_net_worth(self.month, 100, {"A": 100})
        self.repo.save_cash_flow(self.month, 100, 100)
        self.repo.calculate_and_save_risk_management(self.month)
        history = self.repo.get_by_month(self.month)
        self.assertIsNotNone(history.risk_management)

    def test_save_credit_card_bills_updates_existing(self):
        """save_credit_card_bills faz UPDATE quando o mês já existe."""
        self.repo.save_credit_card_bills(self.month, 1000.0, 1200.0)
        history = self.repo.get_by_month(self.month)
        self.assertEqual(history.credit_card_bill, 1000.0)
        self.assertEqual(history.credit_card_future_bill, 1200.0)

        # Atualiza
        self.repo.save_credit_card_bills(self.month, 1500.0, 1800.0)
        history = self.repo.get_by_month(self.month)
        self.assertEqual(history.credit_card_bill, 1500.0)
        self.assertEqual(history.credit_card_future_bill, 1800.0)

    def test_save_credit_card_bills_inserts_new_month(self):
        """save_credit_card_bills faz INSERT quando o mês ainda não existe."""
        new_month = "2099-02"
        self.repo.save_credit_card_bills(new_month, 500.0, 600.0)
        history = self.repo.get_by_month(new_month)
        self.assertIsNotNone(history)
        self.assertEqual(history.credit_card_bill, 500.0)
        self.assertEqual(history.credit_card_future_bill, 600.0)


if __name__ == "__main__":
    unittest.main()
