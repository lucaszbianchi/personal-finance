"""Testes para TransactionService"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch
from services.transaction_service import TransactionService


class TestTransactionService(unittest.TestCase):
    """Testes para a classe TransactionService"""

    def setUp(self):
        with patch("services.transaction_service.TransactionRepository"), patch(
            "services.transaction_service.CategoryRepository"
        ), patch("services.transaction_service.PersonRepository"):
            self.service = TransactionService()

        self.mock_repo = MagicMock()
        self.mock_cat_repo = MagicMock()
        self.mock_person_repo = MagicMock()
        self.service.transaction_repository = self.mock_repo
        self.service.category_repository = self.mock_cat_repo
        self.service.person_repository = self.mock_person_repo

    def test_get_bank_transactions(self):
        """Testa get_bank_transactions sem filtros"""
        self.mock_repo.get_bank_transactions.return_value = [MagicMock(), MagicMock()]
        result = self.service.get_bank_transactions()
        self.mock_repo.get_bank_transactions.assert_called()
        self.assertEqual(len(result), 2)

    def test_get_bank_transactions_with_category_filter(self):
        """Testa get_bank_transactions com filtro de categoria - linha 37"""
        mock_transaction1 = MagicMock(date="2025-01-15", category_id="cat1")
        mock_transaction2 = MagicMock(date="2025-01-16", category_id="cat2")
        self.mock_repo.get_bank_transactions.return_value = [
            mock_transaction1,
            mock_transaction2,
        ]

        result = self.service.get_bank_transactions(category_id="cat1")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].category_id, "cat1")

    def test_get_credit_transactions(self):
        """Testa get_credit_transactions sem filtros"""
        self.mock_repo.get_credit_transactions.return_value = [MagicMock()]
        result = self.service.get_credit_transactions()
        self.mock_repo.get_credit_transactions.assert_called()
        self.assertEqual(len(result), 1)

    def test_get_credit_transactions_with_category_filter(self):
        """Testa get_credit_transactions com filtro de categoria - linha 59"""
        mock_transaction1 = MagicMock(date="2025-01-15", category_id="cat1")
        mock_transaction2 = MagicMock(date="2025-01-16", category_id="cat2")
        self.mock_repo.get_credit_transactions.return_value = [
            mock_transaction1,
            mock_transaction2,
        ]

        result = self.service.get_credit_transactions(category_id="cat1")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].category_id, "cat1")

    def test_get_investments(self):
        """Testa get_investments"""
        self.mock_repo.get_investments.return_value = [MagicMock()]
        result = self.service.get_investments()
        self.mock_repo.get_investments.assert_called()
        self.assertEqual(len(result), 1)

    def test_get_bank_transactions_by_period(self):
        """Testa get_bank_transactions com filtros de data"""
        mock_transaction = MagicMock(date="2025-01-15", category_id="cat1")
        self.mock_repo.get_bank_transactions.return_value = [mock_transaction]
        result = self.service.get_bank_transactions(
            start_date="2025-01-01", end_date="2025-01-31"
        )
        self.mock_repo.get_bank_transactions.assert_called_once()
        self.assertEqual(len(result), 1)

    def test_get_credit_transactions_by_period(self):
        """Testa get_credit_transactions com filtros de data"""
        mock_transaction = MagicMock(date="2025-01-15", category_id="cat1")
        self.mock_repo.get_credit_transactions.return_value = [mock_transaction]
        result = self.service.get_credit_transactions(
            start_date="2025-01-01", end_date="2025-01-31"
        )
        self.mock_repo.get_credit_transactions.assert_called_once()
        self.assertEqual(len(result), 1)

    def test_update_transaction_bank_with_none_values(self):
        """Testa update_transaction com valores None - linhas 80, 82"""
        mock_transaction = MagicMock(
            description="Original Desc", category_id="original_cat"
        )
        self.mock_repo.get_bank_transaction_by_id.return_value = mock_transaction
        self.mock_repo.update_bank_transaction.return_value = True

        result = self.service.update_transaction("bank", "txid", None, None)

        self.mock_repo.update_bank_transaction.assert_called_with(
            "txid", "Original Desc", "original_cat", split_info=None
        )
        self.assertTrue(result)

    def test_update_transaction_credit_type(self):
        """Testa update_transaction com tipo credit - linhas 86-97"""
        mock_transaction = MagicMock(
            description="Credit Desc", category_id="credit_cat"
        )
        self.mock_repo.get_credit_transaction_by_id.return_value = mock_transaction
        self.mock_repo.update_credit_transaction.return_value = True

        result = self.service.update_transaction(
            "credit", "txid", "New Desc", "new_cat"
        )

        self.mock_repo.update_credit_transaction.assert_called_with(
            "txid", "New Desc", "new_cat", split_info=None
        )
        self.assertTrue(result)

    def test_update_transaction_invalid_type(self):
        """Testa update_transaction com tipo inválido - retorna False"""
        result = self.service.update_transaction("invalid", "txid", "desc", "cat")
        self.assertFalse(result)

    def test_add_person_to_share_transaction_bank(self):
        """Testa add_person_to_share_transaction com banco"""
        partners = {"p1": 50.0, "p2": 50.0}
        self.mock_repo.update_bank_transaction.return_value = True
        result = self.service.add_person_to_share_transaction("bank", "txid", partners)
        self.mock_repo.update_bank_transaction.assert_called_once()
        self.assertTrue(result)

    def test_add_person_to_share_transaction_credit(self):
        """Testa add_person_to_share_transaction com crédito - linhas 120-124"""
        partners = {"p1": 30.0, "p2": 70.0}
        self.mock_repo.update_credit_transaction.return_value = True
        result = self.service.add_person_to_share_transaction(
            "credit", "txid", partners
        )

        self.mock_repo.update_credit_transaction.assert_called_once()
        self.assertTrue(result)

    def test_add_person_to_share_transaction_invalid_type(self):
        """Testa add_person_to_share_transaction com tipo inválido"""
        partners = {"p1": 50.0}
        result = self.service.add_person_to_share_transaction(
            "invalid", "txid", partners
        )
        self.assertFalse(result)

    def test_settle_up_split_invalid_document_type(self):
        """Testa settle_up_split com tipo de documento inválido - linha 135"""
        mock_transaction = MagicMock(
            payment_data={"payer": {"documentNumber": {"type": "CNPJ", "value": "123"}}}
        )
        self.mock_repo.get_bank_transaction_by_id.return_value = mock_transaction

        with self.assertRaises(ValueError) as context:
            self.service.settle_up_split("txid")

        self.assertIn("Apenas CPFs são suportados", str(context.exception))

    def test_settle_up_split_success(self):
        """Testa settle_up_split com sucesso"""
        mock_transaction = MagicMock(
            payment_data={
                "payer": {"documentNumber": {"type": "CPF", "value": "12345678901"}}
            }
        )
        self.mock_repo.get_bank_transaction_by_id.return_value = mock_transaction
        self.mock_repo.update_bank_transaction.return_value = True

        result = self.service.settle_up_split("txid")

        self.mock_repo.update_bank_transaction.assert_called_with(
            "txid", None, None, {"settle_up": True, "partner_id": "12345678901"}
        )
        self.assertTrue(result)

    def test_add_category_to_settle_up_transaction_not_settle_up(self):
        """Testa add_category_to_settle_up_transaction quando não é settle up - linha 153"""
        mock_transaction = MagicMock(split_info={"settle_up": False})
        self.mock_repo.get_bank_transaction_by_id.return_value = mock_transaction

        with self.assertRaises(ValueError) as context:
            self.service.add_category_to_settle_up_transaction("txid", "catid")

        self.assertIn("não é uma transação de 'settle up'", str(context.exception))

    def test_add_category_to_settle_up_transaction_no_split_info(self):
        """Testa add_category_to_settle_up_transaction sem split_info"""
        mock_transaction = MagicMock(split_info=None)
        self.mock_repo.get_bank_transaction_by_id.return_value = mock_transaction

        with self.assertRaises(ValueError) as context:
            self.service.add_category_to_settle_up_transaction("txid", "catid")

        self.assertIn("não é uma transação de 'settle up'", str(context.exception))

    def test_add_category_to_settle_up_transaction_success(self):
        """Testa add_category_to_settle_up_transaction com sucesso"""
        mock_transaction = MagicMock(split_info={"settle_up": True, "partner_id": "p1"})
        self.mock_repo.get_bank_transaction_by_id.return_value = mock_transaction
        self.mock_repo.update_bank_transaction.return_value = True
        result = self.service.add_category_to_settle_up_transaction("txid", "catid")
        self.mock_repo.update_bank_transaction.assert_called_once()
        self.assertTrue(result)

    def test_check_split_settle_up_no_partner_id(self):
        """Testa check_split_settle_up com transação sem partner_id - linha 183"""
        mock_transaction = MagicMock(
            split_info={"settle_up": True, "partner_id": None},
            transaction_id="txid",
            amount=100.0,
            description="settle up",
        )
        self.mock_repo.get_bank_transactions.return_value = [mock_transaction]
        self.mock_person_repo.get_all_people.return_value = []

        result = self.service.check_split_settle_up()
        self.assertEqual(result, [])

    def test_check_split_settle_up_with_partner_creation(self):
        """Testa check_split_settle_up criando novo partner no result - linhas 188-196"""
        mock_transaction = MagicMock(
            split_info={
                "settle_up": True,
                "partner_id": "new_partner",
                "category": "cat1",
            },
            transaction_id="txid",
            date=datetime.strptime("2025-01-01", "%Y-%m-%d"),
            amount=100.0,
            description="settle up",
        )
        self.mock_repo.get_bank_transactions.return_value = [mock_transaction]
        self.mock_person_repo.get_all_people.return_value = [
            MagicMock(id="new_partner", name="New Partner")
        ]

        result = self.service.check_split_settle_up()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["person_id"], "new_partner")
        self.assertEqual(result[0]["total_settle_up"], 100.0)

    def test_check_split_settle_up_with_category(self):
        """Testa check_split_settle_up com categoria - linhas 208-213"""
        mock_transaction = MagicMock(
            split_info={"settle_up": True, "partner_id": "p1", "category": "cat1"},
            transaction_id="txid",
            date=datetime.strptime("2025-01-01", "%Y-%m-%d"),
            amount=100.0,
            description="settle up with category",
        )
        self.mock_repo.get_bank_transactions.return_value = [mock_transaction]
        self.mock_person_repo.get_all_people.return_value = [
            MagicMock(id="p1", name="Partner 1")
        ]

        result = self.service.check_split_settle_up()
        self.assertEqual(len(result), 1)
        self.assertIn("cat1", result[0]["categories"])

    def test_check_split_settle_up_with_splits(self):
        """Testa check_split_settle_up com partners - linhas 222-254"""
        # Transação com partners no split_info
        mock_transaction = MagicMock(
            split_info={
                "partners": [
                    {"person_id": "p1", "share": 50.0},
                    {"person_id": "p2", "share": 30.0},
                ]
            },
            transaction_id="txid",
            date=datetime.strptime("2025-01-01", "%Y-%m-%d"),
            amount=100.0,
            description="split transaction",
            category_id="cat1",
        )
        self.mock_repo.get_bank_transactions.return_value = [mock_transaction]
        self.mock_person_repo.get_all_people.return_value = [
            MagicMock(id="p1", name="Partner 1"),
            MagicMock(id="p2", name="Partner 2"),
        ]

        result = self.service.check_split_settle_up()

        # Verifica se p1 e p2 estão no resultado
        partner_ids = [r["person_id"] for r in result]
        self.assertIn("p1", partner_ids)
        self.assertIn("p2", partner_ids)

        # Verifica valores
        p1_result = next(r for r in result if r["person_id"] == "p1")
        self.assertEqual(p1_result["total_splits"], 50.0)

    def test_check_split_settle_up_with_splits_no_person_id(self):
        """Testa check_split_settle_up com partner sem person_id"""
        mock_transaction = MagicMock(
            split_info={
                "partners": [
                    {"person_id": None, "share": 50.0}  # Partner sem person_id
                ]
            },
            transaction_id="txid",
        )
        self.mock_repo.get_bank_transactions.return_value = [mock_transaction]
        self.mock_person_repo.get_all_people.return_value = []

        result = self.service.check_split_settle_up()
        self.assertEqual(result, [])

    def test_check_split_settle_up_person_not_in_result(self):
        """Testa check_split_settle_up com pessoa não no resultado - linha 262"""
        self.mock_repo.get_bank_transactions.return_value = []
        self.mock_person_repo.get_all_people.return_value = [
            MagicMock(id="p_without_transactions", name="Person Without Transactions")
        ]

        result = self.service.check_split_settle_up()
        self.assertEqual(result, [])

    def test_check_split_settle_up_categories_diff(self):
        """Testa check_split_settle_up com diferenças por categoria - linha 271"""
        # Transação settle up
        settle_up_transaction = MagicMock(
            split_info={"settle_up": True, "partner_id": "p1", "category": "cat1"},
            transaction_id="settle_txid",
            date=datetime.strptime("2025-01-01", "%Y-%m-%d"),
            amount=100.0,
            description="settle up",
        )

        # Transação split
        split_transaction = MagicMock(
            split_info={"partners": [{"person_id": "p1", "share": 60.0}]},
            transaction_id="split_txid",
            date=datetime.strptime("2025-01-02", "%Y-%m-%d"),
            amount=120.0,
            description="split transaction",
            category_id="cat1",
        )

        self.mock_repo.get_bank_transactions.return_value = [
            settle_up_transaction,
            split_transaction,
        ]
        self.mock_person_repo.get_all_people.return_value = [
            MagicMock(id="p1", name="Partner 1")
        ]

        result = self.service.check_split_settle_up()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["categories"]["cat1"], 40.0)  # 100 - 60

    def test_create_bank_transaction_missing_id(self):
        """Testa create_bank_transaction sem ID - linha 300-301"""
        transaction_data = {
            "description": "Test",
            "amount": 100.0,
            "date": "2025-01-01",
        }

        with self.assertRaises(ValueError) as context:
            self.service.create_bank_transaction(transaction_data)

        self.assertIn("ID da transação é obrigatório", str(context.exception))

    def test_create_bank_transaction_missing_description(self):
        """Testa create_bank_transaction sem descrição - linhas 302-303"""
        transaction_data = {"id": "txid", "amount": 100.0, "date": "2025-01-01"}

        with self.assertRaises(ValueError) as context:
            self.service.create_bank_transaction(transaction_data)

        self.assertIn("Descrição é obrigatória", str(context.exception))

    def test_create_bank_transaction_missing_amount(self):
        """Testa create_bank_transaction sem valor - linhas 304-305"""
        transaction_data = {"id": "txid", "description": "Test", "date": "2025-01-01"}

        with self.assertRaises(ValueError) as context:
            self.service.create_bank_transaction(transaction_data)

        self.assertIn("Valor é obrigatório", str(context.exception))

    def test_create_bank_transaction_missing_date(self):
        """Testa create_bank_transaction sem data - linhas 306-307"""
        transaction_data = {"id": "txid", "description": "Test", "amount": 100.0}

        with self.assertRaises(ValueError) as context:
            self.service.create_bank_transaction(transaction_data)

        self.assertIn("Data é obrigatória", str(context.exception))

    def test_create_bank_transaction_invalid_amount(self):
        """Testa create_bank_transaction com valor inválido - linhas 310-313"""
        transaction_data = {
            "id": "txid",
            "description": "Test",
            "amount": "invalid",
            "date": "2025-01-01",
        }

        with self.assertRaises(ValueError) as context:
            self.service.create_bank_transaction(transaction_data)

        self.assertIn("Valor deve ser um número", str(context.exception))

    def test_create_bank_transaction_invalid_category(self):
        """Testa create_bank_transaction com categoria inválida - linhas 317-320"""
        transaction_data = {
            "id": "txid",
            "description": "Test",
            "amount": 100.0,
            "date": "2025-01-01",
            "category_id": "invalid_cat",
        }

        self.mock_cat_repo.get_category_by_id.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.create_bank_transaction(transaction_data)

        self.assertIn(
            "Categoria com ID invalid_cat não encontrada", str(context.exception)
        )

    def test_create_bank_transaction_amount_too_small(self):
        """Testa create_bank_transaction com valor muito pequeno - linhas 336-337"""
        transaction_data = {
            "id": "txid",
            "description": "Test",
            "amount": 0.001,  # Menor que 0.01
            "date": "2025-01-01",
        }

        with self.assertRaises(ValueError) as context:
            self.service.create_bank_transaction(transaction_data)

        self.assertIn("Valor deve ser maior que 0.01", str(context.exception))

    def test_create_bank_transaction_success(self):
        """Testa create_bank_transaction com sucesso - linhas 322-341"""
        transaction_data = {
            "id": "txid",
            "description": "Test Transaction",
            "amount": 100.0,
            "date": "2025-01-01",
            "category_id": "cat1",
            "type": "debit",
            "operation_type": "PIX",
            "split_info": {"test": True},
            "payment_data": {"method": "pix"},
        }

        mock_category = MagicMock()
        self.mock_cat_repo.get_category_by_id.return_value = mock_category

        mock_transaction = MagicMock()
        self.mock_repo.create_bank_transaction.return_value = mock_transaction

        result = self.service.create_bank_transaction(transaction_data)

        self.mock_repo.create_bank_transaction.assert_called_once()
        self.assertEqual(result, mock_transaction)

    def test_create_credit_transaction_missing_fields(self):
        """Testa create_credit_transaction com campos obrigatórios faltando - linhas 356-363"""
        # Teste para ID faltando
        with self.assertRaises(ValueError) as context:
            self.service.create_credit_transaction({})
        self.assertIn("ID da transação é obrigatório", str(context.exception))

        # Teste para descrição faltando
        with self.assertRaises(ValueError) as context:
            self.service.create_credit_transaction({"id": "txid"})
        self.assertIn("Descrição é obrigatória", str(context.exception))

        # Teste para valor faltando
        with self.assertRaises(ValueError) as context:
            self.service.create_credit_transaction(
                {"id": "txid", "description": "Test"}
            )
        self.assertIn("Valor é obrigatório", str(context.exception))

        # Teste para data faltando
        with self.assertRaises(ValueError) as context:
            self.service.create_credit_transaction(
                {"id": "txid", "description": "Test", "amount": 100.0}
            )
        self.assertIn("Data é obrigatória", str(context.exception))

    def test_create_credit_transaction_invalid_amount(self):
        """Testa create_credit_transaction com valor inválido - linhas 365-369"""
        transaction_data = {
            "id": "txid",
            "description": "Test",
            "amount": "invalid",
            "date": "2025-01-01",
        }

        with self.assertRaises(ValueError) as context:
            self.service.create_credit_transaction(transaction_data)

        self.assertIn("Valor deve ser um número", str(context.exception))

    def test_create_credit_transaction_invalid_category(self):
        """Testa create_credit_transaction com categoria inválida - linhas 372-376"""
        transaction_data = {
            "id": "txid",
            "description": "Test",
            "amount": 100.0,
            "date": "2025-01-01",
            "category_id": "invalid_cat",
        }

        self.mock_cat_repo.get_category_by_id.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.create_credit_transaction(transaction_data)

        self.assertIn(
            "Categoria com ID invalid_cat não encontrada", str(context.exception)
        )

    def test_create_credit_transaction_amount_too_small(self):
        """Testa create_credit_transaction com valor muito pequeno - linhas 389-390"""
        transaction_data = {
            "id": "txid",
            "description": "Test",
            "amount": 0.005,  # Menor que 0.01
            "date": "2025-01-01",
        }

        with self.assertRaises(ValueError) as context:
            self.service.create_credit_transaction(transaction_data)

        self.assertIn("Valor deve ser maior que 0.01", str(context.exception))

    def test_create_credit_transaction_success(self):
        """Testa create_credit_transaction com sucesso - linhas 378-394"""
        transaction_data = {
            "id": "txid",
            "description": "Credit Transaction",
            "amount": 200.0,
            "date": "2025-01-01",
            "category_id": "cat1",
            "status": "posted",
        }

        mock_category = MagicMock()
        self.mock_cat_repo.get_category_by_id.return_value = mock_category

        mock_transaction = MagicMock()
        self.mock_repo.create_credit_transaction.return_value = mock_transaction

        result = self.service.create_credit_transaction(transaction_data)

        self.mock_repo.create_credit_transaction.assert_called_once()
        self.assertEqual(result, mock_transaction)

    def test_delete_bank_transaction_missing_id(self):
        """Testa delete_bank_transaction sem ID - linhas 409-410"""
        with self.assertRaises(ValueError) as context:
            self.service.delete_bank_transaction("")

        self.assertIn("ID da transação é obrigatório", str(context.exception))

    def test_delete_bank_transaction_not_found(self):
        """Testa delete_bank_transaction com transação não encontrada - linhas 413-416"""
        self.mock_repo.get_bank_transaction_by_id.side_effect = ValueError("Not found")

        with self.assertRaises(ValueError) as context:
            self.service.delete_bank_transaction("nonexistent")

        self.assertIn(
            "Transação bancária com ID nonexistent não encontrada",
            str(context.exception),
        )

    def test_delete_bank_transaction_investment_type(self):
        """Testa delete_bank_transaction com transação de investimento - linhas 420-421"""
        mock_transaction = MagicMock(description="Aplicação RDB - Test Investment")
        self.mock_repo.get_bank_transaction_by_id.return_value = mock_transaction

        with self.assertRaises(ValueError) as context:
            self.service.delete_bank_transaction("txid")

        self.assertIn(
            "Não é possível deletar transação de investimento", str(context.exception)
        )

    @patch("builtins.print")
    def test_delete_bank_transaction_with_split_info_warning(self, mock_print):
        """Testa delete_bank_transaction com split_info (aviso) - linhas 424-425"""
        mock_transaction = MagicMock(
            description="Normal Transaction",
            split_info={"partners": [{"person_id": "p1", "share": 50.0}]},
        )
        self.mock_repo.get_bank_transaction_by_id.return_value = mock_transaction
        self.mock_repo.delete_bank_transaction.return_value = True

        result = self.service.delete_bank_transaction("txid")

        mock_print.assert_called_once()
        self.assertIn("Aviso: Deletando transação", mock_print.call_args[0][0])
        self.assertTrue(result)

    def test_delete_bank_transaction_success(self):
        """Testa delete_bank_transaction com sucesso - linha 428"""
        mock_transaction = MagicMock(description="Normal Transaction", split_info=None)
        self.mock_repo.get_bank_transaction_by_id.return_value = mock_transaction
        self.mock_repo.delete_bank_transaction.return_value = True

        result = self.service.delete_bank_transaction("txid")

        self.mock_repo.delete_bank_transaction.assert_called_with("txid")
        self.assertTrue(result)

    def test_delete_credit_transaction_missing_id(self):
        """Testa delete_credit_transaction sem ID - linhas 443-444"""
        with self.assertRaises(ValueError) as context:
            self.service.delete_credit_transaction("")

        self.assertIn("ID da transação é obrigatório", str(context.exception))

    def test_delete_credit_transaction_not_found(self):
        """Testa delete_credit_transaction não encontrada - linhas 447-450"""
        self.mock_repo.get_credit_transaction_by_id.side_effect = ValueError(
            "Not found"
        )

        with self.assertRaises(ValueError) as context:
            self.service.delete_credit_transaction("nonexistent")

        self.assertIn(
            "Transação de crédito com ID nonexistent não encontrada",
            str(context.exception),
        )

    @patch("builtins.print")
    def test_delete_credit_transaction_pending_warning(self, mock_print):
        """Testa delete_credit_transaction com status pendente - linhas 453-454"""
        mock_transaction = MagicMock(
            description="Pending Transaction", status="pending"
        )
        self.mock_repo.get_credit_transaction_by_id.return_value = mock_transaction
        self.mock_repo.delete_credit_transaction.return_value = True

        result = self.service.delete_credit_transaction("txid")

        mock_print.assert_called_once()
        self.assertIn("Aviso: Deletando transação", mock_print.call_args[0][0])
        self.assertTrue(result)

    def test_delete_credit_transaction_success(self):
        """Testa delete_credit_transaction com sucesso - linha 457"""
        mock_transaction = MagicMock(description="Posted Transaction", status="posted")
        self.mock_repo.get_credit_transaction_by_id.return_value = mock_transaction
        self.mock_repo.delete_credit_transaction.return_value = True

        result = self.service.delete_credit_transaction("txid")

        self.mock_repo.delete_credit_transaction.assert_called_with("txid")
        self.assertTrue(result)

    def test_update_bank_transaction_missing_id(self):
        """Testa update_bank_transaction sem ID - linhas 473-474"""
        with self.assertRaises(ValueError) as context:
            self.service.update_bank_transaction("", {})

        self.assertIn("ID da transação é obrigatório", str(context.exception))

    def test_update_bank_transaction_not_found(self):
        """Testa update_bank_transaction não encontrada - linhas 477-479"""
        self.mock_repo.get_bank_transaction_by_id.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.update_bank_transaction("nonexistent", {})

        self.assertIn(
            "Transação bancária com ID nonexistent não encontrada",
            str(context.exception),
        )

    def test_update_bank_transaction_invalid_amount(self):
        """Testa update_bank_transaction com valor inválido - linhas 482-488"""
        mock_transaction = MagicMock()
        self.mock_repo.get_bank_transaction_by_id.return_value = mock_transaction

        # Teste valor não numérico
        with self.assertRaises(ValueError) as context:
            self.service.update_bank_transaction("txid", {"amount": "invalid"})
        self.assertIn("Valor deve ser um número válido", str(context.exception))

        # Teste valor muito pequeno - também retorna "número válido" por causa do except
        with self.assertRaises(ValueError) as context:
            self.service.update_bank_transaction("txid", {"amount": 0.001})
        self.assertIn("Valor deve ser um número válido", str(context.exception))

    def test_update_bank_transaction_invalid_category(self):
        """Testa update_bank_transaction com categoria inválida - linhas 490-493"""
        mock_transaction = MagicMock()
        self.mock_repo.get_bank_transaction_by_id.return_value = mock_transaction
        self.mock_cat_repo.get_category_by_id.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.update_bank_transaction("txid", {"category_id": "invalid_cat"})

        self.assertIn(
            "Categoria com ID invalid_cat não encontrada", str(context.exception)
        )

    def test_update_bank_transaction_success(self):
        """Testa update_bank_transaction com sucesso - linhas 495-497"""
        mock_transaction = MagicMock()
        self.mock_repo.get_bank_transaction_by_id.return_value = mock_transaction

        updated_transaction = MagicMock()
        self.mock_repo.update_bank_transaction.return_value = updated_transaction

        result = self.service.update_bank_transaction(
            "txid", {"description": "Updated"}
        )

        self.mock_repo.update_bank_transaction.assert_called_with(
            "txid", {"description": "Updated"}
        )
        self.assertEqual(result, updated_transaction)

    def test_update_credit_transaction_missing_id(self):
        """Testa update_credit_transaction sem ID - linhas 513-514"""
        with self.assertRaises(ValueError) as context:
            self.service.update_credit_transaction("", {})

        self.assertIn("ID da transação é obrigatório", str(context.exception))

    def test_update_credit_transaction_not_found(self):
        """Testa update_credit_transaction não encontrada - linhas 517-519"""
        self.mock_repo.get_credit_transaction_by_id.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.update_credit_transaction("nonexistent", {})

        self.assertIn(
            "Transação de crédito com ID nonexistent não encontrada",
            str(context.exception),
        )

    def test_update_credit_transaction_invalid_amount(self):
        """Testa update_credit_transaction com valor inválido - linhas 522-528"""
        mock_transaction = MagicMock()
        self.mock_repo.get_credit_transaction_by_id.return_value = mock_transaction

        # Teste valor não numérico
        with self.assertRaises(ValueError) as context:
            self.service.update_credit_transaction("txid", {"amount": "invalid"})
        self.assertIn("Valor deve ser um número válido", str(context.exception))

        # Teste valor muito pequeno - também retorna "número válido" por causa do except
        with self.assertRaises(ValueError) as context:
            self.service.update_credit_transaction("txid", {"amount": 0.005})
        self.assertIn("Valor deve ser um número válido", str(context.exception))

    def test_update_credit_transaction_invalid_category(self):
        """Testa update_credit_transaction com categoria inválida - linhas 530-533"""
        mock_transaction = MagicMock()
        self.mock_repo.get_credit_transaction_by_id.return_value = mock_transaction
        self.mock_cat_repo.get_category_by_id.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.update_credit_transaction(
                "txid", {"category_id": "invalid_cat"}
            )

        self.assertIn(
            "Categoria com ID invalid_cat não encontrada", str(context.exception)
        )

    def test_update_credit_transaction_success(self):
        """Testa update_credit_transaction com sucesso - linhas 535-537"""
        mock_transaction = MagicMock()
        self.mock_repo.get_credit_transaction_by_id.return_value = mock_transaction

        updated_transaction = MagicMock()
        self.mock_repo.update_credit_transaction.return_value = updated_transaction

        result = self.service.update_credit_transaction("txid", {"status": "posted"})

        self.mock_repo.update_credit_transaction.assert_called_with(
            "txid", {"status": "posted"}
        )
        self.assertEqual(result, updated_transaction)

    def test_get_operation_types(self):
        """Testa get_operation_types - linha 546"""
        mock_types = ["PIX", "TED", "DOC"]
        self.mock_repo.get_operation_types.return_value = mock_types

        result = self.service.get_operation_types()

        self.mock_repo.get_operation_types.assert_called_once()
        self.assertEqual(result, mock_types)


if __name__ == "__main__":
    unittest.main()
