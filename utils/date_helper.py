import datetime


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
