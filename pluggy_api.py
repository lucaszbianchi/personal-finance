from datetime import datetime, timedelta, timezone
import json
import os

import dotenv
import requests

from repositories.base_repository import BaseRepository
from repositories.pluggy_item_repository import PluggyItemRepository
from repositories.transaction_repository import TransactionRepository
from repositories.investment_repository import InvestmentRepository
from repositories.splitwise_repository import SplitwiseRepository
from services.pluggy_auth_service import get_api_key as _get_api_key

INCREMENTAL_DAYS = 6


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
        return _get_api_key()

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

    def _load_existing_json(self, filepath):
        if os.path.exists(filepath):
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
        Busca dados da API e salva diretamente no banco usando repositórios.
        Mantém arquivos JSON em paralelo para debug/desenvolvimento.
        Retorna dict com contagens de inserções e atualizações por tipo de dados.
        """
        self._initialize_database()

        transaction_repo = TransactionRepository()
        investment_repo = InvestmentRepository()
        splitwise_repo = SplitwiseRepository()

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

            # 1. Transações bancárias e de cartão (todos os items role=bank)
            item_ids = self._get_item_ids_to_sync()
            print(f"[INFO] Sincronizando {len(item_ids)} item(s): {item_ids}")
            for item_id in item_ids:
                accounts = self.list_accounts(item_id).get("results", [])
                for account in accounts:
                    account_type = account.get("type")
                    if account_type not in ["BANK", "CREDIT"]:
                        continue
                    account_id = account.get("id")
                    print(
                        f"Processando conta {account_type}: {account_id} (item: {item_id})"
                    )
                    transactions = self._fetch_all_pages(account_id, from_date, to_date)
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
                        else:
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
                                f"Erro ao processar transação {transaction['id']}: "
                                f"{result.get('error', 'Erro desconhecido')}"
                            )
                    self._save_incremental_json(
                        f"data/{account_type}_transactions.json", transactions
                    )
                    print(
                        f"[OK] Processadas {len(transactions)} transações do tipo {account_type}"
                    )

            # 2. Investimentos
            print("[INFO] Processando investimentos...")
            investments = self.fetch_investments_data()
            for investment in investments:
                result = investment_repo.upsert_investment(investment)
                if result["success"]:
                    if result["action"] == "inserted":
                        summary["investments_inserted"] += 1
                    elif result["action"] == "updated":
                        summary["investments_updated"] += 1
                else:
                    print(
                        f"Erro ao processar investimento {investment['id']}: "
                        f"{result.get('error', 'Erro desconhecido')}"
                    )
            if investments:
                self._save_incremental_json("data/investments.json", investments)
                print(f"Processados {len(investments)} investimentos")

            # 3. Splitwise
            print("Processando transações Splitwise...")
            splitwise_transactions = self.fetch_splitwise_data()
            for transaction in splitwise_transactions:
                result = splitwise_repo.upsert_splitwise_transaction(transaction)
                if result["success"]:
                    if result["action"] == "inserted":
                        summary["splitwise_inserted"] += 1
                    elif result["action"] == "updated":
                        summary["splitwise_updated"] += 1
                else:
                    print(
                        f"Erro ao processar Splitwise {transaction['id']}: "
                        f"{result.get('error', 'Erro desconhecido')}"
                    )
            if splitwise_transactions:
                self._save_incremental_json(
                    "data/splitwise_transactions.json", splitwise_transactions
                )
                print(f"Processadas {len(splitwise_transactions)} transações Splitwise")

            print("[OK] Coleta de dados concluída com sucesso!")
            return summary

        finally:
            transaction_repo.close()
            investment_repo.close()
            splitwise_repo.close()

    def _get_item_ids_to_sync(self) -> list:
        """Retorna item_ids de role 'bank' para sincronizar. Fallback: ITEM_ID do .env."""
        repo = PluggyItemRepository()
        try:
            items = repo.get_items_by_role("bank")
            if items:
                return [item["item_id"] for item in items]
        except Exception as e:
            print(f"[WARN] Não foi possível consultar pluggy_items, usando fallback do .env: {e}")
        finally:
            repo.close()
        return [self.item_id] if self.item_id else []

    def _get_splitwise_item_id(self) -> str | None:
        """Retorna o item_id de role 'splitwise' do banco. Fallback: ITEM_ID_SPLITWISE do .env."""
        repo = PluggyItemRepository()
        try:
            items = repo.get_items_by_role("splitwise")
            if items:
                return items[0]["item_id"]
        except Exception as e:
            print(f"[WARN] Não foi possível consultar pluggy_items, usando fallback do .env: {e}")
        finally:
            repo.close()
        return self.splitwise_item_id

    def fetch_investments_data(self) -> list:
        """Busca investimentos de todos os items de role 'bank'."""
        headers = {"accept": "application/json", "X-API-KEY": f"{self.api_key}"}
        investments = []
        for item_id in self._get_item_ids_to_sync():
            url = f"{self.base_url}/investments?itemId={item_id}&pageSize=100"
            response = requests.get(url, headers=headers, timeout=30)
            investments.extend(json.loads(response.content).get("results", []))
        return investments

    def fetch_splitwise_data(self) -> list:
        """Busca dados do Splitwise da API para a janela incremental."""
        splitwise_item_id = self._get_splitwise_item_id()
        if not splitwise_item_id:
            return []
        from_date, to_date = self._incremental_date_range()
        accounts = self.list_accounts(splitwise_item_id).get("results", [])
        for account in accounts:
            if account.get("name") == os.getenv("SPLITWISE_ACCOUNT_NAME"):
                return self._fetch_all_pages(account.get("id"), from_date, to_date)
        return []

    def _initialize_database(self):
        """Inicializa o banco de dados com as tabelas necessárias via BaseRepository."""
        print("[INFO] Inicializando banco de dados...")
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
            """
            CREATE TABLE IF NOT EXISTS pluggy_items (
                item_id TEXT PRIMARY KEY,
                connector_name TEXT,
                status TEXT,
                role TEXT DEFAULT 'bank',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
            """,
        ]
        repo = BaseRepository()
        for sql in tables_sql:
            repo.execute_query(sql)
        repo.close()
        print("[OK] Banco de dados inicializado com sucesso!")


if __name__ == "__main__":
    api = PluggyAPI()
    summary = api.fetch_and_store_data_to_db()
    print(summary)
