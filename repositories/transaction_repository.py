from typing import List
import json
from utils.date_helper import DateHelper
from repositories.base_repository import BaseRepository
from models.transaction import BankTransaction, CreditTransaction
from models.investment import Investment


class TransactionRepository(BaseRepository):
    """Repositório para gerenciar operações de banco de dados relacionadas a transações."""

    def __init__(self, db_path: str = "finance.db"):
        super().__init__(db_path=db_path)
        self.date_helper = DateHelper()

    def get_bank_transactions(self) -> List[BankTransaction]:
        """Retorna todas as transações bancárias como objetos BankTransaction."""
        query = """
            SELECT 
                bank_transactions.id,
                date,
                description,
                amount,
                category_id,
                operation_type,
                split_info,
                payment_data
            FROM bank_transactions
            WHERE description NOT IN ('Resgate RDB', 'Aplicação RDB', 'Aplicação em CDB')
            ORDER BY date DESC
        """
        cursor = self.execute_query(query)
        return [
            BankTransaction(
                transaction_id=row["id"],
                date=self.date_helper.format_date(row["date"]),
                description=row["description"],
                amount=row["amount"],
                category_id=row["category_id"],
                operation_type=row["operation_type"],
                split_info=(
                    json.loads(row["split_info"]) if row["split_info"] else None
                ),
                payment_data=(
                    json.loads(row["payment_data"]) if row["payment_data"] else None
                ),
            )
            for row in cursor.fetchall()
        ]

    def get_credit_transactions(self) -> List[CreditTransaction]:
        """Retorna todas as transações de crédito como objetos CreditTransaction."""
        query = """
            SELECT 
                credit_transactions.id,
                date,
                description,
                amount,
                category_id,
                status
            FROM credit_transactions
            ORDER BY date DESC
        """
        cursor = self.execute_query(query)
        return [
            CreditTransaction(
                transaction_id=row["id"],
                date=self.date_helper.format_date(row["date"]),
                description=row["description"],
                amount=row["amount"],
                category_id=row["category_id"],
                status=row["status"],
            )
            for row in cursor.fetchall()
        ]

    def get_investments(self) -> List[Investment]:
        """Retorna todas as transações de investimentos."""
        investment_query = """
            SELECT 
                id,
                name,
                balance,
                type,
                subtype,
                date,
                due_date,
                issuer,
                rate_type
            FROM investments
            WHERE balance != 0
            ORDER BY date DESC
        """
        cursor = self.execute_query(investment_query)
        return [
            Investment(
                investment_id=row["id"],
                name=row["name"],
                balance=row["balance"],
                type_=row["type"],
                subtype=row["subtype"],
                date=self.date_helper.format_date(row["date"]),
                due_date=self.date_helper.format_date(row["due_date"]),
                issuer=row["issuer"],
                rate_type=row["rate_type"],
            )
            for row in cursor.fetchall()
        ]

    def get_bank_transaction_by_id(self, transaction_id: str) -> BankTransaction:
        """Retorna uma transação bancária específica pelo ID."""
        query = """
            SELECT 
                bank_transactions.id AS id,
                date,
                description,
                amount,
                category_id,
                operation_type,
                split_info,
                payment_data
            FROM bank_transactions
            WHERE bank_transactions.id = ?
        """
        cursor = self.execute_query(query, (transaction_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(
                f"Transação bancária com ID {transaction_id} não encontrada."
            )
        return BankTransaction(
            transaction_id=row["id"],
            date=self.date_helper.format_date(row["date"]),
            description=row["description"],
            amount=row["amount"],
            category_id=row["category_id"],
            type_=row["type"] if "type" in row.keys() else None,
            operation_type=row["operation_type"],
            split_info=(json.loads(row["split_info"]) if row["split_info"] else None),
            payment_data=(
                json.loads(row["payment_data"]) if row["payment_data"] else None
            ),
        )

    def get_credit_transaction_by_id(self, transaction_id: str) -> CreditTransaction:
        """Retorna uma transação de cartão de crédito específica pelo ID."""
        query = """
            SELECT 
                credit_transactions.id AS id,
                date,
                description,
                amount,
                category_id,
                status
            FROM credit_transactions
            WHERE credit_transactions.id = ?
        """
        cursor = self.execute_query(query, (transaction_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(
                f"Transação de crédito com ID {transaction_id} não encontrada."
            )
        return CreditTransaction(
            transaction_id=row["id"],
            date=self.date_helper.format_date(row["date"]),
            description=row["description"],
            amount=row["amount"],
            category_id=row["category_id"],
            status=row["status"],
        )

    def add_bank_transaction(self, bank_transaction: BankTransaction) -> bool:
        """Adiciona uma nova transação bancária."""
        query = """
            INSERT OR IGNORE INTO bank_transactions
            (id, date, description, amount, category_id, type, operation_type, split_info, payment_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            bank_transaction.transaction_id,
            bank_transaction.date,
            bank_transaction.description,
            bank_transaction.amount,
            bank_transaction.category_id,
            bank_transaction.type_,
            bank_transaction.operation_type,
            (
                json.dumps(bank_transaction.split_info)
                if bank_transaction.split_info
                else None
            ),
            (
                json.dumps(bank_transaction.payment_data)
                if bank_transaction.payment_data
                else None
            ),
        )
        cursor = self.execute_query(query, values)
        return cursor.rowcount > 0

    def add_credit_transaction(self, credit_transaction: CreditTransaction) -> bool:
        """Adiciona uma nova transação de cartão de crédito."""
        query = """
            INSERT OR IGNORE INTO credit_transactions
            (id, date, description, amount, category_id, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        values = (
            credit_transaction.transaction_id,
            credit_transaction.date,
            credit_transaction.description,
            credit_transaction.amount,
            credit_transaction.category_id,
            credit_transaction.status,
        )
        cursor = self.execute_query(query, values)
        return cursor.rowcount > 0

    def update_bank_transaction(
        self,
        transaction_id: str,
        transaction_data: dict,
    ) -> BankTransaction:
        """Atualiza uma transação bancária existente."""
        existing_transaction = self.get_bank_transaction_by_id(transaction_id)
        if not existing_transaction:
            raise ValueError(
                f"Transação bancária com ID {transaction_id} não encontrada"
            )

        field_processors = {
            "description": lambda x: x,
            "amount": float,
            "date": lambda x: x,
            "category_id": lambda x: x,
            "operation_type": lambda x: x,
            "type": lambda x: x,
            "split_info": lambda x: json.dumps(x) if x else None,
        }

        fields_to_update = []
        values = []

        for field, processor in field_processors.items():
            if field in transaction_data:
                fields_to_update.append(f"{field} = ?")
                values.append(processor(transaction_data[field]))

        if not fields_to_update:
            return existing_transaction

        values.append(transaction_id)

        query = (
            f"UPDATE bank_transactions SET {', '.join(fields_to_update)} WHERE id = ?"
        )
        cursor = self.execute_query(query, tuple(values))

        if cursor.rowcount == 0:
            raise ValueError(
                f"Falha ao atualizar transação bancária com ID {transaction_id}"
            )
        return self.get_bank_transaction_by_id(transaction_id)

    def update_credit_transaction(
        self,
        transaction_id: str,
        transaction_data: dict,
    ) -> CreditTransaction:
        """Atualiza uma transação de cartão de crédito existente."""
        existing_transaction = self.get_credit_transaction_by_id(transaction_id)
        if not existing_transaction:
            raise ValueError(
                f"Transação de crédito com ID {transaction_id} não encontrada"
            )

        field_processors = {
            "description": lambda x: x,
            "amount": float,
            "date": lambda x: x,
            "category_id": lambda x: x,
            "status": lambda x: x,
        }

        fields_to_update = []
        values = []

        for field, processor in field_processors.items():
            if field in transaction_data:
                fields_to_update.append(f"{field} = ?")
                values.append(processor(transaction_data[field]))

        if not fields_to_update:
            return existing_transaction
        values.append(transaction_id)

        query = (
            f"UPDATE credit_transactions SET {', '.join(fields_to_update)} WHERE id = ?"
        )
        cursor = self.execute_query(query, tuple(values))

        if cursor.rowcount == 0:
            raise ValueError(
                f"Falha ao atualizar transação de crédito com ID {transaction_id}"
            )

        return self.get_credit_transaction_by_id(transaction_id)

    def category_in_use(self, category_id: int) -> bool:
        """Verifica se uma categoria está em uso em transações."""
        query = """
            SELECT COUNT(*) as count FROM (
                SELECT id FROM bank_transactions WHERE category_id = ?
                UNION ALL
                SELECT id FROM credit_transactions WHERE category_id = ?
            )
        """
        values = (category_id, category_id)
        cursor = self.execute_query(query, values)
        row = cursor.fetchone()
        return row["count"] > 0

    def get_unlinked_transactions(self) -> List[BankTransaction]:
        """Retorna transações bancárias que não estão vinculadas a nenhum splitwise (split_info vazio ou None)."""
        query = """
            SELECT id, date, description, amount, category_id, operation_type, split_info, payment_data
            FROM bank_transactions
            WHERE split_info IS NULL OR split_info = ''
            ORDER BY date DESC
        """
        cursor = self.execute_query(query)
        return [
            BankTransaction(
                transaction_id=row["id"],
                date=self.date_helper.format_date(row["date"]),
                description=row["description"],
                amount=row["amount"],
                category_id=row["category_id"],
                operation_type=row["operation_type"],
                split_info=None,
                payment_data=json.loads(row["payment_data"]),
            )
            for row in cursor.fetchall()
        ]

    # Métodos de Upsert usando a nova funcionalidade do BaseRepository

    def upsert_bank_transaction(self, transaction_data: dict) -> dict:
        """
        Insere ou atualiza uma transação bancária usando strategy insert_only.
        Transações bancárias são consideradas imutáveis, então apenas novos registros são inseridos.

        Args:
            transaction_data: Dict com dados da transação da API Pluggy

        Returns:
            Dict com resultado da operação
        """
        mapped_data = {
            "id": transaction_data["id"],
            "date": transaction_data["date"],
            "description": transaction_data.get("description"),
            "amount": transaction_data.get("amount"),
            "category_id": transaction_data.get("categoryId"),
            "type": transaction_data.get("type"),
            "operation_type": transaction_data.get("operationType"),
            "payment_data": transaction_data.get("paymentData"),
        }

        result = self.upsert(
            "bank_transactions", "id", mapped_data
        )

        if result["action"] == "inserted":
            self._process_pix_person_extraction(transaction_data)
            self._process_category_creation(transaction_data)

        return result

    def upsert_credit_transaction(self, transaction_data: dict) -> dict:
        """
        Insere uma transação de cartão de crédito usando strategy insert_only.
        Transações já existentes são ignoradas.

        Args:
            transaction_data: Dict com dados da transação da API Pluggy

        Returns:
            Dict com resultado da operação
        """
        mapped_data = {
            "id": transaction_data["id"],
            "date": transaction_data["date"],
            "description": transaction_data.get("description"),
            "amount": (
                transaction_data.get("amountInAccountCurrency")
                if transaction_data.get("amountInAccountCurrency") is not None
                else transaction_data.get("amount")
            ),
            "category_id": transaction_data.get("categoryId"),
            "status": transaction_data.get("status"),
        }

        result = self.upsert(
            "credit_transactions",
            "id",
            mapped_data,
        )

        self._process_category_creation(transaction_data)

        return result

    def _process_pix_person_extraction(self, transaction_data: dict) -> None:
        """
        Extrai informações de pessoa de transações PIX e cria registro de pessoa.
        Mantém a lógica existente de fetch_data.py.
        """
        if transaction_data.get(
            "operationType"
        ) == "PIX" and "|" in transaction_data.get("description", ""):

            person_name = transaction_data["description"].split("|")[-1].strip()
            document_number = None

            payment_data = transaction_data.get("paymentData", {})
            if "transferência recebida|" in transaction_data["description"].lower():
                document_number = payment_data.get("payer", {}).get("documentNumber")
            elif "transferência enviada|" in transaction_data["description"].lower():
                document_number = payment_data.get("receiver", {}).get("documentNumber")

            if person_name and document_number and document_number.get("type") == "CPF":

                # Usa upsert para pessoa com insert_only (pessoas não mudam)
                person_data = {"id": document_number["value"], "name": person_name}

                self.upsert("persons", "id", person_data)

    def _process_category_creation(self, transaction_data: dict) -> None:
        """
        Cria categoria automaticamente se não existir.
        Mantém a lógica existente de fetch_data.py.
        """
        category_id = transaction_data.get("categoryId")
        category_name = transaction_data.get("category")

        if category_id and category_name:
            category_data = {"id": category_id, "name": category_name}

            # Usa insert_only para categorias (não devem ser alteradas automaticamente)
            self.upsert("categories", "id", category_data)

    def create_bank_transaction(self, transaction: BankTransaction) -> BankTransaction:
        """
        Cria uma nova transação bancária no banco de dados.

        Args:
            transaction: Objeto BankTransaction com os dados da nova transação

        Returns:
            BankTransaction: A transação criada

        Raises:
            ValueError: Se a transação já existe ou dados são inválidos
        """
        if not transaction.transaction_id:
            raise ValueError("ID da transação é obrigatório")
        if not transaction.description:
            raise ValueError("Descrição da transação é obrigatória")
        if transaction.amount is None:
            raise ValueError("Valor da transação é obrigatório")

        # Verifica se já existe uma transação com o mesmo ID
        try:
            existing_transaction = self.get_bank_transaction_by_id(
                transaction.transaction_id
            )
            if existing_transaction:
                raise ValueError(
                    f"Transação bancária com ID {transaction.transaction_id} já existe"
                )
        except ValueError:
            # Se der erro, significa que não encontrou a transação (esperado)
            pass

        # Cria a transação usando o método existente
        success = self.add_bank_transaction(transaction)

        if success:
            return transaction
        else:
            raise ValueError("Falha ao criar transação bancária")

    def create_credit_transaction(
        self, transaction: CreditTransaction
    ) -> CreditTransaction:
        """
        Cria uma nova transação de cartão de crédito no banco de dados.

        Args:
            transaction: Objeto CreditTransaction com os dados da nova transação

        Returns:
            CreditTransaction: A transação criada

        Raises:
            ValueError: Se a transação já existe ou dados são inválidos
        """
        if not transaction.transaction_id:
            raise ValueError("ID da transação é obrigatório")
        if not transaction.description:
            raise ValueError("Descrição da transação é obrigatória")
        if transaction.amount is None:
            raise ValueError("Valor da transação é obrigatório")

        # Verifica se já existe uma transação com o mesmo ID
        try:
            existing_transaction = self.get_credit_transaction_by_id(
                transaction.transaction_id
            )
            if existing_transaction:
                raise ValueError(
                    f"Transação de crédito com ID {transaction.transaction_id} já existe"
                )
        except ValueError:
            # Se der erro, significa que não encontrou a transação (esperado)
            pass

        # Cria a transação usando o método existente
        success = self.add_credit_transaction(transaction)

        if success:
            return transaction
        else:
            raise ValueError("Falha ao criar transação de crédito")

    def delete_bank_transaction(self, transaction_id: str) -> bool:
        """
        Deleta uma transação bancária do banco de dados.

        Args:
            transaction_id: ID da transação a ser deletada

        Returns:
            bool: True se a transação foi deletada com sucesso

        Raises:
            ValueError: Se a transação não existe ou está sendo referenciada
        """
        if not transaction_id:
            raise ValueError("ID da transação é obrigatório")

        # Verifica se a transação existe
        try:
            transaction = self.get_bank_transaction_by_id(transaction_id)
        except ValueError as exc:
            raise ValueError(
                f"Transação bancária com ID {transaction_id} não encontrada"
            ) from exc

        # Verifica se a transação está sendo referenciada no splitwise
        query_check_splitwise = """
            SELECT COUNT(*) as count
            FROM splitwise
            WHERE transaction_id = ?
        """
        cursor = self.execute_query(query_check_splitwise, (transaction_id,))
        if cursor.fetchone()["count"] > 0:
            raise ValueError(
                f"Não é possível deletar transação '{transaction.description}'. Ela está vinculada a entradas do Splitwise."
            )

        # Verifica se faz parte de alguma divisão (split_info)
        if transaction.split_info:
            raise ValueError(
                f"Não é possível deletar transação '{transaction.description}'. Ela possui informações de divisão."
            )

        # Deleta a transação
        query = "DELETE FROM bank_transactions WHERE id = ?"
        cursor = self.execute_query(query, (transaction_id,))
        return cursor.rowcount > 0

    def delete_credit_transaction(self, transaction_id: str) -> bool:
        """
        Deleta uma transação de cartão de crédito do banco de dados.

        Args:
            transaction_id: ID da transação a ser deletada

        Returns:
            bool: True se a transação foi deletada com sucesso

        Raises:
            ValueError: Se a transação não existe ou está sendo referenciada
        """
        if not transaction_id:
            raise ValueError("ID da transação é obrigatório")

        # Verifica se a transação existe
        try:
            transaction = self.get_credit_transaction_by_id(transaction_id)
        except ValueError as exc:
            raise ValueError(
                f"Transação de crédito com ID {transaction_id} não encontrada"
            ) from exc

        # Verifica se a transação está sendo referenciada no splitwise
        query_check_splitwise = """
            SELECT COUNT(*) as count
            FROM splitwise
            WHERE transaction_id = ?
        """
        cursor = self.execute_query(query_check_splitwise, (transaction_id,))
        if cursor.fetchone()["count"] > 0:
            raise ValueError(
                f"Não é possível deletar transação '{transaction.description}'. Ela está vinculada a entradas do Splitwise."
            )

        # Deleta a transação
        query = "DELETE FROM credit_transactions WHERE id = ?"
        cursor = self.execute_query(query, (transaction_id,))
        return cursor.rowcount > 0

    def get_operation_types(self) -> List[str]:
        """
        Retorna lista de tipos de operação únicos das transações bancárias.

        Returns:
            List[str]: Lista de tipos de operação únicos
        """
        query = """
            SELECT DISTINCT operation_type
            FROM bank_transactions
            WHERE operation_type IS NOT NULL
            AND operation_type != ''
            ORDER BY operation_type
        """
        cursor = self.execute_query(query)
        return [row["operation_type"] for row in cursor.fetchall()]
