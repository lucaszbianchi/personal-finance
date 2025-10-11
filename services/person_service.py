from typing import List
from repositories.person_repository import PersonRepository


class PersonService:
    """
    Serviço para cadastro e associação de pessoas (persons).
    """

    def __init__(self):
        self.person_repo = PersonRepository()

    def add_person(self, name: str) -> str:
        """Adiciona uma nova pessoa e retorna o id gerado."""
        return self.person_repo.add_person(name)

    def get_all_people(self) -> List[dict]:
        """Retorna todas as pessoas cadastradas."""
        return self.person_repo.get_all_people()
