import unittest
from repositories.category_repository import CategoryRepository


class TestCategoryRepository(unittest.TestCase):
    def setUp(self):
        self.repo = CategoryRepository(db_path=":memory:")
        self.test_name = "TestCat"
        # Criar todas as tabelas necessárias
        self._create_tables()

    def _create_tables(self):
        """Cria todas as tabelas necessárias para os testes"""
        self.repo.execute_query(
            """
            CREATE TABLE categories (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                description_translated TEXT,
                parent_id TEXT,
                parent_description TEXT
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
                type TEXT,
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
                status TEXT,
                split_info TEXT
            )
        """
        )
        self.repo.execute_query(
            """
            CREATE TABLE splitwise (
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

    def test_create_and_get_category(self):
        cat_id = self.repo.create_category(self.test_name)
        category = self.repo.get_category_by_id(cat_id)
        self.assertIsNotNone(category)
        self.assertEqual(category.description, self.test_name)

    def test_update_category(self):
        # Cria categoria de teste e garante que existe
        cat_id = self.repo.create_category(self.test_name)
        category = self.repo.get_category_by_id(cat_id)
        self.assertIsNotNone(category)
        self.assertEqual(category.description, self.test_name)

        # Atualiza o nome
        new_name = "UpdatedCat"
        new_id = self.repo.update_category(self.test_name, new_name)
        updated = self.repo.get_category_by_id(new_id)
        self.assertIsNotNone(updated)
        self.assertEqual(updated.description, new_name)

    def test_delete_category(self):
        cat_id = self.repo.create_category(self.test_name)
        deleted = self.repo.delete_category(cat_id)
        self.assertTrue(deleted)
        self.assertIsNone(self.repo.get_category_by_id(cat_id))

    def test_generate_id_root_empty_db(self):
        """Sem categorias no DB, root deve ser 01000000"""
        id_ = self.repo._generate_category_id(None)
        self.assertEqual(id_, "01000000")

    def test_generate_id_root_with_existing(self):
        """Com root 01000000 já existente, próximo deve ser 02000000"""
        self.repo.create_category("Root1", id_="01000000")
        id_ = self.repo._generate_category_id(None)
        self.assertEqual(id_, "02000000")

    def test_generate_id_level2(self):
        """Filho de 01000000 sem filhos existentes → 01010000"""
        self.repo.create_category("Root1", id_="01000000")
        id_ = self.repo._generate_category_id("01000000")
        self.assertEqual(id_, "01010000")

    def test_generate_id_level2_with_existing(self):
        """Filho de 01000000 com 01010000 já existente → 01020000"""
        self.repo.create_category("Root1", id_="01000000")
        self.repo.create_category("Child1", id_="01010000", parent_id="01000000")
        id_ = self.repo._generate_category_id("01000000")
        self.assertEqual(id_, "01020000")

    def test_generate_id_level3(self):
        """Filho de 01010000 sem netos existentes → 01010001"""
        self.repo.create_category("Root1", id_="01000000")
        self.repo.create_category("Child1", id_="01010000", parent_id="01000000")
        id_ = self.repo._generate_category_id("01010000")
        self.assertEqual(id_, "01010001")

    def test_generate_id_level3_with_existing(self):
        """Filho de 01010000 com 01010001 já existente → 01010002"""
        self.repo.create_category("Root1", id_="01000000")
        self.repo.create_category("Child1", id_="01010000", parent_id="01000000")
        self.repo.create_category("Grand1", id_="01010001", parent_id="01010000")
        id_ = self.repo._generate_category_id("01010000")
        self.assertEqual(id_, "01010002")

    def test_generate_id_invalid_parent_level3(self):
        """parent_id de nível 3 deve lançar ValueError"""
        with self.assertRaises(ValueError):
            self.repo._generate_category_id("01010001")

    def test_generate_id_invalid_format(self):
        """parent_id não-numérico deve lançar ValueError"""
        with self.assertRaises(ValueError):
            self.repo._generate_category_id("abcdefgh")

    def test_create_category_auto_id_root(self):
        """create_category sem id_ e sem parent_id gera ID root válido"""
        cat_id = self.repo.create_category("Nova Root")
        self.assertRegex(cat_id, r"^\d{2}000000$")

    def test_create_category_auto_id_level2(self):
        """create_category sem id_ com parent root gera ID nível 2 válido"""
        self.repo.create_category("Root1", id_="01000000")
        cat_id = self.repo.create_category("Filho", parent_id="01000000")
        self.assertRegex(cat_id, r"^01\d{2}0000$")
        self.assertNotEqual(cat_id[2:4], "00")

    def test_update_category_fields_success(self):
        """update_category_fields retorna True quando categoria existe"""
        cat_id = self.repo.create_category("CatFields", id_="05000000")
        result = self.repo.update_category_fields(
            cat_id,
            description_translated="CatFieldsTranslated",
            parent_id=None,
            parent_description=None,
        )
        self.assertTrue(result)
        updated = self.repo.get_category_by_id(cat_id)
        self.assertEqual(updated.description_translated, "CatFieldsTranslated")

    def test_update_category_fields_not_found(self):
        """update_category_fields retorna False quando categoria não existe"""
        result = self.repo.update_category_fields("99999999", description_translated="X")
        self.assertFalse(result)

    def test_get_children_of_returns_children(self):
        """get_children_of retorna filhos diretos do pai"""
        self.repo.create_category("Root", id_="01000000")
        self.repo.create_category("Child1", id_="01010000", parent_id="01000000", parent_description="Root")
        self.repo.create_category("Child2", id_="01020000", parent_id="01000000", parent_description="Root")
        self.repo.create_category("Other", id_="02000000")

        children = self.repo.get_children_of("01000000")
        child_ids = {c.id for c in children}
        self.assertEqual(child_ids, {"01010000", "01020000"})

    def test_get_children_of_excludes_self_reference(self):
        """Categoria self-parent (grupo raiz) não deve aparecer como filha de si mesma"""
        self.repo.create_category("Root", id_="01000000", parent_id="01000000", parent_description="Root")
        children = self.repo.get_children_of("01000000")
        self.assertEqual(children, [])

    def test_clear_parent_refs(self):
        """clear_parent_refs zera parent_id e parent_description dos filhos"""
        self.repo.create_category("Root", id_="01000000")
        self.repo.create_category("Child1", id_="01010000", parent_id="01000000", parent_description="Root")
        self.repo.create_category("Child2", id_="01020000", parent_id="01000000", parent_description="Root")

        count = self.repo.clear_parent_refs("01000000")
        self.assertEqual(count, 2)

        child1 = self.repo.get_category_by_id("01010000")
        self.assertIsNone(child1.parent_id)
        self.assertIsNone(child1.parent_description)

    def test_update_children_parent(self):
        """update_children_parent atualiza parent_id e parent_description dos filhos"""
        self.repo.create_category("Root", id_="01000000")
        self.repo.create_category("Child1", id_="01010000", parent_id="01000000", parent_description="Root")
        self.repo.create_category("Root2", id_="02000000")

        count = self.repo.update_children_parent("01000000", "02000000", "Root2")
        self.assertEqual(count, 1)

        child1 = self.repo.get_category_by_id("01010000")
        self.assertEqual(child1.parent_id, "02000000")
        self.assertEqual(child1.parent_description, "Root2")

    def test_update_category_preserves_parent_on_rename(self):
        """Renomear categoria preserva parent_id e parent_description no novo registro"""
        self.repo.create_category("Root", id_="01000000", parent_id="01000000", parent_description="Root")
        self.repo.create_category("Child", id_="01010000", parent_id="01000000", parent_description="Root")

        new_id = self.repo.update_category("Child", "ChildRenamed")
        renamed = self.repo.get_category_by_id(new_id)

        self.assertEqual(renamed.parent_id, "01000000")
        self.assertEqual(renamed.parent_description, "Root")

    def test_update_category_propagates_new_parent_to_children(self):
        """Renomear categoria-pai propaga novo parent_id e parent_description para os filhos"""
        self.repo.create_category("Root", id_="01000000", parent_id="01000000", parent_description="Root")
        self.repo.create_category("Child", id_="01010000", parent_id="01000000", parent_description="Root")

        new_id = self.repo.update_category("Root", "RootRenamed")

        child = self.repo.get_category_by_id("01010000")
        self.assertEqual(child.parent_id, new_id)
        self.assertEqual(child.parent_description, "RootRenamed")


if __name__ == "__main__":
    unittest.main()
