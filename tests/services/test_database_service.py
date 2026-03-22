"""Testes para DatabaseService"""

import unittest
from unittest.mock import patch
from services.database_service import reset_and_reseed


class TestDatabaseService(unittest.TestCase):
    """Testes para a função reset_and_reseed"""

    @patch("services.database_service.reset_db")
    def test_reset_and_reseed_calls_reset_db(self, mock_reset_db):
        """Verifica que reset_and_reseed chama reset_db"""
        reset_and_reseed()

        mock_reset_db.assert_called_once()


if __name__ == "__main__":
    unittest.main()
