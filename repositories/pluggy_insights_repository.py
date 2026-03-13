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

    def upsert_book_category(
        self,
        item_id: str,
        month: str,
        category: str,
        transaction_type: str,
        account_subtype: str,
        periods: dict,
        fetched_at: str,
    ) -> None:
        def _get(p, key):
            return periods.get(p, {}).get(key)

        self.execute_query(
            """
            INSERT INTO pluggy_book_categories (
                item_id, month, category, transaction_type, account_subtype,
                m1_avg, m1_total, m1_min, m1_max,
                m2_avg, m2_total, m2_min, m2_max,
                m3_avg, m3_total, m3_min, m3_max,
                m6_avg, m6_total, m6_min, m6_max,
                m12_avg, m12_total, m12_min, m12_max,
                fetched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(item_id, month, category, transaction_type, account_subtype) DO UPDATE SET
                m1_avg = excluded.m1_avg, m1_total = excluded.m1_total,
                m1_min = excluded.m1_min, m1_max = excluded.m1_max,
                m2_avg = excluded.m2_avg, m2_total = excluded.m2_total,
                m2_min = excluded.m2_min, m2_max = excluded.m2_max,
                m3_avg = excluded.m3_avg, m3_total = excluded.m3_total,
                m3_min = excluded.m3_min, m3_max = excluded.m3_max,
                m6_avg = excluded.m6_avg, m6_total = excluded.m6_total,
                m6_min = excluded.m6_min, m6_max = excluded.m6_max,
                m12_avg = excluded.m12_avg, m12_total = excluded.m12_total,
                m12_min = excluded.m12_min, m12_max = excluded.m12_max,
                fetched_at = excluded.fetched_at
            """,
            (
                item_id, month, category, transaction_type, account_subtype,
                _get("M1", "avg"), _get("M1", "total"), _get("M1", "min"), _get("M1", "max"),
                _get("M2", "avg"), _get("M2", "total"), _get("M2", "min"), _get("M2", "max"),
                _get("M3", "avg"), _get("M3", "total"), _get("M3", "min"), _get("M3", "max"),
                _get("M6", "avg"), _get("M6", "total"), _get("M6", "min"), _get("M6", "max"),
                _get("M12", "avg"), _get("M12", "total"), _get("M12", "min"), _get("M12", "max"),
                fetched_at,
            ),
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

    def get_book_categories(self, item_id: str, month: str) -> list:
        cursor = self.execute_query(
            """
            SELECT category, transaction_type, account_subtype,
                   m1_avg, m1_total, m1_min, m1_max,
                   m2_avg, m2_total, m2_min, m2_max,
                   m3_avg, m3_total, m3_min, m3_max,
                   m6_avg, m6_total, m6_min, m6_max,
                   m12_avg, m12_total, m12_min, m12_max
            FROM pluggy_book_categories
            WHERE item_id = ? AND month = ?
            ORDER BY category, transaction_type
            """,
            (item_id, month),
        )
        rows = cursor.fetchall()

        def _period(avg, total, min_, max_):
            return {"avg": avg, "total": total, "min": min_, "max": max_}

        return [
            {
                "category": r[0],
                "transaction_type": r[1],
                "account_subtype": r[2],
                "M1": _period(r[3], r[4], r[5], r[6]),
                "M2": _period(r[7], r[8], r[9], r[10]),
                "M3": _period(r[11], r[12], r[13], r[14]),
                "M6": _period(r[15], r[16], r[17], r[18]),
                "M12": _period(r[19], r[20], r[21], r[22]),
            }
            for r in rows
        ]
