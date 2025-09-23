import sqlite3
import json
import os

from services.pluggy_api import PluggyAPI


class FetchData:
    """
    Classe para buscar dados da API Pluggy e armazená-los em arquivos JSON.
    """

    # Arquivos JSON
    FILES = {
        "bank": "data/BANK_transactions.json",
        "credit": "data/CREDIT_transactions.json",
        "investments": "data/investments.json",
    }
    DB_PATH = "finance.db"

    def __init__(self):
        self.pluggy = PluggyAPI()
        self.conn = sqlite3.connect(self.DB_PATH)
        self.cur = self.conn.cursor()

    def execute(self):
        self._create_tables()
        self.pluggy.fetch_and_store_data()
        self.pluggy.fetch_and_store_investments()

        # Executar importações
        self._import_json_to_db(self.FILES["bank"], "bank_transactions")
        self._import_json_to_db(self.FILES["credit"], "credit_transactions")
        self._import_json_to_db(self.FILES["investments"], "investments")

        self.conn.commit()
        self.conn.close()
        print("✅ Importação concluída com sucesso!")

    def _create_tables(self):

        # Criação das tabelas
        self.cur.execute(
            """
        CREATE TABLE IF NOT EXISTS bank_transactions (
            id TEXT PRIMARY KEY,
            date TEXT,
            description TEXT,
            amount REAL,
            category_id TEXT,
            partner_id TEXT,
            accountId TEXT,
            operationType TEXT,
            status TEXT,
            metadata_raw TEXT
        )
        """
        )

        # Tabela de transações de cartão de crédito
        self.cur.execute(
            """
        CREATE TABLE IF NOT EXISTS credit_transactions (
            id TEXT PRIMARY KEY,
            date TEXT,
            description TEXT,
            amount REAL,
            category_id TEXT,
            partner_id TEXT,
            accountId TEXT,
            status TEXT,
            metadata_raw TEXT
        )
        """
        )

        # Tabela de investimentos
        self.cur.execute(
            """
        CREATE TABLE IF NOT EXISTS investments (
            id TEXT PRIMARY KEY,
            name TEXT,
            type TEXT,
            subtype TEXT,
            value REAL,
            amount REAL,
            rate REAL,
            date TEXT,
            due_date TEXT,
            issuer TEXT,
            metadata_raw TEXT
        )
        """
        )
        # Tabela de categorias
        self.cur.execute(
            """
        CREATE TABLE IF NOT EXISTS categories (
            id TEXT PRIMARY KEY,
            name TEXT,
            type TEXT
        )
        """
        )

        # Tabela de parceiros
        self.cur.execute(
            """
        CREATE TABLE IF NOT EXISTS persons (
            id TEXT PRIMARY KEY,
            name TEXT
        )
        """
        )

    # Função para importar JSON
    def _import_json_to_db(self, file_path, table):
        if not os.path.exists(file_path):
            print(f"⚠ Arquivo não encontrado: {file_path}")
            return

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if table == "bank_transactions":
            for item in data:
                self.cur.execute(
                    """
                INSERT OR REPLACE INTO bank_transactions
                (id, date, description, amount, category, accountId, operationType, status, metadata_raw)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        item["id"],
                        item["date"],
                        item.get("description"),
                        item.get("amount"),
                        item.get("category"),
                        item.get("accountId"),
                        item.get("operationType"),
                        item.get("status"),
                        json.dumps(
                            {
                                "paymentData": item.get("paymentData"),
                                "merchant": item.get("merchant"),
                            },
                            ensure_ascii=False,
                        ),
                    ),
                )
                self.cur.execute(
                    """
                INSERT OR IGNORE INTO categories (id, name)
                VALUES (?, ?)
                """,
                    (
                        item.get("categoryId"),
                        item.get("category"),
                    ),
                )

        elif table == "credit_transactions":
            for item in data:
                self.cur.execute(
                    """
                INSERT OR REPLACE INTO credit_transactions
                (id, date, description, amount, category, accountId, status, metadata_raw)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        item["id"],
                        item["date"],
                        item.get("description"),
                        item.get("amount"),
                        item.get("category"),
                        item.get("accountId"),
                        item.get("status"),
                        json.dumps(
                            {
                                "creditCardMetadata": item.get("creditCardMetadata"),
                                "acquirerData": item.get("acquirerData"),
                            },
                            ensure_ascii=False,
                        ),
                    ),
                )
                self.cur.execute(
                    """
                INSERT OR IGNORE INTO categories (id, name)
                VALUES (?, ?)
                """,
                    (
                        item.get("categoryId"),
                        item.get("category"),
                    ),
                )

        elif table == "investments":
            for item in data:
                self.cur.execute(
                    """
                INSERT OR REPLACE INTO investments
                (id, name, type, subtype, value, amount, rate, date, issuer, metadata_raw)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        item["id"],
                        item.get("name"),
                        item.get("type"),
                        item.get("subtype"),
                        item.get("value"),
                        item.get("amount"),
                        item.get("rate"),
                        item.get("date"),
                        item.get("issuer"),
                        json.dumps(
                            {
                                "issuerCNPJ": item.get("issuerCNPJ"),
                                "issueDate": item.get("issueDate"),
                                "status": item.get("status"),
                            },
                            ensure_ascii=False,
                        ),
                    ),
                )
