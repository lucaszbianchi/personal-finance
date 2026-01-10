import unittest
from unittest.mock import MagicMock
from services.person_service import PersonService


class TestPersonService(unittest.TestCase):
    def setUp(self):
        self.mock_repo = MagicMock()
        self.service = PersonService()
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


if __name__ == "__main__":
    unittest.main()
