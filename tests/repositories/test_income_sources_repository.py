"""Tests for IncomeSourcesRepository"""

import unittest

from repositories.income_sources_repository import IncomeSourcesRepository

_CREATE_TABLE = """
CREATE TABLE income_sources (
    id              TEXT PRIMARY KEY,
    description     TEXT,
    amount          REAL,
    frequency       TEXT,
    next_occurrence TEXT,
    category_id     TEXT,
    merchant_name   TEXT,
    amount_min      REAL,
    amount_max      REAL,
    confidence      REAL,
    source          TEXT DEFAULT 'manual',
    synced_at       TEXT
)
"""

_CREATE_BANK_TABLE = """
CREATE TABLE bank_transactions (
    id          TEXT PRIMARY KEY,
    description TEXT,
    amount      REAL,
    date        TEXT,
    excluded    INTEGER DEFAULT 0
)
"""

_SAMPLE = {
    "id": "inc-1",
    "description": "Salario",
    "amount": 4800.0,
    "frequency": "monthly",
    "next_occurrence": "2026-04-05",
    "category_id": None,
    "merchant_name": "Empresa XYZ",
    "amount_min": None,
    "amount_max": None,
    "confidence": None,
    "source": "manual",
    "synced_at": "2026-03-01",
}


class TestIncomeSourcesRepository(unittest.TestCase):

    def setUp(self):
        self.repo = IncomeSourcesRepository(db_path=":memory:")
        self.repo.execute_query(_CREATE_TABLE)

    def tearDown(self):
        self.repo.close()

    # ── upsert ──

    def test_upsert_insert_new(self):
        self.repo.upsert(_SAMPLE.copy())
        rows = self.repo.get_all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], "inc-1")
        self.assertEqual(rows[0]["description"], "Salario")

    def test_upsert_updates_existing(self):
        self.repo.upsert(_SAMPLE.copy())
        self.repo.upsert({**_SAMPLE, "amount": 5200.0})
        rows = self.repo.get_all()
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]["amount"], 5200.0)

    def test_upsert_idempotent(self):
        self.repo.upsert(_SAMPLE.copy())
        self.repo.upsert(_SAMPLE.copy())
        self.assertEqual(len(self.repo.get_all()), 1)

    # ── get_all ──

    def test_get_all_empty(self):
        self.assertEqual(self.repo.get_all(), [])

    def test_get_all_multiple(self):
        self.repo.upsert(_SAMPLE.copy())
        self.repo.upsert({**_SAMPLE, "id": "inc-2", "description": "Freelance"})
        self.assertEqual(len(self.repo.get_all()), 2)

    # ── get_by_id ──

    def test_get_by_id_found(self):
        self.repo.upsert(_SAMPLE.copy())
        row = self.repo.get_by_id("inc-1")
        self.assertEqual(row["id"], "inc-1")

    def test_get_by_id_not_found_raises(self):
        with self.assertRaises(ValueError):
            self.repo.get_by_id("nonexistent")

    # ── update ──

    def test_update_changes_allowed_fields(self):
        self.repo.upsert(_SAMPLE.copy())
        self.repo.update("inc-1", {"amount": 5000.0, "description": "Novo Salario"})
        row = self.repo.get_by_id("inc-1")
        self.assertAlmostEqual(row["amount"], 5000.0)
        self.assertEqual(row["description"], "Novo Salario")

    def test_update_ignores_disallowed_fields(self):
        self.repo.upsert(_SAMPLE.copy())
        self.repo.update("inc-1", {"source": "hacked", "amount": 1.0})
        row = self.repo.get_by_id("inc-1")
        self.assertEqual(row["source"], "manual")
        self.assertAlmostEqual(row["amount"], 1.0)

    def test_update_allows_amount_min_max(self):
        self.repo.upsert(_SAMPLE.copy())
        self.repo.update("inc-1", {"amount_min": 4000.0, "amount_max": 6000.0})
        row = self.repo.get_by_id("inc-1")
        self.assertAlmostEqual(row["amount_min"], 4000.0)
        self.assertAlmostEqual(row["amount_max"], 6000.0)

    def test_update_not_found_raises(self):
        with self.assertRaises(ValueError):
            self.repo.update("ghost", {"amount": 1.0})

    # ── delete ──

    def test_delete_removes_record(self):
        self.repo.upsert(_SAMPLE.copy())
        self.repo.delete("inc-1")
        self.assertEqual(self.repo.get_all(), [])

    def test_delete_not_found_raises(self):
        with self.assertRaises(ValueError):
            self.repo.delete("ghost")


