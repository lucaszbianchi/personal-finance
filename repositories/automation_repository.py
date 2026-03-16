"""Repository for automation rules."""

import json
from repositories.base_repository import BaseRepository

_FIELD_TO_COL = {
    "description": "description",
    "category": "category_id",
    "amount": "amount",
}

_TABLE_MAP = {
    "bank": "bank_transactions",
    "credit": "credit_transactions",
}

_AMOUNT_OPERATORS = {"equals": "=", "gt": ">", "lt": "<"}


class AutomationRepository(BaseRepository):
    def __init__(self, db_path: str = "finance.db"):
        super().__init__(db_path)

    def _row_to_dict(self, row) -> dict:
        d = dict(row)
        d["conditions"] = json.loads(d["conditions"]) if d["conditions"] else []
        d["actions"] = json.loads(d["actions"]) if d["actions"] else []
        d["enabled"] = bool(d["enabled"])
        return d

    def get_all(self) -> list[dict]:
        cursor = self.execute_query(
            "SELECT * FROM automation_rules ORDER BY priority DESC, id ASC"
        )
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_by_id(self, rule_id: int) -> dict:
        cursor = self.execute_query(
            "SELECT * FROM automation_rules WHERE id = ?", (rule_id,)
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError(f"Automation rule {rule_id} not found")
        return self._row_to_dict(row)

    def create(self, data: dict) -> dict:
        self.execute_query(
            """
            INSERT INTO automation_rules (name, conditions, actions, priority, enabled)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data.get("name"),
                json.dumps(data["conditions"]),
                json.dumps(data["actions"]),
                data.get("priority", 0),
                1 if data.get("enabled", True) else 0,
            ),
        )
        cursor = self.execute_query("SELECT last_insert_rowid() AS id")
        row = cursor.fetchone()
        return self.get_by_id(row["id"])

    def update(self, rule_id: int, data: dict) -> dict:
        existing = self.get_by_id(rule_id)
        name = data.get("name", existing["name"])
        conditions = data.get("conditions", existing["conditions"])
        actions = data.get("actions", existing["actions"])
        priority = data.get("priority", existing["priority"])
        enabled = data.get("enabled", existing["enabled"])
        self.execute_query(
            """
            UPDATE automation_rules
            SET name = ?, conditions = ?, actions = ?, priority = ?, enabled = ?
            WHERE id = ?
            """,
            (
                name,
                json.dumps(conditions),
                json.dumps(actions),
                priority,
                1 if enabled else 0,
                rule_id,
            ),
        )
        return self.get_by_id(rule_id)

    def delete(self, rule_id: int) -> None:
        self.get_by_id(rule_id)  # raises ValueError if not found
        self.execute_query("DELETE FROM automation_rules WHERE id = ?", (rule_id,))

    # ── matching ──

    def find_matching_transactions(self, conditions: list) -> list[dict]:
        """Return bank and credit transactions that satisfy all conditions."""
        if not conditions:
            return []
        clauses, params = self._build_where(conditions)
        if not clauses:
            return []
        where_sql = " AND ".join(clauses)
        results = []
        for txn_type, table in _TABLE_MAP.items():
            cursor = self.execute_query(
                f"SELECT id, date, description, amount, category_id"
                f" FROM {table}"
                f" WHERE excluded = 0 AND {where_sql}"
                f" ORDER BY date DESC LIMIT 100",
                tuple(params),
            )
            for row in cursor.fetchall():
                d = dict(row)
                d["type"] = txn_type
                results.append(d)
        results.sort(key=lambda x: (x.get("date") or ""), reverse=True)
        return results[:100]

    def apply_actions_to_transactions(
        self, ids_by_type: dict, actions: list
    ) -> int:
        """Apply actions to transactions grouped by type. Returns total rows affected."""
        count = 0
        for txn_type, ids in ids_by_type.items():
            if not ids:
                continue
            table = _TABLE_MAP.get(txn_type)
            if not table:
                continue
            placeholders = ",".join("?" for _ in ids)
            for action in actions:
                atype = action.get("type")
                value = action.get("value")
                if atype == "set_category":
                    self.execute_query(
                        f"UPDATE {table} SET category_id = ? WHERE id IN ({placeholders})",
                        (value, *ids),
                    )
                elif atype == "exclude":
                    self.execute_query(
                        f"UPDATE {table} SET excluded = 1 WHERE id IN ({placeholders})",
                        tuple(ids),
                    )
                elif atype == "set_description":
                    self.execute_query(
                        f"UPDATE {table} SET description = ? WHERE id IN ({placeholders})",
                        (value, *ids),
                    )
            count += len(ids)
        return count

    @staticmethod
    def _build_where(conditions: list) -> tuple[list[str], list]:
        """Translate condition dicts into parameterized SQL WHERE clauses."""
        clauses: list[str] = []
        params: list = []
        for cond in conditions:
            field = cond.get("field", "")
            operator = cond.get("operator", "")
            value = cond.get("value", "")
            col = _FIELD_TO_COL.get(field)
            if not col:
                continue
            if field in ("description",):
                if operator == "equals":
                    clauses.append(f"LOWER({col}) = LOWER(?)")
                    params.append(value)
                elif operator == "contains":
                    clauses.append(f"LOWER({col}) LIKE LOWER(?)")
                    params.append(f"%{value}%")
                elif operator == "starts_with":
                    clauses.append(f"LOWER({col}) LIKE LOWER(?)")
                    params.append(f"{value}%")
                elif operator == "ends_with":
                    clauses.append(f"LOWER({col}) LIKE LOWER(?)")
                    params.append(f"%{value}")
            elif field == "category":
                if operator == "equals":
                    clauses.append(f"{col} = ?")
                    params.append(value)
            elif field == "amount":
                if operator in _AMOUNT_OPERATORS:
                    try:
                        clauses.append(f"{col} {_AMOUNT_OPERATORS[operator]} ?")
                        params.append(float(value))
                    except (ValueError, TypeError):
                        pass
        return clauses, params
