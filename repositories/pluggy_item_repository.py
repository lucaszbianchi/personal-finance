from repositories.base_repository import BaseRepository


class PluggyItemRepository(BaseRepository):
    """Repositório para gerenciar os itens Pluggy conectados pelo usuário."""

    def __init__(self, db_path: str = "finance.db"):
        super().__init__(db_path=db_path)

    def upsert_item(
        self,
        item_id: str,
        connector_name: str = None,
        status: str = None,
        role: str = "bank",
    ) -> None:
        query = """
            INSERT INTO pluggy_items (item_id, connector_name, status, role)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(item_id) DO UPDATE SET
                connector_name = excluded.connector_name,
                status = excluded.status,
                updated_at = datetime('now')
        """
        self.execute_query(query, (item_id, connector_name, status, role))

    def get_items_by_role(self, role: str) -> list:
        cursor = self.execute_query(
            "SELECT * FROM pluggy_items WHERE role = ? ORDER BY created_at DESC", (role,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def list_all(self) -> list:
        cursor = self.execute_query("SELECT * FROM pluggy_items ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    def delete(self, item_id: str) -> None:
        self.execute_query("DELETE FROM pluggy_items WHERE item_id = ?", (item_id,))
