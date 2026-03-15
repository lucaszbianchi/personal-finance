import datetime
from datetime import date as _date


class DateHelper:

    def __init__(self):
        self.date_format = "%Y-%m-%dT%H:%M:%S.%fZ"

    def format_date(self, date_str):
        try:
            dt = datetime.datetime.strptime(date_str, self.date_format)
            dt = dt - datetime.timedelta(hours=3)
            return dt.strftime("%Y-%m-%d\n%H:%M:%S")
        except Exception:
            return date_str

    def month_key(self, date_str):
        """Converte uma string de data para uma chave de mês.
        Ex: "2025-09-15T12:34:56.789Z" -> "2025-09"
        """
        try:
            dt = datetime.datetime.strptime(date_str, self.date_format)
            dt = dt - datetime.timedelta(hours=3)
            return dt.strftime("%Y-%m")
        except Exception:
            return date_str[:7]

    @staticmethod
    def day_of_month(date_str: str | None) -> int | None:
        """Extract day-of-month integer from a YYYY-MM-DD string."""
        if not date_str:
            return None
        try:
            return int(date_str[8:10])
        except (ValueError, IndexError):
            return None

    @staticmethod
    def build_match_timeline(txns: list[dict]) -> list[dict]:
        """Return 12 monthly entries (oldest to newest), matched=True if any txn falls in that month."""
        matched_months = {t["date"][:7] for t in txns}
        today = _date.today()
        result = []
        for delta in range(11, -1, -1):
            m = today.month - delta
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            month_str = f"{y}-{m:02d}"
            result.append({"month": month_str, "matched": month_str in matched_months})
        return result

    @staticmethod
    def compute_transaction_metrics(txns: list[dict], last_date_key: str) -> dict:
        """Return standard metrics dict for a list of matched transactions."""
        amounts = [t["amount"] for t in txns]
        year = _date.today().year
        year_amounts = [t["amount"] for t in txns if t["date"].startswith(str(year))]
        return {
            "last_amount": round(amounts[0], 2) if amounts else None,
            "avg_amount": round(sum(amounts) / len(amounts), 2) if amounts else None,
            "total_this_year": round(sum(year_amounts), 2),
            last_date_key: txns[0]["date"] if txns else None,
        }
