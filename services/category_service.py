from typing import List
from repositories.category_repository import CategoryRepository
from repositories.transaction_repository import TransactionRepository
from repositories.splitwise_repository import SplitwiseRepository
from models.category import Category


class CategoryService:
    """
    Serviço para edição e unificação de categorias.
    """

    def __init__(self):
        self.category_repo = CategoryRepository()
        self.transaction_repo = TransactionRepository()
        self.splitwise_repo = SplitwiseRepository()

    def get_all_categories(self) -> List[dict]:
        """Retorna todas as categorias com suas respectivas contagens de transações."""
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
        success = True
        for category in categories:
            if category != target:
                success = success and self.category_repo.update_category(category, target)

        return success

    def create_category(
        self,
        name: str,
        description_translated: str = None,
        parent_id: str = None,
        parent_description: str = None,
    ) -> Category:
        """
        Cria uma nova categoria.
        Raises ValueError se a categoria já existe.
        """
        if self.category_repo.get_category_by_name(name):
            raise ValueError(f"Categoria '{name}' já existe")

        category_id = self.category_repo.create_category(name, description_translated=description_translated, parent_id=parent_id, parent_description=parent_description)
        return self.category_repo.get_category_by_id(category_id)

    def update_category_fields(
        self,
        category_id: str,
        description_translated: str = None,
        parent_id: str = None,
        parent_description: str = None,
    ) -> bool:
        """Atualiza campos diretos de uma categoria (sem renomear nem migrar transações)."""
        updated = self.category_repo.update_category_fields(category_id, description_translated, parent_id, parent_description)
        if not updated:
            raise ValueError(f"Categoria '{category_id}' não encontrada.")
        return True

    def delete_category(self, category_name: str) -> bool:
        """
        Deleta uma categoria específica.
        Raises ValueError se a categoria ou algum de seus filhos estiver em uso por transações.
        Filhos que não estiverem em uso têm suas referências ao pai limpas automaticamente.
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

        # Verificar se algum filho está em uso por transações.
        # Custo: 1 query (get_children_of) + 2 queries por filho (transaction + splitwise).
        # Aceitável dado que categorias têm cardinalidade baixa. Refatorar para JOIN
        # caso o número de filhos por categoria cresça significativamente.
        children = self.category_repo.get_children_of(category.id)
        children_in_use = [
            child.description
            for child in children
            if self.transaction_repo.category_in_use(child.id)
            or self.splitwise_repo.category_in_use(child.id)
        ]
        if children_in_use:
            raise ValueError(
                f"Categoria '{category_name}' não pode ser deletada: "
                f"os seguintes filhos ainda estão em uso: {', '.join(children_in_use)}"
            )

        # Limpar referências de filhos que não estão em uso
        self.category_repo.clear_parent_refs(category.id)

        return self.category_repo.delete_category(category.id)
