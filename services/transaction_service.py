"""
Serviço para gerenciar transações financeiras.
"""

from typing import List
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

    def get_bank_transactions(self) -> List[BankTransaction]:
        """Retorna todas as transações bancárias."""
        return self.transaction_repository.get_bank_transactions()

    def get_credit_transactions(self) -> List[CreditTransaction]:
        """Retorna todas as transações de crédito."""
        return self.transaction_repository.get_credit_transactions()

    def get_investments(self) -> List[Investment]:
        """Retorna todas as transações de investimento."""
        return self.transaction_repository.get_investments()

    def get_bank_transactions_by_period(
        self, start_date: str, end_date: str
    ) -> List[BankTransaction]:
        """Retorna todas as transações bancárias em um determinado período."""
        return self.transaction_repository.get_bank_transactions_by_period(
            start_date, end_date
        )

    def get_credit_transactions_by_period(
        self, start_date: str, end_date: str
    ) -> List[CreditTransaction]:
        """Retorna todas as transações de crédito em um determinado período."""
        return self.transaction_repository.get_credit_transactions_by_period(
            start_date, end_date
        )

    def update_transaction(
        self,
        transaction_type: str,
        transaction_id: str,
        description: str | None,
        category_id: str | None,
    ) -> bool:
        """Atualiza uma transação existente."""
        if transaction_type == "bank":
            transaction = self.transaction_repository.get_bank_transaction_by_id(
                transaction_id
            )
            if description is None:
                description = transaction.description
            if category_id is None:
                category_id = transaction.category_id
            return self.transaction_repository.update_bank_transaction(
                transaction_id, description, category_id, split_info=None
            )
        elif transaction_type == "credit":
            transaction = self.transaction_repository.get_credit_transaction_by_id(
                transaction_id
            )
            if description is None:
                description = transaction.description
            if category_id is None:
                category_id = transaction.category_id
            return self.transaction_repository.update_credit_transaction(
                transaction_id, description, category_id, split_info=None
            )
        return False

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
                transaction_id, None, None, split_info
            )
        elif transaction_type == "credit":
            return self.transaction_repository.update_credit_transaction(
                transaction_id, None, None, split_info
            )
        return False

    def settle_up_split(self, transaction_id: str) -> bool:
        """Configura o split_info.transaction_type de uma transação para "settle up"."""
        transaction = self.transaction_repository.get_bank_transaction_by_id(
            transaction_id
        )
        payment_data = transaction.payment_data
        print(payment_data)
        payer_info = payment_data.get("payer", {})
        document_number = payer_info.get("documentNumber", {})
        if document_number.get("type") != "CPF":
            raise ValueError("Apenas CPFs são suportados no momento.")
        partner_id = document_number.get("value")

        split_info = {"settle_up": True, "partner_id": partner_id}
        return self.transaction_repository.update_bank_transaction(
            transaction_id, None, None, split_info
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
            transaction_id, None, None, split_info
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


if __name__ == "__main__":
    service = TransactionService()
    text = """d4b45254-8ce4-4fa9-8f93-034aa490dd79
            0ae7090d-6b57-44ce-9d46-dd3f0748be65
            cceff951-2ffc-4aac-8978-d1b36afb38a5
            84f7d27f-bcfd-43a6-9caf-1586260c1829
            248a6a2f-e95f-4249-960c-253f0266dfe1
            9b5c7056-ed33-491f-8635-674905737f0b
            82eac901-d3f1-404b-8f94-0f5c54384b45
            287f7ebf-36d5-49cc-a339-7173b4fb44df
            d3ae7648-ddf4-4958-8bae-6e8da9eb65d5
            0cb32630-be63-41bf-bb37-c757b95a16d6
            44b9649e-0568-495d-b1df-209fd8965b0f
            8c8d8fc4-4f95-4052-aa44-055573b98282
            0a14dc2d-c008-4101-929d-4d3022ec38a9
            10af2a9d-a105-4583-889a-c77a1a04d151
            13c25585-9ed2-4f94-b1a7-c7cf60c4d370
            c12a37f1-41a7-4715-b0fd-b9e8298145ea
            7f895804-10cb-4972-ab70-a56e880c1007
            fe9cc3bb-bab2-48bf-97c0-6d71f257a881
            0acaed0d-82e8-4eac-a8ca-b2c3862b841f
            a3d63a17-63c3-4eaa-916e-a4fec4cc06fb
            96e70aa3-155d-4342-b3fd-ed921f879569
            0ebc8035-da20-443f-b2c8-843a2ef9bbb7
            265492d8-4f32-44c6-8ce1-6f693c1d987a
            5c6f3cb0-4c00-4ea3-9133-47ed1850eaca
            27f4a102-1130-4902-8c3a-742c4d3ed6e9
            0ee1a857-bce1-4e1d-a212-65652c8ac5e2
            69fecb78-4bab-4c77-bb31-0288bd2c0848
            de65f824-9e32-42d4-a16e-8e57f61023ae
            d44713e8-0670-4d02-a21e-691eccb15649
            e171b978-b64f-4360-9313-4437c6388aaf
            72d92aa5-2638-4fd1-a461-92b34df0ba1b
            c177539c-8e65-46fd-bfc5-628840072756
            a97e8353-1757-4f3b-a4e1-9375c04da32a
            """
    ids = [line.strip() for line in text.split("\n")]
    for _id in ids:
        service.settle_up_split(_id)
