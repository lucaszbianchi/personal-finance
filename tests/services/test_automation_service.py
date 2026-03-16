"""Tests for AutomationService."""

import unittest
from unittest.mock import MagicMock, patch


class TestAutomationService(unittest.TestCase):
    def setUp(self):
        with patch("services.automation_service.AutomationRepository"):
            from services.automation_service import AutomationService
            self.svc = AutomationService()
        self.repo = MagicMock()
        self.svc.automation_repo = self.repo

    def _make_payload(self, **kwargs):
        base = {
            "name": "Rule",
            "conditions": [{"field": "description", "operator": "equals", "value": "x"}],
            "actions": [{"type": "set_category", "value": "cat-1"}],
        }
        base.update(kwargs)
        return base

    def _make_rule(self, rule_id=1, **kwargs):
        base = {
            "id": rule_id,
            "name": "Rule",
            "conditions": [{"field": "description", "operator": "equals", "value": "x"}],
            "actions": [{"type": "set_category", "value": "cat-1"}],
            "priority": 0,
            "enabled": True,
        }
        base.update(kwargs)
        return base

    # ── list_rules ──

    def test_list_rules_delegates_to_repo(self):
        self.repo.get_all.return_value = []
        result = self.svc.list_rules()
        self.repo.get_all.assert_called_once()
        self.assertEqual(result, [])

    def test_list_rules_returns_repo_data(self):
        rules = [self._make_rule(1), self._make_rule(2)]
        self.repo.get_all.return_value = rules
        self.assertEqual(self.svc.list_rules(), rules)

    # ── get_rule ──

    def test_get_rule_delegates_to_repo(self):
        rule = self._make_rule()
        self.repo.get_by_id.return_value = rule
        result = self.svc.get_rule(1)
        self.repo.get_by_id.assert_called_once_with(1)
        self.assertEqual(result, rule)

    def test_get_rule_propagates_value_error(self):
        self.repo.get_by_id.side_effect = ValueError("not found")
        with self.assertRaises(ValueError):
            self.svc.get_rule(99)

    # ── create_rule ──

    def test_create_rule_valid_calls_repo(self):
        payload = self._make_payload()
        self.repo.create.return_value = self._make_rule()
        self.svc.create_rule(payload)
        self.repo.create.assert_called_once_with(payload)

    def test_create_rule_empty_conditions_raises(self):
        payload = self._make_payload(conditions=[])
        with self.assertRaises(ValueError, msg="At least one condition is required"):
            self.svc.create_rule(payload)

    def test_create_rule_missing_field_in_condition_raises(self):
        payload = self._make_payload(conditions=[{"operator": "equals", "value": "x"}])
        with self.assertRaises(ValueError):
            self.svc.create_rule(payload)

    def test_create_rule_invalid_field_raises(self):
        payload = self._make_payload(
            conditions=[{"field": "unknown", "operator": "equals", "value": "x"}]
        )
        with self.assertRaises(ValueError):
            self.svc.create_rule(payload)

    def test_create_rule_invalid_operator_raises(self):
        payload = self._make_payload(
            conditions=[{"field": "description", "operator": "regex", "value": "x"}]
        )
        with self.assertRaises(ValueError):
            self.svc.create_rule(payload)

    def test_create_rule_empty_actions_raises(self):
        payload = self._make_payload(actions=[])
        with self.assertRaises(ValueError):
            self.svc.create_rule(payload)

    def test_create_rule_missing_type_in_action_raises(self):
        payload = self._make_payload(actions=[{"value": "something"}])
        with self.assertRaises(ValueError):
            self.svc.create_rule(payload)

    def test_create_rule_invalid_action_type_raises(self):
        payload = self._make_payload(actions=[{"type": "send_email"}])
        with self.assertRaises(ValueError):
            self.svc.create_rule(payload)

    # ── update_rule ──

    def test_update_rule_no_conditions_or_actions_skips_validation(self):
        self.repo.update.return_value = self._make_rule(name="Updated")
        result = self.svc.update_rule(1, {"name": "Updated"})
        self.repo.update.assert_called_once_with(1, {"name": "Updated"})
        self.assertEqual(result["name"], "Updated")

    def test_update_rule_with_conditions_validates(self):
        self.repo.get_by_id.return_value = self._make_rule()
        payload = {"conditions": [{"field": "bad_field", "operator": "equals", "value": "x"}]}
        with self.assertRaises(ValueError):
            self.svc.update_rule(1, payload)

    def test_update_rule_valid_conditions_calls_repo(self):
        existing = self._make_rule()
        self.repo.get_by_id.return_value = existing
        new_conditions = [{"field": "amount", "operator": "gt", "value": "50"}]
        self.repo.update.return_value = self._make_rule(conditions=new_conditions)
        self.svc.update_rule(1, {"conditions": new_conditions})
        self.repo.update.assert_called_once()

    # ── delete_rule ──

    def test_delete_rule_delegates_to_repo(self):
        self.svc.delete_rule(1)
        self.repo.delete.assert_called_once_with(1)

    def test_delete_rule_propagates_value_error(self):
        self.repo.delete.side_effect = ValueError("not found")
        with self.assertRaises(ValueError):
            self.svc.delete_rule(99)

    # ── toggle_enabled ──

    def test_toggle_enabled_true(self):
        self.repo.update.return_value = self._make_rule(enabled=True)
        self.svc.toggle_enabled(1, True)
        self.repo.update.assert_called_once_with(1, {"enabled": True})

    def test_toggle_enabled_false(self):
        self.repo.update.return_value = self._make_rule(enabled=False)
        self.svc.toggle_enabled(1, False)
        self.repo.update.assert_called_once_with(1, {"enabled": False})

    # ── preview_matches ──

    def test_preview_matches_delegates_to_repo(self):
        conditions = [{"field": "description", "operator": "contains", "value": "x"}]
        self.repo.find_matching_transactions.return_value = []
        result = self.svc.preview_matches(conditions)
        self.repo.find_matching_transactions.assert_called_once_with(conditions)
        self.assertEqual(result, [])

    def test_preview_matches_returns_transactions(self):
        txns = [{"id": "b1", "description": "foo", "type": "bank"}]
        self.repo.find_matching_transactions.return_value = txns
        result = self.svc.preview_matches([{"field": "description", "operator": "contains", "value": "foo"}])
        self.assertEqual(result, txns)

    # ── apply_rule ──

    def test_apply_rule_calls_find_and_apply(self):
        rule = self._make_rule()
        self.repo.get_by_id.return_value = rule
        matches = [
            {"id": "b1", "type": "bank"},
            {"id": "c1", "type": "credit"},
        ]
        self.repo.find_matching_transactions.return_value = matches
        self.repo.apply_actions_to_transactions.return_value = 2

        result = self.svc.apply_rule(1)

        self.repo.find_matching_transactions.assert_called_once_with(rule["conditions"])
        called_ids = self.repo.apply_actions_to_transactions.call_args[0][0]
        self.assertIn("b1", called_ids["bank"])
        self.assertIn("c1", called_ids["credit"])
        self.assertEqual(result["applied"], 2)
        self.assertEqual(result["matches_found"], 2)

    def test_apply_rule_no_matches_returns_zero(self):
        self.repo.get_by_id.return_value = self._make_rule()
        self.repo.find_matching_transactions.return_value = []
        self.repo.apply_actions_to_transactions.return_value = 0
        result = self.svc.apply_rule(1)
        self.assertEqual(result["applied"], 0)
        self.assertEqual(result["matches_found"], 0)

    def test_apply_rule_not_found_raises(self):
        self.repo.get_by_id.side_effect = ValueError("not found")
        with self.assertRaises(ValueError):
            self.svc.apply_rule(99)


if __name__ == "__main__":
    unittest.main()
