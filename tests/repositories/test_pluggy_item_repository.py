import unittest
from repositories.pluggy_item_repository import PluggyItemRepository


class TestPluggyItemRepository(unittest.TestCase):
    def setUp(self):
        self.repo = PluggyItemRepository(db_path=":memory:")
        self.repo.execute_query(
            """
            CREATE TABLE pluggy_items (
                item_id TEXT PRIMARY KEY,
                connector_name TEXT,
                status TEXT,
                role TEXT DEFAULT 'bank',
                alias TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
            """
        )

    def tearDown(self):
        self.repo.close()

    # --- upsert_item ---

    def test_upsert_item_insert(self):
        self.repo.upsert_item("item-1", connector_name="Nubank", status="UPDATED", role="bank")

        rows = self.repo.list_all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["item_id"], "item-1")
        self.assertEqual(rows[0]["connector_name"], "Nubank")
        self.assertEqual(rows[0]["status"], "UPDATED")
        self.assertEqual(rows[0]["role"], "bank")

    def test_upsert_item_updates_connector_and_status(self):
        self.repo.upsert_item("item-1", connector_name="Nubank", status="UPDATED")
        self.repo.upsert_item("item-1", connector_name="Nubank Business", status="OUTDATED")

        rows = self.repo.list_all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["connector_name"], "Nubank Business")
        self.assertEqual(rows[0]["status"], "OUTDATED")

    def test_upsert_item_preserves_role_on_update(self):
        """role não é atualizado no ON CONFLICT — deve manter o valor original."""
        self.repo.upsert_item("item-1", role="investment")
        self.repo.upsert_item("item-1", role="bank")

        rows = self.repo.list_all()
        self.assertEqual(rows[0]["role"], "investment")

    def test_upsert_item_nullable_fields(self):
        self.repo.upsert_item("item-1")

        rows = self.repo.list_all()
        self.assertIsNone(rows[0]["connector_name"])
        self.assertIsNone(rows[0]["status"])
        self.assertEqual(rows[0]["role"], "bank")

    # --- get_items_by_role ---

    def test_get_items_by_role_returns_matching(self):
        self.repo.upsert_item("item-bank", role="bank")
        self.repo.upsert_item("item-split", role="investment")

        result = self.repo.get_items_by_role("bank")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["item_id"], "item-bank")

    def test_get_items_by_role_empty(self):
        result = self.repo.get_items_by_role("bank")
        self.assertEqual(result, [])

    def test_get_items_by_role_multiple(self):
        self.repo.upsert_item("item-1", role="bank")
        self.repo.upsert_item("item-2", role="bank")
        self.repo.upsert_item("item-3", role="investment")

        result = self.repo.get_items_by_role("bank")
        self.assertEqual(len(result), 2)
        item_ids = {r["item_id"] for r in result}
        self.assertEqual(item_ids, {"item-1", "item-2"})

    # --- list_all ---

    def test_list_all_empty(self):
        self.assertEqual(self.repo.list_all(), [])

    def test_list_all_returns_all_roles(self):
        self.repo.upsert_item("item-1", role="bank")
        self.repo.upsert_item("item-2", role="investment")

        result = self.repo.list_all()
        self.assertEqual(len(result), 2)

    def test_list_all_returns_dicts(self):
        self.repo.upsert_item("item-1", connector_name="Itaú")

        result = self.repo.list_all()
        self.assertIsInstance(result[0], dict)
        self.assertIn("item_id", result[0])
        self.assertIn("connector_name", result[0])

    # --- update_alias ---

    def test_update_alias_changes_value(self):
        self.repo.upsert_item("item-1", alias="Old Name")
        self.repo.update_alias("item-1", "New Name")
        rows = self.repo.list_all()
        self.assertEqual(rows[0]["alias"], "New Name")

    def test_update_alias_nonexistent_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.repo.update_alias("nao-existe", "Qualquer")
        self.assertIn("nao-existe", str(ctx.exception))

    def test_update_alias_to_none(self):
        self.repo.upsert_item("item-1", alias="Nome")
        self.repo.update_alias("item-1", None)
        rows = self.repo.list_all()
        self.assertIsNone(rows[0]["alias"])

    # --- delete ---

    def test_delete_existing_item(self):
        self.repo.upsert_item("item-1")
        self.repo.delete("item-1")

        self.assertEqual(self.repo.list_all(), [])

    def test_delete_nonexistent_item_does_not_raise(self):
        self.repo.delete("nao-existe")
        self.assertEqual(self.repo.list_all(), [])

    def test_delete_removes_only_target(self):
        self.repo.upsert_item("item-1")
        self.repo.upsert_item("item-2")
        self.repo.delete("item-1")

        result = self.repo.list_all()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["item_id"], "item-2")


if __name__ == "__main__":
    unittest.main()
