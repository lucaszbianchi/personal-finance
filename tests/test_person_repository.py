import unittest
import uuid
from repositories.person_repository import PersonRepository
from models.person import Person


class TestPersonRepository(unittest.TestCase):
    def setUp(self):
        self.repo = PersonRepository(db_path="test-finance.db")
        self.test_id = str(uuid.uuid4())
        # Cria tabela se não existir
        self.repo.execute_query(
            """
            CREATE TABLE IF NOT EXISTS persons (
                id TEXT PRIMARY KEY,
                name TEXT,
                split_info TEXT
            )
            """
        )
        self.repo.execute_query("DELETE FROM persons WHERE id = ?", (self.test_id,))

    def test_create_and_get_person(self):
        person = Person(person_id=self.test_id, name="TestUser")
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (person.person_id, person.name, "{}"),
        )
        found = self.repo.get_person_by_id(self.test_id)
        self.assertIsNotNone(found)
        self.assertEqual(found.name, person.name)
        self.assertEqual(found.person_id, person.person_id)

    def test_update_person_split_info(self):
        person = Person(person_id=self.test_id, name="TestUser")
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (person.person_id, person.name, "{}"),
        )
        split_info = {"is_partner": True}
        updated = self.repo.update_person_split_info(self.test_id, split_info)
        self.assertTrue(updated)
        found = self.repo.get_person_by_id(self.test_id)
        self.assertTrue(found.is_partner())

    def test_set_splitwise_partner(self):
        person = Person(person_id=self.test_id, name="TestUser")
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (person.person_id, person.name, "{}"),
        )
        self.repo.set_splitwise_partner(self.test_id)
        found = self.repo.get_person_by_id(self.test_id)
        self.assertTrue(found.is_partner())

    def test_mark_person_settled(self):
        person = Person(person_id=self.test_id, name="TestUser")
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (person.person_id, person.name, "{}"),
        )
        result = self.repo.mark_person_settled(self.test_id)
        self.assertTrue(result)
        found = self.repo.get_person_by_id(self.test_id)
        self.assertTrue(found.settled_up())

    def test_get_partner_and_pending_settlements(self):
        person = Person(person_id=self.test_id, name="TestUser")
        # Limpa a tabela antes do teste
        self.repo.execute_query("DELETE FROM persons", ())
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (person.person_id, person.name, "{}"),
        )
        self.repo.set_splitwise_partner(self.test_id)
        partner = self.repo.get_partner()
        self.assertIsNotNone(partner)
        self.assertEqual(partner.person_id, self.test_id)
        pending = self.repo.get_pending_settlements()
        self.assertTrue(any(p.person_id == self.test_id for p in pending))


if __name__ == "__main__":
    unittest.main()
