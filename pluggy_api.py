from datetime import datetime, timedelta, timezone
import json
import os
import requests

from repositories.accounts_snapshot_repository import AccountsSnapshotRepository
from repositories.bill_repository import BillRepository
from repositories.category_repository import CategoryRepository
from repositories.pluggy_item_repository import PluggyItemRepository
from repositories.rate_limit_repository import RateLimitRepository
from repositories.transaction_repository import TransactionRepository
from repositories.investment_repository import InvestmentRepository
from services.finance_history_service import FinanceHistoryService
from services.pluggy_auth_service import get_api_key as _get_api_key
from services.recurrence_detector_service import RecurrenceDetectorService

INCREMENTAL_DAYS = 6


class PluggyAPI:
    """
    A class to interact with the Pluggy API to fetch and store financial data.
    """

    def __init__(self):
        self.base_url = "https://api.pluggy.ai"
        self.api_key = self._create_api_key()

    def _create_api_key(self):
        return _get_api_key()

    def list_consents(self, item_id):
        url = f"{self.base_url}/consents?itemId={item_id}"
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

                    if not rate_limit_repo.can_call("recent", item_id):
                        print(
                            "[WARN] Rate limit de sincronização recente atingido para este mês"
                        )
                        continue

                    url = f"{self.base_url}/bills?accountId={account['id']}"
                    headers = {"X-API-KEY": self.api_key}
                    response = requests.get(url, headers=headers, timeout=30)
                    rate_limit_repo.increment("recent", item_id)

                    for bill in response.json().get("results", []):
                        bill_repo.upsert_bill(bill, account["id"])
                        count += 1
        finally:
            rate_limit_repo.close()
            bill_repo.close()

        return count

    def fetch_and_store_data_to_db(self, import_type: str = "recent", item_id: str | None = None):
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
            item_ids = self._get_item_ids_to_sync(item_id)
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

                    if not rate_limit_repo.can_call(call_type, item_id):
                        print(
                            f"[WARN] Rate limit de sincronização/{call_type} atingido"
                        )
                        continue

                    print(
                        f"Processando conta {account_type}: {account_id} (item: {item_id})"
                    )
                    transactions = self._fetch_all_pages(account_id, from_date, to_date)
                    rate_limit_repo.increment(call_type, item_id)

                    for transaction in transactions:
                        if account_type == "BANK":
                            result = transaction_repo.upsert_bank_transaction(
                                transaction, item_id=item_id
                            )
                            if result["success"]:
                                if result["action"] == "inserted":
                                    summary["bank_transactions_inserted"] += 1
                                elif result["action"] == "updated":
                                    summary["bank_transactions_updated"] += 1
                        else:
                            result = transaction_repo.upsert_credit_transaction(
                                transaction, item_id=item_id
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
                fh_service.update_finance_history_from_sync(month)
                print(f"[OK] Snapshot mensal gravado para {month}")

            # 4. Recalculate bill close/open dates from installment transactions
            try:
                bill_repo.recalculate_all_close_dates()
                print("[OK] Bill close/open dates recalculated")
            except Exception as e:
                print(f"[WARN] Bill date recalculation failed: {e}")

            # 5. Recurrence detection
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
            rate_limit_repo.close()
            accounts_snapshot_repo.close()
            bill_repo.close()

    def _get_item_ids_to_sync(self, item_id: str | None = None) -> list:
        """Retorna item_ids de role 'bank' para sincronizar.

        Se item_id for fornecido, retorna apenas esse item se existir.
        Retorna lista vazia (com aviso) se o item_id nao for encontrado.
        """
        repo = PluggyItemRepository()
        try:
            items = repo.get_items_by_role("bank")
            all_ids = [item["item_id"] for item in items]
            if item_id is not None:
                if item_id not in all_ids:
                    print(f"[WARN] item_id {item_id!r} not found in bank items; skipping sync")
                    return []
                return [item_id]
            return all_ids
        finally:
            repo.close()

    def fetch_investments_data(self) -> list:
        """Busca investimentos de todos os items de role 'bank'."""
        headers = {"accept": "application/json", "X-API-KEY": f"{self.api_key}"}
        investments = []
        for item_id in self._get_item_ids_to_sync():
            url = f"{self.base_url}/investments?itemId={item_id}&pageSize=100"
            response = requests.get(url, headers=headers, timeout=30)
            investments.extend(json.loads(response.content).get("results", []))
        return investments

    def _initialize_database(self):
        """Inicializa o banco de dados com as tabelas necessárias."""
        from init_db import init_db
        print("[INFO] Inicializando banco de dados...")
        init_db()
