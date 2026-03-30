"""Testes para PersonRepository"""

import unittest
import uuid
from unittest.mock import patch
from repositories.person_repository import PersonRepository
from models.person import Person


class TestPersonRepository(unittest.TestCase):
    def setUp(self):
        self.repo = PersonRepository(db_path=":memory:")
        self.test_id = str(uuid.uuid4())
        self.test_id_2 = str(uuid.uuid4())

        self.repo.execute_query(
            """
            CREATE TABLE persons (
                id TEXT PRIMARY KEY,
                name TEXT
            )
            """
        )
        self._cleanup_test_data()

    def _cleanup_test_data(self):
        self.repo.execute_query(
            "DELETE FROM persons WHERE id IN (?, ?)", (self.test_id, self.test_id_2)
        )

    def test_get_all_people(self):
        self.repo.execute_query(
            "INSERT INTO persons (id, name) VALUES (?, ?)",
            (self.test_id, "João Silva"),
        )
        self.repo.execute_query(
            "INSERT INTO persons (id, name) VALUES (?, ?)",
            (self.test_id_2, "Maria Santos"),
        )

        people = self.repo.get_all_people()
        self.assertIsInstance(people, list)
        self.assertGreaterEqual(len(people), 2)

        found_ids = [p.person_id for p in people]
        self.assertIn(self.test_id, found_ids)
        self.assertIn(self.test_id_2, found_ids)

    def test_get_person_by_id_success(self):
        self.repo.execute_query(
            "INSERT INTO persons (id, name) VALUES (?, ?)",
            (self.test_id, "TestUser"),
        )

        found = self.repo.get_person_by_id(self.test_id)
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "TestUser")
        self.assertEqual(found.person_id, self.test_id)

    def test_get_person_by_id_not_found(self):
        found = self.repo.get_person_by_id("nonexistent_id")
        self.assertIsNone(found)

    def test_create_person_success(self):
        person = Person(person_id=self.test_id, name="New Person")

        with patch.object(self.repo, "upsert") as mock_upsert:
            mock_upsert.return_value = {"success": True, "action": "inserted"}
            result = self.repo.create_person(person)
            self.assertEqual(result.person_id, self.test_id)
            self.assertEqual(result.name, "New Person")
            mock_upsert.assert_called_once_with(
                "persons",
                "id",
                {"id": self.test_id, "name": "New Person"},
            )

    def test_create_person_no_id(self):
        person = Person(person_id="", name="Test")
        with self.assertRaises(ValueError) as context:
            self.repo.create_person(person)
        self.assertIn("ID da pessoa é obrigatório", str(context.exception))

    def test_create_person_no_name(self):
        person = Person(person_id=self.test_id, name="")
        with self.assertRaises(ValueError) as context:
            self.repo.create_person(person)
        self.assertIn("Nome da pessoa é obrigatório", str(context.exception))

    def test_create_person_already_exists(self):
        self.repo.execute_query(
            "INSERT INTO persons (id, name) VALUES (?, ?)",
            (self.test_id, "Existing Person"),
        )
        person = Person(person_id=self.test_id, name="New Name")
        with self.assertRaises(ValueError) as context:
            self.repo.create_person(person)
        self.assertIn("já existe", str(context.exception))

    def test_create_person_upsert_failure(self):
        person = Person(person_id=self.test_id, name="Test Person")
        with patch.object(self.repo, "upsert") as mock_upsert:
            mock_upsert.return_value = {"success": False, "error": "Database error"}
            with self.assertRaises(ValueError) as context:
                self.repo.create_person(person)
            self.assertIn("Falha ao criar pessoa", str(context.exception))

    def test_delete_person_success(self):
        self.repo.execute_query(
            "INSERT INTO persons (id, name) VALUES (?, ?)",
            (self.test_id, "To Delete"),
        )
        result = self.repo.delete_person(self.test_id)
        self.assertTrue(result)
        found = self.repo.get_person_by_id(self.test_id)
        self.assertIsNone(found)

    def test_delete_person_no_id(self):
        with self.assertRaises(ValueError) as context:
            self.repo.delete_person("")
        self.assertIn("ID da pessoa é obrigatório", str(context.exception))

    def test_delete_person_not_found(self):
        with self.assertRaises(ValueError) as context:
            self.repo.delete_person("nonexistent_id")
        self.assertIn("não encontrada", str(context.exception))

    def tearDown(self):
        self._cleanup_test_data()


if __name__ == "__main__":
    unittest.main()
