import json
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
            Person(
                person_id=row["id"],
                name=row["name"],
                split_info=(json.loads(row["split_info"]) if row["split_info"] else {}),
            )
            for row in cursor.fetchall()
        ]

    def get_person_by_id(self, person_id: str) -> Person:
        """Retorna uma pessoa específica pelo ID."""
        query = "SELECT * FROM persons WHERE id = ?"
        cursor = self.execute_query(query, (person_id,))
        row = cursor.fetchone()
        if row:
            return Person(
                person_id=row["id"],
                name=row["name"],
                split_info=(json.loads(row["split_info"]) if row["split_info"] else {}),
            )
        return None

    def update_person_split_info(self, person_id: str, split_info: dict) -> bool:
        """Atualiza as informações de divisão de uma pessoa."""
        query = "UPDATE persons SET split_info = ? WHERE id = ?"
        cursor = self.execute_query(query, (json.dumps(split_info), person_id))
        return cursor.rowcount > 0

    def set_splitwise_partner(self, person_id: str) -> None:
        """Define uma pessoa como parceira no Splitwise."""
        person = self.get_person_by_id(person_id)
        if not person:
            raise ValueError(f"Pessoa com ID {person_id} não encontrada.")
        split_info = person.split_info
        split_info["is_partner"] = True
        self.update_person_split_info(person_id, split_info)

    def mark_person_settled(self, person_id: str) -> bool:
        """Marca pessoa como quitada (settled_up)."""
        person = self.get_person_by_id(person_id)
        if not person:
            raise ValueError(f"Pessoa com ID {person_id} não encontrada.")
        person.split_info["settled_up"] = True
        return self.update_person_split_info(person_id, person.split_info)

    def get_partner(self) -> Person | None:
        """Retorna a pessoa marcada como parceira."""
        partners = [p for p in self.get_all_people() if p.is_partner()]
        return partners[0] if partners else None

    def get_pending_settlements(self) -> List[Person]:
        """Retorna parceiros que ainda não estão settled_up ou possuem transferências sem categoria."""
        persons = self.get_all_people()
        if not persons:
            return []
        return [p for p in persons if not p.settled_up()]

    def create_person(self, person: Person) -> Person:
        """
        Cria uma nova pessoa no banco de dados.

        Args:
            person: Objeto Person com os dados da nova pessoa

        Returns:
            Person: A pessoa criada com ID atualizado

        Raises:
            ValueError: Se a pessoa já existe ou dados são inválidos
        """
        if not person.person_id:
            raise ValueError("ID da pessoa é obrigatório")
        if not person.name:
            raise ValueError("Nome da pessoa é obrigatório")

        # Verifica se já existe uma pessoa com o mesmo ID
        existing_person = self.get_person_by_id(person.person_id)
        if existing_person:
            raise ValueError(f"Pessoa com ID {person.person_id} já existe")

        # Usa upsert com strategy insert_only para garantir que não sobrescreva
        person_data = {
            "id": person.person_id,
            "name": person.name,
            "split_info": person.split_info if person.split_info else {}
        }

        result = self.upsert("persons", "id", person_data)

        if result["success"] and result["action"] == "inserted":
            return person
        else:
            raise ValueError(f"Falha ao criar pessoa: {result.get('error', 'Erro desconhecido')}")

    def delete_person(self, person_id: str) -> bool:
        """
        Deleta uma pessoa do banco de dados.

        Args:
            person_id: ID da pessoa a ser deletada

        Returns:
            bool: True se a pessoa foi deletada com sucesso

        Raises:
            ValueError: Se a pessoa não existe ou está sendo referenciada
        """
        if not person_id:
            raise ValueError("ID da pessoa é obrigatório")

        # Verifica se a pessoa existe
        person = self.get_person_by_id(person_id)
        if not person:
            raise ValueError(f"Pessoa com ID {person_id} não encontrada")

        # Verifica se a pessoa está sendo referenciada em splitwise
        # (verificação de integridade referencial)
        query_check_splitwise = """
            SELECT COUNT(*) as count
            FROM splitwise
            WHERE transaction_id IN (
                SELECT id FROM bank_transactions
                WHERE split_info LIKE '%"person_id":"' || ? || '"%'
            )
        """
        cursor = self.execute_query(query_check_splitwise, (person_id,))
        if cursor.fetchone()["count"] > 0:
            raise ValueError(f"Não é possível deletar pessoa {person.name}. Ela está sendo referenciada em transações compartilhadas.")

        # Deleta a pessoa
        query = "DELETE FROM persons WHERE id = ?"
        cursor = self.execute_query(query, (person_id,))
        return cursor.rowcount > 0
