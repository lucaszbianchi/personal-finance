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

    def _ensure_record(self, call_type: str, year_month: str) -> None:
        """Cria o registro do mês se ainda não existir."""
        limit = RATE_LIMITS.get(call_type)
        if limit is None:
            raise ValueError(f"Tipo de chamada desconhecido: {call_type}")
        self.execute_query(
            """
            INSERT OR IGNORE INTO rate_limit_usage
                (call_type, year_month, count, limit_value)
            VALUES (?, ?, 0, ?)
            """,
            (call_type, year_month, limit),
        )

    def increment(self, call_type: str) -> dict:
        """Incrementa o contador do mês atual e retorna o estado atual."""
        year_month = self._current_year_month()
        self._ensure_record(call_type, year_month)
        self.execute_query(
            """
            UPDATE rate_limit_usage
            SET count = count + 1
            WHERE call_type = ? AND year_month = ?
            """,
            (call_type, year_month),
        )
        return self._get_record(call_type, year_month)

    def can_call(self, call_type: str) -> bool:
        """Retorna True se ainda há chamadas disponíveis neste mês."""
        year_month = self._current_year_month()
        self._ensure_record(call_type, year_month)
        record = self._get_record(call_type, year_month)
        return record["count"] < record["limit_value"]

    def get_usage_summary(self) -> list:
        """Retorna todos os registros do mês atual."""
        year_month = self._current_year_month()
        cursor = self.execute_query(
            "SELECT * FROM rate_limit_usage WHERE year_month = ?", (year_month,)
        )
        rows = cursor.fetchall()
        return [
            {
                "call_type": row["call_type"],
                "year_month": row["year_month"],
                "count": row["count"],
                "limit_value": row["limit_value"],
                "remaining": row["limit_value"] - row["count"],
                "exceeded": row["count"] >= row["limit_value"],
            }
            for row in rows
        ]

    def _get_record(self, call_type: str, year_month: str) -> dict:
        cursor = self.execute_query(
            "SELECT * FROM rate_limit_usage WHERE call_type = ? AND year_month = ?",
            (call_type, year_month),
        )
        row = cursor.fetchone()
        return {
            "call_type": row["call_type"],
            "year_month": row["year_month"],
            "count": row["count"],
            "limit_value": row["limit_value"],
            "remaining": row["limit_value"] - row["count"],
            "exceeded": row["count"] >= row["limit_value"],
        }
