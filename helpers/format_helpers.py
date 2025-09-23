import datetime


class FormatHelpers:
    def format_date(self, date_str):
        try:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            dt = dt - datetime.timedelta(hours=3)
            return dt.strftime("%Y-%m-%d\n%H:%M:%S")
        except Exception:
            return date_str
