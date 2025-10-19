import json
from typing import List
from repositories.base_repository import BaseRepository
from models.person import Person


class PersonRepository(BaseRepository):
    """Repositório para gerenciar operações de banco de dados relacionadas a pessoas."""

    def get_all_people(self) -> List[Person]:
        """Retorna todas as pessoas"""
        query = "SELECT * FROM persons ORDER BY name"
        rows = self.execute_query(query)
        return [
            Person(
                person_id=row["id"],
                name=row["name"],
                split_info=(
                    json.loads(row["split_info"]) if row.get("split_info") else {}
                ),
            )
            for row in rows
        ]

    def get_person_by_id(self, person_id: str) -> Person:
        """Retorna uma pessoa específica pelo ID."""
        query = "SELECT * FROM persons WHERE id = ?"
        rows = self.execute_query(query, (person_id,))
        return (
            Person(
                rows[0]["id"],
                rows[0]["name"],
                json.loads(rows[0]["split_info"]) if rows[0].get("split_info") else {},
            )
            if rows
            else None
        )

    def update_person_split_info(self, person_id: str, split_info: dict) -> bool:
        """Atualiza as informações de divisão de uma pessoa."""
        query = "UPDATE persons SET split_info = ? WHERE id = ?"
        result = self.execute_update(query, (json.dumps(split_info), person_id))
        return result > 0

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
