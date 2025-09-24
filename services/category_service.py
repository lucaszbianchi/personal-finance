from typing import Optional, List


class CategoryService:
    """
    Serviço para edição e unificação de categorias.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def get_all_categories(self) -> List[dict]:
        pass

    def edit_category(
        self,
        category_id: str,
        new_name: Optional[str] = None,
        new_type: Optional[str] = None,
    ):
        pass

    def unify_categories(self, source_ids: List[str], target_id: str):
        """
        Unifica múltiplas categorias em uma só (target_id).
        Atualiza todas as transações para referenciar a categoria alvo e remove as categorias antigas.
        """
        pass
