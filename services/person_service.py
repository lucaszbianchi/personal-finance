from typing import List
from repositories.person_repository import PersonRepository
from models.person import Person


class PersonService:
    """
    Serviço para cadastro e associação de pessoas (persons).
    """

    def __init__(self):
        self.person_repo = PersonRepository()

    def get_person_by_id(self, person_id: str) -> Person:
        """Retorna uma pessoa específica pelo ID."""
        return self.person_repo.get_person_by_id(person_id)

    def get_all_people(self) -> List[Person]:
        """Retorna todas as pessoas cadastradas."""
        return self.person_repo.get_all_people()

    def set_partner(self, person_id: str):
        """Define uma pessoa como parceira no Splitwise."""
        self.person_repo.set_splitwise_partner(person_id)

    def mark_settled(self, person_id: str):
        """Marca uma pessoa como quitada (settled up)."""
        self.person_repo.mark_person_settled(person_id)

    def get_partners_pending_settlement(self) -> List[Person]:
        """Retorna parceiros com pendências de quitação ou transferências sem categoria."""
        return self.person_repo.get_pending_settlements()
