"""
Testes para BaseRepository - método upsert genérico.
"""

import unittest
import json
from repositories.base_repository import BaseRepository


class TestBaseRepository(unittest.TestCase):
    def setUp(self):
        """Cria banco de teste em memória para cada teste"""
        self.repo = BaseRepository(db_path=":memory:")

        # Cria tabela de teste
        self.repo.execute_query(
            """
            CREATE TABLE test_table (
                id TEXT PRIMARY KEY,
                name TEXT,
                data TEXT,
                status TEXT,
                balance REAL
            )
        """
        )

    def tearDown(self):
        """Limpeza após os testes"""
        # Com :memory:, o banco é automaticamente destruído quando a conexão é fechada
        self.repo.close()

    def test_upsert_insert_only_new(self):
        """Testa insert_only com novo registro"""
        data = {"id": "test_3", "name": "Insert Only Test", "status": "new"}

        result = self.repo.upsert("test_table", "id", data)

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "inserted")
        self.assertEqual(result["affected_rows"], 1)

    def test_upsert_insert_only_existing(self):
        """Testa insert_only com registro existente (deve ignorar)"""
        # Insere registro inicial
        initial_data = {"id": "test_4", "name": "Original Name", "status": "original"}
        self.repo.upsert("test_table", "id", initial_data)

        # Tenta inserir novamente (deve ignorar)
        duplicate_data = {"id": "test_4", "name": "New Name", "status": "new"}

        result = self.repo.upsert(
            "test_table", "id", duplicate_data
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "ignored")
        self.assertEqual(result["affected_rows"], 0)

        # Verifica que dados originais foram preservados
        cursor = self.repo.execute_query(
            "SELECT * FROM test_table WHERE id = ?", ("test_4",)
        )
        row = cursor.fetchone()
        self.assertEqual(row["name"], "Original Name")
        self.assertEqual(row["status"], "original")

    def test_upsert_json_serialization(self):
        """Testa serialização automática de JSON"""
        data = {
            "id": "test_5",
            "name": "JSON Test",
            "data": {"key": "value", "nested": {"array": [1, 2, 3]}},  # Dict para JSON
            "status": "active",
        }

        result = self.repo.upsert("test_table", "id", data)

        self.assertTrue(result["success"])

        # Verifica que JSON foi serializado
        cursor = self.repo.execute_query(
            "SELECT data FROM test_table WHERE id = ?", ("test_5",)
        )
        row = cursor.fetchone()
        stored_data = json.loads(row["data"])
        self.assertEqual(stored_data["key"], "value")
        self.assertEqual(stored_data["nested"]["array"], [1, 2, 3])

    def test_upsert_missing_id(self):
        """Testa dados sem ID obrigatório"""
        data = {"name": "Test without ID"}

        with self.assertRaises(ValueError):
            self.repo.upsert("test_table", "id", data)


if __name__ == "__main__":
    unittest.main()
