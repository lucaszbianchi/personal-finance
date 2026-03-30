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
                c.expense_type,
                COALESCE(tc.transaction_count, 0) as transaction_count,
                COALESCE(ec.expense_transaction_count, 0) as expense_transaction_count
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
            LEFT JOIN (
                SELECT
                    category_id,
                    COUNT(*) as expense_transaction_count
                FROM (
                    SELECT category_id FROM bank_transactions WHERE category_id IS NOT NULL AND amount < 0 AND excluded = 0
                    UNION ALL
                    SELECT category_id FROM credit_transactions WHERE category_id IS NOT NULL AND amount > 0 AND excluded = 0
                ) expense_transactions
                GROUP BY category_id
            ) ec ON c.id = ec.category_id
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
                "expense_type": row["expense_type"],
                "transaction_count": row["transaction_count"],
                "expense_transaction_count": row["expense_transaction_count"],
            }
            for row in cursor.fetchall()
        ]

    def get_category_by_id(self, category_id: int) -> Category:
        """Retorna uma categoria específica pelo ID."""
        query = "SELECT id, description, description_translated, parent_id, parent_description, expense_type FROM categories WHERE id = ?"
        cursor = self.execute_query(query, (category_id,))
        row = cursor.fetchone()
        if row:
            return Category(
                id_=row["id"],
                description=row["description"],
                description_translated=row["description_translated"],
                parent_id=row["parent_id"],
                parent_description=row["parent_description"],
                expense_type=row["expense_type"],
            )
        return None

    def get_category_by_name(self, name: str) -> Category:
        """Retorna uma categoria específica pela descrição."""
        query = "SELECT id, description, description_translated, parent_id, parent_description, expense_type FROM categories WHERE description = ?"
        cursor = self.execute_query(query, (name,))
        row = cursor.fetchone()
        if row:
            return Category(
                id_=row["id"],
                description=row["description"],
                description_translated=row["description_translated"],
                parent_id=row["parent_id"],
                parent_description=row["parent_description"],
                expense_type=row["expense_type"],
            )
        return None

    def update_category(self, old_name: str, new_name: str) -> str:
        """Atualiza a descrição de uma categoria e ajusta todas as transações que referenciam ela. Retorna o novo id da categoria.

        ATENÇÃO: esta operação não é atômica — cada execute_query faz commit individualmente.
        Se ocorrer erro após a criação da nova categoria e antes do DELETE final, o banco ficará
        em estado inconsistente. Refatorar para usar BEGIN/ROLLBACK explícito quando necessário.
        """
        cursor = self.execute_query(
            "SELECT id, parent_id, parent_description FROM categories WHERE description = ?", (old_name,)
        )
        old_cat = cursor.fetchone()
        if not old_cat:
            raise ValueError(f"Categoria '{old_name}' não encontrada.")
        old_id = old_cat["id"]
        old_parent_id = old_cat["parent_id"]
        old_parent_description = old_cat["parent_description"]

        cursor = self.execute_query(
            "SELECT id FROM categories WHERE description = ?", (new_name,)
        )
        new_cat_row = cursor.fetchone()
        if new_cat_row:
            new_id = new_cat_row["id"]
        else:
            # Preservar parent_id/parent_description ao criar a categoria renomeada.
            # execute_query já faz commit automaticamente — commit() explícito removido.
            new_id = self.create_category(new_name, parent_id=old_parent_id, parent_description=old_parent_description)

        bank_query = (
            "UPDATE bank_transactions SET category_id = ? WHERE category_id = ?"
        )
        self.execute_query(bank_query, (new_id, old_id))

        credit_query = (
            "UPDATE credit_transactions SET category_id = ? WHERE category_id = ?"
        )
        self.execute_query(credit_query, (new_id, old_id))

        # Propagar novo parent_id e novo nome para todos os filhos da categoria renomeada
        self.update_children_parent(old_id, new_id, new_name)

        self.execute_query("DELETE FROM categories WHERE id = ?", (old_id,))
        return new_id

    def _generate_category_id(self, parent_id: str | None) -> str:
        """Gera o próximo ID seguindo o padrão de 8 dígitos numéricos.

        Nível 1 (root, parent_id=None):  PP000000
        Nível 2 (parent termina 000000): PPCC0000
        Nível 3 (parent termina 0000):   PPCCGGGG
        """
        if parent_id is None:
            cursor = self.execute_query(
                "SELECT MAX(CAST(SUBSTR(id, 1, 2) AS INTEGER)) AS max_val "
                "FROM categories WHERE SUBSTR(id, 3) = '000000'"
            )
            max_pp = cursor.fetchone()["max_val"] or 0
            return f"{max_pp + 1:02d}000000"

        if len(parent_id) != 8 or not parent_id.isdigit():
            raise ValueError(f"parent_id inválido: '{parent_id}'")

        if parent_id[2:] == "000000":
            # Filho de root → nível 2
            pp = parent_id[:2]
            cursor = self.execute_query(
                "SELECT MAX(CAST(SUBSTR(id, 3, 2) AS INTEGER)) AS max_val "
                "FROM categories "
                "WHERE SUBSTR(id, 1, 2) = ? AND SUBSTR(id, 5) = '0000' AND SUBSTR(id, 3, 2) != '00'",
                (pp,),
            )
            max_cc = cursor.fetchone()["max_val"] or 0
            return f"{pp}{max_cc + 1:02d}0000"

        if parent_id[4:] == "0000":
            # Filho de nível 2 → nível 3
            ppcc = parent_id[:4]
            cursor = self.execute_query(
                "SELECT MAX(CAST(SUBSTR(id, 5) AS INTEGER)) AS max_val "
                "FROM categories "
                "WHERE SUBSTR(id, 1, 4) = ? AND CAST(SUBSTR(id, 5) AS INTEGER) > 0",
                (ppcc,),
            )
            max_gggg = cursor.fetchone()["max_val"] or 0
            return f"{ppcc}{max_gggg + 1:04d}"

        raise ValueError(
            f"parent_id '{parent_id}' é um ID de nível 3 — não é possível criar subfilhos (máximo 3 níveis)"
        )

    def create_category(
        self,
        name: str,
        id_: str = None,
        description_translated: str = None,
        parent_id: str = None,
        parent_description: str = None,
    ) -> str:
        """Cria uma nova categoria e retorna seu ID."""
        if id_ is None:
            id_ = self._generate_category_id(parent_id)
        self.execute_query(
            "INSERT INTO categories (id, description, description_translated, parent_id, parent_description) VALUES (?, ?, ?, ?, ?)",
            (id_, name, description_translated, parent_id, parent_description),
        )
        return id_

    def update_category_fields(
        self,
        category_id: str,
        description_translated: str = None,
        parent_id: str = None,
        parent_description: str = None,
        expense_type: str = None,
    ) -> bool:
        """Atualiza campos diretos de uma categoria (sem renomear nem migrar transações)."""
        cursor = self.execute_query(
            "UPDATE categories SET description_translated = ?, parent_id = ?, parent_description = ?, expense_type = ? WHERE id = ?",
            (description_translated, parent_id, parent_description, expense_type, category_id),
        )
        return cursor.rowcount > 0

    def _get_category_ids_by_expense_type(self, expense_type: str) -> set:
        cursor = self.execute_query(
            """
            SELECT c.id FROM categories c
            LEFT JOIN categories parent
                ON c.parent_id = parent.id AND c.parent_id != c.id
            WHERE c.expense_type = ?
               OR parent.expense_type = ?
            """,
            (expense_type, expense_type),
        )
        return {row["id"] for row in cursor.fetchall()}

    def get_necessary_category_ids(self) -> set:
        """Retorna IDs de todas as categorias cuja raiz tem expense_type='necessary'."""
        return self._get_category_ids_by_expense_type("necessary")

    def get_optional_category_ids(self) -> set:
        """Retorna IDs de todas as categorias cuja raiz tem expense_type='optional'."""
        return self._get_category_ids_by_expense_type("optional")

    def get_children_of(self, parent_id: str) -> List[Category]:
        """Retorna todas as categorias filhas de um dado parent_id."""
        cursor = self.execute_query(
            # AND id != ? exclui self-parent (grupos raiz onde parent_id = id)
            "SELECT id, description, description_translated, parent_id, parent_description, expense_type FROM categories WHERE parent_id = ? AND id != ?",
            (parent_id, parent_id),
        )
        return [
            Category(
                id_=row["id"],
                description=row["description"],
                description_translated=row["description_translated"],
                parent_id=row["parent_id"],
                parent_description=row["parent_description"],
                expense_type=row["expense_type"],
            )
            for row in cursor.fetchall()
        ]

    def clear_parent_refs(self, parent_id: str) -> int:
        """Limpa parent_id e parent_description de todos os filhos de um pai.
        Retorna o número de linhas afetadas. Com 0 filhos, é no-op seguro."""
        cursor = self.execute_query(
            # AND id != ? exclui self-parent (grupos raiz onde parent_id = id)
            "UPDATE categories SET parent_id = NULL, parent_description = NULL WHERE parent_id = ? AND id != ?",
            (parent_id, parent_id),
        )
        return cursor.rowcount

    def update_children_parent(self, old_parent_id: str, new_parent_id: str, new_parent_description: str) -> int:
        """Atualiza parent_id e parent_description de todos os filhos de old_parent_id.
        Retorna o número de linhas afetadas."""
        cursor = self.execute_query(
            # AND id != ? exclui self-parent (grupos raiz onde parent_id = id)
            "UPDATE categories SET parent_id = ?, parent_description = ? WHERE parent_id = ? AND id != ?",
            (new_parent_id, new_parent_description, old_parent_id, old_parent_id),
        )
        return cursor.rowcount

    def delete_category(self, category_id: str) -> bool:
        """Deleta uma categoria pelo seu ID."""
        cursor = self.execute_query(
            "DELETE FROM categories WHERE id = ?", (category_id,)
        )
        return cursor.rowcount > 0
