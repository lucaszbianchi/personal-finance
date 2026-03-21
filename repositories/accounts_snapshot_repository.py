from repositories.base_repository import BaseRepository


class AccountsSnapshotRepository(BaseRepository):
    """Repositorio para snapshots de contas bancarias e de credito."""

    def upsert_snapshot(self, account: dict, item_id: str, snapshotted_at: str) -> dict:
        """Insere ou atualiza o snapshot de uma conta para o instante dado.

        O snapshot e identificado por (id, snapshotted_at) — chave composta. Chamadas
        multiplas com o mesmo par substituem o registro anterior, garantindo
        idempotencia dentro do mesmo periodo.

        Args:
            account: Dict com dados da conta retornados pela Pluggy API.
            item_id: ID do item ao qual a conta pertence.
            snapshotted_at: Timestamp do snapshot (ex.: '2026-03-14').

        Returns:
            Dict com resultado: {"success": bool, "action": str, "id": str}
        """
        credit_data = account.get("creditData") or {}
        account_id = account["id"]

        conn = self._get_connection()
        changes_before = conn.total_changes

        self.execute_query(
            """
            INSERT OR REPLACE INTO accounts_snapshot
                (id, item_id, name, type, subtype, balance,
                 credit_limit, available_credit, due_date, snapshotted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account_id,
                item_id,
                account.get("name"),
                account.get("type"),
                account.get("subtype"),
                account.get("balance"),
                credit_data.get("creditLimit"),
                credit_data.get("availableCreditLimit"),
                credit_data.get("balanceCloseDate"),
                snapshotted_at,
            ),
        )
        # INSERT OR REPLACE on conflict counts as 2 changes (delete + insert)
        action = "updated" if conn.total_changes - changes_before > 1 else "inserted"
        return {"success": True, "action": action, "id": account_id}

    def get_latest_snapshot_by_type(self, account_type: str) -> list:
        """Retorna o snapshot mais recente de cada conta do tipo informado."""
        cursor = self.execute_query(
            """
            SELECT a.*
            FROM accounts_snapshot a
            INNER JOIN (
                SELECT id, MAX(snapshotted_at) AS latest
                FROM accounts_snapshot
                WHERE type = ?
                GROUP BY id
            ) sub ON a.id = sub.id AND a.snapshotted_at = sub.latest
            """,
            (account_type,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_snapshot_for_month(self, account_type: str, month: str) -> list:
        """Retorna o snapshot mais recente por conta antes do fim do mês informado (YYYY-MM)."""
        year, mon = int(month[:4]), int(month[5:7])
        next_month_start = f"{year + 1}-01-01" if mon == 12 else f"{year}-{mon + 1:02d}-01"
        cursor = self.execute_query(
            """
            SELECT a.*
            FROM accounts_snapshot a
            INNER JOIN (
                SELECT id, MAX(snapshotted_at) AS latest
                FROM accounts_snapshot
                WHERE type = ? AND snapshotted_at < ?
                GROUP BY id
            ) sub ON a.id = sub.id AND a.snapshotted_at = sub.latest
            """,
            (account_type, next_month_start),
        )
        return [dict(row) for row in cursor.fetchall()]
