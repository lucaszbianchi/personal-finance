import unittest
from repositories.category_repository import CategoryRepository


class TestCategoryRepository(unittest.TestCase):
    def setUp(self):
        self.repo = CategoryRepository(db_path="test-finance.db")
        self.test_name = "TestCat"
        # Cria tabelas se não existirem
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
            """
            CREATE TABLE IF NOT EXISTS credit_transactions (
                id TEXT PRIMARY KEY,
                date TEXT,
                description TEXT,
                amount REAL,
                category_id TEXT,
                status TEXT,
                split_info TEXT
            )
        """
        )
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
                split_info TEXT,
                transaction_id TEXT
            )
        """
        )
        # Limpa categoria de teste se existir
        existing_cat = self.repo.get_category_by_name(self.test_name)
        if existing_cat:
            self.repo.delete_category(existing_cat.id)

    def test_create_and_get_category(self):
        cat_id = self.repo.create_category(self.test_name)
        category = self.repo.get_category_by_id(cat_id)
        self.assertIsNotNone(category)
        self.assertEqual(category.name, self.test_name)

    def test_update_category(self):
        # Cria categoria de teste e garante que existe
        cat_id = self.repo.create_category(self.test_name)
        category = self.repo.get_category_by_id(cat_id)
        self.assertIsNotNone(category)
        self.assertEqual(category.name, self.test_name)

        # Atualiza o nome
        new_name = "UpdatedCat"
        new_id = self.repo.update_category(self.test_name, new_name)
        updated = self.repo.get_category_by_id(new_id)
        self.assertIsNotNone(updated)
        self.assertEqual(updated.name, new_name)

    def test_delete_category(self):
        cat_id = self.repo.create_category(self.test_name)
        deleted = self.repo.delete_category(cat_id)
        self.assertTrue(deleted)
        self.assertIsNone(self.repo.get_category_by_id(cat_id))


if __name__ == "__main__":
    unittest.main()
