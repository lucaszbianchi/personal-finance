import sqlite3
import threading
import json
from typing import Dict, Any, List, Optional


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

    def upsert(
        self,
        table: str,
        id_col: str,
        data: Dict[str, Any],
        strategy: str = "smart_merge",
        update_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Método genérico de upsert que suporta múltiplas estratégias.

        Args:
            table: Nome da tabela alvo
            id_col: Nome da coluna chave primária
            data: Dicionário com pares coluna-valor para upsert
            strategy: "smart_merge" (padrão) ou "insert_only"
            update_fields: Lista de campos para atualizar (usado em smart_merge)

        Returns:
            Dict com resultado da operação: {"success": bool, "action": str, "affected_rows": int, "id": str}
        """
        if not data or id_col not in data:
            raise ValueError(f"Dados inválidos: {id_col} é obrigatório")

        # Serialização JSON automática para dicts e listas
        processed_data = {}
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                processed_data[key] = json.dumps(value, ensure_ascii=False)
            else:
                processed_data[key] = value

        record_id = processed_data[id_col]

        try:
            if strategy == "insert_only":
                return self._upsert_insert_only(table, processed_data)

            elif strategy == "smart_merge":
                return self._upsert_smart_merge(
                    table, id_col, processed_data, update_fields
                )

            else:
                raise ValueError(f"Estratégia inválida: {strategy}")

        except ValueError as e:
            return {
                "success": False,
                "action": "error",
                "affected_rows": 0,
                "id": record_id,
                "error": str(e),
            }

    def _upsert_insert_only(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """INSERT OR IGNORE - insere apenas se novo"""
        columns = list(data.keys())
        placeholders = ", ".join(["?" for _ in columns])
        column_names = ", ".join(columns)

        query = (
            f"INSERT OR IGNORE INTO {table} ({column_names}) VALUES ({placeholders})"
        )
        cursor = self.execute_query(query, tuple(data[col] for col in columns))

        action = "inserted" if cursor.rowcount > 0 else "ignored"

        return {
            "success": True,
            "action": action,
            "affected_rows": cursor.rowcount,
            "id": data[list(data.keys())[0]],
        }

    def _upsert_smart_merge(
        self,
        table: str,
        id_col: str,
        data: Dict[str, Any],
        update_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """INSERT OR IGNORE seguido de UPDATE condicional"""

        # Primeiro, tenta inserir
        insert_result = self._upsert_insert_only(table, data)

        if insert_result["action"] == "inserted":
            return insert_result

        # Se não inseriu (já existe), faz update dos campos especificados
        if update_fields is None:
            # Se não especificou campos, atualiza todos exceto o ID
            update_fields = [col for col in data.keys() if col != id_col]

        if not update_fields:
            return insert_result  # Nada para atualizar

        # Constroi query de UPDATE
        set_clause = ", ".join([f"{field} = ?" for field in update_fields])
        update_query = f"UPDATE {table} SET {set_clause} WHERE {id_col} = ?"

        update_params = [data[field] for field in update_fields] + [data[id_col]]
        cursor = self.execute_query(update_query, tuple(update_params))

        return {
            "success": True,
            "action": "updated",
            "affected_rows": cursor.rowcount,
            "id": data[id_col],
        }
