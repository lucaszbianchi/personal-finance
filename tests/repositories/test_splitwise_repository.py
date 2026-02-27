"""Testes para SplitwiseRepository"""

import unittest
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock
from repositories.splitwise_repository import SplitwiseRepository
from models.splitwise import Splitwise


class TestSplitwiseRepository(unittest.TestCase):
    def setUp(self):
        self.repo = SplitwiseRepository(db_path="test-finance.db")
        self.test_id = str(uuid.uuid4())
        self.test_id_2 = str(uuid.uuid4())

        self.repo.execute_query("DROP TABLE IF EXISTS splitwise")
        self.repo.execute_query("DROP TABLE IF EXISTS bank_transactions")
        self.repo.execute_query("DROP TABLE IF EXISTS credit_transactions")
        self.repo.execute_query("DROP TABLE IF EXISTS categories")

        self.repo.execute_query(
            """
            CREATE TABLE splitwise (
                id TEXT PRIMARY KEY,
                amount REAL,
                date TEXT,
                description TEXT,
                category_id TEXT,
                transaction_id TEXT,
                is_invalid INTEGER DEFAULT 0
            )
            """
        )

        self.repo.execute_query(
            """
            CREATE TABLE bank_transactions (
                id TEXT PRIMARY KEY,
                date TEXT,
                description TEXT,
                amount REAL,
                category_id TEXT,
                operation_type TEXT,
                split_info TEXT,
                payment_data TEXT
            )
            """
        )

        self.repo.execute_query(
            """
            CREATE TABLE credit_transactions (
                id TEXT PRIMARY KEY,
                date TEXT,
                description TEXT,
                amount REAL,
                category_id TEXT,
                split_info TEXT,
                status TEXT
            )
            """
        )

        self.repo.execute_query(
            """
            CREATE TABLE categories (
                id TEXT PRIMARY KEY,
                name TEXT
            )
            """
        )

        self._cleanup_test_data()

    def _cleanup_test_data(self):
        """Remove dados de teste existentes"""
        self.repo.execute_query("DELETE FROM splitwise WHERE id IN (?, ?)", (self.test_id, self.test_id_2))
        self.repo.execute_query("DELETE FROM bank_transactions")
        self.repo.execute_query("DELETE FROM credit_transactions")
        self.repo.execute_query("DELETE FROM categories")

    def test_get_all_splitwise(self):
        """Testa get_all_splitwise - linhas 18-39"""
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id, is_invalid) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.test_id, 100.0, "2025-01-01", "Test Splitwise", "cat1", "txn1", 0),
        )
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id, is_invalid) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.test_id_2, 200.0, "2025-01-02", "Invalid Splitwise", "cat2", "txn2", 1),
        )

        result = self.repo.get_all_splitwise()
        self.assertIsInstance(result, list)
        valid_ids = [s.splitwise_id for s in result]
        self.assertIn(self.test_id, valid_ids)
        self.assertNotIn(self.test_id_2, valid_ids)

    def test_get_splitwise_by_transaction_id_found(self):
        """Testa get_splitwise_by_transaction_id encontrando - linhas 41-58"""
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id, is_invalid) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.test_id, 150.0, "2025-01-03", "Transaction Test", "cat3", "txn123", 0),
        )

        result = self.repo.get_splitwise_by_transaction_id("txn123")
        self.assertIsNotNone(result)
        self.assertEqual(result.splitwise_id, self.test_id)
        self.assertEqual(result.transaction_id, "txn123")

    def test_get_splitwise_by_transaction_id_not_found(self):
        """Testa get_splitwise_by_transaction_id não encontrando - linha 58"""
        result = self.repo.get_splitwise_by_transaction_id("nonexistent")
        self.assertIsNone(result)

    def test_get_splitwise_by_id_found(self):
        """Testa get_splitwise_by_id encontrando - linhas 60-75"""
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id, is_invalid) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.test_id, 75.0, "2025-01-04", "ID Test", "cat4", "txn456", 0),
        )

        result = self.repo.get_splitwise_by_id(self.test_id)
        self.assertIsNotNone(result)
        self.assertEqual(result.amount, 75.0)
        self.assertEqual(result.description, "ID Test")

    def test_get_splitwise_by_id_not_found(self):
        """Testa get_splitwise_by_id não encontrando - linha 75"""
        result = self.repo.get_splitwise_by_id("nonexistent")
        self.assertIsNone(result)

    def test_update_splitwise_with_transaction(self):
        """Testa update_splitwise com transaction - linhas 77-89"""
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id, is_invalid) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.test_id, 100.0, "2025-01-05", "Update Test", "old_cat", "", 0),
        )

        self.repo.update_splitwise(self.test_id, "new_cat", "new_txn")

        updated = self.repo.get_splitwise_by_id(self.test_id)
        self.assertEqual(updated.category_id, "new_cat")
        self.assertEqual(updated.transaction_id, "new_txn")

    def test_update_splitwise_with_none_transaction(self):
        """Testa update_splitwise com transaction None - linhas 86-87"""
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id, is_invalid) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.test_id, 100.0, "2025-01-05", "None Test", "cat", "old_txn", 0),
        )

        self.repo.update_splitwise(self.test_id, "updated_cat", None)

        updated = self.repo.get_splitwise_by_id(self.test_id)
        self.assertEqual(updated.category_id, "updated_cat")
        self.assertEqual(updated.transaction_id, "")

    def test_set_transaction_to_splitwise(self):
        """Testa set_transaction_to_splitwise - linhas 91-97"""
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id, is_invalid) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.test_id, 200.0, "2025-01-06", "Set Transaction Test", "", "", 0),
        )

        mock_transaction = MagicMock()
        mock_transaction.category_id = "set_cat"
        mock_transaction.transaction_id = "set_txn"

        result = self.repo.set_transaction_to_splitwise(self.test_id, mock_transaction)
        self.assertTrue(result)

        updated = self.repo.get_splitwise_by_id(self.test_id)
        self.assertEqual(updated.category_id, "set_cat")
        self.assertEqual(updated.transaction_id, "set_txn")

    def test_category_in_use_true(self):
        """Testa category_in_use retornando True - linhas 99-104"""
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id, is_invalid) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.test_id, 50.0, "2025-01-07", "Category Test", "used_cat", "", 0),
        )

        result = self.repo.category_in_use("used_cat")
        self.assertTrue(result)

    def test_category_in_use_false(self):
        """Testa category_in_use retornando False - linha 104"""
        result = self.repo.category_in_use("unused_cat")
        self.assertFalse(result)

    def test_get_unsettled_splitwise(self):
        """Testa get_unsettled_splitwise - linhas 106-125"""
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id, is_invalid) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.test_id, 300.0, "2025-01-08", "Unsettled", "cat", "", 0),
        )
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id, is_invalid) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.test_id_2, 400.0, "2025-01-09", "Settled", "cat", "settled_txn", 0),
        )

        unsettled = self.repo.get_unsettled_splitwise()
        unsettled_ids = [s.splitwise_id for s in unsettled]
        self.assertIn(self.test_id, unsettled_ids)
        self.assertNotIn(self.test_id_2, unsettled_ids)

    def test_upsert_splitwise_transaction(self):
        """Testa upsert_splitwise_transaction - linhas 129-164"""
        transaction_data = {
            "id": self.test_id,
            "date": "2025-01-10",
            "description": "Upsert Test",
            "amount": 250.0,
            "categoryId": "upsert_cat"
        }

        with patch.object(self.repo, 'upsert') as mock_upsert, \
             patch.object(self.repo, '_process_category_creation') as mock_category:
            mock_upsert.return_value = {"action": "inserted", "success": True}

            result = self.repo.upsert_splitwise_transaction(transaction_data)

            mock_upsert.assert_called_once()
            mock_category.assert_called_once_with(transaction_data)
            self.assertEqual(result["action"], "inserted")

    def test_process_category_creation(self):
        """Testa _process_category_creation - linhas 166-178"""
        transaction_data = {
            "categoryId": "proc_cat",
            "category": "Process Category"
        }

        with patch.object(self.repo, 'upsert') as mock_upsert:
            mock_upsert.return_value = {"action": "inserted"}

            self.repo._process_category_creation(transaction_data)

            mock_upsert.assert_called_once_with(
                "categories",
                "id",
                {"id": "proc_cat", "name": "Process Category"},
                strategy="insert_only"
            )

    def test_process_category_creation_no_data(self):
        """Testa _process_category_creation sem dados"""
        transaction_data = {}

        with patch.object(self.repo, 'upsert') as mock_upsert:
            self.repo._process_category_creation(transaction_data)
            mock_upsert.assert_not_called()

    def test_get_bank_transactions_by_date(self):
        """Testa get_bank_transactions_by_date - linhas 180-207"""
        self.repo.execute_query(
            "INSERT INTO bank_transactions (id, date, description, amount, category_id, operation_type, split_info, payment_data) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("bank_txn1", "2025-01-10", "Bank Test", 500.0, "bank_cat", "PIX", '{}', '{}'),
        )

        transactions = self.repo.get_bank_transactions_by_date("2025-01-10")
        self.assertIsInstance(transactions, list)
        self.assertGreater(len(transactions), 0)
        self.assertEqual(transactions[0].transaction_id, "bank_txn1")

    def test_get_credit_transactions_by_date(self):
        """Testa get_credit_transactions_by_date - linhas 209-232"""
        self.repo.execute_query(
            "INSERT INTO credit_transactions (id, date, description, amount, category_id, split_info, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("credit_txn1", "2025-01-11", "Credit Test", 600.0, "credit_cat", '{}', "POSTED"),
        )

        transactions = self.repo.get_credit_transactions_by_date("2025-01-11")
        self.assertIsInstance(transactions, list)
        self.assertGreater(len(transactions), 0)
        self.assertEqual(transactions[0].transaction_id, "credit_txn1")

    def test_update_match_type(self):
        """Testa update_match_type - linhas 234-237"""
        self.repo.execute_query(
            "ALTER TABLE splitwise ADD COLUMN match_type TEXT"
        )
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id, is_invalid) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.test_id, 100.0, "2025-01-12", "Match Test", "cat", "", 0),
        )

        self.repo.update_match_type(self.test_id, "exact_match")

        cursor = self.repo.execute_query("SELECT match_type FROM splitwise WHERE id = ?", (self.test_id,))
        row = cursor.fetchone()
        self.assertEqual(row["match_type"], "exact_match")

    def test_mark_splitwise_invalid(self):
        """Testa mark_splitwise_invalid - linhas 239-246"""
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id, is_invalid) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.test_id, 100.0, "2025-01-13", "Invalid Test", "cat", "", 0),
        )

        result = self.repo.mark_splitwise_invalid(self.test_id)
        self.assertTrue(result)

        updated = self.repo.get_splitwise_by_id(self.test_id)
        self.assertTrue(updated.is_invalid)

    def test_mark_splitwise_invalid_nonexistent(self):
        """Testa mark_splitwise_invalid com ID inexistente"""
        result = self.repo.mark_splitwise_invalid("nonexistent")
        self.assertFalse(result)

    def test_mark_splitwise_valid(self):
        """Testa mark_splitwise_valid - linhas 248-255"""
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id, is_invalid) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.test_id, 100.0, "2025-01-14", "Valid Test", "cat", "", 1),
        )

        result = self.repo.mark_splitwise_valid(self.test_id)
        self.assertTrue(result)

        updated = self.repo.get_splitwise_by_id(self.test_id)
        self.assertFalse(updated.is_invalid)

    def test_mark_splitwise_valid_nonexistent(self):
        """Testa mark_splitwise_valid com ID inexistente"""
        result = self.repo.mark_splitwise_valid("nonexistent")
        self.assertFalse(result)

    def test_update_splitwise_content(self):
        """Testa update_splitwise_content - linhas 257-264"""
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id, is_invalid) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.test_id, 100.0, "2025-01-01", "Content Test", "cat", "", 0),
        )

        result = self.repo.update_splitwise_content(self.test_id, "2025-02-01", 999.0)
        self.assertTrue(result)

        updated = self.repo.get_splitwise_by_id(self.test_id)
        self.assertEqual(updated.amount, 999.0)

    def test_update_splitwise_content_nonexistent(self):
        """Testa update_splitwise_content com ID inexistente"""
        result = self.repo.update_splitwise_content("nonexistent", "2025-01-01", 100.0)
        self.assertFalse(result)

    def test_get_all_splitwise_including_invalid(self):
        """Testa get_all_splitwise_including_invalid - linhas 266-286"""
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id, is_invalid) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.test_id, 100.0, "2025-01-15", "Valid Entry", "cat1", "", 0),
        )
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id, is_invalid) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.test_id_2, 200.0, "2025-01-16", "Invalid Entry", "cat2", "", 1),
        )

        result = self.repo.get_all_splitwise_including_invalid()
        all_ids = [s.splitwise_id for s in result]
        self.assertIn(self.test_id, all_ids)
        self.assertIn(self.test_id_2, all_ids)

    def test_create_splitwise_success(self):
        """Testa create_splitwise com sucesso - linhas 288-334"""
        splitwise = Splitwise(
            splitwise_id=self.test_id,
            amount=123.45,
            date=datetime(2025, 1, 17),
            description="Create Test",
            category_id="create_cat",
            transaction_id="create_txn",
            is_invalid=False
        )

        with patch.object(self.repo, 'upsert') as mock_upsert:
            mock_upsert.return_value = {"success": True, "action": "inserted"}

            result = self.repo.create_splitwise(splitwise)
            self.assertEqual(result.splitwise_id, self.test_id)

    def test_create_splitwise_no_id(self):
        """Testa create_splitwise sem ID - linha 302"""
        splitwise = Splitwise(
            splitwise_id="",
            amount=100.0,
            date=datetime(2025, 1, 18),
            description="No ID Test",
            category_id="cat",
            transaction_id="",
            is_invalid=False
        )

        with self.assertRaises(ValueError) as context:
            self.repo.create_splitwise(splitwise)
        self.assertIn("ID da entrada do Splitwise é obrigatório", str(context.exception))

    def test_create_splitwise_no_description(self):
        """Testa create_splitwise sem descrição - linha 304"""
        splitwise = Splitwise(
            splitwise_id=self.test_id,
            amount=100.0,
            date=datetime(2025, 1, 18),
            description="",
            category_id="cat",
            transaction_id="",
            is_invalid=False
        )

        with self.assertRaises(ValueError) as context:
            self.repo.create_splitwise(splitwise)
        self.assertIn("Descrição é obrigatória", str(context.exception))

    def test_create_splitwise_no_amount(self):
        """Testa create_splitwise sem valor - linha 306"""
        splitwise = Splitwise(
            splitwise_id=self.test_id,
            amount=None,
            date=datetime(2025, 1, 18),
            description="No Amount Test",
            category_id="cat",
            transaction_id="",
            is_invalid=False
        )

        with self.assertRaises(ValueError) as context:
            self.repo.create_splitwise(splitwise)
        self.assertIn("Valor é obrigatório", str(context.exception))

    def test_create_splitwise_already_exists(self):
        """Testa create_splitwise quando já existe - linha 311"""
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id, is_invalid) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.test_id, 100.0, "2025-01-19", "Existing", "cat", "", 0),
        )

        splitwise = Splitwise(
            splitwise_id=self.test_id,
            amount=200.0,
            date=datetime(2025, 1, 19),
            description="Duplicate Test",
            category_id="cat",
            transaction_id="",
            is_invalid=False
        )

        with self.assertRaises(ValueError) as context:
            self.repo.create_splitwise(splitwise)
        self.assertIn("já existe", str(context.exception))

    def test_create_splitwise_upsert_failure(self):
        """Testa create_splitwise quando upsert falha - linha 334"""
        splitwise = Splitwise(
            splitwise_id=self.test_id,
            amount=100.0,
            date=datetime(2025, 1, 20),
            description="Failure Test",
            category_id="cat",
            transaction_id="",
            is_invalid=False
        )

        with patch.object(self.repo, 'upsert') as mock_upsert:
            mock_upsert.return_value = {"success": False, "error": "Database error"}

            with self.assertRaises(ValueError) as context:
                self.repo.create_splitwise(splitwise)
            self.assertIn("Falha ao criar entrada do Splitwise", str(context.exception))

    def test_delete_splitwise_success(self):
        """Testa delete_splitwise com sucesso - linhas 336-365"""
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id, is_invalid) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.test_id, 100.0, "2025-01-21", "Delete Test", "cat", "", 0),
        )

        result = self.repo.delete_splitwise(self.test_id)
        self.assertTrue(result)

        deleted = self.repo.get_splitwise_by_id(self.test_id)
        self.assertIsNone(deleted)

    def test_delete_splitwise_no_id(self):
        """Testa delete_splitwise sem ID - linha 350"""
        with self.assertRaises(ValueError) as context:
            self.repo.delete_splitwise("")
        self.assertIn("ID da entrada do Splitwise é obrigatório", str(context.exception))

    def test_delete_splitwise_not_found(self):
        """Testa delete_splitwise não encontrado - linha 355"""
        with self.assertRaises(ValueError) as context:
            self.repo.delete_splitwise("nonexistent")
        self.assertIn("não encontrada", str(context.exception))

    def test_delete_splitwise_linked_to_transaction(self):
        """Testa delete_splitwise vinculado a transação - linha 360"""
        self.repo.execute_query(
            "INSERT INTO splitwise (id, amount, date, description, category_id, transaction_id, is_invalid) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.test_id, 100.0, "2025-01-22", "Linked Test", "cat", "linked_txn", 0),
        )

        with self.assertRaises(ValueError) as context:
            self.repo.delete_splitwise(self.test_id)
        self.assertIn("está vinculada à transação", str(context.exception))

    def tearDown(self):
        """Limpeza após os testes"""
        self._cleanup_test_data()
        self.repo.execute_query("DELETE FROM splitwise WHERE id LIKE '%test%'")


if __name__ == "__main__":
    unittest.main()