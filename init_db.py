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
        name TEXT NOT NULL
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
]


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
