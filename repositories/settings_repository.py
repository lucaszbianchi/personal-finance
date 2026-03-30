from typing import Any, Optional
import json
from repositories.base_repository import BaseRepository, DEFAULT_DB_PATH


class SettingsRepository(BaseRepository):
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        super().__init__(db_path=db_path)

    def set_value(self, key: str, value: Any) -> None:
        """Salva ou atualiza um valor nas configurações"""
        value_json = json.dumps(value)
        self.execute_query(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value_json),
        )

    def get_value(self, key: str) -> Optional[Any]:
        """Retorna um valor das configurações"""
        cursor = self.execute_query("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None

    def delete_value(self, key: str) -> None:
        """Remove um valor das configurações"""
        self.execute_query("DELETE FROM settings WHERE key = ?", (key,))

    def get_all(self) -> dict[str, Any]:
        """Retorna todas as configurações"""
        cursor = self.execute_query("SELECT key, value FROM settings")
        return {row[0]: json.loads(row[1]) for row in cursor.fetchall()}
