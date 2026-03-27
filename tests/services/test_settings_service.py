"""Testes para SettingsService"""

import unittest
from unittest.mock import MagicMock, patch
from services.settings_service import SettingsService


class TestSettingsService(unittest.TestCase):
    """Testes para a classe SettingsService"""

    def setUp(self):
        # Patch repository dependency
        with patch("services.settings_service.SettingsRepository"):
            self.service = SettingsService()

        # Create mock for repository
        self.mock_settings_repo = MagicMock()
        self.service.settings_repository = self.mock_settings_repo

    def test_update_credit_card_dates_valid_days(self):
        """Testa atualização válida das datas do cartão de crédito"""
        # Act
        self.service.update_credit_card_dates(closing_day=15, due_day=25)

        # Assert
        self.mock_settings_repo.set_value.assert_called_once_with(
            "credit_card_dates", {"closing_day": 15, "due_day": 25}
        )

    def test_update_credit_card_dates_boundary_values(self):
        """Testa valores limite válidos para datas do cartão"""
        # Test minimum valid values
        self.service.update_credit_card_dates(closing_day=1, due_day=1)
        self.mock_settings_repo.set_value.assert_called_with(
            "credit_card_dates", {"closing_day": 1, "due_day": 1}
        )

        # Test maximum valid values
        self.service.update_credit_card_dates(closing_day=31, due_day=31)
        self.mock_settings_repo.set_value.assert_called_with(
            "credit_card_dates", {"closing_day": 31, "due_day": 31}
        )

    def test_update_credit_card_dates_invalid_closing_day_too_low(self):
        """Testa erro com dia de fechamento muito baixo"""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.service.update_credit_card_dates(closing_day=0, due_day=15)

        self.assertEqual(str(context.exception), "Dias devem estar entre 1 e 31")
        self.mock_settings_repo.set_value.assert_not_called()

    def test_update_credit_card_dates_invalid_closing_day_too_high(self):
        """Testa erro com dia de fechamento muito alto"""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.service.update_credit_card_dates(closing_day=32, due_day=15)

        self.assertEqual(str(context.exception), "Dias devem estar entre 1 e 31")
        self.mock_settings_repo.set_value.assert_not_called()

    def test_update_credit_card_dates_invalid_due_day_too_low(self):
        """Testa erro com dia de vencimento muito baixo"""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.service.update_credit_card_dates(closing_day=15, due_day=0)

        self.assertEqual(str(context.exception), "Dias devem estar entre 1 e 31")
        self.mock_settings_repo.set_value.assert_not_called()

    def test_update_credit_card_dates_invalid_due_day_too_high(self):
        """Testa erro com dia de vencimento muito alto"""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.service.update_credit_card_dates(closing_day=15, due_day=32)

        self.assertEqual(str(context.exception), "Dias devem estar entre 1 e 31")
        self.mock_settings_repo.set_value.assert_not_called()

    def test_update_credit_card_dates_both_days_invalid(self):
        """Testa erro quando ambos os dias são inválidos"""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.service.update_credit_card_dates(closing_day=0, due_day=32)

        self.assertEqual(str(context.exception), "Dias devem estar entre 1 e 31")
        self.mock_settings_repo.set_value.assert_not_called()

    def test_get_credit_card_dates_with_existing_value(self):
        """Testa obtenção de datas existentes do cartão de crédito"""
        # Arrange
        expected_dates = {"closing_day": 20, "due_day": 30}
        self.mock_settings_repo.get_value.return_value = expected_dates

        # Act
        result = self.service.get_credit_card_dates()

        # Assert
        self.mock_settings_repo.get_value.assert_called_once_with("credit_card_dates")
        self.assertEqual(result, expected_dates)

    def test_get_credit_card_dates_with_no_existing_value(self):
        """Testa obtenção de datas padrão do cartão de crédito quando não existe"""
        # Arrange
        self.mock_settings_repo.get_value.return_value = None

        # Act
        result = self.service.get_credit_card_dates()

        # Assert
        self.mock_settings_repo.get_value.assert_called_once_with("credit_card_dates")
        expected_default = {"closing_day": 1, "due_day": 10}
        self.assertEqual(result, expected_default)

    def test_get_all_settings(self):
        """Testa obtenção de todas as configurações"""
        # Arrange
        expected_settings = {
            "meal_allowance": {"active": True, "value": 50.0},
            "credit_card_dates": {"closing_day": 15, "due_day": 25},
            "other_setting": "value"
        }
        self.mock_settings_repo.get_all.return_value = expected_settings

        # Act
        result = self.service.get_all_settings()

        # Assert
        self.mock_settings_repo.get_all.assert_called_once()
        self.assertEqual(result, expected_settings)

    def test_get_all_settings_empty_repository(self):
        """Testa obtenção de configurações quando repositório está vazio"""
        # Arrange
        self.mock_settings_repo.get_all.return_value = {}

        # Act
        result = self.service.get_all_settings()

        # Assert
        self.mock_settings_repo.get_all.assert_called_once()
        self.assertEqual(result, {})

    # ── get_optional_expenses_target ──

    def test_get_optional_expenses_target_returns_stored_value(self):
        """Testa retorno da meta de gastos opcionais quando existe valor salvo"""
        self.mock_settings_repo.get_value.return_value = 500.0

        result = self.service.get_optional_expenses_target()

        self.mock_settings_repo.get_value.assert_called_once_with("optional_expenses_target")
        self.assertEqual(result, 500.0)

    def test_get_optional_expenses_target_returns_zero_when_none(self):
        """Testa retorno de 0.0 quando nenhum valor está salvo"""
        self.mock_settings_repo.get_value.return_value = None

        result = self.service.get_optional_expenses_target()

        self.assertEqual(result, 0.0)

    # ── update_optional_expenses_target ──

    def test_update_optional_expenses_target_saves_value(self):
        """Testa salvamento válido da meta de gastos opcionais"""
        self.service.update_optional_expenses_target(300.0)

        self.mock_settings_repo.set_value.assert_called_once_with("optional_expenses_target", 300.0)

    def test_update_optional_expenses_target_allows_zero(self):
        """Testa que meta zero é válida"""
        self.service.update_optional_expenses_target(0.0)

        self.mock_settings_repo.set_value.assert_called_once_with("optional_expenses_target", 0.0)

    def test_update_optional_expenses_target_raises_on_negative(self):
        """Testa erro quando valor negativo é fornecido"""
        with self.assertRaises(ValueError) as context:
            self.service.update_optional_expenses_target(-50.0)

        self.assertIn("negativa", str(context.exception))
        self.mock_settings_repo.set_value.assert_not_called()


if __name__ == "__main__":
    unittest.main()