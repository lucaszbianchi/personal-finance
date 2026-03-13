from typing import Optional
from repositories.base_repository import BaseRepository


class UserGoalsRepository(BaseRepository):
    def __init__(self, db_path: str = "finance.db"):
        super().__init__(db_path=db_path)

    def get_total_monthly_goal(self) -> Optional[float]:
        cursor = self.execute_query(
            "SELECT amount FROM user_goals WHERE category_id IS NULL AND type = 'monthly' LIMIT 1"
        )
        row = cursor.fetchone()
        return row["amount"] if row else None
