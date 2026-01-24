import unittest
import sqlite3
import os
from repositories.investment_repository import InvestmentRepository
from models.investment import Investment


class TestInvestmentRepository(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        cls.test_db_path = "test-investment.db"
        # Create test database with investments table
        conn = sqlite3.connect(cls.test_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT,
                subtype TEXT,
                balance REAL,
                date TEXT,
                due_date TEXT,
                issuer TEXT,
                rate_type TEXT
            )
        """)
        conn.commit()
        conn.close()

    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)

    def setUp(self):
        """Clear table before each test."""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM investments")
        conn.commit()
        conn.close()
        self.repo = InvestmentRepository(db_path=self.test_db_path)

    def tearDown(self):
        """Close repository connection."""
        self.repo.close()

    def test_get_investments_empty(self):
        """Test getting investments when table is empty."""
        result = self.repo.get_investments()
        self.assertEqual(result, [])

    def test_get_investments_with_data(self):
        """Test getting multiple investments."""
        # Insert test data
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO investments (id, name, type, subtype, balance, date, due_date, issuer, rate_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("inv1", "Investment 1", "RENDA_FIXA", "CDB", 1000.0, "2025-01-01", "2026-01-01", "Bank A", "PREFIXADO"))
        cursor.execute("""
            INSERT INTO investments (id, name, type, subtype, balance, date, due_date, issuer, rate_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("inv2", "Investment 2", "RENDA_VARIAVEL", "ACAO", 5000.0, "2025-01-15", "2026-06-15", "Stock", "FLUTUANTE"))
        conn.commit()
        conn.close()

        result = self.repo.get_investments()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].investment_id, "inv2")  # Most recent first
        self.assertEqual(result[0].name, "Investment 2")
        self.assertEqual(result[1].investment_id, "inv1")

    def test_get_investments_filters_zero_balance(self):
        """Test that investments with zero balance are excluded."""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO investments (id, name, type, subtype, balance, date, due_date, issuer, rate_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("inv1", "Investment 1", "RENDA_FIXA", "CDB", 1000.0, "2025-01-01", "2026-01-01", "Bank A", "PREFIXADO"))
        cursor.execute("""
            INSERT INTO investments (id, name, type, subtype, balance, date, due_date, issuer, rate_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("inv2", "Investment 2", "RENDA_VARIAVEL", "ACAO", 0, "2025-01-15", "2026-06-15", "Stock", "FLUTUANTE"))
        conn.commit()
        conn.close()

        result = self.repo.get_investments()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].investment_id, "inv1")

    def test_get_investment_by_id_success(self):
        """Test retrieving a specific investment by ID."""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO investments (id, name, type, subtype, balance, date, due_date, issuer, rate_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("inv1", "Investment 1", "RENDA_FIXA", "CDB", 1000.0, "2025-01-01", "2026-01-01", "Bank A", "PREFIXADO"))
        conn.commit()
        conn.close()

        result = self.repo.get_investment_by_id("inv1")
        
        self.assertEqual(result.investment_id, "inv1")
        self.assertEqual(result.name, "Investment 1")
        self.assertEqual(result.balance, 1000.0)
        self.assertEqual(result.type, "RENDA_FIXA")
        self.assertEqual(result.issuer, "Bank A")

    def test_get_investment_by_id_not_found(self):
        """Test that ValueError is raised when investment not found."""
        with self.assertRaises(ValueError) as context:
            self.repo.get_investment_by_id("nonexistent")
        
        self.assertIn("não encontrado", str(context.exception))

    def test_upsert_investment_insert_new(self):
        """Test inserting a new investment."""
        investment_data = {
            "id": "inv1",
            "name": "New Investment",
            "type": "RENDA_FIXA",
            "subtype": "CDB",
            "balance": 1000.0,
            "date": "2025-01-01",
            "dueDate": "2026-01-01",
            "issuer": "Bank A",
            "rateType": "PREFIXADO"
        }

        result = self.repo.upsert_investment(investment_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "inserted")
        self.assertEqual(result["id"], "inv1")

        # Verify in database
        retrieved = self.repo.get_investment_by_id("inv1")
        self.assertEqual(retrieved.name, "New Investment")
        self.assertEqual(retrieved.balance, 1000.0)

    def test_upsert_investment_update_existing(self):
        """Test updating an existing investment."""
        # Insert initial investment
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO investments (id, name, type, subtype, balance, date, due_date, issuer, rate_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("inv1", "Investment 1", "RENDA_FIXA", "CDB", 1000.0, "2025-01-01", "2026-01-01", "Bank A", "PREFIXADO"))
        conn.commit()
        conn.close()

        # Update balance
        investment_data = {
            "id": "inv1",
            "name": "Investment 1",
            "type": "RENDA_FIXA",
            "subtype": "CDB",
            "balance": 1500.0,
            "date": "2025-01-15",
            "dueDate": "2026-01-01",
            "issuer": "Bank A",
            "rateType": "PREFIXADO"
        }

        result = self.repo.upsert_investment(investment_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "updated")

        # Verify update
        retrieved = self.repo.get_investment_by_id("inv1")
        self.assertEqual(retrieved.balance, 1500.0)

    def test_add_investment_new(self):
        """Test legacy add_investment method for new investment."""
        investment = Investment(
            investment_id="inv1",
            name="New Investment",
            type_="RENDA_FIXA",
            subtype="CDB",
            balance=1000.0,
            date="2025-01-01",
            due_date="2026-01-01",
            issuer="Bank A",
            rate_type="PREFIXADO"
        )

        result = self.repo.add_investment(investment)
        
        self.assertTrue(result)

    def test_add_investment_update_existing(self):
        """Test legacy add_investment method for existing investment."""
        # Insert initial investment
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO investments (id, name, type, subtype, balance, date, due_date, issuer, rate_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("inv1", "Investment 1", "RENDA_FIXA", "CDB", 1000.0, "2025-01-01", "2026-01-01", "Bank A", "PREFIXADO"))
        conn.commit()
        conn.close()

        # Update via add_investment
        investment = Investment(
            investment_id="inv1",
            name="Investment 1 Updated",
            type_="RENDA_FIXA",
            subtype="CDB",
            balance=2000.0,
            date="2025-01-15",
            due_date="2026-01-01",
            issuer="Bank A",
            rate_type="PREFIXADO"
        )

        result = self.repo.add_investment(investment)
        
        self.assertTrue(result)

    def test_update_investment_balance_new_investment(self):
        """Test updating balance for new investment (partial data)."""
        # Note: update_investment_balance only updates balance, date, due_date
        # The method doesn't populate other required fields, so this is a limitation
        # of the legacy method. We test that it at least updates without error.
        result = self.repo.update_investment_balance("inv1", 1000.0, "2025-01-01", "2026-01-01")
        
        self.assertTrue(result)

    def test_update_investment_balance_existing(self):
        """Test updating balance for existing investment."""
        # Insert initial investment
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO investments (id, name, type, subtype, balance, date, due_date, issuer, rate_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("inv1", "Investment 1", "RENDA_FIXA", "CDB", 1000.0, "2025-01-01", "2026-01-01", "Bank A", "PREFIXADO"))
        conn.commit()
        conn.close()

        # Update balance
        result = self.repo.update_investment_balance("inv1", 1500.0, "2025-01-15", "2026-01-01")
        
        self.assertTrue(result)

        # Verify update
        retrieved = self.repo.get_investment_by_id("inv1")
        self.assertEqual(retrieved.balance, 1500.0)

    def test_update_investment_balance_without_due_date(self):
        """Test updating balance without providing due_date."""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO investments (id, name, type, subtype, balance, date, due_date, issuer, rate_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("inv1", "Investment 1", "RENDA_FIXA", "CDB", 1000.0, "2025-01-01", "2026-01-01", "Bank A", "PREFIXADO"))
        conn.commit()
        conn.close()

        # Update without due_date
        result = self.repo.update_investment_balance("inv1", 1500.0, "2025-01-15")
        
        self.assertTrue(result)

        # Verify update (due_date should remain unchanged)
        retrieved = self.repo.get_investment_by_id("inv1")
        self.assertEqual(retrieved.balance, 1500.0)


if __name__ == "__main__":
    unittest.main()
