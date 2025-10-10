from datetime import datetime


class Investment:
    def __init__(
        self,
        investment_id: str,
        name: str,
        balance: float,
        type_: str,
        subtype: str,
        date: datetime,
        due_date: datetime,
        issuer: str,
        rate_type: str,
    ):
        self.investment_id = investment_id
        self.name = name
        self.balance = balance
        self.type = type_
        self.subtype = subtype
        self.date = date
        self.due_date = due_date
        self.issuer = issuer
        self.rate_type = rate_type
