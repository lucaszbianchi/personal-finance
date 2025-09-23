import sqlite3


class QueryDB:
    """
    A helper class to query the SQLite database and return results as a list of dictionaries.
    """

    DB_PATH = "finance.db"

    def execute(self, query):
        conn = sqlite3.connect(self.DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]
