from repositories.settings_repository import SettingsRepository
from repositories.pluggy_item_repository import PluggyItemRepository


class OnboardingService:
    def __init__(self):
        self.settings_repo = SettingsRepository()
        self.pluggy_item_repo = PluggyItemRepository()

    def get_status(self) -> dict:
        """Retorna o status do onboarding com flags booleanas para cada etapa."""
        has_credentials = self._has_credentials()
        has_pluggy_items = len(self.pluggy_item_repo.get_items_by_role("bank")) > 0
        has_transactions = self._has_transactions()
        has_history = self._has_rows("finance_history")
        onboarding_completed = bool(
            self.settings_repo.get_value("onboarding_completed")
        )

        return {
            "has_credentials": has_credentials,
            "has_pluggy_items": has_pluggy_items,
            "has_transactions": has_transactions,
            "has_history": has_history,
            "is_complete": onboarding_completed
            or all([has_credentials, has_pluggy_items, has_transactions, has_history]),
        }

    def mark_complete(self) -> None:
        """Marca o onboarding como concluido."""
        self.settings_repo.set_value("onboarding_completed", True)

    def restart(self) -> dict:
        """Limpa o flag de conclusao e retorna o status atual."""
        self.settings_repo.delete_value("onboarding_completed")
        return self.get_status()

    def save_credentials(self, client_id: str, client_secret: str) -> None:
        """Salva credenciais Pluggy na tabela settings."""
        if not client_id or not client_id.strip():
            raise ValueError("client_id e obrigatorio")
        if not client_secret or not client_secret.strip():
            raise ValueError("client_secret e obrigatorio")

        self.settings_repo.set_value("pluggy_client_id", client_id.strip())
        self.settings_repo.set_value("pluggy_client_secret", client_secret.strip())

    def _has_credentials(self) -> bool:
        client_id = self.settings_repo.get_value("pluggy_client_id")
        client_secret = self.settings_repo.get_value("pluggy_client_secret")
        return bool(client_id) and bool(client_secret)

    def _has_transactions(self) -> bool:
        return self._has_rows("bank_transactions") or self._has_rows(
            "credit_transactions"
        )

    _ALLOWED_TABLES = {"bank_transactions", "credit_transactions", "finance_history"}

    def _has_rows(self, table: str) -> bool:
        if table not in self._ALLOWED_TABLES:
            raise ValueError(f"Tabela nao permitida: {table}")
        cursor = self.settings_repo.execute_query(f"SELECT 1 FROM {table} LIMIT 1")
        return cursor.fetchone() is not None
