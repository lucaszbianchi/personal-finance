# pylint: disable=attribute-defined-outside-init
from utils.date_helper import DateHelper


class TestDateHelper:
    def setup_method(self):
        self.date_helper = DateHelper()

    def test_format_date(self):
        date_str = "2023-10-15"
        formatted_date = self.date_helper.format_date(date_str)
        assert formatted_date == "2023-10-15"

    def test_parse_date(self):
        date_str = "2025-09-15T12:34:56.789Z"
        parsed_date = self.date_helper.month_key(date_str)
        assert parsed_date == "2025-09"
