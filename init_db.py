"""Script para inicializar o banco de dados com todas as tabelas necessárias."""

import os
import sqlite3

import dotenv

dotenv.load_dotenv()

DB_PATH = os.getenv("DB_PATH", "finance.db")

TABLES_SQL = [
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
    CREATE TABLE IF NOT EXISTS persons (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        split_info TEXT
    )
    """,
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
        payment_data TEXT,
        excluded INTEGER DEFAULT 0,
        item_id TEXT,
        FOREIGN KEY (category_id) REFERENCES categories(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS credit_transactions (
        id TEXT PRIMARY KEY,
        date TEXT,
        description TEXT,
        amount REAL,
        category_id TEXT,
        status TEXT,
        excluded INTEGER DEFAULT 0,
        installment_number INT,
        total_installments INT,
        total_amount REAL,  -- DEPRECATED: written by sync but never read; kept for backward compat
        item_id TEXT,
        FOREIGN KEY (category_id) REFERENCES categories(id)
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
        is_invalid INTEGER DEFAULT 0,
        match_type TEXT,
        FOREIGN KEY (category_id) REFERENCES categories(id),
        FOREIGN KEY (transaction_id) REFERENCES bank_transactions(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS investments (
        id TEXT PRIMARY KEY,
        name TEXT,
        type TEXT,
        subtype TEXT,
        amount REAL,
        balance REAL,
        date TEXT,
        due_date TEXT,
        issuer TEXT,
        rate_type TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS finance_history (
        month TEXT PRIMARY KEY,
        credit_card_bill REAL,
        credit_card_future_bill REAL,
        total_cash REAL,
        investments TEXT,
        expenses REAL,
        income REAL,
        risk_management REAL,
        bank_expenses REAL,
        credit_expenses REAL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pluggy_items (
        item_id TEXT PRIMARY KEY,
        connector_name TEXT,
        status TEXT,
        role TEXT DEFAULT 'bank',
        alias TEXT,
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
        finance_charges TEXT,
        is_open INTEGER DEFAULT 1,
        payment_date TEXT,
        total_amount_paid REAL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS rate_limit_usage (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id     TEXT NOT NULL DEFAULT '',
        call_type   TEXT NOT NULL,
        year_month  TEXT NOT NULL,
        count       INTEGER DEFAULT 0,
        limit_value INTEGER NOT NULL,
        UNIQUE(item_id, call_type, year_month)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_goals (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id TEXT,
        type        TEXT,
        amount      REAL,
        period      TEXT,
        created_at  TEXT DEFAULT (datetime('now')),
        updated_at  TEXT DEFAULT (datetime('now')),
        UNIQUE(category_id, type)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS accounts_snapshot (
        id               TEXT,
        item_id          TEXT,
        name             TEXT,
        type             TEXT,
        subtype          TEXT,
        balance          REAL,
        credit_limit     REAL,
        available_credit REAL,
        due_date         TEXT,
        snapshotted_at   TEXT,
        PRIMARY KEY (id, snapshotted_at)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS recurrent_expenses (
        id              TEXT PRIMARY KEY,
        item_id         TEXT,
        description     TEXT,
        amount          REAL,
        frequency       TEXT,
        next_occurrence TEXT,
        category_id     TEXT REFERENCES categories(id),
        merchant_name   TEXT,
        amount_min      REAL,
        amount_max      REAL,
        confidence      REAL,
        source          TEXT DEFAULT 'pluggy',
        is_unavoidable  INTEGER DEFAULT 0,
        synced_at       TEXT,
        account_type    TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS income_sources (
        id              TEXT PRIMARY KEY,
        item_id         TEXT,
        description     TEXT,
        amount          REAL,
        frequency       TEXT,
        next_occurrence TEXT,
        last_occurrence TEXT,
        confidence      REAL,
        total_m1        REAL,
        total_m3        REAL,
        total_m6        REAL,
        total_m12       REAL,
        source          TEXT DEFAULT 'pluggy',
        synced_at       TEXT,
        merchant_name   TEXT,
        amount_min      REAL,
        amount_max      REAL,
        category_id     TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS automation_rules (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT,
        conditions  TEXT NOT NULL,
        actions     TEXT NOT NULL,
        priority    INTEGER DEFAULT 0,
        enabled     INTEGER DEFAULT 1,
        created_at  TEXT DEFAULT (datetime('now'))
    )
    """,
]

INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_bank_transactions_date ON bank_transactions(date)",
    "CREATE INDEX IF NOT EXISTS idx_bank_transactions_category_id ON bank_transactions(category_id)",
    "CREATE INDEX IF NOT EXISTS idx_bank_transactions_excluded_date ON bank_transactions(excluded, date)",
    "CREATE INDEX IF NOT EXISTS idx_credit_transactions_date ON credit_transactions(date)",
    "CREATE INDEX IF NOT EXISTS idx_credit_transactions_category_id ON credit_transactions(category_id)",
    "CREATE INDEX IF NOT EXISTS idx_credit_transactions_status ON credit_transactions(status)",
    "CREATE INDEX IF NOT EXISTS idx_credit_transactions_excluded_date ON credit_transactions(excluded, date)",
    "CREATE INDEX IF NOT EXISTS idx_splitwise_date ON splitwise(date)",
    "CREATE INDEX IF NOT EXISTS idx_splitwise_transaction_id ON splitwise(transaction_id)",
    "CREATE INDEX IF NOT EXISTS idx_investments_date ON investments(date)",
    "CREATE INDEX IF NOT EXISTS idx_investments_type ON investments(type)",
    "CREATE INDEX IF NOT EXISTS idx_accounts_snapshot_snapshotted_at ON accounts_snapshot(snapshotted_at)",
    "CREATE INDEX IF NOT EXISTS idx_bills_due_date ON bills(due_date)",
    "CREATE INDEX IF NOT EXISTS idx_bills_account_id ON bills(account_id)",
    "CREATE INDEX IF NOT EXISTS idx_recurrent_expenses_category_id ON recurrent_expenses(category_id)",
    "CREATE INDEX IF NOT EXISTS idx_income_sources_last_occurrence ON income_sources(last_occurrence)",
]

# Tabelas preservadas no reset (configuracao do usuario):
#   settings, persons, user_goals, automation_rules,
#   income_sources, recurrent_expenses
RESET_SQL = [
    "DROP TABLE IF EXISTS pluggy_book_categories",
    "DROP TABLE IF EXISTS pluggy_book_summary",
    "DROP TABLE IF EXISTS pluggy_insights",
    "DROP TABLE IF EXISTS accounts_snapshot",
    "DROP TABLE IF EXISTS bills",
    "DROP TABLE IF EXISTS pluggy_items",
    "DROP TABLE IF EXISTS investments",
    "DROP TABLE IF EXISTS splitwise",
    "DROP TABLE IF EXISTS credit_transactions",
    "DROP TABLE IF EXISTS bank_transactions",
    "DROP TABLE IF EXISTS categories",
]


def reset_db():
    """Dropa todas as tabelas e recria do zero.

    A tabela settings e preservada, mas flags de estado como
    onboarding_completed sao removidos para permitir reconfigurar.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for sql in RESET_SQL:
        cursor.execute(sql)
    for sql in TABLES_SQL:
        cursor.execute(sql)
    for sql in INDEXES_SQL:
        cursor.execute(sql)
    cursor.execute("DELETE FROM settings WHERE key = 'onboarding_completed'")
    conn.commit()
    conn.close()


def init_db():
    # Para bases existentes, rodar migrations pendentes em scripts/:
    #   python scripts/migrate_remove_meal_allowance.py
    #   python scripts/migrate_income_sources_add_columns.py
    #   python scripts/migrate_add_item_alias_and_transaction_item_id.py
    #   python scripts/migrate_add_rate_limit_item_id.py
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for sql in TABLES_SQL:
        cursor.execute(sql)
    for sql in INDEXES_SQL:
        cursor.execute(sql)
    conn.commit()
    conn.close()
    print(f"Banco de dados '{DB_PATH}' inicializado com sucesso.")


def seed_pluggy_items():
    """Insere os items do .env na tabela pluggy_items (ignora se já existirem)."""
    items = [
        (os.getenv("ITEM_ID"), "bank"),
        (os.getenv("ITEM_ID_SPLITWISE"), "splitwise"),
    ]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    inserted = 0
    for item_id, role in items:
        if not item_id:
            print(f"  [AVISO] {role.upper()} item_id não encontrado no .env, pulando.")
            continue
        cursor.execute(
            "INSERT OR IGNORE INTO pluggy_items (item_id, role) VALUES (?, ?)",
            (item_id, role),
        )
        if cursor.rowcount > 0:
            print(f"  [OK] Inserido: {item_id} (role={role})")
            inserted += 1
        else:
            print(f"  [--] Já existe: {item_id} (role={role})")
    conn.commit()
    conn.close()
    print(f"Seed concluído: {inserted} item(s) inserido(s).")


if __name__ == "__main__":
    init_db()
    seed_pluggy_items()
