import unittest
import uuid
from datetime import datetime
from repositories.transaction_repository import TransactionRepository
from models.transaction import BankTransaction


class TestTransactionRepository(unittest.TestCase):
    def setUp(self):
        self.repo = TransactionRepository(db_path="test-finance.db")
        self.test_id = str(uuid.uuid4())
        # Garante que a coluna type existe
        try:
            self.repo.execute_query(
                "ALTER TABLE bank_transactions ADD COLUMN type TEXT"
            )
        except Exception:
            pass
        # Cria tabela se não existir
        self.repo.execute_query(
            """
            CREATE TABLE IF NOT EXISTS bank_transactions (
                id TEXT PRIMARY KEY,
                date TEXT,
                description TEXT,
                amount REAL,
                category_id TEXT,
                type TEXT,
                operation_type TEXT,
                split_info TEXT,
                payment_data TEXT
            )
            """
        )
        self.repo.execute_query(
            "DELETE FROM bank_transactions WHERE id = ?", (self.test_id,)
        )

    def test_create_and_get_bank_transaction(self):
        # Cria categoria de teste
        self.repo.execute_query(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id TEXT PRIMARY KEY,
                name TEXT,
                types TEXT
            )
            """
        )
        self.repo.execute_query(
            "INSERT OR IGNORE INTO categories (id, name, types) VALUES (?, ?, ?)",
            ("cat123", "cat123", '["essencial"]'),
        )
        txn = BankTransaction(
            transaction_id=self.test_id,
            amount=123.45,
            date=datetime.now(),
            description="Test Transaction",
            category_id="cat123",
            type_="debit",
            operation_type="pix",
            split_info=None,
            payment_data=None,
        )
        self.repo.add_bank_transaction(txn)
        found = self.repo.get_bank_transaction_by_id(self.test_id)
        self.assertIsNotNone(found)
        self.assertEqual(found.amount, txn.amount)
        self.assertEqual(found.description, txn.description)
        self.assertEqual(found.category_id, txn.category_id)
        self.assertEqual(found.operation_type, txn.operation_type)

    def test_update_bank_transaction(self):
        # Cria categorias de teste
        self.repo.execute_query(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id TEXT PRIMARY KEY,
                name TEXT,
                types TEXT
            )
            """
        )
        self.repo.execute_query(
            "INSERT OR IGNORE INTO categories (id, name, types) VALUES (?, ?, ?)",
            ("cat123", "cat123", '["essencial"]'),
        )
        self.repo.execute_query(
            "INSERT OR IGNORE INTO categories (id, name, types) VALUES (?, ?, ?)",
            ("cat999", "cat999", '["opcional"]'),
        )
        txn = BankTransaction(
            transaction_id=self.test_id,
            amount=123.45,
            date=datetime.now(),
            description="Test Transaction",
            category_id="cat123",
            type_="debit",
            operation_type="pix",
            split_info=None,
            payment_data=None,
        )
        self.repo.add_bank_transaction(txn)
        # Atualiza apenas descrição e categoria
        updated = self.repo.update_bank_transaction(
            self.test_id, "Updated", "cat999", None
        )
        self.assertTrue(updated)
        found = self.repo.get_bank_transaction_by_id(self.test_id)
        self.assertEqual(found.description, "Updated")
        self.assertEqual(found.category_id, "cat999")

    def test_delete_bank_transaction(self):
        txn = BankTransaction(
            transaction_id=self.test_id,
            amount=123.45,
            date=datetime.now(),
            description="Test Transaction",
            category_id="cat123",
            type_="debit",
            operation_type="pix",
            split_info=None,
            payment_data=None,
        )
        self.repo.add_bank_transaction(txn)
        # Remove diretamente via SQL, pois não há método delete
        self.repo.execute_query(
            "DELETE FROM bank_transactions WHERE id = ?", (self.test_id,)
        )
        with self.assertRaises(ValueError):
            self.repo.get_bank_transaction_by_id(self.test_id)


if __name__ == "__main__":
    unittest.main()
