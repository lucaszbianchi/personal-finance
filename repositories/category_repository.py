from typing import List
from repositories.base_repository import BaseRepository
from models.category import Category


class CategoryRepository(BaseRepository):
    """Repositório para gerenciar operações de banco de dados relacionadas a categorias."""

    def get_all_categories(self) -> List[Category]:
        """Retorna todas as categorias únicas de todas as transações."""
        query = """
            SELECT id, name, types FROM categories ORDER BY name
        """
        return [
            Category(id_=row["id"], name=row["name"], types=row["types"])
            for row in self.execute_query(query)
        ]

    def get_category_by_id(self, category_id: int) -> Category:
        """Retorna uma categoria específica pelo ID."""
        query = "SELECT id, name, types FROM categories WHERE id = ?"
        result = self.execute_query(query, (category_id,))
        return Category(
            id_=result[0]["id"], name=result[0]["name"], types=result[0]["types"]
        )

    def update_category(self, old_name: str, new_name: str) -> bool:
        """Atualiza o nome de uma categoria e ajusta todas as transações que referenciam ela."""
        # 1️⃣ Busca o id da categoria antiga
        old_cat = self.execute_query(
            "SELECT id FROM categories WHERE name = ?", (old_name,)
        )
        if not old_cat:
            raise ValueError(f"Categoria '{old_name}' não encontrada.")
        old_id = old_cat[0]["id"]

        # 2️⃣ Verifica se a nova categoria já existe
        new_cat = self.execute_query(
            "SELECT id FROM categories WHERE name = ?", (new_name,)
        )
        if new_cat:
            new_id = new_cat[0]["id"]
        else:
            # Cria nova categoria se não existir
            self.execute_update("INSERT INTO categories (name) VALUES (?)", (new_name,))
            new_id = self.execute_query(
                "SELECT id FROM categories WHERE name = ?", (new_name,)
            )[0]["id"]

        # 3️⃣ Atualiza todas as transações (banco + crédito) que usavam a antiga categoria
        bank_query = (
            "UPDATE bank_transactions SET category_id = ? WHERE category_id = ?"
        )
        bank_result = self.execute_update(bank_query, (new_id, old_id))

        credit_query = (
            "UPDATE credit_transactions SET category_id = ? WHERE category_id = ?"
        )
        credit_result = self.execute_update(credit_query, (new_id, old_id))

        # 4️⃣ (opcional) Remove a categoria antiga se ela não tiver mais vínculos
        self.execute_update("DELETE FROM categories WHERE id = ?", (old_id,))

        return bank_result > 0 or credit_result > 0
