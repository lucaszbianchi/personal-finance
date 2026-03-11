import sqlite3
import threading
import json
from typing import Dict, Any, List


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

    def initialize_schema(self, tables_sql: List[str]) -> None:
        """Cria tabelas no banco usando a conexão thread-safe do repositório."""
        for sql in tables_sql:
            self.execute_query(sql)

    def upsert(
        self,
        table: str,
        id_col: str,
        data: Dict[str, Any],
        strategy: str = "insert_only",
    ) -> Dict[str, Any]:
        """
        Insere ou atualiza um registro conforme a estratégia escolhida.

        Args:
            table: Nome da tabela alvo
            id_col: Nome da coluna chave primária
            data: Dicionário com pares coluna-valor
            strategy: "insert_only" (INSERT OR IGNORE) ou "smart_merge" (INSERT OR REPLACE)

        Returns:
            Dict com resultado: {"success": bool, "action": str, "affected_rows": int, "id": str}
        """
        if not data or id_col not in data:
            raise ValueError(f"Dados inválidos: {id_col} é obrigatório")

        processed_data = {}
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                processed_data[key] = json.dumps(value, ensure_ascii=False)
            else:
                processed_data[key] = value

        record_id = processed_data[id_col]

        columns = list(processed_data.keys())
        placeholders = ", ".join(["?" for _ in columns])
        column_names = ", ".join(columns)

        if strategy == "smart_merge":
            # Check if record exists to report correct action
            check = self.execute_query(
                f"SELECT 1 FROM {table} WHERE {id_col} = ?", (record_id,)
            )
            existed = check.fetchone() is not None
            query = f"INSERT OR REPLACE INTO {table} ({column_names}) VALUES ({placeholders})"
            cursor = self.execute_query(query, tuple(processed_data[col] for col in columns))
            action = "updated" if existed else "inserted"
        else:
            query = f"INSERT OR IGNORE INTO {table} ({column_names}) VALUES ({placeholders})"
            cursor = self.execute_query(query, tuple(processed_data[col] for col in columns))
            action = "inserted" if cursor.rowcount > 0 else "ignored"

        return {
            "success": True,
            "action": action,
            "affected_rows": cursor.rowcount,
            "id": record_id,
        }
