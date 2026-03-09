import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from services.splitwise_service import SplitwiseService
from models.splitwise import Splitwise


def make_splitwise(
    splitwise_id="sw1",
    amount=50.0,
    date="2025-01-01",
    description="Test",
    category_id="cat1",
    transaction_id=None,
    is_invalid=False,
):
    sw = MagicMock(spec=Splitwise)
    sw.splitwise_id = splitwise_id
    sw.amount = amount
    sw.date = date
    sw.description = description
    sw.category_id = category_id
    sw.transaction_id = transaction_id
    sw.is_invalid = is_invalid
    return sw


class TestSplitwiseService(unittest.TestCase):
    def setUp(self):
        with patch("services.splitwise_service.SplitwiseRepository"):
            self.service = SplitwiseService()

        self.mock_repo = MagicMock()
        self.service.splitwise_repository = self.mock_repo

    # ── get_all_splitwise ─────────────────────────────────────────────────────

    def test_get_all_splitwise(self):
        self.mock_repo.get_all_splitwise.return_value = [MagicMock(), MagicMock()]
        result = self.service.get_all_splitwise()
        self.mock_repo.get_all_splitwise.assert_called()
        self.assertEqual(len(result), 2)

    # ── get_all_splitwise_with_match_info ─────────────────────────────────────

    def test_get_all_splitwise_with_match_info_no_transaction(self):
        row = MagicMock()
        row.__getitem__ = lambda self, k: {
            "id": "sw1", "amount": 50.0, "date": "2025-01-01",
            "description": "Test", "category_id": "cat1",
            "transaction_id": None, "match_type": None,
            "is_invalid": 0, "category_name": "Food",
        }[k]
        cursor = MagicMock()
        cursor.fetchall.return_value = [row]
        self.mock_repo.execute_query.return_value = cursor

        result = self.service.get_all_splitwise_with_match_info()

        self.assertEqual(len(result), 1)
        self.assertIsNone(result[0]["match_status"])
        self.assertIsNone(result[0]["linked_transaction"])

    def test_get_all_splitwise_with_match_info_with_transaction(self):
        row = MagicMock()
        row.__getitem__ = lambda self, k: {
            "id": "sw1", "amount": 50.0, "date": "2025-01-01",
            "description": "Test", "category_id": "cat1",
            "transaction_id": "txn1", "match_type": "auto",
            "is_invalid": 0, "category_name": None,
        }[k]
        cursor = MagicMock()
        cursor.fetchall.return_value = [row]
        self.mock_repo.execute_query.return_value = cursor

        result = self.service.get_all_splitwise_with_match_info()

        self.assertEqual(result[0]["match_status"], "auto")
        self.assertEqual(result[0]["linked_transaction"], "txn1")
        self.assertEqual(result[0]["category"], "")

    def test_get_all_splitwise_with_match_info_match_type_none_defaults_manual(self):
        row = MagicMock()
        row.__getitem__ = lambda self, k: {
            "id": "sw1", "amount": 50.0, "date": "2025-01-01",
            "description": "Test", "category_id": "cat1",
            "transaction_id": "txn1", "match_type": None,
            "is_invalid": 0, "category_name": "Food",
        }[k]
        cursor = MagicMock()
        cursor.fetchall.return_value = [row]
        self.mock_repo.execute_query.return_value = cursor

        result = self.service.get_all_splitwise_with_match_info()

        self.assertEqual(result[0]["match_status"], "manual")

    # ── get_splitwise_by_id / get_splitwise_by_transaction ───────────────────

    def test_get_splitwise_by_id(self):
        sw = make_splitwise()
        self.mock_repo.get_splitwise_by_id.return_value = sw
        result = self.service.get_splitwise_by_id("sw1")
        self.mock_repo.get_splitwise_by_id.assert_called_with("sw1")
        self.assertEqual(result, sw)

    def test_get_splitwise_by_transaction(self):
        sw = make_splitwise()
        self.mock_repo.get_splitwise_by_transaction_id.return_value = sw
        result = self.service.get_splitwise_by_transaction("txn1")
        self.mock_repo.get_splitwise_by_transaction_id.assert_called_with("txn1")
        self.assertEqual(result, sw)

    # ── link_transaction_to_splitwise ─────────────────────────────────────────

    def test_link_transaction_to_splitwise_success(self):
        self.mock_repo.get_splitwise_by_id.return_value = make_splitwise()
        self.service.link_transaction_to_splitwise("sw1", "txn1")
        self.mock_repo.set_transaction_to_splitwise.assert_called_with("sw1", "txn1")

    def test_link_transaction_to_splitwise_not_found(self):
        self.mock_repo.get_splitwise_by_id.return_value = None
        with self.assertRaises(ValueError) as ctx:
            self.service.link_transaction_to_splitwise("sw1", "txn1")
        self.assertIn("Splitwise não encontrado", str(ctx.exception))

    # ── get_splitwise_summary ─────────────────────────────────────────────────

    def test_get_splitwise_summary_with_data(self):
        settled = make_splitwise(transaction_id="txn1", amount=100.0)
        unsettled = make_splitwise(transaction_id=None, amount=50.0)
        self.mock_repo.get_all_splitwise.return_value = [settled, unsettled]

        result = self.service.get_splitwise_summary()

        self.assertEqual(result["total_entries"], 2)
        self.assertEqual(result["total_amount"], 150.0)
        self.assertEqual(result["settled"]["count"], 1)
        self.assertEqual(result["settled"]["amount"], 100.0)
        self.assertEqual(result["unsettled"]["count"], 1)
        self.assertEqual(result["unsettled"]["amount"], 50.0)

    def test_get_splitwise_summary_empty(self):
        self.mock_repo.get_all_splitwise.return_value = []
        result = self.service.get_splitwise_summary()
        self.assertEqual(result["total_entries"], 0)
        self.assertEqual(result["total_amount"], 0)

    # ── update_splitwise ──────────────────────────────────────────────────────

    def test_update_splitwise_success(self):
        self.mock_repo.get_splitwise_by_id.return_value = make_splitwise()
        self.service.update_splitwise("sw1", "catid", "txid")
        self.mock_repo.update_splitwise.assert_called_with("sw1", "catid", "txid")

    def test_update_splitwise_not_found(self):
        self.mock_repo.get_splitwise_by_id.return_value = None
        with self.assertRaises(ValueError) as ctx:
            self.service.update_splitwise("sw1", "catid", "txid")
        self.assertIn("Splitwise não encontrado", str(ctx.exception))

    # ── category_in_use ───────────────────────────────────────────────────────

    def test_category_in_use(self):
        self.mock_repo.category_in_use.return_value = True
        result = self.service.category_in_use("catid")
        self.mock_repo.category_in_use.assert_called_with("catid")
        self.assertTrue(result)

    # ── get_unsettled_splitwise ───────────────────────────────────────────────

    def test_get_unsettled_splitwise(self):
        self.mock_repo.get_unsettled_splitwise.return_value = [MagicMock()]
        result = self.service.get_unsettled_splitwise()
        self.mock_repo.get_unsettled_splitwise.assert_called()
        self.assertEqual(len(result), 1)

    # ── get_all_splitwise_including_invalid ───────────────────────────────────

    def test_get_all_splitwise_including_invalid(self):
        self.mock_repo.get_all_splitwise_including_invalid.return_value = [MagicMock(), MagicMock()]
        result = self.service.get_all_splitwise_including_invalid()
        self.assertEqual(len(result), 2)

    # ── invalidate / validate_splitwise_item ──────────────────────────────────

    def test_invalidate_splitwise_item_success(self):
        self.mock_repo.get_splitwise_by_id.return_value = make_splitwise()
        self.mock_repo.mark_splitwise_invalid.return_value = True
        result = self.service.invalidate_splitwise_item("sw1")
        self.assertTrue(result["success"])

    def test_invalidate_splitwise_item_not_found(self):
        self.mock_repo.get_splitwise_by_id.return_value = None
        result = self.service.invalidate_splitwise_item("sw1")
        self.assertFalse(result["success"])
        self.assertIn("não encontrado", result["error"])

    def test_invalidate_splitwise_item_failure(self):
        self.mock_repo.get_splitwise_by_id.return_value = make_splitwise()
        self.mock_repo.mark_splitwise_invalid.return_value = False
        result = self.service.invalidate_splitwise_item("sw1")
        self.assertFalse(result["success"])

    def test_invalidate_splitwise_item_exception(self):
        self.mock_repo.get_splitwise_by_id.side_effect = Exception("db error")
        result = self.service.invalidate_splitwise_item("sw1")
        self.assertFalse(result["success"])
        self.assertIn("db error", result["error"])

    def test_validate_splitwise_item_success(self):
        self.mock_repo.get_splitwise_by_id.return_value = make_splitwise()
        self.mock_repo.mark_splitwise_valid.return_value = True
        result = self.service.validate_splitwise_item("sw1")
        self.assertTrue(result["success"])

    def test_validate_splitwise_item_not_found(self):
        self.mock_repo.get_splitwise_by_id.return_value = None
        result = self.service.validate_splitwise_item("sw1")
        self.assertFalse(result["success"])

    def test_validate_splitwise_item_failure(self):
        self.mock_repo.get_splitwise_by_id.return_value = make_splitwise()
        self.mock_repo.mark_splitwise_valid.return_value = False
        result = self.service.validate_splitwise_item("sw1")
        self.assertFalse(result["success"])

    def test_validate_splitwise_item_exception(self):
        self.mock_repo.get_splitwise_by_id.side_effect = Exception("db error")
        result = self.service.validate_splitwise_item("sw1")
        self.assertFalse(result["success"])

    # ── edit_splitwise_item ───────────────────────────────────────────────────

    def test_edit_splitwise_item_success(self):
        self.mock_repo.get_splitwise_by_id.return_value = make_splitwise()
        self.mock_repo.update_splitwise_content.return_value = True
        result = self.service.edit_splitwise_item("sw1", "2025-01-01", 50.0)
        self.assertTrue(result["success"])

    def test_edit_splitwise_item_empty_date(self):
        result = self.service.edit_splitwise_item("sw1", "  ", 50.0)
        self.assertFalse(result["success"])
        self.assertIn("Data", result["error"])

    def test_edit_splitwise_item_zero_amount(self):
        result = self.service.edit_splitwise_item("sw1", "2025-01-01", 0)
        self.assertFalse(result["success"])
        self.assertIn("Valor", result["error"])

    def test_edit_splitwise_item_invalid_date_format(self):
        result = self.service.edit_splitwise_item("sw1", "01/01/2025", 50.0)
        self.assertFalse(result["success"])
        self.assertIn("data inválido", result["error"])

    def test_edit_splitwise_item_not_found(self):
        self.mock_repo.get_splitwise_by_id.return_value = None
        result = self.service.edit_splitwise_item("sw1", "2025-01-01", 50.0)
        self.assertFalse(result["success"])
        self.assertIn("não encontrado", result["error"])

    def test_edit_splitwise_item_repo_failure(self):
        self.mock_repo.get_splitwise_by_id.return_value = make_splitwise()
        self.mock_repo.update_splitwise_content.return_value = False
        result = self.service.edit_splitwise_item("sw1", "2025-01-01", 50.0)
        self.assertFalse(result["success"])

    def test_edit_splitwise_item_exception(self):
        self.mock_repo.get_splitwise_by_id.side_effect = Exception("db error")
        result = self.service.edit_splitwise_item("sw1", "2025-01-01", 50.0)
        self.assertFalse(result["success"])

    # ── _parse_date ───────────────────────────────────────────────────────────

    def test_parse_date_simple(self):
        result = self.service._parse_date("2025-01-15")
        self.assertEqual(result, datetime(2025, 1, 15))

    def test_parse_date_iso_format(self):
        result = self.service._parse_date("2025-10-07T13:08:53.002Z")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2025)

    def test_parse_date_newline_format(self):
        result = self.service._parse_date("2025-10-09\n09:17:57")
        self.assertEqual(result, datetime(2025, 10, 9))

    def test_parse_date_invalid(self):
        result = self.service._parse_date("not-a-date")
        self.assertIsNone(result)

    def test_parse_date_none(self):
        result = self.service._parse_date(None)
        self.assertIsNone(result)

    # ── _amounts_match ────────────────────────────────────────────────────────

    def test_amounts_match_equal(self):
        self.assertTrue(self.service._amounts_match(50.0, 50.0))

    def test_amounts_match_not_equal(self):
        self.assertFalse(self.service._amounts_match(50.0, 50.1))

    # ── _is_transaction_already_linked ────────────────────────────────────────

    def test_is_transaction_already_linked_true(self):
        self.mock_repo.get_splitwise_by_transaction_id.return_value = make_splitwise()
        self.assertTrue(self.service._is_transaction_already_linked("txn1"))

    def test_is_transaction_already_linked_false(self):
        self.mock_repo.get_splitwise_by_transaction_id.return_value = None
        self.assertFalse(self.service._is_transaction_already_linked("txn1"))

    # ── find_matching_transaction ─────────────────────────────────────────────

    def test_find_matching_transaction_no_date(self):
        sw = make_splitwise(date="invalid-date")
        with patch.object(self.service, "_parse_date", return_value=None):
            result = self.service.find_matching_transaction(sw)
        self.assertIsNone(result)

    def test_find_matching_transaction_exact_match(self):
        sw = make_splitwise(date="2025-01-01", amount=50.0)
        txn = MagicMock()
        txn.amount = 100.0
        txn.transaction_id = "txn1"
        self.mock_repo.get_bank_transactions_by_date.return_value = [txn]
        self.mock_repo.get_credit_transactions_by_date.return_value = []
        self.mock_repo.get_splitwise_by_transaction_id.return_value = None

        result = self.service.find_matching_transaction(sw)
        self.assertEqual(result, txn)

    def test_find_matching_transaction_no_match(self):
        sw = make_splitwise(date="2025-01-01", amount=30.0)
        txn = MagicMock()
        txn.amount = 100.0
        txn.transaction_id = "txn1"
        self.mock_repo.get_bank_transactions_by_date.return_value = [txn]
        self.mock_repo.get_credit_transactions_by_date.return_value = []

        result = self.service.find_matching_transaction(sw)
        self.assertIsNone(result)

    def test_find_matching_transaction_ambiguous(self):
        sw = make_splitwise(date="2025-01-01", amount=50.0)
        txn1 = MagicMock()
        txn1.amount = 100.0
        txn1.transaction_id = "txn1"
        txn2 = MagicMock()
        txn2.amount = 100.0
        txn2.transaction_id = "txn2"
        self.mock_repo.get_bank_transactions_by_date.return_value = [txn1, txn2]
        self.mock_repo.get_credit_transactions_by_date.return_value = []
        self.mock_repo.get_splitwise_by_transaction_id.return_value = None

        result = self.service.find_matching_transaction(sw)
        self.assertIsNone(result)

    def test_find_matching_transaction_already_linked(self):
        sw = make_splitwise(date="2025-01-01", amount=50.0)
        txn = MagicMock()
        txn.amount = 100.0
        txn.transaction_id = "txn1"
        self.mock_repo.get_bank_transactions_by_date.return_value = [txn]
        self.mock_repo.get_credit_transactions_by_date.return_value = []
        self.mock_repo.get_splitwise_by_transaction_id.return_value = make_splitwise()

        result = self.service.find_matching_transaction(sw)
        self.assertIsNone(result)

    def test_find_matching_transaction_exception(self):
        sw = make_splitwise(date="2025-01-01")
        self.mock_repo.get_bank_transactions_by_date.side_effect = Exception("db error")
        result = self.service.find_matching_transaction(sw)
        self.assertIsNone(result)

    # ── apply_match ───────────────────────────────────────────────────────────

    def test_apply_match_success(self):
        sw = make_splitwise()
        txn = MagicMock()
        self.mock_repo.set_transaction_to_splitwise.return_value = True
        result = self.service.apply_match(sw, txn)
        self.assertTrue(result)
        self.mock_repo.update_match_type.assert_called_with(sw.splitwise_id, "auto")

    def test_apply_match_failure(self):
        sw = make_splitwise()
        txn = MagicMock()
        self.mock_repo.set_transaction_to_splitwise.return_value = False
        result = self.service.apply_match(sw, txn)
        self.assertFalse(result)

    def test_apply_match_exception(self):
        sw = make_splitwise()
        txn = MagicMock()
        self.mock_repo.set_transaction_to_splitwise.side_effect = Exception("db error")
        result = self.service.apply_match(sw, txn)
        self.assertFalse(result)

    # ── auto_match_splitwise_transactions ─────────────────────────────────────

    def test_auto_match_no_unmatched(self):
        self.mock_repo.get_unsettled_splitwise.return_value = []
        result = self.service.auto_match_splitwise_transactions()
        self.assertEqual(result["total_processed"], 0)
        self.assertEqual(result["matches_applied"], 0)

    def test_auto_match_with_match(self):
        sw = make_splitwise()
        txn = MagicMock()
        self.mock_repo.get_unsettled_splitwise.return_value = [sw]
        with patch.object(self.service, "find_matching_transaction", return_value=txn):
            with patch.object(self.service, "apply_match", return_value=True):
                result = self.service.auto_match_splitwise_transactions()
        self.assertEqual(result["matches_found"], 1)
        self.assertEqual(result["matches_applied"], 1)

    def test_auto_match_no_match_found(self):
        sw = make_splitwise()
        self.mock_repo.get_unsettled_splitwise.return_value = [sw]
        with patch.object(self.service, "find_matching_transaction", return_value=None):
            result = self.service.auto_match_splitwise_transactions()
        self.assertEqual(result["matches_found"], 0)

    def test_auto_match_per_entry_exception(self):
        sw = make_splitwise()
        self.mock_repo.get_unsettled_splitwise.return_value = [sw]
        with patch.object(self.service, "find_matching_transaction", side_effect=Exception("err")):
            result = self.service.auto_match_splitwise_transactions()
        self.assertEqual(len(result["errors"]), 1)

    def test_auto_match_critical_exception(self):
        self.mock_repo.get_unsettled_splitwise.side_effect = Exception("critical")
        result = self.service.auto_match_splitwise_transactions()
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("critical", result["errors"][0])

    # ── get_matching_statistics ───────────────────────────────────────────────

    def test_get_matching_statistics_with_data(self):
        self.mock_repo.get_all_splitwise.return_value = [MagicMock(), MagicMock()]
        auto_row = MagicMock()
        auto_row.__getitem__ = lambda self, k: {"match_type": "auto", "count": 1}[k]
        manual_row = MagicMock()
        manual_row.__getitem__ = lambda self, k: {"match_type": "manual", "count": 1}[k]
        cursor = MagicMock()
        cursor.fetchall.return_value = [auto_row, manual_row]
        self.mock_repo.execute_query.return_value = cursor

        result = self.service.get_matching_statistics()

        self.assertEqual(result["total_splitwise"], 2)
        self.assertEqual(result["auto_matched"], 1)
        self.assertEqual(result["manual_matched"], 1)
        self.assertIn("auto_match_rate", result)

    def test_get_matching_statistics_empty(self):
        self.mock_repo.get_all_splitwise.return_value = []
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        self.mock_repo.execute_query.return_value = cursor

        result = self.service.get_matching_statistics()

        self.assertEqual(result["total_splitwise"], 0)
        self.assertEqual(result["auto_match_rate"], 0)
        self.assertEqual(result["total_match_rate"], 0)

    def test_get_matching_statistics_exception(self):
        self.mock_repo.get_all_splitwise.side_effect = Exception("db error")
        result = self.service.get_matching_statistics()
        self.assertEqual(result, {})

    # ── create_splitwise ──────────────────────────────────────────────────────

    def test_create_splitwise_missing_id(self):
        with self.assertRaises(ValueError) as ctx:
            self.service.create_splitwise({})
        self.assertEqual(str(ctx.exception), "ID da entrada do Splitwise é obrigatório")

    def test_create_splitwise_missing_description(self):
        with self.assertRaises(ValueError) as ctx:
            self.service.create_splitwise({"id": "123"})
        self.assertEqual(str(ctx.exception), "Descrição é obrigatória")

    def test_create_splitwise_missing_amount(self):
        with self.assertRaises(ValueError) as ctx:
            self.service.create_splitwise({"id": "123", "description": "test"})
        self.assertEqual(str(ctx.exception), "Valor é obrigatório")

    def test_create_splitwise_missing_date(self):
        with self.assertRaises(ValueError) as ctx:
            self.service.create_splitwise(
                {"id": "123", "description": "test", "amount": 10}
            )
        self.assertEqual(str(ctx.exception), "Data é obrigatória")

    def test_create_splitwise_invalid_string_date(self):
        with patch.object(self.service, "_parse_date", return_value=None):
            with self.assertRaises(ValueError) as ctx:
                self.service.create_splitwise(
                    {"id": "123", "description": "test", "amount": 10, "date": "invalid-date"}
                )
        self.assertEqual(str(ctx.exception), "Formato de data inválido. Use YYYY-MM-DD")

    def test_create_splitwise_invalid_date_exception(self):
        with patch.object(self.service, "_parse_date", side_effect=ValueError("Invalid")):
            with self.assertRaises(ValueError) as ctx:
                self.service.create_splitwise(
                    {"id": "123", "description": "test", "amount": 10, "date": "2023-13-01"}
                )
        self.assertEqual(str(ctx.exception), "Formato de data inválido. Use YYYY-MM-DD")

    def test_create_splitwise_invalid_amount_string(self):
        with self.assertRaises(ValueError) as ctx:
            self.service.create_splitwise(
                {"id": "123", "description": "test", "amount": "not-a-number", "date": datetime(2023, 1, 1)}
            )
        self.assertEqual(str(ctx.exception), "Valor deve ser um número")

    def test_create_splitwise_invalid_amount_none(self):
        with self.assertRaises(ValueError) as ctx:
            self.service.create_splitwise(
                {"id": "123", "description": "test", "amount": None, "date": datetime(2023, 1, 1)}
            )
        self.assertEqual(str(ctx.exception), "Valor é obrigatório")

    def test_create_splitwise_success_datetime(self):
        splitwise_data = {
            "id": "123", "description": "test expense",
            "amount": 50.0, "date": datetime(2023, 1, 15),
        }
        mock_created = MagicMock()
        self.mock_repo.create_splitwise.return_value = mock_created

        result = self.service.create_splitwise(splitwise_data)

        self.mock_repo.create_splitwise.assert_called_once()
        args = self.mock_repo.create_splitwise.call_args[0][0]
        self.assertEqual(args.splitwise_id, "123")
        self.assertEqual(args.amount, 50.0)
        self.assertEqual(result, mock_created)

    def test_create_splitwise_amount_too_small(self):
        with self.assertRaises(ValueError) as ctx:
            self.service.create_splitwise(
                {"id": "123", "description": "test", "amount": 0.005, "date": datetime(2023, 1, 1)}
            )
        self.assertEqual(str(ctx.exception), "Valor deve ser maior que 0.01")

    def test_create_splitwise_calls_repository(self):
        mock_created = MagicMock()
        self.mock_repo.create_splitwise.return_value = mock_created
        result = self.service.create_splitwise(
            {"id": "123", "description": "test", "amount": 10.0, "date": datetime(2023, 1, 1)}
        )
        self.mock_repo.create_splitwise.assert_called_once()
        self.assertEqual(result, mock_created)

    # ── delete_splitwise ──────────────────────────────────────────────────────

    def test_delete_splitwise_missing_id(self):
        with self.assertRaises(ValueError) as ctx:
            self.service.delete_splitwise("")
        self.assertEqual(str(ctx.exception), "ID da entrada do Splitwise é obrigatório")

    def test_delete_splitwise_missing_id_none(self):
        with self.assertRaises(ValueError) as ctx:
            self.service.delete_splitwise(None)
        self.assertEqual(str(ctx.exception), "ID da entrada do Splitwise é obrigatório")

    def test_delete_splitwise_not_found(self):
        self.mock_repo.get_splitwise_by_id.return_value = None
        with self.assertRaises(ValueError) as ctx:
            self.service.delete_splitwise("123")
        self.assertEqual(str(ctx.exception), "Entrada do Splitwise com ID 123 não encontrada")

    def test_delete_splitwise_with_transaction_warning(self):
        mock_sw = MagicMock()
        mock_sw.transaction_id = "txn123"
        mock_sw.description = "Test Entry"
        self.mock_repo.get_splitwise_by_id.return_value = mock_sw
        self.mock_repo.delete_splitwise.return_value = True

        with patch("builtins.print") as mock_print:
            result = self.service.delete_splitwise("123")
            mock_print.assert_called_once_with(
                "Aviso: Deletando entrada do Splitwise 'Test Entry' que estava vinculada à transação txn123"
            )
        self.assertTrue(result)

    def test_delete_splitwise_calls_repository(self):
        mock_sw = MagicMock()
        mock_sw.transaction_id = None
        self.mock_repo.get_splitwise_by_id.return_value = mock_sw
        self.mock_repo.delete_splitwise.return_value = True

        result = self.service.delete_splitwise("123")

        self.mock_repo.delete_splitwise.assert_called_once_with("123")
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
