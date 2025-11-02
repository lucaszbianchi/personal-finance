import sqlite3
import threading


class BaseRepository:
    """Classe base para todos os repositórios, fornecendo funcionalidades comuns de banco de dados."""

    def __init__(self, db_path: str = "finance.db"):
        self.db_path = db_path
        self._local = threading.local()

    def _get_connection(self):
        """Retorna a conexão da thread atual"""
        if not hasattr(self._local, "connection"):
            self._local.connection = sqlite3.connect(self.db_path)
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    def close(self):
        """Fecha a conexão com o banco de dados da thread atual"""
        if hasattr(self._local, "connection"):
            self._local.connection.close()
            del self._local.connection

    def execute_query(self, query: str, params: tuple = ()):
        """Executa uma query e retorna o cursor.
        Para SELECTs: use fetchone() ou fetchall() no resultado
        Para INSERTs/UPDATEs: o commit é feito automaticamente
        """
        connection = self._get_connection()
        cursor = connection.cursor()
        cursor.execute(query, params)

        # Se for uma query de modificação (INSERT, UPDATE, DELETE)
        if any(
            query.strip().upper().startswith(op)
            for op in ["INSERT", "UPDATE", "DELETE"]
        ):
            connection.commit()

        return cursor
