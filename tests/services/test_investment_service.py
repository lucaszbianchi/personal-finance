import unittest
from unittest.mock import MagicMock, patch
from services.investment_service import InvestmentService
from models.investment import Investment
from models.finance_history import FinanceHistory


def _make_investment(name="Tesouro IPCA", inv_type="FIXED_INCOME", balance=1000.0):
    inv = MagicMock(spec=Investment)
    inv.name = name
    inv.type = inv_type
    inv.balance = balance
    inv.investment_id = f"id-{name}"
    inv.subtype = "LCI"
    inv.amount = balance * 0.9
    inv.date = "2026-03-01"
    inv.due_date = "2027-03-01"
    inv.issuer = "Banco X"
    inv.rate_type = "CDI"
    return inv


class TestInvestmentService(unittest.TestCase):
    def setUp(self):
        with patch("services.investment_service.InvestmentRepository"), patch(
            "services.investment_service.FinanceHistoryRepository"
        ):
            self.service = InvestmentService()

        self.mock_inv_repo = MagicMock()
        self.mock_hist_repo = MagicMock()
        self.service.investment_repository = self.mock_inv_repo
        self.service.finance_history_repository = self.mock_hist_repo

    def test_get_investments_returns_list(self):
        inv = _make_investment()
        self.mock_inv_repo.get_investments.return_value = [inv]

        result = self.service.get_investments()

        self.assertEqual(result, [inv])
        self.mock_inv_repo.get_investments.assert_called_once()
        self.mock_inv_repo.close.assert_called_once()

    def test_get_investments_closes_repo_on_error(self):
        self.mock_inv_repo.get_investments.side_effect = RuntimeError("db error")

        with self.assertRaises(RuntimeError):
            self.service.get_investments()

        self.mock_inv_repo.close.assert_called_once()

    def test_get_investment_history_groups_by_type(self):
        inv = _make_investment(name="Tesouro IPCA", inv_type="FIXED_INCOME")
        self.mock_inv_repo.get_investments.return_value = [inv]

        history_entry = FinanceHistory(
            month="2026-03",
            investments={"Tesouro IPCA": 1000.0},
            credit_card_bill=None,
            credit_card_future_bill=None,
            total_cash=None,
            expenses=None,
            income=None,
            risk_management=None,
        )
        self.mock_hist_repo.get_all.return_value = [history_entry]

        result = self.service.get_investment_history()

        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry["month"], "2026-03")
        self.assertEqual(entry["total"], 1000.0)
        self.assertEqual(entry["by_type"], {"FIXED_INCOME": 1000.0})
        self.assertEqual(entry["investments"], {"Tesouro IPCA": 1000.0})

    def test_get_investment_history_unknown_type_defaults_to_other(self):
        self.mock_inv_repo.get_investments.return_value = []

        history_entry = FinanceHistory(
            month="2026-03",
            investments={"Unknown Fund": 500.0},
            credit_card_bill=None,
            credit_card_future_bill=None,
            total_cash=None,
            expenses=None,
            income=None,
            risk_management=None,
        )
        self.mock_hist_repo.get_all.return_value = [history_entry]

        result = self.service.get_investment_history()

        self.assertEqual(result[0]["by_type"], {"OTHER": 500.0})

    def test_get_investment_history_skips_empty_months(self):
        self.mock_inv_repo.get_investments.return_value = []
        empty_entry = FinanceHistory(
            month="2026-02",
            investments={},
            credit_card_bill=None,
            credit_card_future_bill=None,
            total_cash=None,
            expenses=None,
            income=None,
            risk_management=None,
        )
        self.mock_hist_repo.get_all.return_value = [empty_entry]

        result = self.service.get_investment_history()

        self.assertEqual(result, [])

    def test_get_investment_history_aggregates_multiple_investments_by_type(self):
        inv1 = _make_investment(name="CDB Banco A", inv_type="FIXED_INCOME", balance=1000.0)
        inv2 = _make_investment(name="CDB Banco B", inv_type="FIXED_INCOME", balance=500.0)
        self.mock_inv_repo.get_investments.return_value = [inv1, inv2]

        history_entry = FinanceHistory(
            month="2026-03",
            investments={"CDB Banco A": 1000.0, "CDB Banco B": 500.0},
            credit_card_bill=None,
            credit_card_future_bill=None,
            total_cash=None,
            expenses=None,
            income=None,
            risk_management=None,
        )
        self.mock_hist_repo.get_all.return_value = [history_entry]

        result = self.service.get_investment_history()

        self.assertEqual(result[0]["by_type"], {"FIXED_INCOME": 1500.0})
        self.assertEqual(result[0]["total"], 1500.0)

    def test_get_investment_history_closes_repos_on_error(self):
        self.mock_inv_repo.get_investments.side_effect = RuntimeError("db error")

        with self.assertRaises(RuntimeError):
            self.service.get_investment_history()

        self.mock_inv_repo.close.assert_called_once()
        self.mock_hist_repo.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
