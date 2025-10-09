import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Any


class BaseRepository:
    """Classe base para todos os repositórios, fornecendo funcionalidades comuns de banco de dados."""

    def __init__(self, db_path: str = "finance.db"):
        self.db_path = db_path

    @contextmanager
    def get_connection(self):
        """Gerencia a conexão com o banco de dados usando context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permite acesso por nome das colunas
        try:
            yield conn
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Executa uma query e retorna os resultados como lista de dicionários."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Executa uma query de atualização e retorna o número de linhas afetadas."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            conn.commit()
            return cur.rowcount
