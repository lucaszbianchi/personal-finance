import unittest
from unittest.mock import MagicMock, patch
from services.person_service import PersonService


class TestPersonService(unittest.TestCase):
    def setUp(self):
        with patch("services.person_service.PersonRepository"):
            self.service = PersonService()

        self.mock_repo = MagicMock()
        self.service.person_repo = self.mock_repo

    def test_get_all_people(self):
        self.mock_repo.get_all_people.return_value = [
            MagicMock(name="p1"),
            MagicMock(name="p2"),
        ]
        result = self.service.get_all_people()
        self.mock_repo.get_all_people.assert_called()
        self.assertEqual(len(result), 2)

    def test_update_split_info(self):
        self.service.update_split_info("pid", {"is_partner": True})
        self.mock_repo.update_person_split_info.assert_called_with(
            "pid", {"is_partner": True}
        )

    def test_set_partner(self):
        self.service.set_partner("pid")
        self.mock_repo.set_splitwise_partner.assert_called_with("pid")

    def test_mark_settled(self):
        self.service.mark_settled("pid")
        self.mock_repo.mark_person_settled.assert_called_with("pid")

    def test_create_person_missing_id(self):
        with self.assertRaises(ValueError) as context:
            self.service.create_person({})
        self.assertEqual(str(context.exception), "ID da pessoa é obrigatório")

    def test_create_person_missing_name(self):
        with self.assertRaises(ValueError) as context:
            self.service.create_person({"id": "123"})
        self.assertEqual(str(context.exception), "Nome da pessoa é obrigatório")

    def test_create_person_success_default_split_info(self):
        person_data = {"id": "123", "name": "John Doe"}

        mock_created = MagicMock()
        self.mock_repo.create_person.return_value = mock_created

        result = self.service.create_person(person_data)

        self.mock_repo.create_person.assert_called_once()
        args = self.mock_repo.create_person.call_args[0][0]
        self.assertEqual(args.person_id, "123")
        self.assertEqual(args.name, "John Doe")
        self.assertEqual(args.split_info, {})
        self.assertEqual(result, mock_created)

    def test_create_person_name_too_short(self):
        person_data = {"id": "123", "name": "A"}

        with self.assertRaises(ValueError) as context:
            self.service.create_person(person_data)
        self.assertEqual(
            str(context.exception), "Nome da pessoa deve ter pelo menos 2 caracteres"
        )

    def test_create_person_name_whitespace_too_short(self):
        person_data = {"id": "123", "name": " A "}

        with self.assertRaises(ValueError) as context:
            self.service.create_person(person_data)
        self.assertEqual(
            str(context.exception), "Nome da pessoa deve ter pelo menos 2 caracteres"
        )

    def test_create_person_calls_repository(self):
        person_data = {
            "id": "123",
            "name": "John Doe",
            "split_info": {"is_partner": True},
        }

        mock_created = MagicMock()
        self.mock_repo.create_person.return_value = mock_created

        result = self.service.create_person(person_data)

        self.mock_repo.create_person.assert_called_once()
        self.assertEqual(result, mock_created)

    def test_delete_person_missing_id(self):
        with self.assertRaises(ValueError) as context:
            self.service.delete_person("")
        self.assertEqual(str(context.exception), "ID da pessoa é obrigatório")

    def test_delete_person_missing_id_none(self):
        with self.assertRaises(ValueError) as context:
            self.service.delete_person(None)
        self.assertEqual(str(context.exception), "ID da pessoa é obrigatório")

    def test_delete_person_not_found(self):
        self.mock_repo.get_person_by_id.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.delete_person("123")
        self.assertEqual(str(context.exception), "Pessoa com ID 123 não encontrada")

    def test_delete_person_is_partner(self):
        mock_person = MagicMock()
        mock_person.name = "Partner Name"
        mock_person.is_partner.return_value = True
        self.mock_repo.get_person_by_id.return_value = mock_person

        with self.assertRaises(ValueError) as context:
            self.service.delete_person("123")
        self.assertEqual(
            str(context.exception),
            "Não é possível deletar 'Partner Name' pois é o parceiro atual do Splitwise",
        )

    def test_delete_person_not_settled_up(self):
        mock_person = MagicMock()
        mock_person.name = "Person Name"
        mock_person.is_partner.return_value = False
        mock_person.settled_up.return_value = False
        self.mock_repo.get_person_by_id.return_value = mock_person

        with self.assertRaises(ValueError) as context:
            self.service.delete_person("123")
        self.assertEqual(
            str(context.exception),
            "Não é possível deletar 'Person Name' pois possui pendências não quitadas",
        )

    def test_delete_person_calls_repository(self):
        mock_person = MagicMock()
        mock_person.is_partner.return_value = False
        mock_person.settled_up.return_value = True
        self.mock_repo.get_person_by_id.return_value = mock_person
        self.mock_repo.delete_person.return_value = True

        result = self.service.delete_person("123")

        self.mock_repo.delete_person.assert_called_once_with("123")
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
