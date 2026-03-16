"""Repository for category visualization queries (expense history & distribution)."""

from repositories.base_repository import BaseRepository


class CategoryVisualizationRepository(BaseRepository):
    def __init__(self, db_path: str = "finance.db"):
        super().__init__(db_path)

    def get_expenses_by_month_and_category(self, start_date: str) -> list[dict]:
        """Returns (month, category_id, category_name, total) rows from start_date onward."""
        query = """
            SELECT
                strftime('%Y-%m', t.date)                              AS month,
                t.category_id,
                COALESCE(c.description_translated, c.description)      AS category_name,
                SUM(ABS(t.amount))                                     AS total
            FROM bank_transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.excluded = 0
              AND t.amount < 0
              AND t.category_id IS NOT NULL
              AND t.date >= ?
            GROUP BY strftime('%Y-%m', t.date), t.category_id

            UNION ALL

            SELECT
                strftime('%Y-%m', t.date)                              AS month,
                t.category_id,
                COALESCE(c.description_translated, c.description)      AS category_name,
                SUM(t.amount)                                          AS total
            FROM credit_transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.excluded = 0
              AND t.amount > 0
              AND t.category_id IS NOT NULL
              AND t.date >= ?
            GROUP BY strftime('%Y-%m', t.date), t.category_id
        """
        cursor = self.execute_query(query, (start_date, start_date))
        return [dict(row) for row in cursor.fetchall()]

    def get_expenses_by_category(self, month: str) -> list[dict]:
        """Returns (category_id, category_name, parent_id, parent_name, total) for a month."""
        query = """
            SELECT
                t.category_id,
                COALESCE(c.description_translated, c.description)      AS category_name,
                c.parent_id,
                COALESCE(p.description_translated, p.description)      AS parent_name,
                SUM(ABS(t.amount))                                     AS total
            FROM bank_transactions t
            JOIN categories c ON t.category_id = c.id
            LEFT JOIN categories p ON c.parent_id = p.id AND c.parent_id != c.id
            WHERE t.excluded = 0
              AND t.amount < 0
              AND t.category_id IS NOT NULL
              AND strftime('%Y-%m', t.date) = ?
            GROUP BY t.category_id

            UNION ALL

            SELECT
                t.category_id,
                COALESCE(c.description_translated, c.description)      AS category_name,
                c.parent_id,
                COALESCE(p.description_translated, p.description)      AS parent_name,
                SUM(t.amount)                                          AS total
            FROM credit_transactions t
            JOIN categories c ON t.category_id = c.id
            LEFT JOIN categories p ON c.parent_id = p.id AND c.parent_id != c.id
            WHERE t.excluded = 0
              AND t.amount > 0
              AND t.category_id IS NOT NULL
              AND strftime('%Y-%m', t.date) = ?
            GROUP BY t.category_id
        """
        cursor = self.execute_query(query, (month, month))
        return [dict(row) for row in cursor.fetchall()]
