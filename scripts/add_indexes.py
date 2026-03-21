"""Idempotent migration: adds indexes to an existing finance.db."""

import sqlite3
import sys

# Re-use the canonical index list from init_db
sys.path.insert(0, ".")
from init_db import DB_PATH, INDEXES_SQL


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for sql in INDEXES_SQL:
        cursor.execute(sql)
        idx_name = sql.split("IF NOT EXISTS ")[-1].split(" ON")[0]
        print(f"  [OK] {idx_name}")
    conn.commit()
    conn.close()
    print(f"Done. {len(INDEXES_SQL)} indexes ensured on '{DB_PATH}'.")


if __name__ == "__main__":
    main()
