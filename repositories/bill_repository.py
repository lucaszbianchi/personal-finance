import json
from repositories.base_repository import BaseRepository


class BillRepository(BaseRepository):
    """Repositório para gerenciar faturas de cartão de crédito."""

    def upsert_bill(self, bill_data: dict, account_id: str) -> dict:
        """Insere ou atualiza uma fatura."""
        finance_charges = bill_data.get("financeCharges")
        mapped_data = {
            "id": bill_data["id"],
            "account_id": account_id,
            "due_date": bill_data.get("dueDate"),
            "total_amount": bill_data.get("totalAmount"),
            "total_amount_currency_code": bill_data.get("totalAmountCurrencyCode"),
            "minimum_payment_amount": bill_data.get("minimumPaymentAmount"),
            "allows_installments": 1 if bill_data.get("allowsInstallments") else 0,
            "finance_charges": (
                json.dumps(finance_charges, ensure_ascii=False)
                if finance_charges is not None
                else None
            ),
        }
        return self.upsert("bills", "id", mapped_data)

    def get_all_bills(self) -> list:
        """Retorna todas as faturas."""
        cursor = self.execute_query("SELECT * FROM bills ORDER BY due_date DESC")
        rows = cursor.fetchall()
        result = []
        for row in rows:
            bill = dict(row)
            if bill.get("finance_charges"):
                bill["finance_charges"] = json.loads(bill["finance_charges"])
            result.append(bill)
        return result