class TestMatchingTransactions(unittest.TestCase):

    def setUp(self):
        self.repo = IncomeSourcesRepository(db_path=":memory:")
        self.repo.execute_query(_CREATE_TABLE)
        self.repo.execute_query(_CREATE_BANK_TABLE)
        # bank income (amount > 0)
        self.repo.execute_query(
            "INSERT INTO bank_transactions VALUES (?,?,?,?,?)",
            ("t1", "Empresa XYZ salario", 4800.0, "2026-03-05", 0),
        )
        self.repo.execute_query(
            "INSERT INTO bank_transactions VALUES (?,?,?,?,?)",
            ("t2", "Empresa XYZ salario", 4800.0, "2026-02-05", 0),
        )
        self.repo.execute_query(
            "INSERT INTO bank_transactions VALUES (?,?,?,?,?)",
            ("t3", "Freelance pagamento", 1200.0, "2026-03-10", 0),
        )
        # excluded income
        self.repo.execute_query(
            "INSERT INTO bank_transactions VALUES (?,?,?,?,?)",
            ("t4", "Empresa XYZ excluido", 4800.0, "2026-01-05", 1),
        )
        # bank expense (amount < 0) - must NOT be counted as income
        self.repo.execute_query(
            "INSERT INTO bank_transactions VALUES (?,?,?,?,?)",
            ("t5", "Empresa XYZ debito", -100.0, "2026-03-01", 0),
        )

    def tearDown(self):
        self.repo.close()

    # ── count_matching_transactions ──

    def test_count_by_name_filter(self):
        # t1 + t2 (positive amounts only)
        count = self.repo.count_matching_transactions("empresa xyz")
        self.assertEqual(count, 2)

    def test_count_excludes_negative_amounts(self):
        # t5 has amount < 0, must not be counted
        count = self.repo.count_matching_transactions("debito")
        self.assertEqual(count, 0)

    def test_count_excludes_excluded_rows(self):
        count = self.repo.count_matching_transactions("excluido")
        self.assertEqual(count, 0)

    def test_count_with_amount_min(self):
        count = self.repo.count_matching_transactions("empresa xyz", amount_min=4000.0)
        self.assertEqual(count, 2)

    def test_count_with_amount_max(self):
        count = self.repo.count_matching_transactions("empresa xyz", amount_max=3000.0)
        self.assertEqual(count, 0)

    def test_count_with_range(self):
        count = self.repo.count_matching_transactions("empresa xyz", amount_min=4000.0, amount_max=5000.0)
        self.assertEqual(count, 2)

    def test_count_empty_merchant_raises(self):
        with self.assertRaises(ValueError):
            self.repo.count_matching_transactions("")

    def test_count_none_merchant_raises(self):
        with self.assertRaises(ValueError):
            self.repo.count_matching_transactions(None)

    # ── get_month_actual ──

    def test_get_month_actual_sums_matching_month(self):
        total = self.repo.get_month_actual("2026-03", "empresa xyz")
        self.assertAlmostEqual(total, 4800.0)

    def test_get_month_actual_excludes_other_months(self):
        total = self.repo.get_month_actual("2026-01", "empresa xyz")
        self.assertAlmostEqual(total, 0.0)

    def test_get_month_actual_returns_zero_when_no_match(self):
        total = self.repo.get_month_actual("2026-03", "nonexistent")
        self.assertAlmostEqual(total, 0.0)

    def test_get_month_actual_excludes_negative_amounts(self):
        total = self.repo.get_month_actual("2026-03", "debito")
        self.assertAlmostEqual(total, 0.0)

    # ── get_monthly_actuals ──

    def test_get_monthly_actuals_groups_by_month(self):
        result = self.repo.get_monthly_actuals(2026, "empresa xyz")
        self.assertAlmostEqual(result.get("2026-03"), 4800.0)
        self.assertAlmostEqual(result.get("2026-02"), 4800.0)

    def test_get_monthly_actuals_excludes_negative_amounts(self):
        result = self.repo.get_monthly_actuals(2026, "debito")
        self.assertEqual(result, {})

    def test_get_monthly_actuals_excludes_different_year(self):
        result = self.repo.get_monthly_actuals(2025, "empresa xyz")
        self.assertEqual(result, {})

    def test_get_monthly_actuals_with_day_filter(self):
        # t1 is on 2026-03-05, day_of_month=5 ±5 → days 1-10 → matches
        result = self.repo.get_monthly_actuals(2026, "empresa xyz", day_of_month=5)
        self.assertIn("2026-03", result)

    # ── get_matching_transactions ──

    def test_get_returns_dicts_with_expected_keys(self):
        rows = self.repo.get_matching_transactions("empresa xyz")
        self.assertEqual(len(rows), 2)
        self.assertIn("id", rows[0])
        self.assertIn("description", rows[0])
        self.assertIn("amount", rows[0])
        self.assertIn("date", rows[0])

    def test_get_ordered_by_date_desc(self):
        rows = self.repo.get_matching_transactions("empresa xyz")
        self.assertEqual(rows[0]["date"], "2026-03-05")

    def test_get_amount_is_positive(self):
        rows = self.repo.get_matching_transactions("empresa xyz")
        self.assertTrue(all(r["amount"] > 0 for r in rows))

    def test_get_empty_merchant_raises(self):
        with self.assertRaises(ValueError):
            self.repo.get_matching_transactions("")


if __name__ == "__main__":
    unittest.main()
