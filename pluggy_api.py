from datetime import datetime, timedelta, timezone
import json
import os
import requests

import dotenv

from repositories.accounts_snapshot_repository import AccountsSnapshotRepository
from repositories.bill_repository import BillRepository
from repositories.category_repository import CategoryRepository
from repositories.pluggy_item_repository import PluggyItemRepository
from repositories.rate_limit_repository import RateLimitRepository
from repositories.transaction_repository import TransactionRepository
from repositories.investment_repository import InvestmentRepository
from repositories.splitwise_repository import SplitwiseRepository
from services.finance_history_service import FinanceHistoryService
from services.pluggy_auth_service import get_api_key as _get_api_key
from services.recurrence_detector_service import RecurrenceDetectorService

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

    def fetch_and_store_categories(self) -> int:
        """Busca todas as categorias da Pluggy e faz upsert no banco.
        Retorna número de categorias inseridas/atualizadas.
        """
        url = f"{self.base_url}/categories"
        headers = {"X-API-KEY": self.api_key}
        response = requests.get(url, headers=headers, timeout=30)
        categories = response.json().get("results", [])

        repo = CategoryRepository()
        count = 0
        try:
            for cat in categories:
                is_root = not cat.get("parentId")
                repo.upsert(
                    "categories",
                    "id",
                    {
                        "id": cat["id"],
                        "description": cat["description"],
                        "description_translated": cat.get("descriptionTranslated"),
                        "parent_id": cat["id"] if is_root else cat.get("parentId"),
                        "parent_description": (
                            cat["description"]
                            if is_root
                            else cat.get("parentDescription")
                        ),
                    },
                )
                count += 1
        finally:
            repo.close()
        return count

    def fetch_and_store_bills(self) -> int:
        """Busca faturas de todos os accounts CREDIT.
        Usa rate_limit_usage para controlar chamadas (produto: 'bills', 30/mês).
        Retorna número de faturas inseridas/atualizadas.
        """
        rate_limit_repo = RateLimitRepository()
        bill_repo = BillRepository()
        count = 0

        try:
            for item_id in self._get_item_ids_to_sync():
                accounts = self.list_accounts(item_id).get("results", [])
                for account in accounts:
                    if account["type"] != "CREDIT":
                        continue

                    if not rate_limit_repo.can_call("recent"):
                        print(
                            "[WARN] Rate limit de sincronização recente atingido para este mês"
                        )
                        continue

                    url = f"{self.base_url}/bills?accountId={account['id']}"
                    headers = {"X-API-KEY": self.api_key}
                    response = requests.get(url, headers=headers, timeout=30)
                    rate_limit_repo.increment("recent")

                    for bill in response.json().get("results", []):
                        bill_repo.upsert_bill(bill, account["id"])
                        count += 1
        finally:
            rate_limit_repo.close()
            bill_repo.close()

        return count

    def fetch_and_store_data_to_db(self, import_type: str = "recent"):
        """
        Busca dados da API e salva diretamente no banco usando repositórios.
        Mantém arquivos JSON em paralelo para debug/desenvolvimento.
        Retorna dict com contagens de inserções e atualizações por tipo de dados.

        Args:
            import_type: "recent" (últimos 6 dias, default) ou "non_recent" (7-365 dias)
        """
        self._initialize_database()

        transaction_repo = TransactionRepository()
        investment_repo = InvestmentRepository()
        splitwise_repo = SplitwiseRepository()
        rate_limit_repo = RateLimitRepository()
        accounts_snapshot_repo = AccountsSnapshotRepository()
        bill_repo = BillRepository()
        bank_balance = 0.0

        summary = {
            "bank_transactions_inserted": 0,
            "bank_transactions_updated": 0,
            "credit_transactions_inserted": 0,
            "credit_transactions_updated": 0,
            "investments_inserted": 0,
            "investments_updated": 0,
            "splitwise_inserted": 0,
            "splitwise_updated": 0,
            "categories_synced": 0,
            "bills_synced": 0,
            "accounts_snapshots_saved": 0,
            "rate_limit_usage": [],
        }

        try:
            print("[INFO] Iniciando coleta de dados da API...")

            # 0. Categorias (sem rate-limit) — só importa se tabela estiver vazia
            print("[INFO] Verificando categorias...")
            repo = CategoryRepository()
            try:
                has_categories = (
                    repo.execute_query("SELECT 1 FROM categories LIMIT 1").fetchone()
                    is not None
                )
            finally:
                repo.close()

            if not has_categories:
                print("[INFO] Tabela vazia, sincronizando categorias...")
                summary["categories_synced"] = self.fetch_and_store_categories()
                print(f"[OK] {summary['categories_synced']} categorias sincronizadas")
            else:
                print("[INFO] Categorias já existem, pulando sincronização")
                summary["categories_synced"] = 0

            # 1. Faturas (com rate-limit)
            print("[INFO] Sincronizando faturas...")
            summary["bills_synced"] = self.fetch_and_store_bills()
            print(f"[OK] {summary['bills_synced']} faturas sincronizadas")

            # 2. Transações bancárias e de cartão
            today = datetime.now(timezone.utc)
            if import_type == "non_recent":
                from_date = (today - timedelta(days=365)).strftime("%Y-%m-%d")
                to_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
                print(f"[INFO] Janela non_recent: {from_date} -> {to_date}")
            else:
                from_date, to_date = self._incremental_date_range()
                print(
                    f"[INFO] Janela incremental: {from_date} -> {to_date} ({INCREMENTAL_DAYS} dias)"
                )

            call_type = import_type
            snapshotted_at = today.strftime("%Y-%m-%d")
            item_ids = self._get_item_ids_to_sync()
            print(f"[INFO] Sincronizando {len(item_ids)} item(s): {item_ids}")
            for item_id in item_ids:
                accounts = self.list_accounts(item_id).get("results", [])
                for account in accounts:
                    account_type = account.get("type")
                    if account_type == "BANK":
                        bank_balance += account.get("balance", 0) or 0
                    if account_type not in ["BANK", "CREDIT"]:
                        continue

                    accounts_snapshot_repo.upsert_snapshot(account, item_id, snapshotted_at)
                    summary["accounts_snapshots_saved"] += 1

                    account_id = account.get("id")

                    if not rate_limit_repo.can_call(call_type):
                        print(
                            f"[WARN] Rate limit de sincronização/{call_type} atingido"
                        )
                        continue

                    print(
                        f"Processando conta {account_type}: {account_id} (item: {item_id})"
                    )
                    transactions = self._fetch_all_pages(account_id, from_date, to_date)
                    rate_limit_repo.increment(call_type)

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

            # 3. Investimentos
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

                # Snapshot mensal automático
                month = today.strftime("%Y-%m")
                fh_service = FinanceHistoryService()
                fh_service.update_finance_history_net_worth(month, bank_balance)
                print(f"[OK] Snapshot mensal gravado para {month}")

            # 4. Splitwise
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

            # 6. Pluggy Insights (book) — apenas para itens de banco
            try:
                from services.pluggy_insights_service import PluggyInsightsService
                insights_service = PluggyInsightsService(self.api_key)
                insights_service.fetch_and_store(self._get_item_ids_to_sync(), month)
            except Exception as e:
                print(f"[WARN] Não foi possível sincronizar Pluggy Insights: {e}")

            # 6b. Recalculate bill close/open dates from installment transactions
            try:
                bill_repo.recalculate_all_close_dates()
                print("[OK] Bill close/open dates recalculated")
            except Exception as e:
                print(f"[WARN] Bill date recalculation failed: {e}")

            # 7. Recurrence detection
            svc = RecurrenceDetectorService()
            try:
                summary["recurrences_synced"] = svc.detect_and_store()
            except Exception as e:
                print(f"[WARN] Recurrence detection failed: {e}")
            finally:
                svc.close()

            summary["rate_limit_usage"] = rate_limit_repo.get_usage_summary()
            print("[OK] Coleta de dados concluída com sucesso!")
            return summary

        finally:
            transaction_repo.close()
            investment_repo.close()
            splitwise_repo.close()
            rate_limit_repo.close()
            accounts_snapshot_repo.close()
            bill_repo.close()

    def _get_item_ids_to_sync(self) -> list:
        """Retorna item_ids de role 'bank' para sincronizar. Fallback: ITEM_ID do .env."""
        repo = PluggyItemRepository()
        try:
            items = repo.get_items_by_role("bank")
            if items:
                return [item["item_id"] for item in items]
        except Exception as e:
            print(
                f"[WARN] Não foi possível consultar pluggy_items, usando fallback do .env: {e}"
            )
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
            print(
                f"[WARN] Não foi possível consultar pluggy_items, usando fallback do .env: {e}"
            )
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
        from repositories.base_repository import BaseRepository

        print("[INFO] Inicializando banco de dados...")

        tables_sql = [
            """
            CREATE TABLE IF NOT EXISTS categories (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                description_translated TEXT,
                parent_id TEXT,
                parent_description TEXT
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
                amount REAL,
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
            """
            CREATE TABLE IF NOT EXISTS bills (
                id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                due_date TEXT,
                open_date TEXT,
                close_date TEXT,
                total_amount REAL,
                total_amount_currency_code TEXT,
                minimum_payment_amount REAL,
                allows_installments INTEGER DEFAULT 0,
                finance_charges TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS rate_limit_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_type TEXT NOT NULL,
                year_month TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                limit_value INTEGER NOT NULL,
                UNIQUE(call_type, year_month)
            )
            """,
        ]
        repo = BaseRepository()
        for sql in tables_sql:
            repo.execute_query(sql)
        repo.close()
        print("[OK] Banco de dados inicializado com sucesso!")
