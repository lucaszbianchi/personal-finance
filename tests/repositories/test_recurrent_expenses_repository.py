"""Tests for RecurrentExpensesRepository"""

import unittest

from repositories.recurrent_expenses_repository import RecurrentExpensesRepository

_CREATE_TABLE = """
CREATE TABLE recurrent_expenses (
    id              TEXT PRIMARY KEY,
    item_id         TEXT,
    description     TEXT,
    amount          REAL,
    frequency       TEXT,
    next_occurrence TEXT,
    category_id     TEXT,
    merchant_name   TEXT,
    amount_min      REAL,
    amount_max      REAL,
    confidence      REAL,
    source          TEXT DEFAULT 'pluggy',
    is_unavoidable  INTEGER DEFAULT 0,
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

_CREATE_CREDIT_TABLE = """
CREATE TABLE credit_transactions (
    id          TEXT PRIMARY KEY,
    description TEXT,
    amount      REAL,
    date        TEXT,
    excluded    INTEGER DEFAULT 0
)
"""

_SAMPLE = {
    "id": "abc123",
    "description": "Netflix",
    "amount": 55.90,
    "frequency": "monthly",
    "next_occurrence": "2026-04-10",
    "category_id": None,
    "merchant_name": "Netflix Inc",
    "amount_min": None,
    "amount_max": None,
    "confidence": 0.95,
    "source": "manual",
    "is_unavoidable": 0,
    "synced_at": "2026-03-14 10:00:00",
}


class TestRecurrentExpensesRepository(unittest.TestCase):

    def setUp(self):
        self.repo = RecurrentExpensesRepository(db_path=":memory:")
        self.repo.execute_query(_CREATE_TABLE)

    def tearDown(self):
        self.repo.close()

    # ── upsert_recurrence ──

    def test_upsert_insert_new(self):
        self.repo.upsert_recurrence(_SAMPLE.copy())
        rows = self.repo.get_all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], "abc123")
        self.assertEqual(rows[0]["description"], "Netflix")

    def test_upsert_updates_existing(self):
        self.repo.upsert_recurrence(_SAMPLE.copy())
        updated = {**_SAMPLE, "amount": 69.90}
        self.repo.upsert_recurrence(updated)
        rows = self.repo.get_all()
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]["amount"], 69.90)

    def test_upsert_idempotent(self):
        self.repo.upsert_recurrence(_SAMPLE.copy())
        self.repo.upsert_recurrence(_SAMPLE.copy())
        rows = self.repo.get_all()
        self.assertEqual(len(rows), 1)

    # ── get_all ──

    def test_get_all_empty(self):
        self.assertEqual(self.repo.get_all(), [])

    def test_get_all_multiple(self):
        self.repo.upsert_recurrence(_SAMPLE.copy())
        second = {**_SAMPLE, "id": "def456", "description": "Spotify"}
        self.repo.upsert_recurrence(second)
        rows = self.repo.get_all()
        self.assertEqual(len(rows), 2)

    # ── get_by_id ──

    def test_get_by_id_found(self):
        self.repo.upsert_recurrence(_SAMPLE.copy())
        row = self.repo.get_by_id("abc123")
        self.assertEqual(row["id"], "abc123")
        self.assertEqual(row["description"], "Netflix")

    def test_get_by_id_not_found_raises(self):
        with self.assertRaises(ValueError):
            self.repo.get_by_id("nonexistent")

    # ── update ──

    def test_update_changes_allowed_fields(self):
        self.repo.upsert_recurrence(_SAMPLE.copy())
        self.repo.update("abc123", {"amount": 79.90, "is_unavoidable": 1})
        row = self.repo.get_by_id("abc123")
        self.assertAlmostEqual(row["amount"], 79.90)
        self.assertEqual(row["is_unavoidable"], 1)

    def test_update_ignores_disallowed_fields(self):
        self.repo.upsert_recurrence(_SAMPLE.copy())
        self.repo.update("abc123", {"source": "hacked", "amount": 10.0})
        row = self.repo.get_by_id("abc123")
        self.assertEqual(row["source"], "manual")
        self.assertAlmostEqual(row["amount"], 10.0)

    def test_update_allows_amount_min_max(self):
        self.repo.upsert_recurrence(_SAMPLE.copy())
        self.repo.update("abc123", {"amount_min": 10.0, "amount_max": 100.0})
        row = self.repo.get_by_id("abc123")
        self.assertAlmostEqual(row["amount_min"], 10.0)
        self.assertAlmostEqual(row["amount_max"], 100.0)

    def test_update_not_found_raises(self):
        with self.assertRaises(ValueError):
            self.repo.update("ghost", {"amount": 1.0})

    # ── delete ──

    def test_delete_removes_record(self):
        self.repo.upsert_recurrence(_SAMPLE.copy())
        self.repo.delete("abc123")
        self.assertEqual(self.repo.get_all(), [])

    def test_delete_not_found_raises(self):
        with self.assertRaises(ValueError):
            self.repo.delete("ghost")


class TestMatchingTransactions(unittest.TestCase):

    def setUp(self):
        self.repo = RecurrentExpensesRepository(db_path=":memory:")
        self.repo.execute_query(_CREATE_TABLE)
        self.repo.execute_query(_CREATE_BANK_TABLE)
        self.repo.execute_query(_CREATE_CREDIT_TABLE)
        # bank transactions (expenses: amount < 0)
        self.repo.execute_query(
            "INSERT INTO bank_transactions VALUES (?,?,?,?,?)",
            ("t1", "Netflix cobranca", -55.90, "2026-03-10", 0),
        )
        self.repo.execute_query(
            "INSERT INTO bank_transactions VALUES (?,?,?,?,?)",
            ("t2", "Netflix cobranca", -69.90, "2026-02-10", 0),
        )
        self.repo.execute_query(
            "INSERT INTO bank_transactions VALUES (?,?,?,?,?)",
            ("t3", "Spotify mensal", -25.90, "2026-03-10", 0),
        )
        self.repo.execute_query(
            "INSERT INTO bank_transactions VALUES (?,?,?,?,?)",
            ("t4", "Netflix excluido", -55.90, "2026-01-10", 1),
        )
        # credit transactions (expenses: amount > 0)
        self.repo.execute_query(
            "INSERT INTO credit_transactions VALUES (?,?,?,?,?)",
            ("c1", "Netflix credito", 55.90, "2026-03-15", 0),
        )
        self.repo.execute_query(
            "INSERT INTO credit_transactions VALUES (?,?,?,?,?)",
            ("c2", "Netflix excluido credito", 55.90, "2026-03-15", 1),
        )
        # credit payment (amount < 0) should NOT be matched
        self.repo.execute_query(
            "INSERT INTO credit_transactions VALUES (?,?,?,?,?)",
            ("c3", "Netflix pagamento", -55.90, "2026-03-15", 0),
        )

    def tearDown(self):
        self.repo.close()

    # ── count_matching_transactions ──

    def test_count_by_name_filter(self):
        # t1 + t2 (bank) + c1 (credit) = 3
        count = self.repo.count_matching_transactions("netflix")
        self.assertEqual(count, 3)

    def test_count_includes_credit_transactions(self):
        count = self.repo.count_matching_transactions("credito")
        self.assertEqual(count, 1)

    def test_count_excludes_credit_payments(self):
        # c3 has amount < 0 (payment), should not be counted
        count = self.repo.count_matching_transactions("pagamento")
        self.assertEqual(count, 0)

    def test_count_with_amount_min(self):
        # t2 (69.90) + c1 (55.90 < 60 so NO) -> only t2
        count = self.repo.count_matching_transactions("netflix", amount_min=60.0)
        self.assertEqual(count, 1)

    def test_count_with_amount_max(self):
        # t1 (55.90) + c1 (55.90) -> 2; t2 (69.90) excluded
        count = self.repo.count_matching_transactions("netflix", amount_max=60.0)
        self.assertEqual(count, 2)

    def test_count_with_range(self):
        count = self.repo.count_matching_transactions("netflix", amount_min=50.0, amount_max=60.0)
        self.assertEqual(count, 2)

    def test_count_excludes_excluded_rows(self):
        count = self.repo.count_matching_transactions("excluido")
        self.assertEqual(count, 0)

    def test_count_empty_merchant_raises(self):
        with self.assertRaises(ValueError):
            self.repo.count_matching_transactions("")

    def test_count_none_merchant_raises(self):
        with self.assertRaises(ValueError):
            self.repo.count_matching_transactions(None)

    # ── get_matching_transactions ──

    def test_get_returns_dicts_with_expected_keys(self):
        rows = self.repo.get_matching_transactions("netflix")
        self.assertEqual(len(rows), 3)
        self.assertIn("id", rows[0])
        self.assertIn("description", rows[0])
        self.assertIn("amount", rows[0])
        self.assertIn("date", rows[0])

    def test_get_includes_credit_transactions(self):
        rows = self.repo.get_matching_transactions("credito")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], "c1")

    def test_get_excludes_credit_payments(self):
        rows = self.repo.get_matching_transactions("pagamento")
        self.assertEqual(len(rows), 0)

    def test_get_ordered_by_date_desc(self):
        rows = self.repo.get_matching_transactions("netflix")
        # c1 date 2026-03-15 is the most recent
        self.assertEqual(rows[0]["date"], "2026-03-15")

    def test_get_amount_is_positive(self):
        rows = self.repo.get_matching_transactions("netflix")
        self.assertTrue(all(r["amount"] > 0 for r in rows))

    def test_get_empty_merchant_raises(self):
        with self.assertRaises(ValueError):
            self.repo.get_matching_transactions("")


if __name__ == "__main__":
    unittest.main()
