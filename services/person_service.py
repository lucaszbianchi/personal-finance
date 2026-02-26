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

    def update_split_info(self, person_id: str, split_info: dict) -> bool:
        """Atualiza split_info de uma pessoa."""
        person = self.person_repo.get_person_by_id(person_id)
        if not person:
            raise ValueError(f"Pessoa com ID {person_id} não encontrada.")
        return self.person_repo.update_person_split_info(person_id, split_info)

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

        # Cria objeto Person com split_info vazio se não fornecido
        person = Person(
            person_id=person_data["id"],
            name=person_data["name"],
            split_info=person_data.get("split_info", {})
        )

        # Valida dados de negócio adicionais se necessário
        if len(person.name.strip()) < 2:
            raise ValueError("Nome da pessoa deve ter pelo menos 2 caracteres")

        # Cria no repositório
        created_person = self.person_repo.create_person(person)
        return created_person

    def delete_person(self, person_id: str) -> bool:
        """
        Deleta uma pessoa.

        Args:
            person_id: ID da pessoa a ser deletada

        Returns:
            bool: True se deletada com sucesso

        Raises:
            ValueError: Se pessoa não existe ou não pode ser deletada
        """
        if not person_id:
            raise ValueError("ID da pessoa é obrigatório")

        # Valida se existe
        person = self.person_repo.get_person_by_id(person_id)
        if not person:
            raise ValueError(f"Pessoa com ID {person_id} não encontrada")

        # Regra de negócio: não permite deletar se é o parceiro atual
        if person.is_partner():
            raise ValueError(f"Não é possível deletar '{person.name}' pois é o parceiro atual do Splitwise")

        # Regra de negócio: não permite deletar se tem pendências não quitadas
        if not person.settled_up():
            raise ValueError(f"Não é possível deletar '{person.name}' pois possui pendências não quitadas")

        # Deleta no repositório (que fará as verificações de integridade)
        return self.person_repo.delete_person(person_id)
