from typing import Any, Dict
from repositories.settings_repository import SettingsRepository


class SettingsService:
    def __init__(self):
        self.settings_repository = SettingsRepository()

    def update_credit_card_dates(self, closing_day: int, due_day: int):
        """Atualiza as datas do cartão de crédito"""
        if not (1 <= closing_day <= 31 and 1 <= due_day <= 31):
            raise ValueError("Dias devem estar entre 1 e 31")

        self.settings_repository.set_value(
            "credit_card_dates", {"closing_day": closing_day, "due_day": due_day}
        )

    def get_credit_card_dates(self) -> Dict[str, int]:
        """Retorna as datas do cartão de crédito"""
        return self.settings_repository.get_value("credit_card_dates") or {
            "closing_day": 1,
            "due_day": 10,
        }

    def get_all_settings(self) -> Dict[str, Any]:
        """Retorna todas as configurações"""
        return self.settings_repository.get_all()
