"""
Serviço para gerenciar transações financeiras.
"""

from typing import List, Optional
from repositories.transaction_repository import TransactionRepository
from repositories.category_repository import CategoryRepository
from repositories.person_repository import PersonRepository
from models.transaction import BankTransaction, CreditTransaction
from models.investment import Investment


class TransactionService:
    def __init__(self):
        self.transaction_repository = TransactionRepository()
        self.category_repository = CategoryRepository()
        self.person_repository = PersonRepository()

    def get_bank_transactions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category_id: Optional[str] = None,
    ) -> List[BankTransaction]:
        """Retorna transações bancárias com filtros opcionais."""
        transactions = self.transaction_repository.get_bank_transactions()

        # Aplicar filtros
        if start_date and end_date:
            transactions = [
                t
                for t in transactions
                if start_date <= t.date.split("\n")[0] <= end_date
            ]

        if category_id:
            transactions = [t for t in transactions if t.category_id == category_id]

        return transactions

    def get_credit_transactions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category_id: Optional[str] = None,
    ) -> List[CreditTransaction]:
        """Retorna transações de crédito com filtros opcionais."""
        transactions = self.transaction_repository.get_credit_transactions()

        # Aplicar filtros
        if start_date and end_date:
            transactions = [
                t
                for t in transactions
                if start_date <= t.date.split("\n")[0] <= end_date
            ]

        if category_id:
            transactions = [t for t in transactions if t.category_id == category_id]

        return transactions

    def get_investments(self) -> List[Investment]:
        """Retorna todas as transações de investimento."""
        return self.transaction_repository.get_investments()

    def bulk_update_category(
        self,
        transaction_type: str,
        transaction_ids: list[str],
        category_id: str | None,
    ) -> int:
        """Atualiza a categoria de múltiplas transações em lote."""
        if category_id:
            category = self.category_repository.get_category_by_id(category_id)
            if not category:
                raise ValueError(f"Categoria com ID {category_id} não encontrada")
        return self.transaction_repository.bulk_update_category(
            transaction_type, transaction_ids, category_id
        )

    def add_person_to_share_transaction(
        self,
        transaction_type: str,
        transaction_id: str,
        partners: List[dict],
    ):
        """Associa uma pessoa a uma transação específica.
        transaction_type: 'bank_transactions' ou 'credit_transactions'
        transaction_id: ID da transação
        person_id: ID da pessoa
        share: valor associado à pessoa na transação
        """
        split_info = {
            "partners": [
                {"person_id": pid, "share": share} for pid, share in partners.items()
            ],
        }
        if transaction_type == "bank":
            return self.transaction_repository.update_bank_transaction(
                transaction_id, {"split_info": split_info}
            )
        elif transaction_type == "credit":
            return self.transaction_repository.update_credit_transaction(
                transaction_id, {"split_info": split_info}
            )
        return False

    def settle_up_split(self, transaction_id: str) -> bool:
        """Configura o split_info.transaction_type de uma transação para "settle up"."""
        transaction = self.transaction_repository.get_bank_transaction_by_id(
            transaction_id
        )
        payment_data = transaction.payment_data
        payer_info = payment_data.get("payer", {})
        document_number = payer_info.get("documentNumber", {})
        if document_number.get("type") != "CPF":
            raise ValueError("Apenas CPFs são suportados no momento.")
        partner_id = document_number.get("value")

        split_info = {"settle_up": True, "partner_id": partner_id}
        return self.transaction_repository.update_bank_transaction(
            transaction_id, {"split_info": split_info}
        )

    def add_category_to_settle_up_transaction(
        self,
        transaction_id: str,
        category_id: str,
    ) -> bool:
        """Adiciona uma categoria a uma transação de "settle up"."""
        transaction = self.transaction_repository.get_bank_transaction_by_id(
            transaction_id
        )
        if not transaction.split_info or not transaction.split_info.get("settle_up"):
            raise ValueError("A transação não é uma transação de 'settle up'.")
        split_info = transaction.split_info
        split_info["category"] = category_id
        return self.transaction_repository.update_bank_transaction(
            transaction_id, {"split_info": split_info}
        )

    def check_split_settle_up(self):
        """Verifica se o valor das transações com split_info.settle_up = True
        é igual à soma dos valores do partner associado em transações
        com split_info.partners.
        Retorna um relatório detalhado por pessoa com:
        - Total de settle_up
        - Total de splits
        - Diferença entre settle_up e splits
        - Detalhamento por categoria
        - Lista de transações
        """
        bank_transactions = self.transaction_repository.get_bank_transactions()
        partners_settle_up = [
            t
            for t in bank_transactions
            if t.split_info and t.split_info.get("settle_up", True)
        ]
        persons = self.person_repository.get_all_people()
        result = {}

        # Agrupar transações de settle up por pessoa
        for transaction in partners_settle_up:
            if not transaction.split_info.get("partner_id"):
                continue

            partner_id = transaction.split_info["partner_id"]
            category = transaction.split_info.get("category")

            if partner_id not in result:
                result[partner_id] = {
                    "total_settle_up": 0,
                    "total_splits": 0,
                    "categories": {},
                    "transactions": {"settle_up": [], "splits": []},
                }

            result[partner_id]["total_settle_up"] += transaction.amount
            result[partner_id]["transactions"]["settle_up"].append(
                {
                    "id": transaction.transaction_id,
                    "date": transaction.date.strftime("%Y-%m-%d"),
                    "amount": transaction.amount,
                    "description": transaction.description,
                    "category": category,
                }
            )

            if category:
                if category not in result[partner_id]["categories"]:
                    result[partner_id]["categories"][category] = {
                        "settle_up": 0,
                        "splits": 0,
                    }
                result[partner_id]["categories"][category][
                    "settle_up"
                ] += transaction.amount

        # Calcular total de splits por pessoa
        for transaction in bank_transactions:
            if not transaction.split_info or not transaction.split_info.get("partners"):
                continue

            for partner in transaction.split_info["partners"]:
                partner_id = partner.get("person_id")
                if not partner_id:
                    continue

                share = partner.get("share", 0)

                if partner_id not in result:
                    result[partner_id] = {
                        "total_settle_up": 0,
                        "total_splits": 0,
                        "categories": {},
                        "transactions": {"settle_up": [], "splits": []},
                    }

                result[partner_id]["total_splits"] += share
                result[partner_id]["transactions"]["splits"].append(
                    {
                        "id": transaction.transaction_id,
                        "date": transaction.date.strftime("%Y-%m-%d"),
                        "amount": share,
                        "description": transaction.description,
                        "category": transaction.category_id,
                    }
                )

                if transaction.category_id:
                    if transaction.category_id not in result[partner_id]["categories"]:
                        result[partner_id]["categories"][transaction.category_id] = {
                            "settle_up": 0,
                            "splits": 0,
                        }
                    result[partner_id]["categories"][transaction.category_id][
                        "splits"
                    ] += share

        # Calcular diferenças e formatar resultado final
        final_result = []
        for person in persons:
            if person.id not in result:
                continue

            person_result = result[person.id]
            difference = (
                person_result["total_settle_up"] - person_result["total_splits"]
            )

            categories_diff = {}
            for category, values in person_result["categories"].items():
                categories_diff[category] = values["settle_up"] - values["splits"]

            final_result.append(
                {
                    "person_id": person.id,
                    "name": person.name,
                    "total_settle_up": person_result["total_settle_up"],
                    "total_splits": person_result["total_splits"],
                    "difference": difference,
                    "categories": categories_diff,
                    "transactions": person_result["transactions"],
                }
            )

        return final_result

    def create_bank_transaction(self, transaction_data: dict) -> BankTransaction:
        """
        Cria uma nova transação bancária.

        Args:
            transaction_data: Dict com dados da transação - deve conter 'id', 'description', 'amount', 'date'

        Returns:
            BankTransaction: A transação criada

        Raises:
            ValueError: Se dados são inválidos ou transação já existe
        """
        if not transaction_data.get("id"):
            raise ValueError("ID da transação é obrigatório")
        if not transaction_data.get("description"):
            raise ValueError("Descrição é obrigatória")
        if transaction_data.get("amount") is None:
            raise ValueError("Valor é obrigatório")
        if not transaction_data.get("date"):
            raise ValueError("Data é obrigatória")

        # Valida valor
        try:
            amount = float(transaction_data["amount"])
        except (ValueError, TypeError):
            raise ValueError("Valor deve ser um número")

        # Valida categoria se fornecida
        category_id = transaction_data.get("category_id")
        if category_id:
            category = self.category_repository.get_category_by_id(category_id)
            if not category:
                raise ValueError(f"Categoria com ID {category_id} não encontrada")

        # Cria objeto BankTransaction
        transaction = BankTransaction(
            transaction_id=transaction_data["id"],
            date=transaction_data["date"],
            description=transaction_data["description"],
            amount=amount,
            category_id=category_id,
            type_=transaction_data.get("type"),
            operation_type=transaction_data.get("operation_type"),
            split_info=transaction_data.get("split_info"),
            payment_data=transaction_data.get("payment_data"),
        )

        # Valida regras de negócio
        if abs(amount) < 0.01:  # Valor mínimo
            raise ValueError("Valor deve ser maior que 0.01")

        # Cria no repositório
        created_transaction = self.transaction_repository.create_bank_transaction(
            transaction
        )
        return created_transaction

    def create_credit_transaction(self, transaction_data: dict) -> CreditTransaction:
        """
        Cria uma nova transação de cartão de crédito.

        Args:
            transaction_data: Dict com dados da transação - deve conter 'id', 'description', 'amount', 'date'

        Returns:
            CreditTransaction: A transação criada

        Raises:
            ValueError: Se dados são inválidos ou transação já existe
        """
        if not transaction_data.get("id"):
            raise ValueError("ID da transação é obrigatório")
        if not transaction_data.get("description"):
            raise ValueError("Descrição é obrigatória")
        if transaction_data.get("amount") is None:
            raise ValueError("Valor é obrigatório")
        if not transaction_data.get("date"):
            raise ValueError("Data é obrigatória")

        # Valida valor
        try:
            amount = float(transaction_data["amount"])
        except (ValueError, TypeError):
            raise ValueError("Valor deve ser um número")

        # Valida categoria se fornecida
        category_id = transaction_data.get("category_id")
        if category_id:
            category = self.category_repository.get_category_by_id(category_id)
            if not category:
                raise ValueError(f"Categoria com ID {category_id} não encontrada")

        # Cria objeto CreditTransaction
        transaction = CreditTransaction(
            transaction_id=transaction_data["id"],
            date=transaction_data["date"],
            description=transaction_data["description"],
            amount=amount,
            category_id=category_id,
            status=transaction_data.get("status", "pending"),
        )

        # Valida regras de negócio
        if abs(amount) < 0.01:  # Valor mínimo
            raise ValueError("Valor deve ser maior que 0.01")

        # Cria no repositório
        created_transaction = self.transaction_repository.create_credit_transaction(
            transaction
        )
        return created_transaction

    def delete_bank_transaction(self, transaction_id: str) -> bool:
        """
        Deleta uma transação bancária.

        Args:
            transaction_id: ID da transação a ser deletada

        Returns:
            bool: True se deletada com sucesso

        Raises:
            ValueError: Se transação não existe ou não pode ser deletada
        """
        if not transaction_id:
            raise ValueError("ID da transação é obrigatório")

        # Valida se existe
        try:
            transaction = self.transaction_repository.get_bank_transaction_by_id(
                transaction_id
            )
        except ValueError:
            raise ValueError(
                f"Transação bancária com ID {transaction_id} não encontrada"
            )

        # Regras de negócio adicionais
        # Verifica se é uma transação crítica do sistema (investimentos, etc.)
        if transaction.description and any(
            keyword in transaction.description.lower()
            for keyword in ["resgate rdb", "aplicação rdb", "aplicação em cdb"]
        ):
            raise ValueError(
                f"Não é possível deletar transação de investimento: '{transaction.description}'"
            )

        # Aviso se tem informações de divisão
        if transaction.split_info:
            print(
                f"Aviso: Deletando transação '{transaction.description}' que possui informações de divisão"
            )

        # Deleta no repositório (que fará as verificações de integridade)
        return self.transaction_repository.delete_bank_transaction(transaction_id)

    def delete_credit_transaction(self, transaction_id: str) -> bool:
        """
        Deleta uma transação de cartão de crédito.

        Args:
            transaction_id: ID da transação a ser deletada

        Returns:
            bool: True se deletada com sucesso

        Raises:
            ValueError: Se transação não existe ou não pode ser deletada
        """
        if not transaction_id:
            raise ValueError("ID da transação é obrigatório")

        # Valida se existe
        try:
            transaction = self.transaction_repository.get_credit_transaction_by_id(
                transaction_id
            )
        except ValueError:
            raise ValueError(
                f"Transação de crédito com ID {transaction_id} não encontrada"
            )

        # Regras de negócio: avisa se ainda está pendente de pagamento
        if transaction.status and transaction.status.lower() == "pending":
            print(
                f"Aviso: Deletando transação '{transaction.description}' que ainda está pendente de pagamento"
            )

        # Deleta no repositório (que fará as verificações de integridade)
        return self.transaction_repository.delete_credit_transaction(transaction_id)

    def set_excluded(self, transaction_type: str, transaction_id: str, excluded: bool) -> bool:
        """Marca ou desmarca uma transação como excluída das análises."""
        return self.transaction_repository.set_excluded(transaction_type, transaction_id, excluded)

    def get_operation_types(self) -> List[str]:
        """
        Retorna lista de tipos de operação únicos das transações bancárias.

        Returns:
            List[str]: Lista de tipos de operação únicos
        """
        return self.transaction_repository.get_operation_types()
