from datetime import datetime, timedelta, timezone
import json
import os
import requests
import dotenv

from repositories.transaction_repository import TransactionRepository
from repositories.investment_repository import InvestmentRepository
from repositories.splitwise_repository import SplitwiseRepository

INCREMENTAL_DAYS = 7


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

    def list_transactions(
        self, account_id, page_size=500, page=1, from_date=None, to_date=None
    ):
        url = f"{self.base_url}/transactions?accountId={account_id}&pageSize={page_size}&page={page}"
        if from_date:
            url += f"&from={from_date}"
        if to_date:
            url += f"&to={to_date}"
        headers = {"accept": "application/json", "X-API-KEY": f"{self.api_key}"}
        response = requests.get(url, headers=headers, timeout=30)
        return json.loads(response.content)

    def fetch_and_store_data(self):
        from_date, to_date = self._incremental_date_range()
        accounts = self.list_accounts(self.item_id).get("results")
        for account in accounts:
            account_type = account.get("type")
            if account_type in ["BANK", "CREDIT"]:
                account_id = account.get("id")
                transactions = self._fetch_all_pages(account_id, from_date, to_date)
                self._save_incremental_json(
                    f"data/{account_type}_transactions.json", transactions
                )

    def _incremental_date_range(self):
        """Retorna tupla (from_date, to_date) para janela incremental de INCREMENTAL_DAYS dias."""
        today = datetime.now(timezone.utc)
        from_dt = today - timedelta(days=INCREMENTAL_DAYS)
        return from_dt.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

    def _fetch_all_pages(self, account_id, from_date=None, to_date=None):
        """Busca todas as páginas de transações de uma conta com filtro de data opcional."""
        transactions = []
        first_page = self.list_transactions(
            account_id, page_size=500, page=1, from_date=from_date, to_date=to_date
        )
        total_pages = first_page.get("totalPages", 1)
        transactions.extend(first_page.get("results", []))
        for page in range(2, total_pages + 1):
            page_data = self.list_transactions(
                account_id,
                page_size=500,
                page=page,
                from_date=from_date,
                to_date=to_date,
            )
            transactions.extend(page_data.get("results", []))
        return transactions

    def fetch_and_store_investments(self):
        headers = {"accept": "application/json", "X-API-KEY": f"{self.api_key}"}
        item_id = os.getenv("ITEM_ID")

        url = f"{self.base_url}/investments?itemId={item_id}&pageSize=100"

        response = requests.get(url, headers=headers, timeout=30)
        investments = json.loads(response.content).get("results")
        self._save_incremental_json("data/investments.json", investments)

    def fetch_and_store_splitwise_data(self):
        from_date, to_date = self._incremental_date_range()
        accounts = self.list_accounts(self.splitwise_item_id).get("results", [])
        for account in accounts:
            if account.get("name") == os.getenv("SPLITWISE_ACCOUNT_NAME"):
                transactions = self._fetch_all_pages(account.get("id"), from_date, to_date)
                self._save_incremental_json("data/splitwise_transactions.json", transactions)

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
        Retorna dict com contagens de inserções e atualizações por tipo de dados.
        """
        # Inicializa o banco de dados com as tabelas necessárias
        self._initialize_database()

        # Inicializa repositórios
        transaction_repo = TransactionRepository()
        investment_repo = InvestmentRepository()
        splitwise_repo = SplitwiseRepository()

        # Inicializa contadores
        summary = {
            "bank_transactions_inserted": 0,
            "bank_transactions_updated": 0,
            "credit_transactions_inserted": 0,
            "credit_transactions_updated": 0,
            "investments_inserted": 0,
            "investments_updated": 0,
            "splitwise_inserted": 0,
            "splitwise_updated": 0,
        }

        try:
            print("[INFO] Iniciando coleta de dados da API...")
            from_date, to_date = self._incremental_date_range()
            print(
                f"[INFO] Janela incremental: {from_date} → {to_date} ({INCREMENTAL_DAYS} dias)"
            )

            # 1. Processa transações bancárias e de cartão
            accounts = self.list_accounts(self.item_id).get("results", [])
            for account in accounts:
                account_type = account.get("type")
                if account_type in ["BANK", "CREDIT"]:
                    account_id = account.get("id")
                    print(f"Processando conta {account_type}: {account_id}")

                    transactions = self._fetch_all_pages(account_id, from_date, to_date)

                    # Salva no banco usando repositórios
                    for transaction in transactions:
                        if account_type == "BANK":
                            result = transaction_repo.upsert_bank_transaction(
                                transaction
                            )
                            if result["success"]:
                                if result["action"] == "inserted":
                                    summary["bank_transactions_inserted"] += 1
                                elif result["action"] == "updated":
                                    summary["bank_transactions_updated"] += 1
                        elif account_type == "CREDIT":
                            result = transaction_repo.upsert_credit_transaction(
                                transaction
                            )
                            if result["success"]:
                                if result["action"] == "inserted":
                                    summary["credit_transactions_inserted"] += 1
                                elif result["action"] == "updated":
                                    summary["credit_transactions_updated"] += 1

                        if not result["success"]:
                            print(
                                f"Erro ao processar transação {transaction['id']}: {result.get('error', 'Erro desconhecido')}"
                            )

                    # Mantém arquivo JSON para debug (temporário)
                    self._save_incremental_json(
                        f"data/{account_type}_transactions.json", transactions
                    )
                    print(
                        f"[OK] Processadas {len(transactions)} transações do tipo {account_type}"
                    )

            # 2. Processa investimentos
            print("[INFO] Processando investimentos...")
            investments = self.fetch_investments_data()
            for investment in investments:
                result = investment_repo.upsert_investment(investment)
                if result["success"]:
                    if result["action"] == "inserted":
                        summary["investments_inserted"] += 1
                    elif result["action"] == "updated":
                        summary["investments_updated"] += 1
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
                if result["success"]:
                    if result["action"] == "inserted":
                        summary["splitwise_inserted"] += 1
                    elif result["action"] == "updated":
                        summary["splitwise_updated"] += 1
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

            print("[OK] Coleta de dados concluída com sucesso!")
            return summary

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
        """Busca dados do Splitwise da API para a janela incremental."""
        from_date, to_date = self._incremental_date_range()
        accounts = self.list_accounts(self.splitwise_item_id).get("results", [])

        for account in accounts:
            if account.get("name") == os.getenv("SPLITWISE_ACCOUNT_NAME"):
                return self._fetch_all_pages(account.get("id"), from_date, to_date)

        return []

    def _initialize_database(self):
        """Inicializa o banco de dados com as tabelas necessárias via BaseRepository."""
        from repositories.base_repository import BaseRepository

        print(f"[INFO] Inicializando banco de dados...")

        tables_sql = [
            """
            CREATE TABLE IF NOT EXISTS categories (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                types TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS bank_transactions (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                description TEXT,
                amount REAL,
                category_id TEXT,
                type TEXT,
                operation_type TEXT,
                split_info TEXT,
                payment_data TEXT,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS credit_transactions (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                description TEXT,
                amount REAL,
                category_id TEXT,
                status TEXT,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS investments (
                id TEXT PRIMARY KEY,
                name TEXT,
                balance REAL,
                type TEXT,
                subtype TEXT,
                date TEXT,
                due_date TEXT,
                issuer TEXT,
                rate_type TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS persons (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS splitwise (
                id TEXT PRIMARY KEY,
                amount REAL,
                date TEXT,
                description TEXT,
                category_id TEXT,
                transaction_id TEXT,
                is_invalid INTEGER DEFAULT 0
            )
            """,
        ]

        repo = BaseRepository()
        repo.initialize_schema(tables_sql)
        repo.close()
        print("[OK] Banco de dados inicializado com sucesso!")


if __name__ == "__main__":
    api = PluggyAPI()
    summary = api.fetch_and_store_data_to_db()
    print(summary)
