import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from services.splitwise_service import SplitwiseService


class TestSplitwiseService(unittest.TestCase):
    def setUp(self):
        with patch("services.splitwise_service.SplitwiseRepository"):
            self.service = SplitwiseService()

        self.mock_repo = MagicMock()
        self.service.splitwise_repository = self.mock_repo

    def test_get_all_splitwise(self):
        self.mock_repo.get_all_splitwise.return_value = [MagicMock(), MagicMock()]
        result = self.service.get_all_splitwise()
        self.mock_repo.get_all_splitwise.assert_called()
        self.assertEqual(len(result), 2)

    def test_update_splitwise_calls_repo(self):
        self.service.update_splitwise("sid", "catid", "txid")
        self.mock_repo.update_splitwise.assert_called_with("sid", "catid", "txid")

    def test_link_transaction_to_splitwise(self):
        txn = MagicMock()
        self.service.link_transaction_to_splitwise("sid", txn)
        self.mock_repo.set_transaction_to_splitwise.assert_called_with("sid", txn)

    def test_category_in_use(self):
        self.mock_repo.category_in_use.return_value = True
        result = self.service.category_in_use("catid")
        self.mock_repo.category_in_use.assert_called_with("catid")
        self.assertTrue(result)

    def test_get_unsettled_splitwise(self):
        self.mock_repo.get_unsettled_splitwise.return_value = [MagicMock()]
        result = self.service.get_unsettled_splitwise()
        self.mock_repo.get_unsettled_splitwise.assert_called()
        self.assertEqual(len(result), 1)

    def test_create_splitwise_missing_id(self):
        with self.assertRaises(ValueError) as context:
            self.service.create_splitwise({})
        self.assertEqual(
            str(context.exception), "ID da entrada do Splitwise é obrigatório"
        )

    def test_create_splitwise_missing_description(self):
        with self.assertRaises(ValueError) as context:
            self.service.create_splitwise({"id": "123"})
        self.assertEqual(str(context.exception), "Descrição é obrigatória")

    def test_create_splitwise_missing_amount(self):
        with self.assertRaises(ValueError) as context:
            self.service.create_splitwise({"id": "123", "description": "test"})
        self.assertEqual(str(context.exception), "Valor é obrigatório")

    def test_create_splitwise_missing_date(self):
        with self.assertRaises(ValueError) as context:
            self.service.create_splitwise(
                {"id": "123", "description": "test", "amount": 10}
            )
        self.assertEqual(str(context.exception), "Data é obrigatória")

    def test_create_splitwise_invalid_string_date(self):
        with patch.object(self.service, "_parse_date", return_value=None):
            with self.assertRaises(ValueError) as context:
                self.service.create_splitwise(
                    {
                        "id": "123",
                        "description": "test",
                        "amount": 10,
                        "date": "invalid-date",
                    }
                )
            self.assertEqual(
                str(context.exception), "Formato de data inválido. Use YYYY-MM-DD"
            )

    def test_create_splitwise_invalid_date_exception(self):
        with patch.object(
            self.service, "_parse_date", side_effect=ValueError("Invalid")
        ):
            with self.assertRaises(ValueError) as context:
                self.service.create_splitwise(
                    {
                        "id": "123",
                        "description": "test",
                        "amount": 10,
                        "date": "2023-13-01",
                    }
                )
            self.assertEqual(
                str(context.exception), "Formato de data inválido. Use YYYY-MM-DD"
            )

    def test_create_splitwise_invalid_amount_string(self):
        with self.assertRaises(ValueError) as context:
            self.service.create_splitwise(
                {
                    "id": "123",
                    "description": "test",
                    "amount": "not-a-number",
                    "date": datetime(2023, 1, 1),
                }
            )
        self.assertEqual(str(context.exception), "Valor deve ser um número")

    def test_create_splitwise_invalid_amount_none(self):
        with self.assertRaises(ValueError) as context:
            self.service.create_splitwise(
                {
                    "id": "123",
                    "description": "test",
                    "amount": None,
                    "date": datetime(2023, 1, 1),
                }
            )
        self.assertEqual(str(context.exception), "Valor é obrigatório")

    def test_create_splitwise_success_datetime(self):
        splitwise_data = {
            "id": "123",
            "description": "test expense",
            "amount": 50.0,
            "date": datetime(2023, 1, 15),
        }

        mock_created = MagicMock()
        self.mock_repo.create_splitwise.return_value = mock_created

        result = self.service.create_splitwise(splitwise_data)

        self.mock_repo.create_splitwise.assert_called_once()
        args = self.mock_repo.create_splitwise.call_args[0][0]
        self.assertEqual(args.splitwise_id, "123")
        self.assertEqual(args.description, "test expense")
        self.assertEqual(args.amount, 50.0)
        self.assertEqual(args.date, datetime(2023, 1, 15))
        self.assertEqual(result, mock_created)

    def test_create_splitwise_amount_too_small(self):
        splitwise_data = {
            "id": "123",
            "description": "test",
            "amount": 0.005,
            "date": datetime(2023, 1, 1),
        }

        with self.assertRaises(ValueError) as context:
            self.service.create_splitwise(splitwise_data)
        self.assertEqual(str(context.exception), "Valor deve ser maior que 0.01")

    def test_create_splitwise_calls_repository(self):
        splitwise_data = {
            "id": "123",
            "description": "test",
            "amount": 10.0,
            "date": datetime(2023, 1, 1),
        }

        mock_created = MagicMock()
        self.mock_repo.create_splitwise.return_value = mock_created

        result = self.service.create_splitwise(splitwise_data)

        self.mock_repo.create_splitwise.assert_called_once()
        self.assertEqual(result, mock_created)

    def test_delete_splitwise_missing_id(self):
        with self.assertRaises(ValueError) as context:
            self.service.delete_splitwise("")
        self.assertEqual(
            str(context.exception), "ID da entrada do Splitwise é obrigatório"
        )

    def test_delete_splitwise_missing_id_none(self):
        with self.assertRaises(ValueError) as context:
            self.service.delete_splitwise(None)
        self.assertEqual(
            str(context.exception), "ID da entrada do Splitwise é obrigatório"
        )

    def test_delete_splitwise_not_found(self):
        self.mock_repo.get_splitwise_by_id.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.delete_splitwise("123")
        self.assertEqual(
            str(context.exception), "Entrada do Splitwise com ID 123 não encontrada"
        )

    def test_delete_splitwise_with_transaction_warning(self):
        mock_splitwise = MagicMock()
        mock_splitwise.transaction_id = "txn123"
        mock_splitwise.description = "Test Entry"
        self.mock_repo.get_splitwise_by_id.return_value = mock_splitwise
        self.mock_repo.delete_splitwise.return_value = True

        with patch("builtins.print") as mock_print:
            result = self.service.delete_splitwise("123")
            mock_print.assert_called_once_with(
                "Aviso: Deletando entrada do Splitwise 'Test Entry' que estava vinculada à transação txn123"
            )

        self.assertTrue(result)

    def test_delete_splitwise_calls_repository(self):
        mock_splitwise = MagicMock()
        mock_splitwise.transaction_id = None
        self.mock_repo.get_splitwise_by_id.return_value = mock_splitwise
        self.mock_repo.delete_splitwise.return_value = True

        result = self.service.delete_splitwise("123")

        self.mock_repo.delete_splitwise.assert_called_once_with("123")
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
