"""Idempotent migration: drops the deprecated pluggy_book_categories table."""

import sqlite3
import sys

sys.path.insert(0, ".")
from init_db import DB_PATH


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS pluggy_book_categories")
    conn.commit()
    conn.close()
    print("[OK] pluggy_book_categories dropped from '%s'." % DB_PATH)


if __name__ == "__main__":
    main()
