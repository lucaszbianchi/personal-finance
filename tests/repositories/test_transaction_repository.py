"""Testes para TransactionRepository"""

import unittest
import uuid
from unittest.mock import patch
from repositories.transaction_repository import TransactionRepository
from models.transaction import BankTransaction, CreditTransaction


class TestTransactionRepository(unittest.TestCase):
    """Testes para a classe TransactionRepository"""

    def setUp(self):
        self.repo = TransactionRepository(db_path=":memory:")
        self.test_bank_id = str(uuid.uuid4())
        self.test_credit_id = str(uuid.uuid4())

        # Criar todas as tabelas necessárias
        self._create_test_tables()

    def _create_test_tables(self):
        """Cria todas as tabelas necessárias para os testes"""
        # Tabela bank_transactions
        self.repo.execute_query(
            """
            CREATE TABLE bank_transactions (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                description TEXT,
                amount REAL,
                category_id TEXT,
                type TEXT,
                operation_type TEXT,
                payment_data TEXT,
                excluded INTEGER DEFAULT 0,
                item_id TEXT,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """
        )

        # Tabela credit_transactions
        self.repo.execute_query(
            """
            CREATE TABLE credit_transactions (
                id TEXT PRIMARY KEY,
                date TEXT,
                description TEXT,
                amount REAL,
                category_id TEXT,
                status TEXT,
                excluded INTEGER DEFAULT 0,
                item_id TEXT
            )
        """
        )

        # Tabela investments
        self.repo.execute_query(
            """
            CREATE TABLE investments (
                id TEXT PRIMARY KEY,
                name TEXT,
                amount REAL,
                balance REAL,
                type TEXT,
                subtype TEXT,
                date TEXT,
                due_date TEXT,
                issuer TEXT,
                rate_type TEXT
            )
        """
        )

        # Tabela categories
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

        # Tabela persons
        self.repo.execute_query(
            """
            CREATE TABLE persons (
                id TEXT PRIMARY KEY,
                name TEXT
            )
        """
        )

    def _create_test_category(self, category_id="cat123", name="Test Category"):
        """Helper para criar categoria de teste"""
        self.repo.execute_query(
            "INSERT OR IGNORE INTO categories (id, description) VALUES (?, ?)",
            (category_id, name),
        )

    # Testes para linhas 18-33: get_bank_transactions
    def test_get_bank_transactions(self):
        """Testa get_bank_transactions - linhas 18-33"""
        self._create_test_category()

        # Criar transação de teste
        txn = BankTransaction(
            transaction_id=self.test_bank_id,
            amount=100.50,
            date="2023-01-01",
            description="Test Bank Transaction",
            category_id="cat123",
            type_="debit",
            operation_type="PIX",
            payment_data={"method": "pix"},
        )
        self.repo.add_bank_transaction(txn)

        transactions = self.repo.get_bank_transactions()
        self.assertIsInstance(transactions, list)

        # Verificar se nossa transação está na lista
        found = next(
            (t for t in transactions if t.transaction_id == self.test_bank_id), None
        )
        self.assertIsNotNone(found)
        self.assertEqual(found.amount, 100.50)
        self.assertEqual(found.description, "Test Bank Transaction")

    # Testes para linhas 53-65: get_credit_transactions
    def test_get_credit_transactions(self):
        """Testa get_credit_transactions - linhas 53-65"""
        self._create_test_category()

        # Criar transação de crédito de teste
        credit_txn = CreditTransaction(
            transaction_id=self.test_credit_id,
            amount=200.75,
            date="2023-01-02",
            description="Test Credit Transaction",
            category_id="cat123",
            status="POSTED",
        )
        self.repo.add_credit_transaction(credit_txn)

        transactions = self.repo.get_credit_transactions()
        self.assertIsInstance(transactions, list)

        # Verificar se nossa transação está na lista
        found = next(
            (t for t in transactions if t.transaction_id == self.test_credit_id), None
        )
        self.assertIsNotNone(found)
        self.assertEqual(found.amount, 200.75)
        self.assertEqual(found.status, "POSTED")

    # Testes para linhas 79-83: get_investments
    def test_get_investments(self):
        """Testa get_investments — delega ao InvestmentRepository"""
        from unittest.mock import MagicMock
        from models.investment import Investment

        mock_inv = MagicMock(spec=Investment)
        mock_inv.investment_id = "inv123"
        mock_inv.name = "Test Investment"
        mock_inv.balance = 1000.0

        mock_inv_repo = MagicMock()
        mock_inv_repo.get_investments.return_value = [mock_inv]

        with patch(
            "repositories.transaction_repository.InvestmentRepository",
            return_value=mock_inv_repo,
        ):
            investments = self.repo.get_investments()

        self.assertIsInstance(investments, list)
        self.assertEqual(len(investments), 1)
        self.assertEqual(investments[0].investment_id, "inv123")
        self.assertEqual(investments[0].name, "Test Investment")
        mock_inv_repo.close.assert_called_once()

    # Testes para linhas 110-143: get_bank_transaction_by_id
    def test_get_bank_transaction_by_id(self):
        """Testa get_bank_transaction_by_id - linhas 110-143"""
        self._create_test_category()

        # Criar transação bancária
        bank_txn = BankTransaction(
            transaction_id=self.test_bank_id,
            amount=175.75,
            date="2023-01-03",
            description="Test Bank by ID",
            category_id="cat123",
            type_="debit",
            operation_type="PIX",
            payment_data=None,
        )
        self.repo.add_bank_transaction(bank_txn)

        # Buscar por ID
        found = self.repo.get_bank_transaction_by_id(self.test_bank_id)
        self.assertIsNotNone(found)
        self.assertEqual(found.transaction_id, self.test_bank_id)
        self.assertEqual(found.amount, 175.75)

        # Testar transação inexistente
        with self.assertRaises(ValueError):
            self.repo.get_bank_transaction_by_id("nonexistent")

    # Testes para linhas 147-164: get_credit_transaction_by_id
    def test_get_credit_transaction_by_id(self):
        """Testa get_credit_transaction_by_id - linhas 147-164"""
        self._create_test_category()

        # Criar transação de crédito
        credit_txn = CreditTransaction(
            transaction_id=self.test_credit_id,
            amount=150.25,
            date="2023-01-03",
            description="Test Credit by ID",
            category_id="cat123",
            status="PENDING",
        )
        self.repo.add_credit_transaction(credit_txn)

        # Buscar por ID
        found = self.repo.get_credit_transaction_by_id(self.test_credit_id)
        self.assertIsNotNone(found)
        self.assertEqual(found.transaction_id, self.test_credit_id)
        self.assertEqual(found.amount, 150.25)

        # Testar transação inexistente
        with self.assertRaises(ValueError):
            self.repo.get_credit_transaction_by_id("nonexistent")

    # Testes para linhas 204-218: add_credit_transaction
    def test_add_credit_transaction(self):
        """Testa add_credit_transaction - linhas 204-218"""
        self._create_test_category()

        credit_txn = CreditTransaction(
            transaction_id="test-credit-123",
            amount=75.50,
            date="2023-01-04",
            description="New Credit Transaction",
            category_id="cat123",
            status="POSTED",
        )

        result = self.repo.add_credit_transaction(credit_txn)
        self.assertTrue(result)

        # Verificar se foi realmente inserida
        found = self.repo.get_credit_transaction_by_id("test-credit-123")
        self.assertEqual(found.amount, 75.50)
        self.assertEqual(found.description, "New Credit Transaction")

    def test_bulk_update_category(self):
        """Testa bulk_update_category - atualiza categoria de múltiplas transações"""
        self._create_test_category("cat123")

        txn = BankTransaction(
            transaction_id=self.test_bank_id,
            amount=123.45,
            date="2023-01-01",
            description="Original Transaction",
            category_id=None,
            type_="debit",
            operation_type="PIX",
        )
        self.repo.add_bank_transaction(txn)

        result = self.repo.bulk_update_category("bank", [self.test_bank_id], "cat123")
        self.assertEqual(result, 1)
        updated = self.repo.get_bank_transaction_by_id(self.test_bank_id)
        self.assertEqual(updated.category_id, "cat123")

    def test_bulk_update_category_remove(self):
        """Testa bulk_update_category removendo categoria"""
        self._create_test_category("cat123")

        txn = BankTransaction(
            transaction_id=self.test_bank_id,
            amount=123.45,
            date="2023-01-01",
            description="Original Transaction",
            category_id="cat123",
            type_="debit",
            operation_type="PIX",
        )
        self.repo.add_bank_transaction(txn)

        result = self.repo.bulk_update_category("bank", [self.test_bank_id], None)
        self.assertEqual(result, 1)
        updated = self.repo.get_bank_transaction_by_id(self.test_bank_id)
        self.assertIsNone(updated.category_id)

    # Testes para linhas 312-322: category_in_use
    def test_category_in_use(self):
        """Testa category_in_use - linhas 312-322"""
        self._create_test_category("cat123")
        self._create_test_category("cat999")

        # Criar transação usando categoria
        txn = BankTransaction(
            transaction_id=self.test_bank_id,
            amount=100.0,
            date="2023-01-06",
            description="Category Test",
            category_id="cat123",
            type_="debit",
            operation_type="PIX",
            payment_data=None,
        )
        self.repo.add_bank_transaction(txn)

        # Categoria em uso deve retornar True
        self.assertTrue(self.repo.category_in_use("cat123"))

        # Categoria não usada deve retornar False
        self.assertFalse(self.repo.category_in_use("cat999"))

    # Testes para linhas 334-341: set_excluded
    def test_set_excluded_marks_bank_transaction(self):
        """set_excluded=True marca transação bancária como excluída."""
        self._create_test_category()
        txn = BankTransaction(
            transaction_id=self.test_bank_id,
            amount=100.0,
            date="2023-01-01",
            description="Excluir Banco",
            category_id="cat123",
            type_="debit",
            operation_type="PIX",
        )
        self.repo.add_bank_transaction(txn)

        result = self.repo.set_excluded("bank", self.test_bank_id, True)
        self.assertTrue(result)

        row = self.repo.execute_query(
            "SELECT excluded FROM bank_transactions WHERE id = ?", (self.test_bank_id,)
        ).fetchone()
        self.assertEqual(row["excluded"], 1)

    def test_set_excluded_unmarks_bank_transaction(self):
        """set_excluded=False desmarca transação bancária."""
        self._create_test_category()
        txn = BankTransaction(
            transaction_id=self.test_bank_id,
            amount=100.0,
            date="2023-01-01",
            description="Desmarcar Banco",
            category_id="cat123",
            type_="debit",
            operation_type="PIX",
        )
        self.repo.add_bank_transaction(txn)
        self.repo.set_excluded("bank", self.test_bank_id, True)

        result = self.repo.set_excluded("bank", self.test_bank_id, False)
        self.assertTrue(result)

        row = self.repo.execute_query(
            "SELECT excluded FROM bank_transactions WHERE id = ?", (self.test_bank_id,)
        ).fetchone()
        self.assertEqual(row["excluded"], 0)

    def test_set_excluded_marks_credit_transaction(self):
        """set_excluded funciona para tabela credit."""
        self._create_test_category()
        txn = CreditTransaction(
            transaction_id=self.test_credit_id,
            amount=50.0,
            date="2023-01-02",
            description="Excluir Crédito",
            category_id="cat123",
            status="POSTED",
        )
        self.repo.add_credit_transaction(txn)

        result = self.repo.set_excluded("credit", self.test_credit_id, True)
        self.assertTrue(result)

        row = self.repo.execute_query(
            "SELECT excluded FROM credit_transactions WHERE id = ?", (self.test_credit_id,)
        ).fetchone()
        self.assertEqual(row["excluded"], 1)

    def test_set_excluded_raises_for_invalid_table(self):
        """set_excluded levanta ValueError para tabela inválida."""
        with self.assertRaises(ValueError):
            self.repo.set_excluded("invalid_table", "any-id", True)

    def test_set_excluded_returns_false_for_nonexistent_id(self):
        """set_excluded retorna False quando o ID não existe."""
        result = self.repo.set_excluded("bank", "nonexistent-id", True)
        self.assertFalse(result)

    # Testes para linhas 360-379: upsert_bank_transaction
    @patch.object(TransactionRepository, "_process_pix_person_extraction")
    @patch.object(TransactionRepository, "_process_category_creation")
    def test_upsert_bank_transaction(self, mock_category, mock_pix):
        """Testa upsert_bank_transaction - linhas 360-379"""
        transaction_data = {
            "id": "upsert-test-123",
            "date": "2023-01-09",
            "description": "Upsert Test",
            "amount": 150.0,
            "categoryId": "cat123",
            "type": "debit",
            "operationType": "PIX",
            "paymentData": {"method": "pix"},
        }

        # Mock do método upsert da classe base
        with patch.object(self.repo, "upsert") as mock_upsert:
            mock_upsert.return_value = {"action": "inserted", "id": "upsert-test-123"}

            result = self.repo.upsert_bank_transaction(transaction_data)

            self.assertEqual(result["action"], "inserted")
            mock_upsert.assert_called_once()
            mock_pix.assert_called_once()
            mock_category.assert_called_once()

    # Testes para linhas 392-417: upsert_credit_transaction
    @patch.object(TransactionRepository, "_process_category_creation")
    def test_upsert_credit_transaction(self, mock_category):
        """Testa upsert_credit_transaction - linhas 392-417"""
        transaction_data = {
            "id": "upsert-credit-123",
            "date": "2023-01-10",
            "description": "Upsert Credit Test",
            "amount": 75.0,
            "amountInAccountCurrency": 80.0,  # Deve usar este valor
            "categoryId": "cat123",
            "status": "POSTED",
        }

        # Mock do método upsert da classe base
        with patch.object(self.repo, "upsert") as mock_upsert:
            mock_upsert.return_value = {"action": "updated", "id": "upsert-credit-123"}

            result = self.repo.upsert_credit_transaction(transaction_data)

            self.assertEqual(result["action"], "updated")
            mock_upsert.assert_called_once()
            mock_category.assert_called_once()

            # Verificar se foi usado amountInAccountCurrency
            call_args = mock_upsert.call_args[0][2]  # mapped_data
            self.assertEqual(call_args["amount"], 80.0)

    @patch.object(TransactionRepository, "_process_category_creation")
    def test_upsert_credit_transaction_parses_installment_from_description(self, mock_category):
        """When creditCardMetadata is absent, installment info is parsed from description."""
        transaction_data = {
            "id": "inst-credit-123",
            "date": "2026-03-05",
            "description": "Andreia Antoniazzi Joi 2/10",
            "amount": 150.0,
            "categoryId": "cat123",
            "status": "POSTED",
        }
        with patch.object(self.repo, "upsert") as mock_upsert:
            mock_upsert.return_value = {"action": "inserted"}
            self.repo.upsert_credit_transaction(transaction_data)
            call_args = mock_upsert.call_args[0][2]
            self.assertEqual(call_args["installment_number"], 2)
            self.assertEqual(call_args["total_installments"], 10)

    @patch.object(TransactionRepository, "_process_category_creation")
    def test_upsert_credit_transaction_api_metadata_takes_precedence(self, mock_category):
        """When creditCardMetadata is present, it takes precedence over description parsing."""
        transaction_data = {
            "id": "inst-credit-456",
            "date": "2026-03-05",
            "description": "Compra 2/10",
            "amount": 100.0,
            "categoryId": "cat123",
            "status": "POSTED",
            "creditCardMetadata": {"installmentNumber": 3, "installmentTotalCount": 12},
        }
        with patch.object(self.repo, "upsert") as mock_upsert:
            mock_upsert.return_value = {"action": "inserted"}
            self.repo.upsert_credit_transaction(transaction_data)
            call_args = mock_upsert.call_args[0][2]
            self.assertEqual(call_args["installment_number"], 3)
            self.assertEqual(call_args["total_installments"], 12)

    # Testes para linhas 424-442: _process_pix_person_extraction
    def test_process_pix_person_extraction(self):
        """Testa _process_pix_person_extraction - linhas 424-442"""
        transaction_data = {
            "operationType": "PIX",
            "description": "transferência recebida|João Silva",
            "paymentData": {
                "payer": {"documentNumber": {"type": "CPF", "value": "12345678901"}}
            },
        }

        # Mock do método upsert
        with patch.object(self.repo, "upsert") as mock_upsert:
            mock_upsert.return_value = {"action": "inserted"}

            self.repo._process_pix_person_extraction(transaction_data)

            # Verificar se foi chamado com dados corretos
            mock_upsert.assert_called_once_with(
                "persons",
                "id",
                {"id": "12345678901", "name": "João Silva"},
            )

    def test_process_pix_person_extraction_transferencia_enviada(self):
        """Testa _process_pix_person_extraction para transferência enviada"""
        transaction_data = {
            "operationType": "PIX",
            "description": "transferência enviada|Maria Santos",
            "paymentData": {
                "receiver": {"documentNumber": {"type": "CPF", "value": "98765432100"}}
            },
        }

        # Mock do método upsert
        with patch.object(self.repo, "upsert") as mock_upsert:
            mock_upsert.return_value = {"action": "inserted"}

            self.repo._process_pix_person_extraction(transaction_data)

            # Verificar se foi chamado com dados corretos
            mock_upsert.assert_called_once_with(
                "persons",
                "id",
                {"id": "98765432100", "name": "Maria Santos"},
            )

    def test_process_pix_person_extraction_no_pipe(self):
        """Testa _process_pix_person_extraction sem pipe na descrição"""
        transaction_data = {
            "operationType": "PIX",
            "description": "transferência sem pipe",
            "paymentData": {},
        }

        # Mock do método upsert
        with patch.object(self.repo, "upsert") as mock_upsert:
            self.repo._process_pix_person_extraction(transaction_data)

            # Não deve chamar upsert
            mock_upsert.assert_not_called()

    def test_process_pix_person_extraction_not_pix(self):
        """Testa _process_pix_person_extraction para operação que não é PIX"""
        transaction_data = {
            "operationType": "TED",
            "description": "transferência recebida|João Silva",
            "paymentData": {},
        }

        # Mock do método upsert
        with patch.object(self.repo, "upsert") as mock_upsert:
            self.repo._process_pix_person_extraction(transaction_data)

            # Não deve chamar upsert
            mock_upsert.assert_not_called()

    # Testes para linhas 449-456: _process_category_creation
    def test_process_category_creation(self):
        """Testa _process_category_creation - linhas 449-456"""
        transaction_data = {"categoryId": "new-cat-123", "category": "Nova Categoria"}

        # Mock do método upsert
        with patch.object(self.repo, "upsert") as mock_upsert:
            mock_upsert.return_value = {"action": "inserted"}

            self.repo._process_category_creation(transaction_data)

            # Verificar se foi chamado com dados corretos
            mock_upsert.assert_called_once_with(
                "categories",
                "id",
                {"id": "new-cat-123", "description": "Nova Categoria"},
            )

    def test_process_category_creation_no_category(self):
        """Testa _process_category_creation sem categoryId ou category"""
        transaction_data = {"description": "Sem categoria"}

        # Mock do método upsert
        with patch.object(self.repo, "upsert") as mock_upsert:
            self.repo._process_category_creation(transaction_data)

            # Não deve chamar upsert
            mock_upsert.assert_not_called()

    # Testes para linhas 471-502: create_bank_transaction
    def test_create_bank_transaction(self):
        """Testa create_bank_transaction - linhas 471-502"""
        self._create_test_category()

        transaction = BankTransaction(
            transaction_id="create-test-123",
            amount=250.0,
            date="2023-01-11",
            description="Created Transaction",
            category_id="cat123",
            type_="debit",
            operation_type="PIX",
        )

        result = self.repo.create_bank_transaction(transaction)
        self.assertEqual(result.transaction_id, "create-test-123")
        self.assertEqual(result.amount, 250.0)

        # Testar validações - ID vazio
        invalid_transaction = BankTransaction(
            transaction_id="",  # ID vazio
            amount=100.0,
            date="2023-01-12",
            description="Invalid",
            category_id="cat123",
        )

        with self.assertRaises(ValueError):
            self.repo.create_bank_transaction(invalid_transaction)

        # Testar validação - descrição vazia
        invalid_transaction2 = BankTransaction(
            transaction_id="valid-id",
            amount=100.0,
            date="2023-01-12",
            description="",  # Descrição vazia
            category_id="cat123",
        )

        with self.assertRaises(ValueError):
            self.repo.create_bank_transaction(invalid_transaction2)

        # Testar validação - amount None
        invalid_transaction3 = BankTransaction(
            transaction_id="valid-id-2",
            amount=None,  # Amount None
            date="2023-01-12",
            description="Valid Description",
            category_id="cat123",
        )

        with self.assertRaises(ValueError):
            self.repo.create_bank_transaction(invalid_transaction3)

    # Testes para linhas 519-545: create_credit_transaction
    def test_create_credit_transaction(self):
        """Testa create_credit_transaction - linhas 519-545"""
        self._create_test_category()

        transaction = CreditTransaction(
            transaction_id="create-credit-123",
            amount=180.0,
            date="2023-01-13",
            description="Created Credit Transaction",
            category_id="cat123",
            status="PENDING",
        )

        result = self.repo.create_credit_transaction(transaction)
        self.assertEqual(result.transaction_id, "create-credit-123")
        self.assertEqual(result.amount, 180.0)

        # Testar transação já existente
        with self.assertRaises(ValueError):
            self.repo.create_credit_transaction(transaction)

        # Testar validações - ID vazio
        invalid_transaction = CreditTransaction(
            transaction_id="",  # ID vazio
            amount=100.0,
            date="2023-01-13",
            description="Invalid Credit",
            category_id="cat123",
            status="PENDING",
        )

        with self.assertRaises(ValueError):
            self.repo.create_credit_transaction(invalid_transaction)

        # Testar validação - descrição vazia
        invalid_transaction2 = CreditTransaction(
            transaction_id="valid-credit-id",
            amount=100.0,
            date="2023-01-13",
            description="",  # Descrição vazia
            category_id="cat123",
            status="PENDING",
        )

        with self.assertRaises(ValueError):
            self.repo.create_credit_transaction(invalid_transaction2)

        # Testar validação - amount None
        invalid_transaction3 = CreditTransaction(
            transaction_id="valid-credit-id-2",
            amount=None,  # Amount None
            date="2023-01-13",
            description="Valid Credit Description",
            category_id="cat123",
            status="PENDING",
        )

        with self.assertRaises(ValueError):
            self.repo.create_credit_transaction(invalid_transaction3)

    # Testes para linhas 560-592: delete_bank_transaction
    def test_delete_bank_transaction(self):
        """Testa delete_bank_transaction - linhas 560-592"""
        self._create_test_category()

        # Criar transação para deletar
        transaction = BankTransaction(
            transaction_id="delete-test-123",
            amount=120.0,
            date="2023-01-14",
            description="To Delete",
            category_id="cat123",
            type_="debit",
            operation_type="PIX",
        )
        self.repo.add_bank_transaction(transaction)

        # Deletar transação
        result = self.repo.delete_bank_transaction("delete-test-123")
        self.assertTrue(result)

        # Verificar se foi realmente deletada
        with self.assertRaises(ValueError):
            self.repo.get_bank_transaction_by_id("delete-test-123")

        # Testar deleção de transação inexistente
        with self.assertRaises(ValueError):
            self.repo.delete_bank_transaction("nonexistent")

        # Testar validação de ID vazio
        with self.assertRaises(ValueError):
            self.repo.delete_bank_transaction("")

    # Testes para linhas 607-633: delete_credit_transaction
    def test_delete_credit_transaction(self):
        """Testa delete_credit_transaction - linhas 607-633"""
        self._create_test_category()

        # Criar transação de crédito para deletar
        transaction = CreditTransaction(
            transaction_id="delete-credit-123",
            amount=90.0,
            date="2023-01-15",
            description="Credit To Delete",
            category_id="cat123",
            status="POSTED",
        )
        self.repo.add_credit_transaction(transaction)

        # Deletar transação
        result = self.repo.delete_credit_transaction("delete-credit-123")
        self.assertTrue(result)

        # Verificar se foi realmente deletada
        with self.assertRaises(ValueError):
            self.repo.get_credit_transaction_by_id("delete-credit-123")

    def test_delete_credit_transaction_invalid_id(self):
        """Testa delete_credit_transaction com ID vazio."""
        with self.assertRaises(ValueError):
            self.repo.delete_credit_transaction("")

    # Testes para linhas 642-650: get_operation_types
    def test_get_operation_types(self):
        """Testa get_operation_types - linhas 642-650"""
        self._create_test_category()

        # Criar transações com diferentes tipos de operação
        operations = ["PIX", "TED", "DOC", "CARTAO"]
        for i, op in enumerate(operations):
            transaction = BankTransaction(
                transaction_id=f"op-test-{i}",
                amount=100.0,
                date="2023-01-16",
                description=f"Test {op}",
                category_id="cat123",
                type_="debit",
                operation_type=op,
            )
            self.repo.add_bank_transaction(transaction)

        operation_types = self.repo.get_operation_types()
        self.assertIsInstance(operation_types, list)

        for op in operations:
            self.assertIn(op, operation_types)

    # ── get_distinct_months ──

    def test_get_distinct_months_returns_sorted_list(self):
        """Retorna meses distintos de ambas as tabelas, ordenados, sem excluidos."""
        self.repo.execute_query(
            "INSERT INTO bank_transactions (id, date, excluded) VALUES (?, ?, 0)",
            ("b1", "2025-11-15"),
        )
        self.repo.execute_query(
            "INSERT INTO bank_transactions (id, date, excluded) VALUES (?, ?, 0)",
            ("b2", "2025-12-10"),
        )
        self.repo.execute_query(
            "INSERT INTO credit_transactions (id, date, excluded) VALUES (?, ?, 0)",
            ("c1", "2025-11-20"),
        )
        result = self.repo.get_distinct_months()
        self.assertEqual(result, ["2025-11", "2025-12"])

    def test_get_distinct_months_excludes_excluded_transactions(self):
        """Nao inclui meses cujas transacoes estao excluidas."""
        self.repo.execute_query(
            "INSERT INTO bank_transactions (id, date, excluded) VALUES (?, ?, 1)",
            ("b_excl", "2024-06-01"),
        )
        self.repo.execute_query(
            "INSERT INTO bank_transactions (id, date, excluded) VALUES (?, ?, 0)",
            ("b_ok", "2025-01-01"),
        )
        result = self.repo.get_distinct_months()
        self.assertNotIn("2024-06", result)
        self.assertIn("2025-01", result)

    def test_get_distinct_months_empty_db(self):
        """Retorna lista vazia quando nao ha transacoes."""
        result = self.repo.get_distinct_months()
        self.assertEqual(result, [])

    def test_total_amount_not_selected(self):
        """Ensure no repository SELECT query reads the deprecated total_amount column."""
        import inspect
        import repositories.transaction_repository as mod

        source = inspect.getsource(mod)
        # Remove comment lines to avoid false positives
        lines = [line for line in source.splitlines() if not line.strip().startswith("#")]
        selects = [line for line in lines if "SELECT" in line.upper() and "total_amount" in line.lower()]
        self.assertEqual(selects, [], f"SELECT queries still reference total_amount: {selects}")

    def tearDown(self):
        """Limpeza após os testes"""
        # Com :memory:, o banco é automaticamente destruído quando a conexão é fechada
        self.repo.close()


if __name__ == "__main__":
    unittest.main()
