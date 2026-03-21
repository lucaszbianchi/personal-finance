"""Idempotent migration: drops pluggy_book_summary and pluggy_insights tables."""

import sqlite3
import sys

sys.path.insert(0, ".")
from init_db import DB_PATH


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS pluggy_book_summary")
    conn.execute("DROP TABLE IF EXISTS pluggy_insights")
    conn.commit()
    conn.close()
    print("[OK] pluggy_book_summary and pluggy_insights dropped from '%s'." % DB_PATH)


if __name__ == "__main__":
    main()
