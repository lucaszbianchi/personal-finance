from typing import Optional
from datetime import datetime


class Transaction:
    def __init__(
        self,
        transaction_id: str,
        date: datetime,
        description: str,
        amount: float,
        category_id: str,
        type_: str,
        split_info: Optional[dict] = None,
    ):
        self.transaction_id = transaction_id
        self.date = date
        self.description = description
        self.amount = amount
        self.category_id = category_id
        self.transaction_type = type_  # 'bank', 'credit'
        self.split_info = split_info


class BankTransaction(Transaction):
    def __init__(
        self,
        transaction_id: str,
        date: datetime,
        description: str,
        amount: float,
        category_id: str,
        type_: Optional[str] = None,
        operation_type: Optional[str] = None,
        split_info: Optional[dict] = None,
        payment_data: Optional[dict] = None,
    ):
        super().__init__(
            transaction_id, date, description, amount, category_id, "bank", split_info
        )
        self.operation_type = operation_type
        self.payment_data = payment_data
        self.type_ = type_  # 'debit' ou 'credit'


class CreditTransaction(Transaction):
    def __init__(
        self,
        transaction_id: str,
        date: datetime,
        description: str,
        amount: float,
        category_id: str,
        status: Optional[str] = None,
        split_info: Optional[dict] = None,
    ):
        super().__init__(
            transaction_id, date, description, amount, category_id, "credit", split_info
        )
        self.status = status
