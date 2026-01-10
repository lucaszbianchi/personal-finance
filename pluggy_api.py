import requests
import json
import os
import dotenv

from repositories.transaction_repository import TransactionRepository
from repositories.investment_repository import InvestmentRepository
from repositories.splitwise_repository import SplitwiseRepository


class PluggyAPI:
    """
    A class to interact with the Pluggy API to fetch and store financial data.
    """

    def __init__(self):
        dotenv.load_dotenv()
        self.base_url = "https://api.pluggy.ai"
        self.item_id = os.getenv("ITEM_ID")
        self.splitwise_item_id = os.getenv("ITEM_ID_SPLITWISE")
        self.api_key = self._create_api_key()

        consents = self.list_consents()
        accounts = self.list_accounts(self.item_id)
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

    def list_accounts(self, item_id):

        url = f"{self.base_url}/accounts?itemId={item_id}"

        headers = {"accept": "application/json", "X-API-KEY": f"{self.api_key}"}

        response = requests.get(url, headers=headers, timeout=30)
        return json.loads(response.content)

    def list_transactions(self, account_id, page_size=100, page=1):

        url = f"{self.base_url}/transactions?accountId={account_id}&pageSize={page_size}&page={page}"
        headers = {"accept": "application/json", "X-API-KEY": f"{self.api_key}"}
        response = requests.get(url, headers=headers, timeout=30)
        return json.loads(response.content)

    def fetch_and_store_data(self):
        accounts = self.list_accounts(self.item_id).get("results")
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

        url = f"{self.base_url}/investments?itemId={item_id}&pageSize=100"

        response = requests.get(url, headers=headers, timeout=30)
        investments = json.loads(response.content).get("results")
        self._save_incremental_json("data/investments.json", investments)

    def fetch_and_store_splitwise_data(self):
        accounts = self.list_accounts(self.splitwise_item_id).get("results")
        for account in accounts:
            if account.get("name") == os.getenv("SPLITWISE_ACCOUNT_NAME"):
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
                    "data/splitwise_transactions.json", transactions
                )

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

    def fetch_and_store_data_to_db(self):
        """
        Nova implementação: busca dados da API e salva diretamente no banco usando repositórios.
        Mantém arquivos JSON em paralelo apenas para debug/desenvolvimento.
        """
        # Inicializa repositórios
        transaction_repo = TransactionRepository()
        investment_repo = InvestmentRepository()
        splitwise_repo = SplitwiseRepository()

        try:
            print("🔄 Iniciando coleta de dados da API...")

            # 1. Processa transações bancárias e de cartão
            accounts = self.list_accounts(self.item_id).get("results", [])
            for account in accounts:
                account_type = account.get("type")
                if account_type in ["BANK", "CREDIT"]:
                    account_id = account.get("id")
                    print(f"Processando conta {account_type}: {account_id}")

                    # Busca todas as transações da conta
                    transactions = []
                    first_100_transactions = self.list_transactions(
                        account_id, page_size=100, page=1
                    )
                    total_pages = first_100_transactions.get("totalPages", 1)
                    transactions.extend(first_100_transactions.get("results", []))

                    for page in range(2, total_pages + 1):
                        page_transactions = self.list_transactions(
                            account_id, page_size=100, page=page
                        )
                        transactions.extend(page_transactions.get("results", []))

                    # Salva no banco usando repositórios
                    for transaction in transactions:
                        if account_type == "BANK":
                            result = transaction_repo.upsert_bank_transaction(
                                transaction
                            )
                        elif account_type == "CREDIT":
                            result = transaction_repo.upsert_credit_transaction(
                                transaction
                            )

                        if not result["success"]:
                            print(
                                f"Erro ao processar transação {transaction['id']}: {result.get('error', 'Erro desconhecido')}"
                            )

                    # Mantém arquivo JSON para debug (temporário)
                    self._save_incremental_json(
                        f"data/{account_type}_transactions.json", transactions
                    )
                    print(
                        f"✅ Processadas {len(transactions)} transações do tipo {account_type}"
                    )

            # 2. Processa investimentos
            print("💰 Processando investimentos...")
            investments = self.fetch_investments_data()
            for investment in investments:
                result = investment_repo.upsert_investment(investment)
                if not result["success"]:
                    print(
                        f"Erro ao processar investimento {investment['id']}: {result.get('error', 'Erro desconhecido')}"
                    )

            # Mantém arquivo JSON para debug (temporário)
            if investments:
                self._save_incremental_json("data/investments.json", investments)
                print(f"Processados {len(investments)} investimentos")

            # 3. Processa transações Splitwise
            print("Processando transações Splitwise...")
            splitwise_transactions = self.fetch_splitwise_data()
            for transaction in splitwise_transactions:
                result = splitwise_repo.upsert_splitwise_transaction(transaction)
                if not result["success"]:
                    print(
                        f"Erro ao processar Splitwise {transaction['id']}: {result.get('error', 'Erro desconhecido')}"
                    )

            # Mantém arquivo JSON para debug (temporário)
            if splitwise_transactions:
                self._save_incremental_json(
                    "data/splitwise_transactions.json", splitwise_transactions
                )
                print(f"Processadas {len(splitwise_transactions)} transações Splitwise")

            print("Coleta de dados concluída com sucesso!")

        finally:
            # Fecha conexões dos repositórios
            transaction_repo.close()
            investment_repo.close()
            splitwise_repo.close()

    def fetch_investments_data(self) -> list:
        """Busca dados de investimentos da API"""
        headers = {"accept": "application/json", "X-API-KEY": f"{self.api_key}"}
        item_id = os.getenv("ITEM_ID")
        url = f"{self.base_url}/investments?itemId={item_id}&pageSize=100"

        response = requests.get(url, headers=headers, timeout=30)
        return json.loads(response.content).get("results", [])

    def fetch_splitwise_data(self) -> list:
        """Busca dados do Splitwise da API"""
        accounts = self.list_accounts(self.splitwise_item_id).get("results", [])
        splitwise_transactions = []

        for account in accounts:
            if account.get("name") == os.getenv("SPLITWISE_ACCOUNT_NAME"):
                account_id = account.get("id")
                transactions = []
                first_100_transactions = self.list_transactions(
                    account_id, page_size=100, page=1
                )
                total_pages = first_100_transactions.get("totalPages", 1)
                transactions.extend(first_100_transactions.get("results", []))

                for page in range(2, total_pages + 1):
                    page_transactions = self.list_transactions(
                        account_id, page_size=100, page=page
                    )
                    transactions.extend(page_transactions.get("results", []))

                splitwise_transactions.extend(transactions)
                break

        return splitwise_transactions


if __name__ == "__main__":
    api = PluggyAPI()
