"""Tests for AutomationRepository."""

import unittest
from repositories.automation_repository import AutomationRepository

_CREATE_AUTOMATION_RULES = """
    CREATE TABLE automation_rules (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT,
        conditions  TEXT NOT NULL,
        actions     TEXT NOT NULL,
        priority    INTEGER DEFAULT 0,
        enabled     INTEGER DEFAULT 1,
        created_at  TEXT DEFAULT (datetime('now'))
    )
"""

_CREATE_BANK = """
    CREATE TABLE bank_transactions (
        id TEXT PRIMARY KEY,
        date TEXT,
        description TEXT,
        amount REAL,
        category_id TEXT,
        excluded INTEGER DEFAULT 0
    )
"""

_CREATE_CREDIT = """
    CREATE TABLE credit_transactions (
        id TEXT PRIMARY KEY,
        date TEXT,
        description TEXT,
        amount REAL,
        category_id TEXT,
        excluded INTEGER DEFAULT 0
    )
"""


class TestAutomationRepository(unittest.TestCase):
    def setUp(self):
        self.repo = AutomationRepository(db_path=":memory:")
        for sql in (_CREATE_AUTOMATION_RULES, _CREATE_BANK, _CREATE_CREDIT):
            self.repo.execute_query(sql)

    def tearDown(self):
        self.repo.close()

    def _make_rule(self, name="Test", priority=0, enabled=True):
        return {
            "name": name,
            "conditions": [{"field": "description", "operator": "equals", "value": "foo"}],
            "actions": [{"type": "set_category", "value": "cat-1"}],
            "priority": priority,
            "enabled": enabled,
        }

    def _insert_bank(self, txn_id, description, amount=100.0, category_id=None, excluded=0):
        self.repo.execute_query(
            "INSERT INTO bank_transactions (id, date, description, amount, category_id, excluded)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (txn_id, "2026-03-01", description, amount, category_id, excluded),
        )

    def _insert_credit(self, txn_id, description, amount=50.0, category_id=None, excluded=0):
        self.repo.execute_query(
            "INSERT INTO credit_transactions (id, date, description, amount, category_id, excluded)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (txn_id, "2026-03-02", description, amount, category_id, excluded),
        )

    # ── create ──

    def test_create_returns_rule_with_id(self):
        rule = self.repo.create(self._make_rule())
        self.assertIn("id", rule)
        self.assertEqual(rule["name"], "Test")

    def test_create_stores_conditions_as_list(self):
        rule = self.repo.create(self._make_rule())
        self.assertIsInstance(rule["conditions"], list)
        self.assertEqual(rule["conditions"][0]["field"], "description")

    def test_create_stores_actions_as_list(self):
        rule = self.repo.create(self._make_rule())
        self.assertIsInstance(rule["actions"], list)
        self.assertEqual(rule["actions"][0]["type"], "set_category")

    def test_create_defaults_enabled_true(self):
        rule = self.repo.create(self._make_rule())
        self.assertTrue(rule["enabled"])

    def test_create_disabled_rule(self):
        rule = self.repo.create(self._make_rule(enabled=False))
        self.assertFalse(rule["enabled"])

    # ── get_all ──

    def test_get_all_empty(self):
        self.assertEqual(self.repo.get_all(), [])

    def test_get_all_returns_all_rules(self):
        self.repo.create(self._make_rule("A"))
        self.repo.create(self._make_rule("B"))
        self.assertEqual(len(self.repo.get_all()), 2)

    def test_get_all_ordered_by_priority_desc(self):
        self.repo.create(self._make_rule("low", priority=0))
        self.repo.create(self._make_rule("high", priority=10))
        rules = self.repo.get_all()
        self.assertEqual(rules[0]["name"], "high")

    # ── get_by_id ──

    def test_get_by_id_returns_rule(self):
        created = self.repo.create(self._make_rule())
        self.assertEqual(self.repo.get_by_id(created["id"])["id"], created["id"])

    def test_get_by_id_not_found_raises(self):
        with self.assertRaises(ValueError):
            self.repo.get_by_id(9999)

    # ── update ──

    def test_update_name(self):
        rule = self.repo.create(self._make_rule("Original"))
        self.assertEqual(self.repo.update(rule["id"], {"name": "Updated"})["name"], "Updated")

    def test_update_conditions(self):
        rule = self.repo.create(self._make_rule())
        new_conds = [{"field": "amount", "operator": "equals", "value": "100"}]
        updated = self.repo.update(rule["id"], {"conditions": new_conds})
        self.assertEqual(updated["conditions"], new_conds)

    def test_update_enabled_toggle(self):
        rule = self.repo.create(self._make_rule(enabled=True))
        self.assertFalse(self.repo.update(rule["id"], {"enabled": False})["enabled"])

    def test_update_not_found_raises(self):
        with self.assertRaises(ValueError):
            self.repo.update(9999, {"name": "X"})

    # ── delete ──

    def test_delete_removes_rule(self):
        rule = self.repo.create(self._make_rule())
        self.repo.delete(rule["id"])
        self.assertEqual(self.repo.get_all(), [])

    def test_delete_not_found_raises(self):
        with self.assertRaises(ValueError):
            self.repo.delete(9999)

    # ── JSON round-trip ──

    def test_json_round_trip_multiple_conditions(self):
        data = self._make_rule()
        data["conditions"] = [
            {"field": "description", "operator": "contains", "value": "netflix"},
            {"field": "amount", "operator": "equals", "value": "50"},
        ]
        rule = self.repo.create(data)
        self.assertEqual(len(self.repo.get_by_id(rule["id"])["conditions"]), 2)

    def test_json_round_trip_multiple_actions(self):
        data = self._make_rule()
        data["actions"] = [
            {"type": "set_category", "value": "cat-1"},
            {"type": "exclude"},
        ]
        rule = self.repo.create(data)
        self.assertEqual(len(self.repo.get_by_id(rule["id"])["actions"]), 2)

    # ── _build_where ──

    def test_build_where_description_equals(self):
        clauses, params = AutomationRepository._build_where(
            [{"field": "description", "operator": "equals", "value": "foo"}]
        )
        self.assertEqual(len(clauses), 1)
        self.assertIn("LOWER(description)", clauses[0])
        self.assertEqual(params, ["foo"])

    def test_build_where_description_contains(self):
        _, params = AutomationRepository._build_where(
            [{"field": "description", "operator": "contains", "value": "bar"}]
        )
        self.assertEqual(params, ["%bar%"])

    def test_build_where_description_starts_with(self):
        _, params = AutomationRepository._build_where(
            [{"field": "description", "operator": "starts_with", "value": "pre"}]
        )
        self.assertEqual(params, ["pre%"])

    def test_build_where_description_ends_with(self):
        _, params = AutomationRepository._build_where(
            [{"field": "description", "operator": "ends_with", "value": "suf"}]
        )
        self.assertEqual(params, ["%suf"])

    def test_build_where_category_equals(self):
        clauses, params = AutomationRepository._build_where(
            [{"field": "category", "operator": "equals", "value": "cat-1"}]
        )
        self.assertIn("category_id", clauses[0])
        self.assertEqual(params, ["cat-1"])

    def test_build_where_amount_equals(self):
        clauses, params = AutomationRepository._build_where(
            [{"field": "amount", "operator": "equals", "value": "99.5"}]
        )
        self.assertIn("= ?", clauses[0])
        self.assertAlmostEqual(params[0], 99.5)

    def test_build_where_amount_gt(self):
        clauses, params = AutomationRepository._build_where(
            [{"field": "amount", "operator": "gt", "value": "50"}]
        )
        self.assertIn("> ?", clauses[0])
        self.assertAlmostEqual(params[0], 50.0)

    def test_build_where_amount_lt(self):
        clauses, params = AutomationRepository._build_where(
            [{"field": "amount", "operator": "lt", "value": "200"}]
        )
        self.assertIn("< ?", clauses[0])
        self.assertAlmostEqual(params[0], 200.0)

    def test_build_where_unknown_field_skipped(self):
        clauses, params = AutomationRepository._build_where(
            [{"field": "unknown_field", "operator": "equals", "value": "x"}]
        )
        self.assertEqual(clauses, [])
        self.assertEqual(params, [])

    def test_build_where_multiple_conditions_anded(self):
        clauses, params = AutomationRepository._build_where([
            {"field": "description", "operator": "contains", "value": "netflix"},
            {"field": "amount", "operator": "equals", "value": "15.0"},
        ])
        self.assertEqual(len(clauses), 2)
        self.assertEqual(len(params), 2)

    # ── find_matching_transactions ──

    def test_find_matching_empty_conditions_returns_empty(self):
        self._insert_bank("b1", "Netflix")
        self.assertEqual(self.repo.find_matching_transactions([]), [])

    def test_find_matches_bank_by_description_contains(self):
        self._insert_bank("b1", "Netflix assinatura")
        self._insert_bank("b2", "Mercado Livre")
        results = self.repo.find_matching_transactions(
            [{"field": "description", "operator": "contains", "value": "netflix"}]
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "b1")
        self.assertEqual(results[0]["type"], "bank")

    def test_find_matches_credit_transactions(self):
        self._insert_credit("c1", "Amazon Prime")
        results = self.repo.find_matching_transactions(
            [{"field": "description", "operator": "contains", "value": "amazon"}]
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["type"], "credit")

    def test_find_matches_both_tables(self):
        self._insert_bank("b1", "Spotify")
        self._insert_credit("c1", "Spotify anual")
        results = self.repo.find_matching_transactions(
            [{"field": "description", "operator": "contains", "value": "spotify"}]
        )
        self.assertEqual(len(results), 2)

    def test_find_excludes_excluded_transactions(self):
        self._insert_bank("b1", "Netflix", excluded=1)
        results = self.repo.find_matching_transactions(
            [{"field": "description", "operator": "contains", "value": "netflix"}]
        )
        self.assertEqual(results, [])

    def test_find_matches_no_results(self):
        self._insert_bank("b1", "Padaria")
        results = self.repo.find_matching_transactions(
            [{"field": "description", "operator": "contains", "value": "netflix"}]
        )
        self.assertEqual(results, [])

    def test_find_matches_amount_gt(self):
        self._insert_bank("b1", "Salario", amount=5000.0)
        self._insert_bank("b2", "Padaria", amount=20.0)
        results = self.repo.find_matching_transactions(
            [{"field": "amount", "operator": "gt", "value": "100"}]
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "b1")

    def test_find_matches_amount_lt(self):
        self._insert_bank("b1", "Salario", amount=5000.0)
        self._insert_bank("b2", "Padaria", amount=20.0)
        results = self.repo.find_matching_transactions(
            [{"field": "amount", "operator": "lt", "value": "100"}]
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "b2")

    def test_find_matches_category_equals(self):
        self._insert_bank("b1", "Netflix", category_id="cat-streaming")
        self._insert_bank("b2", "Mercado", category_id="cat-food")
        results = self.repo.find_matching_transactions(
            [{"field": "category", "operator": "equals", "value": "cat-streaming"}]
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "b1")

    # ── apply_actions_to_transactions ──

    def test_apply_set_category(self):
        self._insert_bank("b1", "Netflix")
        self.repo.apply_actions_to_transactions(
            {"bank": ["b1"]}, [{"type": "set_category", "value": "cat-99"}]
        )
        row = self.repo.execute_query(
            "SELECT category_id FROM bank_transactions WHERE id = ?", ("b1",)
        ).fetchone()
        self.assertEqual(row["category_id"], "cat-99")

    def test_apply_exclude(self):
        self._insert_bank("b1", "Netflix")
        self.repo.apply_actions_to_transactions(
            {"bank": ["b1"]}, [{"type": "exclude"}]
        )
        row = self.repo.execute_query(
            "SELECT excluded FROM bank_transactions WHERE id = ?", ("b1",)
        ).fetchone()
        self.assertEqual(row["excluded"], 1)

    def test_apply_set_description(self):
        self._insert_credit("c1", "AMZN*Prime")
        self.repo.apply_actions_to_transactions(
            {"credit": ["c1"]}, [{"type": "set_description", "value": "Amazon Prime"}]
        )
        row = self.repo.execute_query(
            "SELECT description FROM credit_transactions WHERE id = ?", ("c1",)
        ).fetchone()
        self.assertEqual(row["description"], "Amazon Prime")

    def test_apply_returns_count(self):
        self._insert_bank("b1", "foo")
        self._insert_bank("b2", "foo")
        count = self.repo.apply_actions_to_transactions(
            {"bank": ["b1", "b2"]}, [{"type": "exclude"}]
        )
        self.assertEqual(count, 2)

    def test_apply_empty_ids_returns_zero(self):
        count = self.repo.apply_actions_to_transactions({}, [{"type": "exclude"}])
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
