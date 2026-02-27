"""Testes para TransactionRepository"""
import unittest
import uuid
from unittest.mock import patch
from repositories.transaction_repository import TransactionRepository
from models.transaction import BankTransaction, CreditTransaction


class TestTransactionRepository(unittest.TestCase):
    """Testes para a classe TransactionRepository"""
    def setUp(self):
        self.repo = TransactionRepository(db_path="test-finance.db")
        self.test_bank_id = str(uuid.uuid4())
        self.test_credit_id = str(uuid.uuid4())

        # Criar todas as tabelas necessárias
        self._create_test_tables()

        # Limpar dados de teste
        self._cleanup_test_data()

    def _create_test_tables(self):
        """Cria todas as tabelas necessárias para os testes"""
        # Remover tabela existente e recriar
        self.repo.execute_query("DROP TABLE IF EXISTS bank_transactions")

        # Tabela bank_transactions
        self.repo.execute_query("""
            CREATE TABLE bank_transactions (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                description TEXT,
                amount REAL,
                category_id TEXT,
                type TEXT,
                operation_type TEXT,
                split_info TEXT,
                payment_data TEXT,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)

        # Remover tabela existente e recriar
        self.repo.execute_query("DROP TABLE IF EXISTS credit_transactions")

        # Tabela credit_transactions
        self.repo.execute_query("""
            CREATE TABLE credit_transactions (
                id TEXT PRIMARY KEY,
                date TEXT,
                description TEXT,
                amount REAL,
                category_id TEXT,
                status TEXT
            )
        """)

        # Remover tabela existente e recriar
        self.repo.execute_query("DROP TABLE IF EXISTS investments")

        # Tabela investments
        self.repo.execute_query("""
            CREATE TABLE investments (
                id TEXT PRIMARY KEY,
                name TEXT,
                balance REAL,
                type TEXT,
                subtype TEXT,
                date TEXT,
                due_date TEXT,
                issuer TEXT,
                rate_type TEXT
            )
        """)

        # Remover tabela existente e recriar
        self.repo.execute_query("DROP TABLE IF EXISTS categories")

        # Tabela categories
        self.repo.execute_query("""
            CREATE TABLE categories (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                types TEXT
            )
        """)

        # Remover tabela existente e recriar
        self.repo.execute_query("DROP TABLE IF EXISTS splitwise")

        # Tabela splitwise
        self.repo.execute_query("""
            CREATE TABLE splitwise (
                id TEXT PRIMARY KEY,
                transaction_id TEXT,
                amount REAL
            )
        """)

        # Remover tabela existente e recriar
        self.repo.execute_query("DROP TABLE IF EXISTS persons")

        # Tabela persons
        self.repo.execute_query("""
            CREATE TABLE persons (
                id TEXT PRIMARY KEY,
                name TEXT
            )
        """)

    def _cleanup_test_data(self):
        """Remove dados de teste existentes"""
        self.repo.execute_query("DELETE FROM bank_transactions WHERE id IN (?, ?)",
                               (self.test_bank_id, "test-bank-123"))
        self.repo.execute_query("DELETE FROM credit_transactions WHERE id IN (?, ?, ?)",
                               (self.test_credit_id, "test-credit-123", "create-credit-123"))
        self.repo.execute_query("DELETE FROM categories WHERE id IN ('cat123', 'cat999')")
        self.repo.execute_query("DELETE FROM splitwise WHERE transaction_id IN (?, ?)",
                               (self.test_bank_id, self.test_credit_id))

    def _create_test_category(self, category_id="cat123", name="Test Category"):
        """Helper para criar categoria de teste"""
        self.repo.execute_query(
            "INSERT OR IGNORE INTO categories (id, name) VALUES (?, ?)",
            (category_id, name)
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
            split_info={"split": True},
            payment_data={"method": "pix"}
        )
        self.repo.add_bank_transaction(txn)

        transactions = self.repo.get_bank_transactions()
        self.assertIsInstance(transactions, list)

        # Verificar se nossa transação está na lista
        found = next((t for t in transactions if t.transaction_id == self.test_bank_id), None)
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
            status="POSTED"
        )
        self.repo.add_credit_transaction(credit_txn)

        transactions = self.repo.get_credit_transactions()
        self.assertIsInstance(transactions, list)

        # Verificar se nossa transação está na lista
        found = next((t for t in transactions if t.transaction_id == self.test_credit_id), None)
        self.assertIsNotNone(found)
        self.assertEqual(found.amount, 200.75)
        self.assertEqual(found.status, "POSTED")

    # Testes para linhas 79-95: get_investments
    def test_get_investments(self):
        """Testa get_investments - linhas 79-95"""
        # Inserir investimento de teste
        self.repo.execute_query("""
            INSERT INTO investments (id, name, balance, type, subtype, date,
            due_date, issuer, rate_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("inv123", "Test Investment", 1000.0, "CDB", "Pré-fixado",
              "2023-01-01", "2024-01-01", "Test Bank", "PRE"))

        investments = self.repo.get_investments()
        self.assertIsInstance(investments, list)
        self.assertGreater(len(investments), 0)

        # Verificar se nosso investimento está na lista
        found = next((i for i in investments if i.investment_id == "inv123"), None)
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "Test Investment")
        self.assertEqual(found.balance, 1000.0)

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
            split_info=None,
            payment_data=None
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
            status="PENDING"
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
            status="POSTED"
        )

        result = self.repo.add_credit_transaction(credit_txn)
        self.assertTrue(result)

        # Verificar se foi realmente inserida
        found = self.repo.get_credit_transaction_by_id("test-credit-123")
        self.assertEqual(found.amount, 75.50)
        self.assertEqual(found.description, "New Credit Transaction")

    # Testes para linhas 226-264: update_bank_transaction (CORRIGIDO)
    def test_update_bank_transaction(self):
        """Testa update_bank_transaction - linhas 226-264"""
        self._create_test_category("cat123")
        self._create_test_category("cat999", "Updated Category")

        # Criar transação inicial
        txn = BankTransaction(
            transaction_id=self.test_bank_id,
            amount=123.45,
            date="2023-01-01",
            description="Original Transaction",
            category_id="cat123",
            type_="debit",
            operation_type="PIX",
            split_info=None,
            payment_data=None
        )
        self.repo.add_bank_transaction(txn)

        # Testar atualização com dicionário (nova assinatura)
        update_data = {
            "description": "Updated Transaction",
            "amount": 200.0,
            "category_id": "cat999",
            "split_info": {"updated": True}
        }

        updated = self.repo.update_bank_transaction(self.test_bank_id, update_data)
        self.assertIsNotNone(updated)
        self.assertEqual(updated.description, "Updated Transaction")
        self.assertEqual(updated.amount, 200.0)
        self.assertEqual(updated.category_id, "cat999")

        # Testar atualização sem dados
        empty_update = self.repo.update_bank_transaction(self.test_bank_id, {})
        self.assertIsNotNone(empty_update)

        # Testar transação inexistente
        with self.assertRaises(ValueError):
            self.repo.update_bank_transaction("nonexistent", {"description": "test"})

    # Testes para linhas 272-308: update_credit_transaction
    def test_update_credit_transaction(self):
        """Testa update_credit_transaction - linhas 272-308"""
        self._create_test_category("cat123")
        self._create_test_category("cat999", "Updated Category")

        # Criar transação de crédito inicial
        credit_txn = CreditTransaction(
            transaction_id=self.test_credit_id,
            amount=50.0,
            date="2023-01-05",
            description="Original Credit",
            category_id="cat123",
            status="PENDING"
        )
        self.repo.add_credit_transaction(credit_txn)

        # Atualizar transação
        update_data = {
            "description": "Updated Credit",
            "amount": 75.0,
            "status": "POSTED"
        }

        updated = self.repo.update_credit_transaction(self.test_credit_id, update_data)
        self.assertIsNotNone(updated)
        self.assertEqual(updated.description, "Updated Credit")
        self.assertEqual(updated.amount, 75.0)
        self.assertEqual(updated.status, "POSTED")

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
            split_info=None,
            payment_data=None
        )
        self.repo.add_bank_transaction(txn)

        # Categoria em uso deve retornar True
        self.assertTrue(self.repo.category_in_use("cat123"))

        # Categoria não usada deve retornar False
        self.assertFalse(self.repo.category_in_use("cat999"))

    # Testes para linhas 326-333: get_unlinked_transactions
    def test_get_unlinked_transactions(self):
        """Testa get_unlinked_transactions - linhas 326-333"""
        self._create_test_category()

        # Transação sem split_info (não vinculada)
        unlinked_txn = BankTransaction(
            transaction_id="unlinked-123",
            amount=100.0,
            date="2023-01-07",
            description="Unlinked Transaction",
            category_id="cat123",
            type_="debit",
            operation_type="PIX",
            split_info=None,  # Sem informação de divisão
            payment_data={"test": "data"}
        )
        self.repo.add_bank_transaction(unlinked_txn)

        # Transação com split_info (vinculada)
        linked_txn = BankTransaction(
            transaction_id="linked-123",
            amount=200.0,
            date="2023-01-08",
            description="Linked Transaction",
            category_id="cat123",
            type_="debit",
            operation_type="PIX",
            split_info={"split": True},  # Com informação de divisão
            payment_data={"test": "data"}
        )
        self.repo.add_bank_transaction(linked_txn)

        unlinked = self.repo.get_unlinked_transactions()
        self.assertIsInstance(unlinked, list)

        # Verificar se apenas a transação não vinculada está na lista
        unlinked_ids = [t.transaction_id for t in unlinked]
        self.assertIn("unlinked-123", unlinked_ids)
        self.assertNotIn("linked-123", unlinked_ids)

    # Testes para linhas 360-379: upsert_bank_transaction
    @patch.object(TransactionRepository, '_process_pix_person_extraction')
    @patch.object(TransactionRepository, '_process_category_creation')
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
            "paymentData": {"method": "pix"}
        }

        # Mock do método upsert da classe base
        with patch.object(self.repo, 'upsert') as mock_upsert:
            mock_upsert.return_value = {"action": "inserted", "id": "upsert-test-123"}

            result = self.repo.upsert_bank_transaction(transaction_data)

            self.assertEqual(result["action"], "inserted")
            mock_upsert.assert_called_once()
            mock_pix.assert_called_once()
            mock_category.assert_called_once()

    # Testes para linhas 392-417: upsert_credit_transaction
    @patch.object(TransactionRepository, '_process_category_creation')
    def test_upsert_credit_transaction(self, mock_category):
        """Testa upsert_credit_transaction - linhas 392-417"""
        transaction_data = {
            "id": "upsert-credit-123",
            "date": "2023-01-10",
            "description": "Upsert Credit Test",
            "amount": 75.0,
            "amountInAccountCurrency": 80.0,  # Deve usar este valor
            "categoryId": "cat123",
            "status": "POSTED"
        }

        # Mock do método upsert da classe base
        with patch.object(self.repo, 'upsert') as mock_upsert:
            mock_upsert.return_value = {"action": "updated", "id": "upsert-credit-123"}

            result = self.repo.upsert_credit_transaction(transaction_data)

            self.assertEqual(result["action"], "updated")
            mock_upsert.assert_called_once()
            mock_category.assert_called_once()

            # Verificar se foi usado amountInAccountCurrency
            call_args = mock_upsert.call_args[0][2]  # mapped_data
            self.assertEqual(call_args["amount"], 80.0)

    # Testes para linhas 424-442: _process_pix_person_extraction
    def test_process_pix_person_extraction(self):
        """Testa _process_pix_person_extraction - linhas 424-442"""
        transaction_data = {
            "operationType": "PIX",
            "description": "transferência recebida|João Silva",
            "paymentData": {
                "payer": {
                    "documentNumber": {
                        "type": "CPF",
                        "value": "12345678901"
                    }
                }
            }
        }

        # Mock do método upsert
        with patch.object(self.repo, 'upsert') as mock_upsert:
            mock_upsert.return_value = {"action": "inserted"}

            self.repo._process_pix_person_extraction(transaction_data)

            # Verificar se foi chamado com dados corretos
            mock_upsert.assert_called_once_with(
                "persons",
                "id",
                {"id": "12345678901", "name": "João Silva"},
                strategy="insert_only"
            )

    def test_process_pix_person_extraction_transferencia_enviada(self):
        """Testa _process_pix_person_extraction para transferência enviada"""
        transaction_data = {
            "operationType": "PIX",
            "description": "transferência enviada|Maria Santos",
            "paymentData": {
                "receiver": {
                    "documentNumber": {
                        "type": "CPF",
                        "value": "98765432100"
                    }
                }
            }
        }

        # Mock do método upsert
        with patch.object(self.repo, 'upsert') as mock_upsert:
            mock_upsert.return_value = {"action": "inserted"}

            self.repo._process_pix_person_extraction(transaction_data)

            # Verificar se foi chamado com dados corretos
            mock_upsert.assert_called_once_with(
                "persons",
                "id",
                {"id": "98765432100", "name": "Maria Santos"},
                strategy="insert_only"
            )

    def test_process_pix_person_extraction_no_pipe(self):
        """Testa _process_pix_person_extraction sem pipe na descrição"""
        transaction_data = {
            "operationType": "PIX",
            "description": "transferência sem pipe",
            "paymentData": {}
        }

        # Mock do método upsert
        with patch.object(self.repo, 'upsert') as mock_upsert:
            self.repo._process_pix_person_extraction(transaction_data)

            # Não deve chamar upsert
            mock_upsert.assert_not_called()

    def test_process_pix_person_extraction_not_pix(self):
        """Testa _process_pix_person_extraction para operação que não é PIX"""
        transaction_data = {
            "operationType": "TED",
            "description": "transferência recebida|João Silva",
            "paymentData": {}
        }

        # Mock do método upsert
        with patch.object(self.repo, 'upsert') as mock_upsert:
            self.repo._process_pix_person_extraction(transaction_data)

            # Não deve chamar upsert
            mock_upsert.assert_not_called()

    # Testes para linhas 449-456: _process_category_creation
    def test_process_category_creation(self):
        """Testa _process_category_creation - linhas 449-456"""
        transaction_data = {
            "categoryId": "new-cat-123",
            "category": "Nova Categoria"
        }

        # Mock do método upsert
        with patch.object(self.repo, 'upsert') as mock_upsert:
            mock_upsert.return_value = {"action": "inserted"}

            self.repo._process_category_creation(transaction_data)

            # Verificar se foi chamado com dados corretos
            mock_upsert.assert_called_once_with(
                "categories",
                "id",
                {"id": "new-cat-123", "name": "Nova Categoria"},
                strategy="insert_only"
            )

    def test_process_category_creation_no_category(self):
        """Testa _process_category_creation sem categoryId ou category"""
        transaction_data = {
            "description": "Sem categoria"
        }

        # Mock do método upsert
        with patch.object(self.repo, 'upsert') as mock_upsert:
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
            operation_type="PIX"
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
            category_id="cat123"
        )

        with self.assertRaises(ValueError):
            self.repo.create_bank_transaction(invalid_transaction)

        # Testar validação - descrição vazia
        invalid_transaction2 = BankTransaction(
            transaction_id="valid-id",
            amount=100.0,
            date="2023-01-12",
            description="",  # Descrição vazia
            category_id="cat123"
        )

        with self.assertRaises(ValueError):
            self.repo.create_bank_transaction(invalid_transaction2)

        # Testar validação - amount None
        invalid_transaction3 = BankTransaction(
            transaction_id="valid-id-2",
            amount=None,  # Amount None
            date="2023-01-12",
            description="Valid Description",
            category_id="cat123"
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
            status="PENDING"
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
            status="PENDING"
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
            status="PENDING"
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
            status="PENDING"
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
            operation_type="PIX"
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

    def test_delete_bank_transaction_with_splitwise_reference(self):
        """Testa deleção de transação bancária vinculada ao Splitwise"""
        self._create_test_category()

        # Criar transação
        transaction = BankTransaction(
            transaction_id="split-ref-123",
            amount=120.0,
            date="2023-01-14",
            description="With Splitwise Ref",
            category_id="cat123",
            type_="debit",
            operation_type="PIX"
        )
        self.repo.add_bank_transaction(transaction)

        # Adicionar referência no splitwise
        self.repo.execute_query(
            "INSERT INTO splitwise (id, transaction_id, amount) VALUES (?, ?, ?)",
            ("split-123", "split-ref-123", 60.0)
        )

        # Tentar deletar deve falhar
        with self.assertRaises(ValueError) as context:
            self.repo.delete_bank_transaction("split-ref-123")

        self.assertIn("vinculada a entradas do Splitwise", str(context.exception))

    def test_delete_bank_transaction_with_split_info(self):
        """Testa deleção de transação bancária com split_info"""
        self._create_test_category()

        # Criar transação com split_info
        transaction = BankTransaction(
            transaction_id="split-info-123",
            amount=120.0,
            date="2023-01-14",
            description="With Split Info",
            category_id="cat123",
            type_="debit",
            operation_type="PIX",
            split_info={"split": True}
        )
        self.repo.add_bank_transaction(transaction)

        # Tentar deletar deve falhar
        with self.assertRaises(ValueError) as context:
            self.repo.delete_bank_transaction("split-info-123")

        self.assertIn("possui informações de divisão", str(context.exception))

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
            status="POSTED"
        )
        self.repo.add_credit_transaction(transaction)

        # Deletar transação
        result = self.repo.delete_credit_transaction("delete-credit-123")
        self.assertTrue(result)

        # Verificar se foi realmente deletada
        with self.assertRaises(ValueError):
            self.repo.get_credit_transaction_by_id("delete-credit-123")

    def test_delete_credit_transaction_with_splitwise_reference(self):
        """Testa deleção de transação de crédito vinculada ao Splitwise"""
        self._create_test_category()

        # Criar transação de crédito
        transaction = CreditTransaction(
            transaction_id="credit-split-123",
            amount=90.0,
            date="2023-01-15",
            description="Credit with Splitwise",
            category_id="cat123",
            status="POSTED"
        )
        self.repo.add_credit_transaction(transaction)

        # Adicionar referência no splitwise
        self.repo.execute_query(
            "INSERT INTO splitwise (id, transaction_id, amount) VALUES (?, ?, ?)",
            ("credit-split", "credit-split-123", 45.0)
        )

        # Tentar deletar deve falhar
        with self.assertRaises(ValueError) as context:
            self.repo.delete_credit_transaction("credit-split-123")

        self.assertIn("vinculada a entradas do Splitwise", str(context.exception))

        # Testar validação de ID vazio para crédito
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
                operation_type=op
            )
            self.repo.add_bank_transaction(transaction)

        operation_types = self.repo.get_operation_types()
        self.assertIsInstance(operation_types, list)

        for op in operations:
            self.assertIn(op, operation_types)

    def tearDown(self):
        """Limpeza após os testes"""
        # Como recriamos as tabelas no setUp, só precisamos fechar a conexão
        pass


if __name__ == "__main__":
    unittest.main()