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

    def get_current_and_future_bill(self, month: str) -> tuple[float, float]:
        """Returns (current_bill, future_bill) totals for the given month and next month."""
        from datetime import datetime, date
        year, mon = int(month[:4]), int(month[5:7])
        # current: due_date in this month
        current_row = self.execute_query(
            "SELECT COALESCE(SUM(total_amount), 0) FROM bills WHERE strftime('%Y-%m', due_date) = ?",
            (month,),
        ).fetchone()
        # future: due_date in next month
        if mon == 12:
            next_month = f"{year + 1}-01"
        else:
            next_month = f"{year}-{mon + 1:02d}"
        future_row = self.execute_query(
            "SELECT COALESCE(SUM(total_amount), 0) FROM bills WHERE strftime('%Y-%m', due_date) = ?",
            (next_month,),
        ).fetchone()
        return float(current_row[0] or 0), float(future_row[0] or 0)

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
