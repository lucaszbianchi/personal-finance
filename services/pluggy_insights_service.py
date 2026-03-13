from datetime import datetime, timezone
import requests
from repositories.pluggy_insights_repository import PluggyInsightsRepository


class PluggyInsightsService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.pluggy.ai"
        self.repo = PluggyInsightsRepository()

    def _headers(self) -> dict:
        return {"accept": "application/json", "X-API-KEY": self.api_key}

    def fetch_book(self, item_id: str) -> dict:
        url = f"{self.base_url}/insights/book?itemId={item_id}"
        response = requests.get(url, headers=self._headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def store_book(self, item_id: str, month: str, data: dict) -> None:
        book = data.get("book", {})
        bank_account = book.get("bankAccount", {})
        credit_card = book.get("creditCard", {})
        categories = book.get("categories", [])
        fetched_at = datetime.now(timezone.utc).isoformat()

        self.repo.upsert_book_summary(item_id, month, bank_account, credit_card, fetched_at)

        for entry in categories:
            periods = {k: v for k, v in entry.items() if k in ("M1", "M2", "M3", "M6", "M12")}
            self.repo.upsert_book_category(
                item_id=item_id,
                month=month,
                category=entry.get("category", ""),
                transaction_type=entry.get("transactionType", ""),
                account_subtype=entry.get("accountSubtype", ""),
                periods=periods,
                fetched_at=fetched_at,
            )

    def fetch_and_store(self, item_ids: list, month: str) -> None:
        for item_id in item_ids:
            try:
                data = self.fetch_book(item_id)
                self.store_book(item_id, month, data)
                print(f"  [OK] Pluggy Insights (book) salvo para item {item_id}, mês {month}")
            except Exception as e:
                print(f"  [WARN] Erro ao buscar Insights para item {item_id}: {e}")
