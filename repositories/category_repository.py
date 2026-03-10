import uuid
from typing import List
from repositories.base_repository import BaseRepository
from models.category import Category


class CategoryRepository(BaseRepository):
    """Repositório para gerenciar operações de banco de dados relacionadas a categorias."""

    def __init__(self, db_path: str = "finance.db"):
        super().__init__(db_path=db_path)

    def get_all_categories(self) -> List[dict]:
        """Retorna todas as categorias com suas respectivas contagens de transações."""
        query = """
            SELECT
                c.id,
                c.description,
                c.description_translated,
                c.parent_id,
                c.parent_description,
                COALESCE(tc.transaction_count, 0) as transaction_count
            FROM categories c
            LEFT JOIN (
                SELECT
                    category_id,
                    COUNT(*) as transaction_count
                FROM (
                    SELECT category_id FROM bank_transactions WHERE category_id IS NOT NULL
                    UNION ALL
                    SELECT category_id FROM credit_transactions WHERE category_id IS NOT NULL
                ) all_transactions
                GROUP BY category_id
            ) tc ON c.id = tc.category_id
            ORDER BY c.description
        """
        cursor = self.execute_query(query)
        return [
            {
                "id": row["id"],
                "description": row["description"],
                "description_translated": row["description_translated"],
                "parent_id": row["parent_id"],
                "parent_description": row["parent_description"],
                "transaction_count": row["transaction_count"],
            }
            for row in cursor.fetchall()
        ]

    def get_category_by_id(self, category_id: int) -> Category:
        """Retorna uma categoria específica pelo ID."""
        query = "SELECT id, description, description_translated, parent_id, parent_description FROM categories WHERE id = ?"
        cursor = self.execute_query(query, (category_id,))
        row = cursor.fetchone()
        if row:
            return Category(
                id_=row["id"],
                description=row["description"],
                description_translated=row["description_translated"],
                parent_id=row["parent_id"],
                parent_description=row["parent_description"],
            )
        return None

    def get_category_by_name(self, name: str) -> Category:
        """Retorna uma categoria específica pela descrição."""
        query = "SELECT id, description, description_translated, parent_id, parent_description FROM categories WHERE description = ?"
        cursor = self.execute_query(query, (name,))
        row = cursor.fetchone()
        if row:
            return Category(
                id_=row["id"],
                description=row["description"],
                description_translated=row["description_translated"],
                parent_id=row["parent_id"],
                parent_description=row["parent_description"],
            )
        return None

    def update_category(self, old_name: str, new_name: str) -> str:
        """Atualiza a descrição de uma categoria e ajusta todas as transações que referenciam ela. Retorna o novo id da categoria."""
        cursor = self.execute_query(
            "SELECT id FROM categories WHERE description = ?", (old_name,)
        )
        old_cat = cursor.fetchone()
        if not old_cat:
            raise ValueError(f"Categoria '{old_name}' não encontrada.")
        old_id = old_cat["id"]

        cursor = self.execute_query(
            "SELECT id FROM categories WHERE description = ?", (new_name,)
        )
        new_cat_row = cursor.fetchone()
        if new_cat_row:
            new_id = new_cat_row["id"]
        else:
            new_id = self.create_category(new_name)
            self._get_connection().commit()

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

        self.execute_query("DELETE FROM categories WHERE id = ?", (old_id,))
        return new_id

    def create_category(self, name: str, id_: str = None) -> str:
        """Cria uma nova categoria e retorna seu ID."""
        if id_ is None:
            id_ = str(uuid.uuid4())
        self.execute_query(
            "INSERT INTO categories (id, description) VALUES (?, ?)",
            (id_, name),
        )
        return id_

    def delete_category(self, category_id: str) -> bool:
        """Deleta uma categoria pelo seu ID."""
        cursor = self.execute_query(
            "DELETE FROM categories WHERE id = ?", (category_id,)
        )
        return cursor.rowcount > 0
