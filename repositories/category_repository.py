import json
import uuid
from typing import List
from repositories.base_repository import BaseRepository
from models.category import Category


class CategoryRepository(BaseRepository):
    """Repositório para gerenciar operações de banco de dados relacionadas a categorias."""

    def __init__(self, db_path: str = "finance.db"):
        super().__init__(db_path=db_path)

    def get_all_categories(self) -> List[Category]:
        """Retorna todas as categorias únicas de todas as transações."""
        query = """
            SELECT id, name FROM categories ORDER BY name
        """
        cursor = self.execute_query(query)
        return [
            Category(
                id_=row["id"],
                name=row["name"],
                types=[]
            )
            for row in cursor.fetchall()
        ]

    def get_category_by_id(self, category_id: int) -> Category:
        """Retorna uma categoria específica pelo ID."""
        query = "SELECT id, name FROM categories WHERE id = ?"
        cursor = self.execute_query(query, (category_id,))
        row = cursor.fetchone()
        if row:
            return Category(id_=row["id"], name=row["name"], types=[])
        return None

    def get_category_by_name(self, name: str) -> Category:
        """Retorna uma categoria específica pelo nome."""
        query = "SELECT id, name FROM categories WHERE name = ?"
        cursor = self.execute_query(query, (name,))
        row = cursor.fetchone()
        if row:
            return Category(id_=row["id"], name=row["name"], types=[])
        return None

    def update_category(self, old_name: str, new_name: str) -> str:
        """Atualiza o nome de uma categoria e ajusta todas as transações que referenciam ela. Retorna o novo id da categoria."""
        # 1️⃣ Busca o id da categoria antiga
        cursor = self.execute_query(
            "SELECT id FROM categories WHERE name = ?", (old_name,)
        )
        old_cat = cursor.fetchone()
        if not old_cat:
            raise ValueError(f"Categoria '{old_name}' não encontrada.")
        old_id = old_cat["id"]

        # 2️⃣ Verifica se a nova categoria já existe
        cursor = self.execute_query(
            "SELECT id FROM categories WHERE name = ?", (new_name,)
        )
        new_cat_row = cursor.fetchone()
        if new_cat_row:
            new_id = new_cat_row["id"]
        else:
            # Cria nova categoria se não existir
            new_id = self.create_category(new_name)
            # Commit explícito para garantir persistência antes de remover a antiga
            self._get_connection().commit()

        # 3️⃣ Atualiza todas as transações (banco + crédito + splitwise) que usavam a antiga categoria
        bank_query = (
            "UPDATE bank_transactions SET category_id = ? WHERE category_id = ?"
        )
        self.execute_query(bank_query, (new_id, old_id))

        credit_query = (
            "UPDATE credit_transactions SET category_id = ? WHERE category_id = ?"
        )
        self.execute_query(credit_query, (new_id, old_id))

        splitwise_query = "UPDATE splitwise SET category_id = ? WHERE category_id = ?"
        self.execute_query(splitwise_query, (new_id, old_id))

        # 4️⃣ (opcional) Remove a categoria antiga se ela não tiver mais vínculos
        self.execute_query("DELETE FROM categories WHERE id = ?", (old_id,))
        return new_id

    def create_category(
        self, name: str, types: List[str] | None = None, id_: str = None
    ) -> str:
        """Cria uma nova categoria e retorna seu ID."""
        if id_ is None:
            id_ = str(uuid.uuid4())
        self.execute_query(
            "INSERT INTO categories (id, name) VALUES (?, ?)",
            (id_, name),
        )
        return id_

    def delete_category(self, category_id: str) -> bool:
        """Deleta uma categoria pelo seu ID."""
        cursor = self.execute_query(
            "DELETE FROM categories WHERE id = ?", (category_id,)
        )
        return cursor.rowcount > 0


if __name__ == "__main__":
    repo = CategoryRepository()
    category = Category(id_="", name="Lazer", types=["opcional"])
