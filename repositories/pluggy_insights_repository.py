import json
from repositories.base_repository import BaseRepository


class PluggyInsightsRepository(BaseRepository):
    def __init__(self, db_path: str = "finance.db"):
        super().__init__(db_path=db_path)

    def upsert_book_summary(
        self, item_id: str, month: str, bank_account: dict, credit_card: dict, fetched_at: str
    ) -> None:
        self.execute_query(
            """
            INSERT INTO pluggy_book_summary (item_id, month, bank_account, credit_card, fetched_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(item_id, month) DO UPDATE SET
                bank_account = excluded.bank_account,
                credit_card  = excluded.credit_card,
                fetched_at   = excluded.fetched_at
            """,
            (item_id, month, json.dumps(bank_account), json.dumps(credit_card), fetched_at),
        )

    def get_book_summary(self, item_id: str, month: str) -> dict | None:
        cursor = self.execute_query(
            "SELECT bank_account, credit_card, fetched_at FROM pluggy_book_summary WHERE item_id = ? AND month = ?",
            (item_id, month),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "bank_account": json.loads(row[0]) if row[0] else {},
            "credit_card": json.loads(row[1]) if row[1] else {},
            "fetched_at": row[2],
        }
