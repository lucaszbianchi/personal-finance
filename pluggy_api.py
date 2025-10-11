import requests
import json
import os
import dotenv


class PluggyAPI:
    """
    A class to interact with the Pluggy API to fetch and store financial data.
    """

    def __init__(self):
        dotenv.load_dotenv()
        self.base_url = "https://api.pluggy.ai"
        self.item_id = os.getenv("ITEM_ID")
        self.api_key = self._create_api_key()

        consents = self.list_consents()
        accounts = self.list_accounts()
        self._save_base_data_first_time("data/consents.json", consents.get("results"))
        self._save_base_data_first_time("data/accounts.json", accounts.get("results"))

    def _create_api_key(self):
        """API Key: This access token has an expiration time of 2 hours and it's meant to be used by backend applications to recover users' data.

        With this token you can:

        Create Connect Tokens
        Read User's Data for all products (Account, Transaction, Investment, Identity, Opportunity).
        Configure Webhooks.
        Create, Update & Delete Items.
        Review Connectors (Financial Institutions) & Transaction's Category tree."""

        payload = {
            "clientId": os.getenv("CLIENT_ID"),
            "clientSecret": os.getenv("CLIENT_SECRET"),
        }
        headers = {"accept": "application/json", "content-type": "application/json"}

        url = f"{self.base_url}/auth"
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        return json.loads(response.content).get("apiKey")

    def list_consents(self):
        url = f"{self.base_url}/consents?itemId={self.item_id}"

        headers = {"accept": "application/json", "X-API-KEY": f"{self.api_key}"}

        response = requests.get(url, headers=headers, timeout=30)
        return json.loads(response.content)

    def list_accounts(self):

        url = f"{self.base_url}/accounts?itemId={self.item_id}"

        headers = {"accept": "application/json", "X-API-KEY": f"{self.api_key}"}

        response = requests.get(url, headers=headers, timeout=30)
        return json.loads(response.content)

    def list_transactions(self, account_id, page_size=100, page=1):

        url = f"{self.base_url}/transactions?accountId={account_id}&pageSize={page_size}&page={page}"
        headers = {"accept": "application/json", "X-API-KEY": f"{self.api_key}"}
        response = requests.get(url, headers=headers, timeout=30)
        return json.loads(response.content)

    def fetch_and_store_data(self):
        accounts = self.list_accounts().get("results")
        for account in accounts:
            account_type = account.get("type")
            if account_type in ["BANK", "CREDIT"]:
                account_id = account.get("id")
                transactions = []
                first_100_transactions = self.list_transactions(
                    account_id, page_size=100, page=1
                )
                total_pages = first_100_transactions.get("totalPages")
                transactions.extend(first_100_transactions.get("results"))
                for page in range(2, total_pages + 1):
                    page_transactions = self.list_transactions(
                        account_id, page_size=100, page=page
                    )
                    transactions.extend(page_transactions.get("results"))
                # Salva incrementalmente as transações em um arquivo .json
                self._save_incremental_json(
                    f"data/{account_type}_transactions.json", transactions
                )

    def fetch_and_store_investments(self):
        headers = {"accept": "application/json", "X-API-KEY": f"{self.api_key}"}
        item_id = os.getenv("ITEM_ID")

        url = f"{self.base_url}/investments?itemId={item_id}&pageSize=57"

        response = requests.get(url, headers=headers, timeout=30)
        investments = json.loads(response.content).get("results")
        self._save_incremental_json("data/investments.json", investments)

    def _load_existing_json(self, filepath):
        if os.path.exists(filepath):
            print(f"Carregando dados existentes de {filepath}")
            with open(filepath, "r", encoding="utf-8") as f:
                return {item["id"]: item for item in json.load(f)}
        return {}

    def _save_incremental_json(self, filepath, new_items):
        existing = self._load_existing_json(filepath)
        for item in new_items:
            existing[item["id"]] = item
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(list(existing.values()), f, ensure_ascii=False, indent=4)

    def _save_base_data_first_time(self, filepath, items):
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=4)
