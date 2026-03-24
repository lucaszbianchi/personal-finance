"""Migration: remove meal_allowance column from finance_history.

SQLite 3.35+ supports ALTER TABLE DROP COLUMN.
Python 3.11 ships with SQLite 3.39+, so this is safe.

Run once on any existing database:
    python scripts/migrate_remove_meal_allowance.py
"""

import sqlite3
import sys
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "finance.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if column exists before trying to drop it
    cursor.execute("PRAGMA table_info(finance_history)")
    columns = [row[1] for row in cursor.fetchall()]

    if "meal_allowance" not in columns:
        print("[INFO] meal_allowance column does not exist — migration already applied.")
        conn.close()
        return

    cursor.execute("ALTER TABLE finance_history DROP COLUMN meal_allowance")
    conn.commit()
    conn.close()
    print("[OK] meal_allowance column removed from finance_history.")


if __name__ == "__main__":
    migrate()
