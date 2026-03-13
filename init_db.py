"""Script para inicializar o banco de dados com todas as tabelas necessárias."""

import os
import sqlite3

import dotenv

dotenv.load_dotenv()

DB_PATH = "finance.db"

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
        total_amount REAL,
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
        meal_allowance REAL,
        credit_card_bill REAL,
        credit_card_future_bill REAL,
        total_cash REAL,
        investments TEXT,
        expenses REAL,
        income REAL,
        risk_management REAL
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
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        call_type  TEXT NOT NULL,
        year_month TEXT NOT NULL,
        count      INTEGER DEFAULT 0,
        limit_value INTEGER NOT NULL,
        UNIQUE(call_type, year_month)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pluggy_book_summary (
        item_id         TEXT NOT NULL,
        month           TEXT NOT NULL,
        bank_account    TEXT,
        credit_card     TEXT,
        fetched_at      TEXT NOT NULL,
        PRIMARY KEY (item_id, month)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pluggy_book_categories (
        item_id             TEXT NOT NULL,
        month               TEXT NOT NULL,
        category            TEXT NOT NULL,
        transaction_type    TEXT NOT NULL,
        account_subtype     TEXT NOT NULL,
        m1_avg              REAL,
        m1_total            REAL,
        m1_min              REAL,
        m1_max              REAL,
        m2_avg              REAL,
        m2_total            REAL,
        m2_min              REAL,
        m2_max              REAL,
        m3_avg              REAL,
        m3_total            REAL,
        m3_min              REAL,
        m3_max              REAL,
        m6_avg              REAL,
        m6_total            REAL,
        m6_min              REAL,
        m6_max              REAL,
        m12_avg             REAL,
        m12_total           REAL,
        m12_min             REAL,
        m12_max             REAL,
        fetched_at          TEXT NOT NULL,
        PRIMARY KEY (item_id, month, category, transaction_type, account_subtype)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pluggy_insights (
        item_id    TEXT NOT NULL,
        month      TEXT NOT NULL,
        type       TEXT NOT NULL,
        data       TEXT,
        fetched_at TEXT,
        PRIMARY KEY (item_id, month, type)
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
        confidence      REAL,
        source          TEXT DEFAULT 'pluggy',
        is_unavoidable  INTEGER DEFAULT 0,
        synced_at       TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS income_sources (
        id              TEXT PRIMARY KEY,
        item_id         TEXT,
        description     TEXT,
        amount          REAL,
        frequency       TEXT,
        last_occurrence TEXT,
        confidence      REAL,
        total_m1        REAL,
        total_m3        REAL,
        total_m6        REAL,
        total_m12       REAL,
        source          TEXT DEFAULT 'pluggy',
        synced_at       TEXT
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

RESET_SQL = [
    "DROP TABLE IF EXISTS pluggy_book_categories",
    "DROP TABLE IF EXISTS pluggy_book_summary",
    "DROP TABLE IF EXISTS rate_limit_usage",
    "DROP TABLE IF EXISTS pluggy_insights",
    "DROP TABLE IF EXISTS user_goals",
    "DROP TABLE IF EXISTS automation_rules",
    "DROP TABLE IF EXISTS accounts_snapshot",
    "DROP TABLE IF EXISTS income_sources",
    "DROP TABLE IF EXISTS recurrent_expenses",
    "DROP TABLE IF EXISTS bills",
    "DROP TABLE IF EXISTS pluggy_items",
    "DROP TABLE IF EXISTS finance_history",
    "DROP TABLE IF EXISTS settings",
    "DROP TABLE IF EXISTS investments",
    "DROP TABLE IF EXISTS splitwise",
    "DROP TABLE IF EXISTS credit_transactions",
    "DROP TABLE IF EXISTS bank_transactions",
    "DROP TABLE IF EXISTS persons",
    "DROP TABLE IF EXISTS categories",
]


def reset_db():
    """Dropa todas as tabelas e recria do zero."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for sql in RESET_SQL:
        cursor.execute(sql)
    for sql in TABLES_SQL:
        cursor.execute(sql)
    conn.commit()
    conn.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for sql in TABLES_SQL:
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
