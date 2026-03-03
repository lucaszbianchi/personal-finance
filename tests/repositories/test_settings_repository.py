import unittest
from repositories.settings_repository import SettingsRepository


class TestSettingsRepository(unittest.TestCase):
    def setUp(self):
        self.repo = SettingsRepository(db_path=":memory:")
        self.key = "test_key"
        # Cria tabela
        self.repo.execute_query(
            """
            CREATE TABLE settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )

    def test_save_and_get_setting(self):
        self.repo.set_value(self.key, "test_value")
        value = self.repo.get_value(self.key)
        self.assertEqual(value, "test_value")

    def test_update_setting(self):
        self.repo.set_value(self.key, "initial")
        self.repo.set_value(self.key, "updated")
        value = self.repo.get_value(self.key)
        self.assertEqual(value, "updated")

    def test_delete_setting(self):
        self.repo.set_value(self.key, "to_delete")
        self.repo.set_value(self.key, None)
        value = self.repo.get_value(self.key)
        self.assertIsNone(value)


if __name__ == "__main__":
    unittest.main()
