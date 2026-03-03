"""Testes para FinanceSummaryService"""

import unittest
from unittest.mock import MagicMock, patch
from services.finance_summary_service import FinanceSummaryService


class TestFinanceSummaryService(unittest.TestCase):
    """Testes para a classe FinanceSummaryService"""

    def setUp(self):
        # Patch all repository and service dependencies
        with patch("services.finance_summary_service.TransactionService"), \
             patch("services.finance_summary_service.TransactionRepository"), \
             patch("services.finance_summary_service.PersonRepository"), \
             patch("services.finance_summary_service.CategoryRepository"), \
             patch("services.finance_summary_service.SplitwiseRepository"):
            self.service = FinanceSummaryService()

        # Create mocks for all dependencies
        self.mock_transaction_service = MagicMock()
        self.mock_transaction_repo = MagicMock()
        self.mock_person_repo = MagicMock()
        self.mock_category_repo = MagicMock()
        self.mock_splitwise_repo = MagicMock()

        # Assign mocks to service
        self.service.transaction_service = self.mock_transaction_service
        self.service.transaction_repository = self.mock_transaction_repo
        self.service.person_repository = self.mock_person_repo
        self.service.category_repository = self.mock_category_repo
        self.service.splitwise_repository = self.mock_splitwise_repo

    def test_get_income_without_split_transactions(self):
        """Testa cálculo de receitas sem transações divididas"""
        # Arrange
        mock_transaction1 = MagicMock()
        mock_transaction1.amount = 1000.0
        mock_transaction1.split_info = None

        mock_transaction2 = MagicMock()
        mock_transaction2.amount = 500.0
        mock_transaction2.split_info = None

        mock_transaction3 = MagicMock()  # Despesa, deve ser ignorada
        mock_transaction3.amount = -200.0
        mock_transaction3.split_info = None

        self.mock_transaction_service.get_bank_transactions.return_value = [
            mock_transaction1, mock_transaction2, mock_transaction3
        ]

        # Act
        result = self.service.get_income("2025-01-01", "2025-01-31")

        # Assert
        self.mock_transaction_service.get_bank_transactions.assert_called_with(
            start_date="2025-01-01", end_date="2025-01-31"
        )
        self.assertEqual(result, 1500.0)

    def test_get_income_excludes_split_transactions(self):
        """Testa que receitas divididas são excluídas do cálculo"""
        # Arrange
        mock_transaction1 = MagicMock()
        mock_transaction1.amount = 1000.0
        mock_transaction1.split_info = None

        mock_transaction2 = MagicMock()  # Deve ser excluída por ter split_info
        mock_transaction2.amount = 500.0
        mock_transaction2.split_info = {"partners": []}

        self.mock_transaction_service.get_bank_transactions.return_value = [
            mock_transaction1, mock_transaction2
        ]

        # Act
        result = self.service.get_income("2025-01-01", "2025-01-31")

        # Assert
        self.assertEqual(result, 1000.0)

    def test_get_expenses_basic_calculation(self):
        """Testa cálculo básico de despesas"""
        # Arrange
        bank_transaction = MagicMock()
        bank_transaction.amount = -100.0
        bank_transaction.transaction_type = "bank"
        bank_transaction.split_info = None
        bank_transaction.transaction_id = "bank1"

        credit_transaction = MagicMock()
        credit_transaction.amount = 200.0
        credit_transaction.transaction_type = "credit"
        credit_transaction.split_info = None
        credit_transaction.transaction_id = "credit1"

        self.mock_transaction_service.get_bank_transactions.return_value = [bank_transaction]
        self.mock_transaction_service.get_credit_transactions.return_value = [credit_transaction]
        self.mock_splitwise_repo.get_splitwise_by_transaction_id.return_value = None

        # Act
        result = self.service.get_expenses("2025-01-01", "2025-01-31")

        # Assert
        self.mock_transaction_service.get_bank_transactions.assert_called_with(
            start_date="2025-01-01", end_date="2025-01-31"
        )
        self.mock_transaction_service.get_credit_transactions.assert_called_with(
            start_date="2025-01-01", end_date="2025-01-31"
        )
        self.assertEqual(result, 300.0)  # 100 + 200

    def test_get_expenses_with_split_info_deduction(self):
        """Testa dedução de despesas divididas via split_info"""
        # Arrange
        transaction = MagicMock()
        transaction.amount = -100.0
        transaction.transaction_type = "bank"
        transaction.split_info = {
            "partners": [
                {"share": 30.0},
                {"share": 20.0}
            ]
        }
        transaction.transaction_id = "test1"

        self.mock_transaction_service.get_bank_transactions.return_value = [transaction]
        self.mock_transaction_service.get_credit_transactions.return_value = []
        self.mock_splitwise_repo.get_splitwise_by_transaction_id.return_value = None

        # Act
        result = self.service.get_expenses("2025-01-01", "2025-01-31")

        # Assert
        # 100 (expense) - 50 (split deduction) = 50
        self.assertEqual(result, 50.0)

    def test_get_expenses_with_splitwise_deduction(self):
        """Testa dedução de despesas via Splitwise"""
        # Arrange
        transaction = MagicMock()
        transaction.amount = -100.0
        transaction.transaction_type = "bank"
        transaction.split_info = None
        transaction.transaction_id = "test1"

        splitwise_ref = MagicMock()
        splitwise_ref.amount = 40.0

        self.mock_transaction_service.get_bank_transactions.return_value = [transaction]
        self.mock_transaction_service.get_credit_transactions.return_value = []
        self.mock_splitwise_repo.get_splitwise_by_transaction_id.return_value = splitwise_ref

        # Act
        result = self.service.get_expenses("2025-01-01", "2025-01-31")

        # Assert
        # 100 (expense) - 40 (splitwise deduction) = 60
        self.assertEqual(result, 60.0)

    def test_get_investment_value(self):
        """Testa obtenção do valor total de investimentos"""
        # Arrange
        investment1 = MagicMock()
        investment1.balance = 1000.0

        investment2 = MagicMock()
        investment2.balance = 2500.0

        self.mock_transaction_repo.get_investments.return_value = [investment1, investment2]

        # Act
        result = self.service.get_investment_value()

        # Assert
        self.mock_transaction_repo.get_investments.assert_called_once()
        self.assertEqual(result, 3500.0)

    def test_get_category_expenses_basic(self):
        """Testa cálculo de despesas por categoria"""
        # Arrange
        transaction = MagicMock()
        transaction.amount = -100.0
        transaction.transaction_type = "bank"
        transaction.split_info = None
        transaction.category_id = "cat1"
        transaction.transaction_id = "test1"

        category = MagicMock()
        category.id = "cat1"
        category.name = "Alimentação"
        category.types = ["expense"]

        self.mock_transaction_service.get_bank_transactions.return_value = [transaction]
        self.mock_transaction_service.get_credit_transactions.return_value = []
        self.mock_splitwise_repo.get_splitwise_by_transaction_id.return_value = None
        self.mock_category_repo.get_category_by_id.return_value = category

        # Act
        result = self.service.get_category_expenses("2025-01-01", "2025-01-31")

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "cat1")
        self.assertEqual(result[0]["name"], "Alimentação")
        self.assertEqual(result[0]["total"], 100.0)

    def test_get_category_expenses_sorted_by_amount(self):
        """Testa ordenação por valor absoluto"""
        # Arrange
        transaction1 = MagicMock()
        transaction1.amount = -50.0
        transaction1.transaction_type = "bank"
        transaction1.split_info = None
        transaction1.category_id = "cat1"
        transaction1.transaction_id = "test1"

        transaction2 = MagicMock()
        transaction2.amount = -200.0
        transaction2.transaction_type = "bank"
        transaction2.split_info = None
        transaction2.category_id = "cat2"
        transaction2.transaction_id = "test2"

        category1 = MagicMock()
        category1.id = "cat1"
        category1.name = "Pequena"
        category1.types = ["expense"]

        category2 = MagicMock()
        category2.id = "cat2"
        category2.name = "Grande"
        category2.types = ["expense"]

        self.mock_transaction_service.get_bank_transactions.return_value = [transaction1, transaction2]
        self.mock_transaction_service.get_credit_transactions.return_value = []
        self.mock_splitwise_repo.get_splitwise_by_transaction_id.return_value = None

        def get_category_side_effect(cat_id):
            if cat_id == "cat1":
                return category1
            elif cat_id == "cat2":
                return category2
            return None

        self.mock_category_repo.get_category_by_id.side_effect = get_category_side_effect

        # Act
        result = self.service.get_category_expenses("2025-01-01", "2025-01-31")

        # Assert
        self.assertEqual(len(result), 2)
        # Deve estar ordenado por valor absoluto (maior primeiro)
        self.assertEqual(result[0]["name"], "Grande")
        self.assertEqual(result[0]["total"], 200.0)
        self.assertEqual(result[1]["name"], "Pequena")
        self.assertEqual(result[1]["total"], 50.0)

    def test_get_category_expenses_excludes_nonexistent_categories(self):
        """Testa que categorias inexistentes são excluídas"""
        # Arrange
        transaction = MagicMock()
        transaction.amount = -100.0
        transaction.transaction_type = "bank"
        transaction.split_info = None
        transaction.category_id = "nonexistent"
        transaction.transaction_id = "test1"

        self.mock_transaction_service.get_bank_transactions.return_value = [transaction]
        self.mock_transaction_service.get_credit_transactions.return_value = []
        self.mock_splitwise_repo.get_splitwise_by_transaction_id.return_value = None
        self.mock_category_repo.get_category_by_id.return_value = None  # Categoria não existe

        # Act
        result = self.service.get_category_expenses("2025-01-01", "2025-01-31")

        # Assert
        self.assertEqual(len(result), 0)

    def test_get_full_summary(self):
        """Testa geração do resumo completo"""
        # Arrange
        # Mock all the individual methods
        self.service.get_income = MagicMock(return_value=2000.0)
        self.service.get_expenses = MagicMock(return_value=1200.0)
        self.service.get_investment_value = MagicMock(return_value=5000.0)
        self.service.get_category_expenses = MagicMock(return_value=[
            {"id": "cat1", "name": "Alimentação", "types": ["expense"], "total": 800.0}
        ])

        # Act
        result = self.service.get_full_summary("2025-01-01", "2025-01-31")

        # Assert
        expected = {
            "period": {"start_date": "2025-01-01", "end_date": "2025-01-31"},
            "totals": {
                "income": 2000.0,
                "expenses": 1200.0,
                "balance": 800.0,  # 2000 - 1200
                "investments": 5000.0,
            },
            "expenses_by_category": [
                {"id": "cat1", "name": "Alimentação", "types": ["expense"], "total": 800.0}
            ],
        }

        self.assertEqual(result, expected)
        self.service.get_income.assert_called_with("2025-01-01", "2025-01-31")
        self.service.get_expenses.assert_called_with("2025-01-01", "2025-01-31")
        self.service.get_investment_value.assert_called_once()
        self.service.get_category_expenses.assert_called_with("2025-01-01", "2025-01-31")


if __name__ == "__main__":
    unittest.main()