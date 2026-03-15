from repositories.base_repository import BaseRepository


class IncomeSourcesRepository(BaseRepository):
    """CRUD + upsert for income_sources table."""

    def upsert(self, data: dict) -> None:
        """INSERT OR REPLACE an income source record."""
        super().upsert("income_sources", "id", data, strategy="smart_merge")

    def get_all(self) -> list[dict]:
        """Return all income sources as dicts."""
        cursor = self.execute_query(
            "SELECT * FROM income_sources ORDER BY description"
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_by_id(self, id: str) -> dict:
        """Return a single income source by id. Raises ValueError if not found."""
        cursor = self.execute_query(
            "SELECT * FROM income_sources WHERE id = ?", (id,)
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError(f"IncomeSource '{id}' not found")
        return dict(row)

    def count_matching_transactions(
        self, merchant_name: str, amount_min=None, amount_max=None, day_of_month=None
    ) -> int:
        """Count bank transactions (amount > 0) matching the given rules.

        Raises ValueError if merchant_name is empty.
        """
        if not merchant_name:
            raise ValueError("merchant_name must not be empty")
        where, params = self._match_where_and_params(merchant_name, amount_min, amount_max, day_of_month)
        query = (
            f"SELECT COUNT(*) FROM bank_transactions"
            f" WHERE excluded = 0 AND amount > 0{where}"
        )
        cursor = self.execute_query(query, tuple(params))
        row = cursor.fetchone()
        return row[0] if row else 0

    def get_matching_transactions(
        self, merchant_name: str, amount_min=None, amount_max=None, day_of_month=None
    ) -> list[dict]:
        """Fetch bank transactions (amount > 0) matching the given rules, ordered by date DESC, limit 60.

        Raises ValueError if merchant_name is empty.
        """
        if not merchant_name:
            raise ValueError("merchant_name must not be empty")
        where, params = self._match_where_and_params(merchant_name, amount_min, amount_max, day_of_month)
        query = (
            f"SELECT id, description, amount, date"
            f" FROM bank_transactions WHERE excluded = 0 AND amount > 0{where}"
            f" ORDER BY date DESC LIMIT 60"
        )
        cursor = self.execute_query(query, tuple(params))
        return [dict(row) for row in cursor.fetchall()]

    def get_month_actual(
        self, month: str, merchant_name: str, amount_min=None, amount_max=None, day_of_month=None
    ) -> float:
        """Return the sum of matched bank income transactions for a specific YYYY-MM month."""
        where, params = self._match_where_and_params(merchant_name, amount_min, amount_max, day_of_month)
        params.append(f"{month}%")
        query = (
            f"SELECT COALESCE(SUM(amount), 0) FROM bank_transactions"
            f" WHERE excluded = 0 AND amount > 0{where} AND date LIKE ?"
        )
        cursor = self.execute_query(query, tuple(params))
        row = cursor.fetchone()
        return float(row[0]) if row else 0.0

    def get_monthly_actuals(
        self, year: int, merchant_name: str, amount_min=None, amount_max=None, day_of_month=None
    ) -> dict[str, float]:
        """Return {YYYY-MM: total} of matched bank income transactions for the given year."""
        where, params = self._match_where_and_params(merchant_name, amount_min, amount_max, day_of_month)
        params.append(str(year))
        query = (
            f"SELECT strftime('%Y-%m', date) AS month, SUM(amount) AS total"
            f" FROM bank_transactions"
            f" WHERE excluded = 0 AND amount > 0{where} AND strftime('%Y', date) = ?"
            f" GROUP BY month"
        )
        cursor = self.execute_query(query, tuple(params))
        return {row["month"]: row["total"] for row in cursor.fetchall()}

    @staticmethod
    def _match_where_and_params(
        merchant_name: str, amount_min, amount_max, day_of_month=None
    ) -> tuple[str, list]:
        """Build WHERE fragment and params for matching bank income transactions."""
        clause = " AND LOWER(description) LIKE LOWER(?)"
        params = [f"%{merchant_name}%"]
        if amount_min is not None:
            clause += " AND amount >= ?"
            params.append(amount_min)
        if amount_max is not None:
            clause += " AND amount <= ?"
            params.append(amount_max)
        if day_of_month is not None:
            day_from = max(1, day_of_month - 5)
            day_to = min(31, day_of_month + 5)
            clause += " AND CAST(strftime('%d', date) AS INTEGER) BETWEEN ? AND ?"
            params.extend([day_from, day_to])
        return clause, params

    def update(self, id: str, data: dict) -> None:
        """Update mutable fields of an income source. Raises ValueError if not found."""
        self.get_by_id(id)
        allowed = {
            "description", "amount", "frequency", "next_occurrence",
            "category_id", "merchant_name", "amount_min", "amount_max",
        }
        updates = {k: v for k, v in data.items() if k in allowed}
        if not updates:
            return
        set_clause = ", ".join(f"{col} = ?" for col in updates)
        values = list(updates.values()) + [id]
        self.execute_query(
            f"UPDATE income_sources SET {set_clause} WHERE id = ?",
            tuple(values),
        )

    def delete(self, id: str) -> None:
        """Delete an income source. Raises ValueError if not found."""
        self.get_by_id(id)
        self.execute_query(
            "DELETE FROM income_sources WHERE id = ?", (id,)
        )
