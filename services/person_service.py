from typing import List
from repositories.person_repository import PersonRepository
from models.person import Person


class PersonService:
    """
    Serviço para cadastro e gestão de pessoas (persons).
    """

    def __init__(self):
        self.person_repo = PersonRepository()

    def get_person_by_id(self, person_id: str) -> Person:
        """Retorna uma pessoa específica pelo ID."""
        return self.person_repo.get_person_by_id(person_id)

    def get_all_people(self) -> List[Person]:
        """Retorna todas as pessoas cadastradas."""
        return self.person_repo.get_all_people()

    def create_person(self, person_data: dict) -> Person:
        """
        Cria uma nova pessoa.

        Args:
            person_data: Dict com dados da pessoa - deve conter 'id' e 'name'

        Returns:
            Person: A pessoa criada

        Raises:
            ValueError: Se dados são inválidos ou pessoa já existe
        """
        if not person_data.get("id"):
            raise ValueError("ID da pessoa é obrigatório")
        if not person_data.get("name"):
            raise ValueError("Nome da pessoa é obrigatório")

        person = Person(person_id=person_data["id"], name=person_data["name"])

        if len(person.name.strip()) < 2:
            raise ValueError("Nome da pessoa deve ter pelo menos 2 caracteres")

        return self.person_repo.create_person(person)

    def delete_person(self, person_id: str) -> bool:
        """
        Deleta uma pessoa.

        Raises:
            ValueError: Se pessoa não existe
        """
        if not person_id:
            raise ValueError("ID da pessoa é obrigatório")

        person = self.person_repo.get_person_by_id(person_id)
        if not person:
            raise ValueError(f"Pessoa com ID {person_id} não encontrada")

        return self.person_repo.delete_person(person_id)
