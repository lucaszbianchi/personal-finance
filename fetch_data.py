import sqlite3
import json
import os

from pluggy_api import PluggyAPI


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
            type TEXT,
            operation_type TEXT,
            split_info TEXT,
            payment_data TEXT
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
            status TEXT,
            split_info TEXT
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
            balance REAL,
            date TEXT,
            due_date TEXT,
            issuer TEXT,
            rate_type TEXT
        )
        """
        )
        # Tabela de categorias
        self.cur.execute(
            """
        CREATE TABLE IF NOT EXISTS categories (
            id TEXT PRIMARY KEY,
            name TEXT,
            types TEXT
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
                INSERT OR IGNORE INTO bank_transactions
                (id, date, description, amount, category_id, type, operation_type, payment_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        item["id"],
                        item["date"],
                        item.get("description"),
                        item.get("amount"),
                        item.get("categoryId"),
                        item.get("type"),
                        item.get("operationType"),
                        json.dumps(item.get("paymentData")),
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
                if item.get("operationType") == "PIX" and "|" in item["description"]:
                    person_name = item["description"].split("|")[-1].strip()
                    document_number = None
                    if "transferência recebida|" in item["description"].lower():
                        document_number = item["paymentData"]["payer"]["documentNumber"]
                    elif "transferência enviada|" in item["description"].lower():
                        document_number = item["paymentData"]["receiver"][
                            "documentNumber"
                        ]
                    if (
                        person_name
                        and document_number
                        and document_number["type"] == "CPF"
                    ):
                        self.cur.execute(
                            """
                        INSERT OR IGNORE INTO persons (id, name)
                        VALUES (?, ?)
                        """,
                            (document_number["value"], person_name),
                        )

        elif table == "credit_transactions":
            for item in data:
                self.cur.execute(
                    """
                INSERT OR IGNORE INTO credit_transactions
                (id, date, description, amount, category_id, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        item["id"],
                        item["date"],
                        item.get("description"),
                        (
                            item.get("amountInAccountCurrency")
                            if item.get("amountInAccountCurrency") is not None
                            else item.get("amount")
                        ),
                        item.get("categoryId"),
                        item.get("status"),
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
                INSERT OR IGNORE INTO investments
                (id, name, type, subtype, balance, date, due_date, issuer, rate_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        item["id"],
                        item.get("name"),
                        item.get("type"),
                        item.get("subtype"),
                        item.get("balance"),
                        item.get("date"),
                        item.get("dueDate"),
                        item.get("issuer"),
                        item.get("rateType"),
                    ),
                )


if __name__ == "__main__":
    FetchData().execute()
