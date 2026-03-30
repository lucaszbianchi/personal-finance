from typing import List
from repositories.base_repository import BaseRepository
from models.person import Person


class PersonRepository(BaseRepository):
    """Repositório para gerenciar operações de banco de dados relacionadas a pessoas."""

    def __init__(self, db_path: str = "finance.db"):
        super().__init__(db_path=db_path)

    def get_all_people(self) -> List[Person]:
        """Retorna todas as pessoas"""
        query = "SELECT * FROM persons ORDER BY name"
        cursor = self.execute_query(query)
        return [
            Person(person_id=row["id"], name=row["name"])
            for row in cursor.fetchall()
        ]

    def get_person_by_id(self, person_id: str) -> Person:
        """Retorna uma pessoa específica pelo ID."""
        query = "SELECT * FROM persons WHERE id = ?"
        cursor = self.execute_query(query, (person_id,))
        row = cursor.fetchone()
        if row:
            return Person(person_id=row["id"], name=row["name"])
        return None

    def create_person(self, person: Person) -> Person:
        """
        Cria uma nova pessoa no banco de dados.

        Raises:
            ValueError: Se a pessoa já existe ou dados são inválidos
        """
        if not person.person_id:
            raise ValueError("ID da pessoa é obrigatório")
        if not person.name:
            raise ValueError("Nome da pessoa é obrigatório")

        existing_person = self.get_person_by_id(person.person_id)
        if existing_person:
            raise ValueError(f"Pessoa com ID {person.person_id} já existe")

        result = self.upsert("persons", "id", {"id": person.person_id, "name": person.name})

        if result["success"] and result["action"] == "inserted":
            return person
        else:
            raise ValueError(f"Falha ao criar pessoa: {result.get('error', 'Erro desconhecido')}")

    def delete_person(self, person_id: str) -> bool:
        """
        Deleta uma pessoa do banco de dados.

        Raises:
            ValueError: Se a pessoa não existe
        """
        if not person_id:
            raise ValueError("ID da pessoa é obrigatório")

        person = self.get_person_by_id(person_id)
        if not person:
            raise ValueError(f"Pessoa com ID {person_id} não encontrada")

        query = "DELETE FROM persons WHERE id = ?"
        cursor = self.execute_query(query, (person_id,))
        return cursor.rowcount > 0
