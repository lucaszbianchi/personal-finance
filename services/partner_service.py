from typing import List


class PartnerService:
    """
    Serviço para cadastro e associação de parceiros (persons).
    """

    def __init__(
        self,
    ):
        self.db_path = "finance.db"

    def add_partner(self, name: str) -> str:
        """Adiciona um novo parceiro e retorna o id gerado."""
        pass

    def get_all_partners(self) -> List[dict]:
        pass

    def associate_partner_with_transaction(
        self, transaction_table: str, transaction_id: str, partner_id: str
    ):
        """Associa um parceiro a uma transação específica."""
        pass
