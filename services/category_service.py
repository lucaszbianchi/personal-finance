from typing import List
from repositories.category_repository import CategoryRepository
from repositories.transaction_repository import TransactionRepository
from repositories.splitwise_repository import SplitwiseRepository
from models.category import Category


class CategoryService:
    """
    Serviço para edição e unificação de categorias.
    """

    VALID_TYPES = {"essencial", "opcional", "fixa", "compartilhada"}

    def __init__(self):
        self.category_repo = CategoryRepository()
        self.transaction_repo = TransactionRepository()
        self.splitwise_repo = SplitwiseRepository()

    def get_all_categories(self) -> List[Category]:
        """Retorna todas as categorias."""
        return self.category_repo.get_all_categories()

    def get_category_by_id(self, category_id: str) -> Category:
        """Retorna uma categoria pelo seu ID."""
        return self.category_repo.get_category_by_id(category_id)

    def edit_category(self, old_name: str, new_name: str) -> bool:
        """
        Edita o nome de uma categoria em todas as transações.
        Retorna True se a atualização foi bem-sucedida, False caso contrário.
        """
        return self.category_repo.update_category(old_name, new_name)

    def unify_categories(self, categories: List[str], target: str) -> bool:
        """
        Unifica múltiplas categorias em uma só (target_id).
        Atualiza todas as transações para referenciar a categoria alvo e remove as categorias antigas.
        """
        success = False
        for category in categories:
            if category != target:
                success = (
                    self.category_repo.update_category(category, target) and success
                )

        return success

    def create_category(self, name: str, types: List[str] | None = None) -> Category:
        """
        Cria uma nova categoria.
        Raises ValueError se a categoria já existe ou se os tipos são inválidos.
        """
        if self.category_repo.get_category_by_name(name):
            raise ValueError(f"Categoria '{name}' já existe")

        if types:
            invalid_types = set(types) - self.VALID_TYPES
            if invalid_types:
                raise ValueError(
                    f"Tipos inválidos: {invalid_types}. Use apenas: {self.VALID_TYPES}"
                )

        category_id = self.category_repo.create_category(name, types)
        return self.category_repo.get_category_by_id(category_id)

    def delete_category(self, category_name: str) -> bool:
        """
        Deleta uma categoria específica.
        Raises ValueError se a categoria estiver em uso.
        """
        category = self.category_repo.get_category_by_name(category_name)
        if not category:
            raise ValueError(f"Categoria '{category_name}' não encontrada")

        if self.transaction_repo.category_in_use(
            category.id
        ) or self.splitwise_repo.category_in_use(category.id):
            raise ValueError(
                f"Categoria '{category_name}' está em uso e não pode ser deletada"
            )

        return self.category_repo.delete_category(category.id)
