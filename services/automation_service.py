"""Service for automation rules."""

from repositories.automation_repository import AutomationRepository

VALID_ACTION_TYPES = {"set_category", "exclude", "set_description"}

_FIELD_VALID_OPERATORS: dict[str, set[str]] = {
    "description": {"equals", "contains", "starts_with", "ends_with"},
    "category":    {"equals"},
    "amount":      {"equals", "gt", "lt"},
}


class AutomationService:
    def __init__(self):
        self.automation_repo = AutomationRepository()

    def list_rules(self) -> list[dict]:
        return self.automation_repo.get_all()

    def get_rule(self, rule_id: int) -> dict:
        return self.automation_repo.get_by_id(rule_id)

    def create_rule(self, payload: dict) -> dict:
        self._validate(payload)
        return self.automation_repo.create(payload)

    def update_rule(self, rule_id: int, payload: dict) -> dict:
        if "conditions" in payload or "actions" in payload:
            merged = dict(self.automation_repo.get_by_id(rule_id))
            merged.update(payload)
            self._validate(merged)
        return self.automation_repo.update(rule_id, payload)

    def delete_rule(self, rule_id: int) -> None:
        self.automation_repo.delete(rule_id)

    def toggle_enabled(self, rule_id: int, enabled: bool) -> dict:
        return self.automation_repo.update(rule_id, {"enabled": enabled})

    def preview_matches(self, conditions: list) -> list[dict]:
        return self.automation_repo.find_matching_transactions(conditions)

    def apply_rule(self, rule_id: int) -> dict:
        rule = self.automation_repo.get_by_id(rule_id)
        matches = self.automation_repo.find_matching_transactions(rule["conditions"])
        ids_by_type: dict[str, list] = {"bank": [], "credit": []}
        for m in matches:
            ids_by_type[m["type"]].append(m["id"])
        applied = self.automation_repo.apply_actions_to_transactions(
            ids_by_type, rule["actions"]
        )
        return {"applied": applied, "matches_found": len(matches)}

    @staticmethod
    def _validate(payload: dict) -> None:
        conditions = payload.get("conditions", [])
        if not conditions:
            raise ValueError("At least one condition is required")
        for c in conditions:
            if "field" not in c or "operator" not in c or "value" not in c:
                raise ValueError("Each condition must have field, operator, and value")
            valid_ops = _FIELD_VALID_OPERATORS.get(c["field"])
            if valid_ops is None:
                raise ValueError(f"Invalid condition field: {c['field']}")
            if c["operator"] not in valid_ops:
                raise ValueError(
                    f"Operator '{c['operator']}' is not valid for field '{c['field']}'"
                )

        actions = payload.get("actions", [])
        if not actions:
            raise ValueError("At least one action is required")
        for a in actions:
            if "type" not in a:
                raise ValueError("Each action must have a type")
            if a["type"] not in VALID_ACTION_TYPES:
                raise ValueError(f"Invalid action type: {a['type']}")
