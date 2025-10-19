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
    ):
        self.splitwise_id = splitwise_id
        self.amount = amount
        self.date = date
        self.description = description
        self.category_id = category_id
        self.transaction_id = transaction_id
