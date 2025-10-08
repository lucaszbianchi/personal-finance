from typing import Optional
from datetime import datetime


class Transaction:
    def __init__(
        self,
        id_: str,
        date: datetime,
        description: str,
        amount: float,
        category: str,
        type_: str,
        partner_id: Optional[str] = None,
    ):
        self.id = id_
        self.date = date
        self.description = description
        self.amount = amount
        self.category = category
        self.type = type_  # 'bank', 'credit'
        self.partner_id = partner_id


class BankTransaction(Transaction):
    def __init__(
        self,
        id_: str,
        date: datetime,
        description: str,
        amount: float,
        category: str,
        operation_type: Optional[str] = None,
        partner_id: Optional[str] = None,
    ):
        super().__init__(id_, date, description, amount, category, "bank", partner_id)
        self.operation_type = operation_type


class CreditTransaction(Transaction):
    def __init__(
        self,
        id_: str,
        date: datetime,
        description: str,
        amount: float,
        category: str,
        status: Optional[str] = None,
        partner_id: Optional[str] = None,
    ):
        super().__init__(id_, date, description, amount, category, "credit", partner_id)
        self.status = status
