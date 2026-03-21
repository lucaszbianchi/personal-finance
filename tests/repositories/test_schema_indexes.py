import sqlite3
import unittest

from init_db import INDEXES_SQL, TABLES_SQL


class TestSchemaIndexes(unittest.TestCase):
    """Verify that all declared indexes are created and idempotent."""

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        cursor = self.conn.cursor()
        for sql in TABLES_SQL:
            cursor.execute(sql)
        for sql in INDEXES_SQL:
            cursor.execute(sql)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_all_indexes_exist(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        created = {row[0] for row in cursor.fetchall()}
        expected = set()
        for sql in INDEXES_SQL:
            name = sql.split("IF NOT EXISTS ")[-1].split(" ON")[0]
            expected.add(name)
        self.assertTrue(expected.issubset(created), f"Missing indexes: {expected - created}")

    def test_indexes_are_idempotent(self):
        cursor = self.conn.cursor()
        for sql in INDEXES_SQL:
            cursor.execute(sql)  # Should not raise

    def test_explain_uses_index_bank_transactions_date(self):
        cursor = self.conn.cursor()
        cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM bank_transactions WHERE date >= '2025-01-01' AND date < '2025-02-01'")
        plan = " ".join(row[-1] for row in cursor.fetchall())
        self.assertIn("idx_bank_transactions_date", plan)

    def test_explain_uses_index_credit_transactions_excluded_date(self):
        cursor = self.conn.cursor()
        cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM credit_transactions WHERE excluded = 0 AND date >= '2025-01-01'")
        plan = " ".join(row[-1] for row in cursor.fetchall())
        self.assertIn("idx_credit_transactions_excluded_date", plan)

    def test_explain_uses_index_splitwise_transaction_id(self):
        cursor = self.conn.cursor()
        cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM splitwise WHERE transaction_id = 'abc'")
        plan = " ".join(row[-1] for row in cursor.fetchall())
        self.assertIn("idx_splitwise_transaction_id", plan)

    def test_explain_uses_index_investments_date(self):
        cursor = self.conn.cursor()
        cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM investments WHERE date = '2025-01-01'")
        plan = " ".join(row[-1] for row in cursor.fetchall())
        self.assertIn("idx_investments_date", plan)

    def test_explain_uses_index_accounts_snapshot_snapshotted_at(self):
        cursor = self.conn.cursor()
        cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM accounts_snapshot WHERE snapshotted_at = '2025-01-01'")
        plan = " ".join(row[-1] for row in cursor.fetchall())
        self.assertIn("idx_accounts_snapshot_snapshotted_at", plan)
