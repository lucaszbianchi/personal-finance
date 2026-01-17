from datetime import datetime


class Splitwise:
    def __init__(
        self,
        splitwise_id: str,
        amount: float,
        date: datetime,
        description: str,
        category_id: str,
        transaction_id: str,
        is_invalid: bool = False,
    ):
        self.splitwise_id = splitwise_id
        self.amount = amount
        self.date = date
        self.description = description
        self.category_id = category_id
        self.transaction_id = transaction_id
        self.is_invalid = is_invalid
