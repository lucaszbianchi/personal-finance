import unittest
import uuid
from datetime import datetime
from repositories.splitwise_repository import SplitwiseRepository
from models.splitwise import Splitwise


class TestSplitwiseRepository(unittest.TestCase):
    def setUp(self):
        self.repo = SplitwiseRepository(db_path="test-finance.db")
        self.test_id = str(uuid.uuid4())
        # Cria tabela se não existir
        self.repo.execute_query(
            """
            CREATE TABLE IF NOT EXISTS splitwise (
                id TEXT PRIMARY KEY,
                amount REAL,
                date TEXT,
                description TEXT,
                category_id TEXT,
                persons TEXT,
                paid_by TEXT,
                split_info TEXT
            )
            """
        )
        # Garante que a coluna transaction_id existe
        try:
            self.repo.execute_query(
                "ALTER TABLE splitwise ADD COLUMN transaction_id TEXT"
            )
        except Exception:
            pass
        self.repo.execute_query("DELETE FROM splitwise WHERE id = ?", (self.test_id,))

    def test_create_and_get_splitwise(self):
        split = Splitwise(
            splitwise_id=self.test_id,
            amount=100.0,
            date=datetime.now(),
            description="TestDesc",
            category_id="cat123",
            transaction_id="",
        )
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id) VALUES (?, ?, ?, ?, ?, ?)",
            (
                split.splitwise_id,
                split.amount,
                split.date.strftime("%Y-%m-%d"),
                split.description,
                split.category_id,
                split.transaction_id,
            ),
        )
        found = self.repo.get_splitwise_by_id(self.test_id)
        self.assertIsNotNone(found)
        self.assertEqual(found.amount, split.amount)
        self.assertEqual(found.description, split.description)
        self.assertEqual(found.category_id, split.category_id)

    def test_update_splitwise(self):
        split = Splitwise(
            splitwise_id=self.test_id,
            amount=100.0,
            date=datetime.now(),
            description="TestDesc",
            category_id="cat123",
            transaction_id="",
        )
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id) VALUES (?, ?, ?, ?, ?, ?)",
            (
                split.splitwise_id,
                split.amount,
                split.date.strftime("%Y-%m-%d"),
                split.description,
                split.category_id,
                split.transaction_id,
            ),
        )
        self.repo.update_splitwise(self.test_id, "cat999", "txn999")
        found = self.repo.get_splitwise_by_id(self.test_id)
        self.assertEqual(found.category_id, "cat999")
        self.assertEqual(found.transaction_id, "txn999")

    def test_get_unsettled_splitwise(self):
        split = Splitwise(
            splitwise_id=self.test_id,
            amount=100.0,
            date=datetime.now(),
            description="TestDesc",
            category_id="cat123",
            transaction_id="",
        )
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id) VALUES (?, ?, ?, ?, ?, ?)",
            (
                split.splitwise_id,
                split.amount,
                split.date.strftime("%Y-%m-%d"),
                split.description,
                split.category_id,
                split.transaction_id,
            ),
        )
        unsettled = self.repo.get_unsettled_splitwise()
        self.assertTrue(any(s.splitwise_id == self.test_id for s in unsettled))


if __name__ == "__main__":
    unittest.main()
