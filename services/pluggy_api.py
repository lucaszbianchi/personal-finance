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
        self.api_key = self._get_auth_token()

    def _get_auth_token(self):
        payload = {
            "clientId": os.getenv("CLIENT_ID"),
            "clientSecret": os.getenv("CLIENT_SECRET"),
        }
        headers = {"accept": "application/json", "content-type": "application/json"}

        url = f"{self.base_url}/auth"
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        return json.loads(response.content).get("apiKey")

    def fetch_accounts(self):

        url = f"{self.base_url}/accounts?itemId={self.item_id}"

        headers = {"accept": "application/json", "X-API-KEY": f"{self.api_key}"}

        response = requests.get(url, headers=headers, timeout=30)
        return response

    def fetch_and_store_data(self):
        headers = {"accept": "application/json", "X-API-KEY": f"{self.api_key}"}
        accounts = json.loads(self.fetch_accounts().content).get("results")
        for account in accounts:
            account_type = account.get("type")
            if account_type in ["BANK", "CREDIT"]:
                account_id = account.get("id")

                url = f"{self.base_url}/transactions?accountId={account_id}&pageSize=100&page=1"

                response = requests.get(url, headers=headers, timeout=30)
                transactions = []
                total_pages = json.loads(response.content).get("totalPages")
                transactions.extend(json.loads(response.content).get("results"))
                for page in range(2, total_pages + 1):
                    url = f"{self.base_url}/transactions?accountId={account_id}&pageSize=100&page={page}"
                    response = requests.get(url, headers=headers, timeout=30)
                    transactions.extend(json.loads(response.content).get("results"))
                if account_type == "BANK":
                    print(transactions[0])
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
