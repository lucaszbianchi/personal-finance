from datetime import datetime
from repositories.base_repository import BaseRepository


RATE_LIMITS = {
    "recent":     120,
    "non_recent": 4,
}


class RateLimitRepository(BaseRepository):
    """Repositório para controle de rate-limit de chamadas à API Pluggy."""

    def _current_year_month(self) -> str:
        return datetime.now().strftime("%Y-%m")

    def _ensure_record(self, call_type: str, year_month: str, item_id: str) -> None:
        """Cria o registro do mês/item se ainda não existir."""
        limit = RATE_LIMITS.get(call_type)
        if limit is None:
            raise ValueError(f"Tipo de chamada desconhecido: {call_type}")
        self.execute_query(
            """
            INSERT OR IGNORE INTO rate_limit_usage
                (item_id, call_type, year_month, count, limit_value)
            VALUES (?, ?, ?, 0, ?)
            """,
            (item_id, call_type, year_month, limit),
        )

    def increment(self, call_type: str, item_id: str) -> dict:
        """Incrementa o contador do mês atual para o item e retorna o estado atual."""
        year_month = self._current_year_month()
        self._ensure_record(call_type, year_month, item_id)
        self.execute_query(
            """
            UPDATE rate_limit_usage
            SET count = count + 1
            WHERE item_id = ? AND call_type = ? AND year_month = ?
            """,
            (item_id, call_type, year_month),
        )
        return self._get_record(call_type, year_month, item_id)

    def can_call(self, call_type: str, item_id: str) -> bool:
        """Retorna True se ainda há chamadas disponíveis neste mês para o item."""
        year_month = self._current_year_month()
        self._ensure_record(call_type, year_month, item_id)
        record = self._get_record(call_type, year_month, item_id)
        return record["count"] < record["limit_value"]

    def get_usage_summary(self, item_id: str | None = None) -> list:
        """Retorna registros do mês atual. Filtra por item_id se fornecido."""
        year_month = self._current_year_month()
        if item_id is not None:
            cursor = self.execute_query(
                "SELECT * FROM rate_limit_usage WHERE year_month = ? AND item_id = ?",
                (year_month, item_id),
            )
        else:
            cursor = self.execute_query(
                "SELECT * FROM rate_limit_usage WHERE year_month = ?", (year_month,)
            )
        rows = cursor.fetchall()
        return [
            {
                "item_id": row["item_id"],
                "call_type": row["call_type"],
                "year_month": row["year_month"],
                "count": row["count"],
                "limit_value": row["limit_value"],
                "remaining": row["limit_value"] - row["count"],
                "exceeded": row["count"] >= row["limit_value"],
            }
            for row in rows
        ]

    def _get_record(self, call_type: str, year_month: str, item_id: str) -> dict:
        cursor = self.execute_query(
            "SELECT * FROM rate_limit_usage WHERE item_id = ? AND call_type = ? AND year_month = ?",
            (item_id, call_type, year_month),
        )
        row = cursor.fetchone()
        return {
            "item_id": row["item_id"],
            "call_type": row["call_type"],
            "year_month": row["year_month"],
            "count": row["count"],
            "limit_value": row["limit_value"],
            "remaining": row["limit_value"] - row["count"],
            "exceeded": row["count"] >= row["limit_value"],
        }
