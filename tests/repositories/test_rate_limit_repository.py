"""Testes para RateLimitRepository"""

import unittest
from unittest.mock import patch
from repositories.rate_limit_repository import RateLimitRepository, RATE_LIMITS


class TestRateLimitRepository(unittest.TestCase):
    def setUp(self):
        self.repo = RateLimitRepository(db_path=":memory:")
        self.repo.execute_query(
            """
            CREATE TABLE rate_limit_usage (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                call_type  TEXT NOT NULL,
                year_month TEXT NOT NULL,
                count      INTEGER DEFAULT 0,
                limit_value INTEGER NOT NULL,
                UNIQUE(call_type, year_month)
            )
            """
        )

    def tearDown(self):
        self.repo.close()

    # ------------------------------------------------------------------
    # RATE_LIMITS constants
    # ------------------------------------------------------------------

    def test_rate_limits_keys(self):
        self.assertIn("recent", RATE_LIMITS)
        self.assertIn("non_recent", RATE_LIMITS)

    def test_rate_limits_values(self):
        self.assertEqual(RATE_LIMITS["recent"], 120)
        self.assertEqual(RATE_LIMITS["non_recent"], 4)

    # ------------------------------------------------------------------
    # can_call
    # ------------------------------------------------------------------

    def test_can_call_recent_initially_true(self):
        self.assertTrue(self.repo.can_call("recent"))

    def test_can_call_non_recent_initially_true(self):
        self.assertTrue(self.repo.can_call("non_recent"))

    def test_can_call_false_when_limit_reached(self):
        with patch.object(self.repo, "_current_year_month", return_value="2026-03"):
            # Inserir registro já no limite
            self.repo.execute_query(
                "INSERT INTO rate_limit_usage (call_type, year_month, count, limit_value) VALUES (?, ?, ?, ?)",
                ("non_recent", "2026-03", 4, 4),
            )
            self.assertFalse(self.repo.can_call("non_recent"))

    def test_can_call_invalid_type_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.repo.can_call("invalid_type")
        self.assertIn("desconhecido", str(ctx.exception))

    # ------------------------------------------------------------------
    # increment
    # ------------------------------------------------------------------

    def test_increment_creates_record_and_returns_dict(self):
        result = self.repo.increment("recent")

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["limit_value"], RATE_LIMITS["recent"])
        self.assertEqual(result["remaining"], RATE_LIMITS["recent"] - 1)
        self.assertFalse(result["exceeded"])

    def test_increment_accumulates(self):
        self.repo.increment("non_recent")
        self.repo.increment("non_recent")
        result = self.repo.increment("non_recent")

        self.assertEqual(result["count"], 3)
        self.assertEqual(result["remaining"], 1)

    def test_increment_exceeded_flag(self):
        with patch.object(self.repo, "_current_year_month", return_value="2026-03"):
            self.repo.execute_query(
                "INSERT INTO rate_limit_usage (call_type, year_month, count, limit_value) VALUES (?, ?, ?, ?)",
                ("non_recent", "2026-03", 3, 4),
            )
            result = self.repo.increment("non_recent")

        self.assertEqual(result["count"], 4)
        self.assertEqual(result["remaining"], 0)
        self.assertTrue(result["exceeded"])

    def test_increment_idempotent_per_month(self):
        with patch.object(self.repo, "_current_year_month", return_value="2026-03"):
            self.repo.increment("recent")
            self.repo.increment("recent")

        # Mesmo mês = mesmo registro
        cursor = self.repo.execute_query(
            "SELECT count FROM rate_limit_usage WHERE call_type = ? AND year_month = ?",
            ("recent", "2026-03"),
        )
        row = cursor.fetchone()
        self.assertEqual(row["count"], 2)

    # ------------------------------------------------------------------
    # get_usage_summary
    # ------------------------------------------------------------------

    def test_get_usage_summary_empty(self):
        self.assertEqual(self.repo.get_usage_summary(), [])

    def test_get_usage_summary_returns_current_month_only(self):
        with patch.object(self.repo, "_current_year_month", return_value="2026-03"):
            self.repo.increment("recent")

        # Inserir registro de mês anterior diretamente
        self.repo.execute_query(
            "INSERT INTO rate_limit_usage (call_type, year_month, count, limit_value) VALUES (?, ?, ?, ?)",
            ("recent", "2026-02", 5, 120),
        )

        with patch.object(self.repo, "_current_year_month", return_value="2026-03"):
            summary = self.repo.get_usage_summary()

        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["year_month"], "2026-03")

    def test_get_usage_summary_fields(self):
        with patch.object(self.repo, "_current_year_month", return_value="2026-03"):
            self.repo.increment("non_recent")
            summary = self.repo.get_usage_summary()

        self.assertEqual(len(summary), 1)
        entry = summary[0]
        self.assertEqual(entry["call_type"], "non_recent")
        self.assertEqual(entry["year_month"], "2026-03")
        self.assertEqual(entry["count"], 1)
        self.assertEqual(entry["limit_value"], 4)
        self.assertEqual(entry["remaining"], 3)
        self.assertFalse(entry["exceeded"])

    def test_get_usage_summary_multiple_types(self):
        with patch.object(self.repo, "_current_year_month", return_value="2026-03"):
            self.repo.increment("recent")
            self.repo.increment("non_recent")
            summary = self.repo.get_usage_summary()

        call_types = {e["call_type"] for e in summary}
        self.assertEqual(call_types, {"recent", "non_recent"})

    # ------------------------------------------------------------------
    # month isolation
    # ------------------------------------------------------------------

    def test_counters_reset_between_months(self):
        with patch.object(self.repo, "_current_year_month", return_value="2026-02"):
            for _ in range(3):
                self.repo.increment("non_recent")

        with patch.object(self.repo, "_current_year_month", return_value="2026-03"):
            result = self.repo.increment("non_recent")

        self.assertEqual(result["count"], 1)


if __name__ == "__main__":
    unittest.main()
