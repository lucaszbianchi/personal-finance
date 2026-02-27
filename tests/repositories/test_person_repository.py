"""Testes para PersonRepository"""

import unittest
import uuid
from unittest.mock import patch
from repositories.person_repository import PersonRepository
from models.person import Person


class TestPersonRepository(unittest.TestCase):
    def setUp(self):
        self.repo = PersonRepository(db_path="test-finance.db")
        self.test_id = str(uuid.uuid4())
        self.test_id_2 = str(uuid.uuid4())

        # Cria tabela com estrutura correta incluindo split_info
        self.repo.execute_query("DROP TABLE IF EXISTS persons")
        self.repo.execute_query(
            """
            CREATE TABLE persons (
                id TEXT PRIMARY KEY,
                name TEXT,
                split_info TEXT
            )
            """
        )
        # Criar tabelas auxiliares para testes de integridade
        self.repo.execute_query(
            """
            CREATE TABLE IF NOT EXISTS bank_transactions (
                id TEXT PRIMARY KEY,
                split_info TEXT
            )
            """
        )
        self.repo.execute_query(
            """
            CREATE TABLE IF NOT EXISTS splitwise (
                id TEXT PRIMARY KEY,
                transaction_id TEXT
            )
            """
        )
        self._cleanup_test_data()

    def _cleanup_test_data(self):
        """Remove dados de teste existentes"""
        self.repo.execute_query(
            "DELETE FROM persons WHERE id IN (?, ?)", (self.test_id, self.test_id_2)
        )
        self.repo.execute_query("DELETE FROM bank_transactions")
        self.repo.execute_query("DELETE FROM splitwise")

    def test_get_all_people(self):
        """Testa get_all_people - linhas 13-24"""
        # Criar pessoas de teste
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (self.test_id, "João Silva", '{"is_partner": true}'),
        )
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (self.test_id_2, "Maria Santos", "{}"),
        )

        people = self.repo.get_all_people()
        self.assertIsInstance(people, list)
        self.assertGreaterEqual(len(people), 2)

        # Verificar se as pessoas foram retornadas corretamente
        found_ids = [p.person_id for p in people]
        self.assertIn(self.test_id, found_ids)
        self.assertIn(self.test_id_2, found_ids)

    def test_get_all_people_empty_split_info(self):
        """Testa get_all_people com split_info vazio ou None - linhas 21"""
        # Pessoa sem split_info
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (self.test_id, "Test User", None),
        )

        people = self.repo.get_all_people()
        found = next((p for p in people if p.person_id == self.test_id), None)
        self.assertIsNotNone(found)
        self.assertEqual(found.split_info, {})

    def test_get_person_by_id_success(self):
        """Testa get_person_by_id com sucesso - linhas 26-37"""
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (self.test_id, "TestUser", '{"test": "data"}'),
        )

        found = self.repo.get_person_by_id(self.test_id)
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "TestUser")
        self.assertEqual(found.person_id, self.test_id)
        self.assertEqual(found.split_info, {"test": "data"})

    def test_get_person_by_id_not_found(self):
        """Testa get_person_by_id quando não encontra - linha 37"""
        found = self.repo.get_person_by_id("nonexistent_id")
        self.assertIsNone(found)

    def test_get_person_by_id_empty_split_info(self):
        """Testa get_person_by_id com split_info None - linha 35"""
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (self.test_id, "TestUser", None),
        )

        found = self.repo.get_person_by_id(self.test_id)
        self.assertIsNotNone(found)
        self.assertEqual(found.split_info, {})

    def test_update_person_split_info_success(self):
        """Testa update_person_split_info com sucesso - linhas 39-43"""
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (self.test_id, "TestUser", "{}"),
        )

        split_info = {"is_partner": True, "settled_up": False}
        updated = self.repo.update_person_split_info(self.test_id, split_info)
        self.assertTrue(updated)

        # Verificar se foi realmente atualizado
        found = self.repo.get_person_by_id(self.test_id)
        self.assertEqual(found.split_info, split_info)

    def test_update_person_split_info_not_found(self):
        """Testa update_person_split_info quando pessoa não existe - linha 42"""
        result = self.repo.update_person_split_info("nonexistent", {"test": True})
        self.assertFalse(result)

    def test_set_splitwise_partner_success(self):
        """Testa set_splitwise_partner com sucesso - linhas 45-52"""
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (self.test_id, "TestUser", "{}"),
        )

        self.repo.set_splitwise_partner(self.test_id)
        found = self.repo.get_person_by_id(self.test_id)
        self.assertTrue(found.is_partner())

    def test_set_splitwise_partner_not_found(self):
        """Testa set_splitwise_partner quando pessoa não existe - linha 49"""
        with self.assertRaises(ValueError) as context:
            self.repo.set_splitwise_partner("nonexistent_id")
        self.assertIn("não encontrada", str(context.exception))

    def test_set_splitwise_partner_preserves_existing_info(self):
        """Testa se set_splitwise_partner preserva informações existentes - linhas 50-52"""
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (self.test_id, "TestUser", '{"existing_key": "existing_value"}'),
        )

        self.repo.set_splitwise_partner(self.test_id)
        found = self.repo.get_person_by_id(self.test_id)
        self.assertTrue(found.is_partner())
        self.assertEqual(found.split_info["existing_key"], "existing_value")

    def test_mark_person_settled_success(self):
        """Testa mark_person_settled com sucesso - linhas 54-60"""
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (self.test_id, "TestUser", "{}"),
        )

        result = self.repo.mark_person_settled(self.test_id)
        self.assertTrue(result)
        found = self.repo.get_person_by_id(self.test_id)
        self.assertTrue(found.settled_up())

    def test_mark_person_settled_not_found(self):
        """Testa mark_person_settled quando pessoa não existe - linha 58"""
        with self.assertRaises(ValueError) as context:
            self.repo.mark_person_settled("nonexistent_id")
        self.assertIn("não encontrada", str(context.exception))

    def test_get_partner_success(self):
        """Testa get_partner quando existe parceiro - linhas 62-65"""
        # Limpar dados existentes
        self.repo.execute_query("DELETE FROM persons")

        # Criar pessoa parceira
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (self.test_id, "Partner User", '{"is_partner": true}'),
        )

        partner = self.repo.get_partner()
        self.assertIsNotNone(partner)
        self.assertEqual(partner.person_id, self.test_id)
        self.assertTrue(partner.is_partner())

    def test_get_partner_none(self):
        """Testa get_partner quando não há parceiros - linha 65"""
        # Limpar dados existentes
        self.repo.execute_query("DELETE FROM persons")

        # Criar pessoa não parceira
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (self.test_id, "Regular User", "{}"),
        )

        partner = self.repo.get_partner()
        self.assertIsNone(partner)

    def test_get_partner_first_partner_returned(self):
        """Testa se get_partner retorna o primeiro parceiro quando há múltiplos - linha 65"""
        # Limpar dados existentes
        self.repo.execute_query("DELETE FROM persons")

        # Criar dois parceiros
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (self.test_id, "First Partner", '{"is_partner": true}'),
        )
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (self.test_id_2, "Second Partner", '{"is_partner": true}'),
        )

        partner = self.repo.get_partner()
        self.assertIsNotNone(partner)
        self.assertTrue(partner.is_partner())

    def test_get_pending_settlements_with_people(self):
        """Testa get_pending_settlements com pessoas - linhas 67-72"""
        # Limpar dados existentes
        self.repo.execute_query("DELETE FROM persons")

        # Pessoa não settled_up (pendente)
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (self.test_id, "Pending User", '{"is_partner": true}'),
        )
        # Pessoa settled_up (não pendente)
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (self.test_id_2, "Settled User", '{"settled_up": true}'),
        )

        pending = self.repo.get_pending_settlements()
        self.assertIsInstance(pending, list)
        pending_ids = [p.person_id for p in pending]
        self.assertIn(self.test_id, pending_ids)
        self.assertNotIn(self.test_id_2, pending_ids)

    def test_get_pending_settlements_empty(self):
        """Testa get_pending_settlements quando não há pessoas - linha 71"""
        # Limpar todos os dados
        self.repo.execute_query("DELETE FROM persons")

        pending = self.repo.get_pending_settlements()
        self.assertEqual(pending, [])

    def test_create_person_success(self):
        """Testa create_person com sucesso - linhas 74-109"""
        person = Person(
            person_id=self.test_id, name="New Person", split_info={"test": "data"}
        )

        with patch.object(self.repo, "upsert") as mock_upsert:
            mock_upsert.return_value = {"success": True, "action": "inserted"}

            result = self.repo.create_person(person)
            self.assertEqual(result.person_id, self.test_id)
            self.assertEqual(result.name, "New Person")

            # Verificar se upsert foi chamado corretamente
            mock_upsert.assert_called_once_with(
                "persons",
                "id",
                {
                    "id": self.test_id,
                    "name": "New Person",
                    "split_info": {"test": "data"},
                },
                strategy="insert_only",
            )

    def test_create_person_no_id(self):
        """Testa create_person sem ID - linha 88"""
        person = Person(person_id="", name="Test")

        with self.assertRaises(ValueError) as context:
            self.repo.create_person(person)
        self.assertIn("ID da pessoa é obrigatório", str(context.exception))

    def test_create_person_no_name(self):
        """Testa create_person sem nome - linha 90"""
        person = Person(person_id=self.test_id, name="")

        with self.assertRaises(ValueError) as context:
            self.repo.create_person(person)
        self.assertIn("Nome da pessoa é obrigatório", str(context.exception))

    def test_create_person_already_exists(self):
        """Testa create_person quando pessoa já existe - linha 95"""
        # Criar pessoa existente
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (self.test_id, "Existing Person", "{}"),
        )

        person = Person(person_id=self.test_id, name="New Name")

        with self.assertRaises(ValueError) as context:
            self.repo.create_person(person)
        self.assertIn("já existe", str(context.exception))

    def test_create_person_empty_split_info(self):
        """Testa create_person com split_info vazio - linha 101"""
        person = Person(person_id=self.test_id, name="Test Person")

        with patch.object(self.repo, "upsert") as mock_upsert:
            mock_upsert.return_value = {"success": True, "action": "inserted"}

            result = self.repo.create_person(person)

            # Verificar se split_info vazio foi convertido para {}
            call_args = mock_upsert.call_args[0][2]
            self.assertEqual(call_args["split_info"], {})

    def test_create_person_upsert_failure(self):
        """Testa create_person quando upsert falha - linha 109"""
        person = Person(person_id=self.test_id, name="Test Person")

        with patch.object(self.repo, "upsert") as mock_upsert:
            mock_upsert.return_value = {"success": False, "error": "Database error"}

            with self.assertRaises(ValueError) as context:
                self.repo.create_person(person)
            self.assertIn("Falha ao criar pessoa", str(context.exception))

    def test_delete_person_success(self):
        """Testa delete_person com sucesso - linhas 111-149"""
        # Criar pessoa para deletar
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (self.test_id, "To Delete", "{}"),
        )

        result = self.repo.delete_person(self.test_id)
        self.assertTrue(result)

        # Verificar se foi realmente deletada
        found = self.repo.get_person_by_id(self.test_id)
        self.assertIsNone(found)

    def test_delete_person_no_id(self):
        """Testa delete_person sem ID - linha 125"""
        with self.assertRaises(ValueError) as context:
            self.repo.delete_person("")
        self.assertIn("ID da pessoa é obrigatório", str(context.exception))

    def test_delete_person_not_found(self):
        """Testa delete_person quando pessoa não existe - linha 130"""
        with self.assertRaises(ValueError) as context:
            self.repo.delete_person("nonexistent_id")
        self.assertIn("não encontrada", str(context.exception))

    def test_delete_person_referenced_in_splitwise(self):
        """Testa delete_person quando pessoa está referenciada - linha 144"""
        # Criar pessoa
        self.repo.execute_query(
            "INSERT INTO persons (id, name, split_info) VALUES (?, ?, ?)",
            (self.test_id, "Referenced Person", "{}"),
        )

        # Criar transação que referencia a pessoa
        self.repo.execute_query(
            "INSERT INTO bank_transactions (id, split_info) VALUES (?, ?)",
            ("txn123", f'{{"person_id":"{self.test_id}"}}'),
        )

        # Criar entrada no splitwise que referencia a transação
        self.repo.execute_query(
            "INSERT INTO splitwise (id, transaction_id) VALUES (?, ?)",
            ("split123", "txn123"),
        )

        with self.assertRaises(ValueError) as context:
            self.repo.delete_person(self.test_id)
        self.assertIn("está sendo referenciada", str(context.exception))

    def tearDown(self):
        """Limpeza após os testes"""
        self._cleanup_test_data()
        # Limpar todas as tabelas de teste
        self.repo.execute_query("DELETE FROM persons WHERE id LIKE '%test%'")


if __name__ == "__main__":
    unittest.main()
