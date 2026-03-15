"""Testes para FinanceSummaryService"""

import unittest
from unittest.mock import MagicMock, patch
from services.finance_summary_service import FinanceSummaryService


def _make_bank(amount, category_id="cat1", description="Compra", excluded=0):
    t = MagicMock()
    t.transaction_type = "bank"
    t.amount = amount
    t.category_id = category_id
    t.description = description
    t.excluded = excluded
    return t


def _make_credit(amount, category_id="cat1", description="Compra", excluded=0):
    t = MagicMock()
    t.transaction_type = "credit"
    t.amount = amount
    t.category_id = category_id
    t.description = description
    t.excluded = excluded
    return t


class TestFinanceSummaryService(unittest.TestCase):

    def setUp(self):
        with patch("services.finance_summary_service.TransactionService"), \
             patch("services.finance_summary_service.TransactionRepository"), \
             patch("services.finance_summary_service.PersonRepository"), \
             patch("services.finance_summary_service.CategoryRepository"), \
             patch("services.finance_summary_service.SplitwiseRepository"):
            self.service = FinanceSummaryService()

        self.mock_transaction_service = MagicMock()
        self.mock_transaction_repo = MagicMock()
        self.mock_category_repo = MagicMock()

        self.service.transaction_service = self.mock_transaction_service
        self.service.transaction_repository = self.mock_transaction_repo
        self.service.category_repository = self.mock_category_repo

    # ── get_income ────────────────────────────────────────────────────────────

    def test_get_income_sums_positive_bank_transactions(self):
        """Receita = bank com amount > 0"""
        self.mock_transaction_service.get_bank_transactions.return_value = [
            _make_bank(1000.0),
            _make_bank(500.0),
            _make_bank(-200.0),  # despesa — ignorada
        ]
        self.assertEqual(self.service.get_income("2025-01-01", "2025-01-31"), 1500.0)

    def test_get_income_excludes_excluded_transactions(self):
        """Receita exclui transações marcadas como excluded=1"""
        self.mock_transaction_service.get_bank_transactions.return_value = [
            _make_bank(1000.0, category_id="cat1"),
            _make_bank(500.0, category_id="cat1", excluded=1),
        ]
        self.assertEqual(self.service.get_income("2025-01-01", "2025-01-31"), 1000.0)

    # ── get_expenses ──────────────────────────────────────────────────────────

    def test_get_expenses_bank_negative_plus_credit_positive(self):
        """Gasto = |bank amount < 0| + credit amount > 0"""
        self.mock_transaction_service.get_bank_transactions.return_value = [
            _make_bank(-100.0),
        ]
        self.mock_transaction_service.get_credit_transactions.return_value = [
            _make_credit(200.0),
        ]
        self.assertEqual(self.service.get_expenses("2025-01-01", "2025-01-31"), 300.0)

    def test_get_expenses_excludes_excluded_transactions(self):
        """Gastos excluem transações marcadas como excluded=1"""
        self.mock_transaction_service.get_bank_transactions.return_value = [
            _make_bank(-100.0, category_id="cat1"),
            _make_bank(-500.0, category_id="cat1", excluded=1),
        ]
        self.mock_transaction_service.get_credit_transactions.return_value = []
        self.assertEqual(self.service.get_expenses("2025-01-01", "2025-01-31"), 100.0)

    def test_get_expenses_excludes_excluded_credit(self):
        """Gastos excluem transações de crédito marcadas como excluded=1"""
        self.mock_transaction_service.get_bank_transactions.return_value = []
        self.mock_transaction_service.get_credit_transactions.return_value = [
            _make_credit(100.0),
            _make_credit(1200.0, excluded=1),
        ]
        self.assertEqual(self.service.get_expenses("2025-01-01", "2025-01-31"), 100.0)

    def test_get_expenses_bank_income_not_counted(self):
        """Receitas bancárias (amount > 0) não entram nos gastos"""
        self.mock_transaction_service.get_bank_transactions.return_value = [
            _make_bank(1000.0),
            _make_bank(-200.0),
        ]
        self.mock_transaction_service.get_credit_transactions.return_value = []
        self.assertEqual(self.service.get_expenses("2025-01-01", "2025-01-31"), 200.0)

    # ── get_investment_value ──────────────────────────────────────────────────

    def test_get_investment_value(self):
        inv1, inv2 = MagicMock(), MagicMock()
        inv1.balance = 1000.0
        inv2.balance = 2500.0
        self.mock_transaction_repo.get_investments.return_value = [inv1, inv2]
        self.assertEqual(self.service.get_investment_value(), 3500.0)

    # ── get_category_expenses ─────────────────────────────────────────────────

    def test_get_category_expenses_basic(self):
        """Despesa bancária negativa aparece na categoria correta"""
        category = MagicMock()
        category.id = "cat1"
        category.description = "Alimentação"

        self.mock_transaction_service.get_bank_transactions.return_value = [
            _make_bank(-100.0, category_id="cat1"),
        ]
        self.mock_transaction_service.get_credit_transactions.return_value = []
        self.mock_category_repo.get_category_by_id.return_value = category

        result = self.service.get_category_expenses("2025-01-01", "2025-01-31")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "cat1")
        self.assertEqual(result[0]["total"], 100.0)

    def test_get_category_expenses_sorted_by_amount(self):
        """Resultado ordenado do maior para o menor gasto"""
        cat1, cat2 = MagicMock(), MagicMock()
        cat1.id, cat1.description = "cat1", "Pequena"
        cat2.id, cat2.description = "cat2", "Grande"

        self.mock_transaction_service.get_bank_transactions.return_value = [
            _make_bank(-50.0, category_id="cat1"),
            _make_bank(-200.0, category_id="cat2"),
        ]
        self.mock_transaction_service.get_credit_transactions.return_value = []
        self.mock_category_repo.get_category_by_id.side_effect = (
            lambda cid: cat1 if cid == "cat1" else cat2
        )

        result = self.service.get_category_expenses("2025-01-01", "2025-01-31")

        self.assertEqual(result[0]["description"], "Grande")
        self.assertEqual(result[1]["description"], "Pequena")

    def test_get_category_expenses_excludes_nonexistent_categories(self):
        """Categorias não encontradas no banco são ignoradas"""
        self.mock_transaction_service.get_bank_transactions.return_value = [
            _make_bank(-100.0, category_id="ghost"),
        ]
        self.mock_transaction_service.get_credit_transactions.return_value = []
        self.mock_category_repo.get_category_by_id.return_value = None

        self.assertEqual(self.service.get_category_expenses("2025-01-01", "2025-01-31"), [])

    def test_get_category_expenses_excludes_excluded_transactions(self):
        """Transações excluídas não aparecem nos gastos por categoria"""
        self.mock_transaction_service.get_bank_transactions.return_value = [
            _make_bank(-500.0, category_id="cat1", excluded=1),
        ]
        self.mock_transaction_service.get_credit_transactions.return_value = []

        self.assertEqual(self.service.get_category_expenses("2025-01-01", "2025-01-31"), [])

    # ── _is_expense edge case ─────────────────────────────────────────────────

    def test_is_expense_unknown_type_returns_false(self):
        """_is_expense retorna False para transaction_type desconhecido (linha 37)."""
        t = MagicMock()
        t.transaction_type = "other"
        t.amount = 100.0
        t.excluded = 0
        self.assertFalse(FinanceSummaryService._is_expense(t))

    # ── get_history_data ──────────────────────────────────────────────────────

    def test_get_history_data_returns_current_and_all(self):
        """get_history_data retorna entry do mês e histórico completo."""
        mock_entry = MagicMock()
        mock_all = [MagicMock(), MagicMock()]

        with patch("services.finance_summary_service.FinanceHistoryRepository") as MockRepo:
            mock_repo_inst = MockRepo.return_value
            mock_repo_inst.get_by_month.return_value = mock_entry
            mock_repo_inst.get_all.return_value = mock_all

            current, history = self.service.get_history_data("2026-03", "2025-04-01")

        mock_repo_inst.get_by_month.assert_called_once_with("2026-03")
        mock_repo_inst.get_all.assert_called_once()
        mock_repo_inst.close.assert_called_once()
        self.assertIs(current, mock_entry)
        self.assertIs(history, mock_all)

    def test_get_history_data_closes_repo_on_exception(self):
        """get_history_data garante close() mesmo quando ocorre erro."""
        with patch("services.finance_summary_service.FinanceHistoryRepository") as MockRepo:
            mock_repo_inst = MockRepo.return_value
            mock_repo_inst.get_by_month.side_effect = RuntimeError("db error")

            with self.assertRaises(RuntimeError):
                self.service.get_history_data("2026-03", "2025-04-01")

            mock_repo_inst.close.assert_called_once()

    # ── _resolve_root_category ────────────────────────────────────────────────

    def _make_cat(self, id_, parent_id=None):
        cat = MagicMock()
        cat.id = id_
        cat.description = f"Cat-{id_}"
        cat.parent_id = parent_id
        return cat

    def test_resolve_root_returns_self_when_no_parent(self):
        root = self._make_cat("01000000", parent_id=None)
        self.mock_category_repo.get_category_by_id.return_value = root
        result = self.service._resolve_root_category("01000000")
        self.assertEqual(result.id, "01000000")

    def test_resolve_root_walks_up_one_level(self):
        child = self._make_cat("01010000", parent_id="01000000")
        root = self._make_cat("01000000", parent_id=None)
        self.mock_category_repo.get_category_by_id.side_effect = (
            lambda cid: child if cid == "01010000" else root
        )
        result = self.service._resolve_root_category("01010000")
        self.assertEqual(result.id, "01000000")

    def test_resolve_root_walks_up_two_levels(self):
        leaf = self._make_cat("01010001", parent_id="01010000")
        mid = self._make_cat("01010000", parent_id="01000000")
        root = self._make_cat("01000000", parent_id=None)
        mapping = {"01010001": leaf, "01010000": mid, "01000000": root}
        self.mock_category_repo.get_category_by_id.side_effect = mapping.get
        result = self.service._resolve_root_category("01010001")
        self.assertEqual(result.id, "01000000")

    def test_resolve_root_returns_none_when_category_missing(self):
        self.mock_category_repo.get_category_by_id.return_value = None
        result = self.service._resolve_root_category("99999999")
        self.assertIsNone(result)

    def test_resolve_root_handles_self_parent(self):
        root = self._make_cat("01000000", parent_id="01000000")
        self.mock_category_repo.get_category_by_id.return_value = root
        result = self.service._resolve_root_category("01000000")
        self.assertEqual(result.id, "01000000")

    # ── get_category_expenses_by_parent ───────────────────────────────────────

    def test_get_category_expenses_by_parent_aggregates_children(self):
        """Gastos de categorias filhas são somados na categoria pai."""
        root = self._make_cat("01000000", parent_id=None)
        child1 = self._make_cat("01010000", parent_id="01000000")
        child2 = self._make_cat("01020000", parent_id="01000000")
        mapping = {"01000000": root, "01010000": child1, "01020000": child2}
        self.mock_category_repo.get_category_by_id.side_effect = mapping.get

        self.service.get_category_expenses = MagicMock(return_value=[
            {"id": "01010000", "description": "Cat-01010000", "total": 300.0},
            {"id": "01020000", "description": "Cat-01020000", "total": 200.0},
        ])

        result = self.service.get_category_expenses_by_parent("2026-01-01", "2026-02-01")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "01000000")
        self.assertEqual(result[0]["total"], 500.0)

    def test_get_category_expenses_by_parent_keeps_root_if_already_root(self):
        """Categorias raiz já são retornadas como estão."""
        root = self._make_cat("01000000", parent_id=None)
        self.mock_category_repo.get_category_by_id.return_value = root
        self.service.get_category_expenses = MagicMock(return_value=[
            {"id": "01000000", "description": "Cat-01000000", "total": 400.0},
        ])
        result = self.service.get_category_expenses_by_parent("2026-01-01", "2026-02-01")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["total"], 400.0)

    def test_get_category_expenses_by_parent_skips_missing_categories(self):
        """Categorias não encontradas no banco são ignoradas."""
        self.mock_category_repo.get_category_by_id.return_value = None
        self.service.get_category_expenses = MagicMock(return_value=[
            {"id": "ghost", "description": "Ghost", "total": 100.0},
        ])
        result = self.service.get_category_expenses_by_parent("2026-01-01", "2026-02-01")
        self.assertEqual(result, [])

    def test_get_category_expenses_by_parent_sorted_descending(self):
        root_a = self._make_cat("01000000", parent_id=None)
        root_b = self._make_cat("02000000", parent_id=None)
        mapping = {"01000000": root_a, "02000000": root_b}
        self.mock_category_repo.get_category_by_id.side_effect = mapping.get
        self.service.get_category_expenses = MagicMock(return_value=[
            {"id": "01000000", "description": "Pequena", "total": 100.0},
            {"id": "02000000", "description": "Grande", "total": 500.0},
        ])
        result = self.service.get_category_expenses_by_parent("2026-01-01", "2026-02-01")
        self.assertEqual(result[0]["id"], "02000000")
        self.assertEqual(result[1]["id"], "01000000")

    # ── get_full_summary ──────────────────────────────────────────────────────

    def test_get_full_summary(self):
        self.service.get_income = MagicMock(return_value=2000.0)
        self.service.get_expenses = MagicMock(return_value=1200.0)
        self.service.get_investment_value = MagicMock(return_value=5000.0)
        self.service.get_category_expenses = MagicMock(return_value=[
            {"id": "cat1", "description": "Alimentação", "total": 800.0}
        ])

        result = self.service.get_full_summary("2025-01-01", "2025-01-31")

        self.assertEqual(result["totals"]["income"], 2000.0)
        self.assertEqual(result["totals"]["expenses"], 1200.0)
        self.assertEqual(result["totals"]["balance"], 800.0)


if __name__ == "__main__":
    unittest.main()
