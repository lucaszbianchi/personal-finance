from repositories.base_repository import BaseRepository


class RecurrentExpensesRepository(BaseRepository):
    """CRUD + upsert for recurrent_expenses table."""

    def upsert_recurrence(self, data: dict) -> None:
        """INSERT OR REPLACE a recurrence record."""
        self.upsert("recurrent_expenses", "id", data, strategy="smart_merge")

    def get_all(self) -> list[dict]:
        """Return all recurrences as dicts."""
        cursor = self.execute_query(
            "SELECT * FROM recurrent_expenses ORDER BY description"
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_by_id(self, id: str) -> dict:
        """Return a single recurrence by id. Raises ValueError if not found."""
        cursor = self.execute_query(
            "SELECT * FROM recurrent_expenses WHERE id = ?", (id,)
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError(f"Recurrence '{id}' not found")
        return dict(row)

    def count_matching_transactions(self, merchant_name: str, amount_min=None, amount_max=None) -> int:
        """Count transactions (bank or credit) matching the given rules.

        Raises ValueError if merchant_name is empty.
        """
        if not merchant_name:
            raise ValueError("merchant_name must not be empty")
        where, half_params = self._match_where_and_params(merchant_name, amount_min, amount_max)
        query = (
            f"SELECT COUNT(*) FROM ("
            f"SELECT id FROM bank_transactions WHERE excluded = 0 AND amount < 0{where}"
            f" UNION ALL"
            f" SELECT id FROM credit_transactions WHERE excluded = 0 AND amount > 0{where}"
            f")"
        )
        cursor = self.execute_query(query, tuple(half_params + half_params))
        row = cursor.fetchone()
        return row[0] if row else 0

    def get_matching_transactions(self, merchant_name: str, amount_min=None, amount_max=None) -> list[dict]:
        """Fetch transactions (bank or credit) matching the given rules, ordered by date DESC, limit 60.

        Raises ValueError if merchant_name is empty.
        """
        if not merchant_name:
            raise ValueError("merchant_name must not be empty")
        where, half_params = self._match_where_and_params(merchant_name, amount_min, amount_max)
        query = (
            f"SELECT id, description, ABS(amount) AS amount, date"
            f" FROM bank_transactions WHERE excluded = 0 AND amount < 0{where}"
            f" UNION ALL"
            f" SELECT id, description, ABS(amount) AS amount, date"
            f" FROM credit_transactions WHERE excluded = 0 AND amount > 0{where}"
            f" ORDER BY date DESC LIMIT 60"
        )
        cursor = self.execute_query(query, tuple(half_params + half_params))
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def _match_where_and_params(merchant_name: str, amount_min, amount_max) -> tuple[str, list]:
        """Build the shared WHERE fragment and params for one half of the UNION."""
        clause = " AND LOWER(description) LIKE LOWER(?)"
        params = [f"%{merchant_name}%"]
        if amount_min is not None:
            clause += " AND ABS(amount) >= ?"
            params.append(amount_min)
        if amount_max is not None:
            clause += " AND ABS(amount) <= ?"
            params.append(amount_max)
        return clause, params

    def update(self, id: str, data: dict) -> None:
        """Update mutable fields of a recurrence. Raises ValueError if not found."""
        self.get_by_id(id)
        allowed = {
            "description", "amount", "frequency", "next_occurrence",
            "category_id", "merchant_name", "is_unavoidable",
            "amount_min", "amount_max",
        }
        updates = {k: v for k, v in data.items() if k in allowed}
        if not updates:
            return
        set_clause = ", ".join(f"{col} = ?" for col in updates)
        values = list(updates.values()) + [id]
        self.execute_query(
            f"UPDATE recurrent_expenses SET {set_clause} WHERE id = ?",
            tuple(values),
        )

    def delete(self, id: str) -> None:
        """Delete a recurrence. Raises ValueError if not found."""
        self.get_by_id(id)
        self.execute_query(
            "DELETE FROM recurrent_expenses WHERE id = ?", (id,)
        )
