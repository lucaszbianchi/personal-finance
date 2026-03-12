"""Testes para CategoryService"""

import unittest
import unittest.mock
from unittest.mock import MagicMock, patch
from services.category_service import CategoryService


class TestCategoryService(unittest.TestCase):
    """Testes para a classe CategoryService"""

    def setUp(self):
        # Patch all repository dependencies
        with patch("services.category_service.CategoryRepository"), \
             patch("services.category_service.TransactionRepository"), \
             patch("services.category_service.SplitwiseRepository"):
            self.service = CategoryService()

        # Create mocks for all repositories
        self.mock_category_repo = MagicMock()
        self.mock_transaction_repo = MagicMock()
        self.mock_splitwise_repo = MagicMock()

        # Assign mocks to service
        self.service.category_repo = self.mock_category_repo
        self.service.transaction_repo = self.mock_transaction_repo
        self.service.splitwise_repo = self.mock_splitwise_repo

    def test_get_all_categories(self):
        """Testa obtenção de todas as categorias"""
        # Arrange
        expected_categories = [
            MagicMock(id="cat1", name="Alimentação"),
            MagicMock(id="cat2", name="Transporte"),
        ]
        self.mock_category_repo.get_all_categories.return_value = expected_categories

        # Act
        result = self.service.get_all_categories()

        # Assert
        self.mock_category_repo.get_all_categories.assert_called_once()
        self.assertEqual(result, expected_categories)
        self.assertEqual(len(result), 2)

    def test_create_category_success(self):
        """Testa criação de categoria quando não existe duplicata"""
        # Arrange
        category_name = "Nova Categoria"
        self.mock_category_repo.get_category_by_name.return_value = None

        # Act
        self.service.create_category(category_name)

        # Assert
        self.mock_category_repo.get_category_by_name.assert_called_once_with(category_name)
        self.mock_category_repo.create_category.assert_called_once_with(category_name, description_translated=None, parent_id=None, parent_description=None)

    def test_edit_category(self):
        """Testa edição de categoria"""
        # Arrange
        old_name = "Nome Antigo"
        new_name = "Nome Novo"

        # Act
        self.service.edit_category(old_name, new_name)

        # Assert
        self.mock_category_repo.update_category.assert_called_once_with(old_name, new_name)

    def test_create_category_already_exists(self):
        """Testa criação de categoria que já existe"""
        # Arrange
        category_name = "Categoria Existente"
        existing_category = MagicMock()
        self.mock_category_repo.get_category_by_name.return_value = existing_category

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.service.create_category(category_name)

        self.assertEqual(str(context.exception), f"Categoria '{category_name}' já existe")
        self.mock_category_repo.get_category_by_name.assert_called_once_with(category_name)
        self.mock_category_repo.create_category.assert_not_called()

    def test_create_category_returns_created_category(self):
        """Testa que create_category retorna a categoria criada"""
        # Arrange
        category_name = "Nova Categoria"
        created_category_id = "cat123"
        created_category = MagicMock()

        self.mock_category_repo.get_category_by_name.return_value = None
        self.mock_category_repo.create_category.return_value = created_category_id
        self.mock_category_repo.get_category_by_id.return_value = created_category

        # Act
        result = self.service.create_category(category_name)

        # Assert
        self.mock_category_repo.get_category_by_name.assert_called_once_with(category_name)
        self.mock_category_repo.create_category.assert_called_once_with(category_name, description_translated=None, parent_id=None, parent_description=None)
        self.mock_category_repo.get_category_by_id.assert_called_once_with(created_category_id)
        self.assertEqual(result, created_category)

    def test_get_category_by_id(self):
        """Testa obtenção de categoria por ID"""
        # Arrange
        category_id = "cat123"
        expected_category = MagicMock()
        self.mock_category_repo.get_category_by_id.return_value = expected_category

        # Act
        result = self.service.get_category_by_id(category_id)

        # Assert
        self.mock_category_repo.get_category_by_id.assert_called_once_with(category_id)
        self.assertEqual(result, expected_category)

    def test_unify_categories_success(self):
        """Testa unificação de categorias com sucesso"""
        # Arrange
        categories = ["cat1", "cat2", "cat3"]
        target = "target_cat"
        self.mock_category_repo.update_category.return_value = True

        # Act
        result = self.service.unify_categories(categories, target)

        # Assert
        self.assertTrue(result)
        # Deve atualizar apenas as categorias que não são o target
        expected_calls = [
            unittest.mock.call("cat1", target),
            unittest.mock.call("cat2", target),
            unittest.mock.call("cat3", target)
        ]
        self.mock_category_repo.update_category.assert_has_calls(expected_calls)

    def test_unify_categories_partial_failure(self):
        """Testa unificação com falha parcial"""
        # Arrange
        categories = ["cat1", "cat2"]
        target = "target_cat"
        # Primeira chamada sucesso, segunda falha
        self.mock_category_repo.update_category.side_effect = [True, False]

        # Act
        result = self.service.unify_categories(categories, target)

        # Assert
        self.assertFalse(result)  # Deve retornar False pois houve falha

    def test_unify_categories_with_target_in_list(self):
        """Testa unificação onde target está na lista de categorias"""
        # Arrange
        categories = ["cat1", "target_cat", "cat3"]
        target = "target_cat"
        self.mock_category_repo.update_category.return_value = True

        # Act
        result = self.service.unify_categories(categories, target)

        # Assert
        self.assertTrue(result)
        # Deve atualizar apenas as categorias que não são o target
        expected_calls = [
            unittest.mock.call("cat1", target),
            unittest.mock.call("cat3", target)
        ]
        self.mock_category_repo.update_category.assert_has_calls(expected_calls)

    def test_delete_category_success(self):
        """Testa exclusão de categoria quando não está em uso e sem filhos"""
        # Arrange
        category_name = "Categoria a Deletar"
        mock_category = MagicMock()
        mock_category.id = "cat123"

        self.mock_category_repo.get_category_by_name.return_value = mock_category
        self.mock_transaction_repo.category_in_use.return_value = False
        self.mock_splitwise_repo.category_in_use.return_value = False
        self.mock_category_repo.get_children_of.return_value = []
        self.mock_category_repo.delete_category.return_value = True

        # Act
        result = self.service.delete_category(category_name)

        # Assert
        self.mock_category_repo.get_category_by_name.assert_called_once_with(category_name)
        self.mock_category_repo.get_children_of.assert_called_once_with("cat123")
        self.mock_category_repo.clear_parent_refs.assert_called_once_with("cat123")
        self.mock_category_repo.delete_category.assert_called_once_with("cat123")
        self.assertTrue(result)

    def test_delete_category_not_found(self):
        """Testa tentativa de exclusão de categoria inexistente"""
        # Arrange
        category_name = "Categoria Inexistente"
        self.mock_category_repo.get_category_by_name.return_value = None

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.service.delete_category(category_name)

        self.assertEqual(str(context.exception), f"Categoria '{category_name}' não encontrada")
        self.mock_category_repo.get_category_by_name.assert_called_once_with(category_name)
        self.mock_transaction_repo.category_in_use.assert_not_called()
        self.mock_splitwise_repo.category_in_use.assert_not_called()
        self.mock_category_repo.delete_category.assert_not_called()

    def test_delete_category_in_use_by_transactions(self):
        """Testa tentativa de exclusão de categoria em uso por transações"""
        # Arrange
        category_name = "Categoria em Uso"
        mock_category = MagicMock()
        mock_category.id = "cat123"

        self.mock_category_repo.get_category_by_name.return_value = mock_category
        self.mock_transaction_repo.category_in_use.return_value = True
        self.mock_splitwise_repo.category_in_use.return_value = False

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.service.delete_category(category_name)

        expected_message = f"Categoria '{category_name}' está em uso e não pode ser deletada"
        self.assertEqual(str(context.exception), expected_message)
        self.mock_category_repo.get_category_by_name.assert_called_once_with(category_name)
        self.mock_transaction_repo.category_in_use.assert_called_once_with("cat123")
        self.mock_category_repo.delete_category.assert_not_called()

    def test_update_category_fields_success(self):
        """Testa atualização de campos diretos de categoria com sucesso"""
        # Arrange
        category_id = "cat123"
        self.mock_category_repo.update_category_fields.return_value = True

        # Act
        result = self.service.update_category_fields(
            category_id,
            description_translated="Translated",
            parent_id="01000000",
            parent_description="Root",
        )

        # Assert
        self.mock_category_repo.update_category_fields.assert_called_once_with(
            category_id, "Translated", "01000000", "Root"
        )
        self.assertTrue(result)

    def test_update_category_fields_not_found(self):
        """Testa atualização de campos quando categoria não existe"""
        # Arrange
        category_id = "nonexistent"
        self.mock_category_repo.update_category_fields.return_value = False

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.service.update_category_fields(category_id)

        self.assertIn(category_id, str(context.exception))
        self.mock_category_repo.update_category_fields.assert_called_once()

    def test_delete_category_in_use_by_splitwise(self):
        """Testa tentativa de exclusão de categoria em uso por Splitwise"""
        # Arrange
        category_name = "Categoria em Uso"
        mock_category = MagicMock()
        mock_category.id = "cat123"

        self.mock_category_repo.get_category_by_name.return_value = mock_category
        self.mock_transaction_repo.category_in_use.return_value = False
        self.mock_splitwise_repo.category_in_use.return_value = True

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.service.delete_category(category_name)

        expected_message = f"Categoria '{category_name}' está em uso e não pode ser deletada"
        self.assertEqual(str(context.exception), expected_message)
        self.mock_category_repo.get_category_by_name.assert_called_once_with(category_name)
        self.mock_transaction_repo.category_in_use.assert_called_once_with("cat123")
        self.mock_splitwise_repo.category_in_use.assert_called_once_with("cat123")
        self.mock_category_repo.delete_category.assert_not_called()

    def test_delete_parent_category_clears_children_refs(self):
        """Deletar categoria pai limpa parent_id/parent_description dos filhos"""
        # Arrange
        category_name = "Pai"
        mock_parent = MagicMock()
        mock_parent.id = "01000000"

        mock_child1 = MagicMock()
        mock_child1.id = "01010000"
        mock_child1.description = "Filho1"
        mock_child2 = MagicMock()
        mock_child2.id = "01020000"
        mock_child2.description = "Filho2"

        self.mock_category_repo.get_category_by_name.return_value = mock_parent
        self.mock_transaction_repo.category_in_use.return_value = False
        self.mock_splitwise_repo.category_in_use.return_value = False
        self.mock_category_repo.get_children_of.return_value = [mock_child1, mock_child2]
        self.mock_category_repo.delete_category.return_value = True

        # Act
        result = self.service.delete_category(category_name)

        # Assert
        self.mock_category_repo.get_children_of.assert_called_once_with("01000000")
        self.mock_category_repo.clear_parent_refs.assert_called_once_with("01000000")
        self.mock_category_repo.delete_category.assert_called_once_with("01000000")
        self.assertTrue(result)

    def test_delete_parent_blocked_when_child_in_use(self):
        """Deletar categoria pai é bloqueado se algum filho estiver em uso"""
        # Arrange
        category_name = "Pai"
        mock_parent = MagicMock()
        mock_parent.id = "01000000"

        mock_child = MagicMock()
        mock_child.id = "01010000"
        mock_child.description = "FilhoEmUso"

        self.mock_category_repo.get_category_by_name.return_value = mock_parent
        # O próprio pai não está em uso
        self.mock_transaction_repo.category_in_use.side_effect = lambda id_: id_ == "01010000"
        self.mock_splitwise_repo.category_in_use.return_value = False
        self.mock_category_repo.get_children_of.return_value = [mock_child]

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.service.delete_category(category_name)

        self.assertIn("FilhoEmUso", str(context.exception))
        self.mock_category_repo.clear_parent_refs.assert_not_called()
        self.mock_category_repo.delete_category.assert_not_called()

    def test_delete_category_without_children_always_calls_clear(self):
        """clear_parent_refs é sempre chamado, mesmo sem filhos — UPDATE com 0 linhas é no-op seguro"""
        # Arrange
        category_name = "SemFilhos"
        mock_category = MagicMock()
        mock_category.id = "01000000"

        self.mock_category_repo.get_category_by_name.return_value = mock_category
        self.mock_transaction_repo.category_in_use.return_value = False
        self.mock_splitwise_repo.category_in_use.return_value = False
        self.mock_category_repo.get_children_of.return_value = []
        self.mock_category_repo.delete_category.return_value = True

        # Act
        self.service.delete_category(category_name)

        # Assert
        self.mock_category_repo.clear_parent_refs.assert_called_once_with("01000000")
        self.mock_category_repo.delete_category.assert_called_once_with("01000000")


if __name__ == "__main__":
    unittest.main()
