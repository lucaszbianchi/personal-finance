"""Testes para DatabaseService"""

import unittest
from unittest.mock import patch
from services.database_service import reset_and_reseed


class TestDatabaseService(unittest.TestCase):
    """Testes para a função reset_and_reseed"""

    @patch("services.database_service.seed_pluggy_items")
    @patch("services.database_service.reset_db")
    def test_reset_and_reseed_calls_both(self, mock_reset_db, mock_seed):
        """Verifica que reset_and_reseed chama reset_db e seed_pluggy_items"""
        reset_and_reseed()

        mock_reset_db.assert_called_once()
        mock_seed.assert_called_once()

    @patch("services.database_service.seed_pluggy_items")
    @patch("services.database_service.reset_db")
    def test_reset_and_reseed_order(self, mock_reset_db, mock_seed):
        """Verifica que reset_db é chamado antes de seed_pluggy_items"""
        call_order = []
        mock_reset_db.side_effect = lambda: call_order.append("reset_db")
        mock_seed.side_effect = lambda: call_order.append("seed_pluggy_items")

        reset_and_reseed()

        self.assertEqual(call_order, ["reset_db", "seed_pluggy_items"])


if __name__ == "__main__":
    unittest.main()
