from typing import List, Dict, Any
from repositories.base_repository import BaseRepository


class PersonRepository(BaseRepository):
    """Repositório para gerenciar operações de banco de dados relacionadas a pessoas."""

    def get_all_people(self) -> List[Dict[str, Any]]:
        """Retorna todas as pessoas."""
        query = "SELECT * FROM persons ORDER BY name"
        return self.execute_query(query)

    def get_person_by_id(self, person_id: str) -> Dict[str, Any]:
        """Retorna uma pessoa específica pelo ID."""
        query = "SELECT * FROM persons WHERE id = ?"
        results = self.execute_query(query, (person_id,))
        return results[0] if results else None

    def add_person(self, name: str) -> str:
        """Adiciona uma nova pessoa."""
        query = "INSERT INTO persons (name) VALUES (?)"
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, (name,))
            conn.commit()
            return cur.lastrowid

    def update_person(self, person_id: str, name: str) -> bool:
        """Atualiza uma pessoa existente."""
        query = "UPDATE persons SET name = ? WHERE id = ?"
        result = self.execute_update(query, (name, person_id))
        return result > 0

    def delete_person(self, person_id: str) -> bool:
        """Remove uma pessoa."""
        query = "DELETE FROM persons WHERE id = ?"
        result = self.execute_update(query, (person_id,))
        return result > 0
