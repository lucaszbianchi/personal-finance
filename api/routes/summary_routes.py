"""
Módulo de rotas relacionadas ao dashboard e resumos financeiros.
"""

from flask import Blueprint, jsonify, request
from datetime import date
from dateutil.relativedelta import relativedelta
from services.finance_summary_service import FinanceSummaryService
from repositories.finance_history_repository import FinanceHistoryRepository

bp = Blueprint("summary", __name__)
summary_service = FinanceSummaryService()


@bp.route("/income", methods=["GET"])
def get_income():
    """Retorna a receita total do período."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not start_date or not end_date:
        return jsonify({"error": "start_date e end_date são obrigatórios"}), 400

    income = summary_service.get_income(start_date, end_date)
    return jsonify(
        {"period": {"start_date": start_date, "end_date": end_date}, "income": income}
    )


@bp.route("/expenses", methods=["GET"])
def get_expenses():
    """Retorna a despesa total do período."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not start_date or not end_date:
        return jsonify({"error": "start_date e end_date são obrigatórios"}), 400

    expenses = summary_service.get_expenses(start_date, end_date)
    return jsonify(
        {
            "period": {"start_date": start_date, "end_date": end_date},
            "expenses": expenses,
        }
    )


@bp.route("/investments", methods=["GET"])
def get_investments():
    """Retorna o valor total investido."""
    investment_value = summary_service.get_investment_value()
    return jsonify({"total_investments": investment_value})


@bp.route("/expenses/categories", methods=["GET"])
def get_expenses_by_category():
    """Retorna as despesas agrupadas por categoria no período."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not start_date or not end_date:
        return jsonify({"error": "start_date e end_date são obrigatórios"}), 400

    category_expenses = summary_service.get_category_expenses(start_date, end_date)
    return jsonify(
        {
            "period": {"start_date": start_date, "end_date": end_date},
            "categories": category_expenses,
        }
    )


@bp.route("/full", methods=["GET"])
def get_full_summary():
    """Retorna um resumo financeiro completo do período."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not start_date or not end_date:
        return jsonify({"error": "start_date e end_date são obrigatórios"}), 400

    summary = summary_service.get_full_summary(start_date, end_date)
    return jsonify(summary)


@bp.route("/monthly", methods=["GET"])
def get_monthly_summary():
    """
    Retorna resumo do mês com comparativo ao anterior, metas e fontes de renda.
    Query param: month=YYYY-MM (default: mês atual)
    """
    month_param = request.args.get("month")
    if month_param:
        try:
            current_date = date.fromisoformat(f"{month_param}-01")
        except ValueError:
            return jsonify({"error": "Formato de month inválido. Use YYYY-MM"}), 400
    else:
        current_date = date.today().replace(day=1)

    month = current_date.strftime("%Y-%m")
    prev_date = (current_date - relativedelta(months=1))
    prev_month = prev_date.strftime("%Y-%m")

    start_date = current_date.strftime("%Y-%m-%d")
    end_date = (current_date + relativedelta(months=1)).strftime("%Y-%m-%d")

    # Dados do mês atual
    category_breakdown = summary_service.get_category_expenses(start_date, end_date)
    income = summary_service.get_income(start_date, end_date)
    expenses = summary_service.get_expenses(start_date, end_date)

    history_repo = FinanceHistoryRepository()
    try:
        current_entry = history_repo.get_by_month(month)
        prev_entry = history_repo.get_by_month(prev_month)
    finally:
        history_repo.close()

    current_data = {
        "month": month,
        "income": income,
        "expenses": expenses,
        "balance": round(income - expenses, 2),
        "credit_card_bill": current_entry.credit_card_bill if current_entry else None,
        "category_breakdown": category_breakdown,
    }

    prev_income = prev_entry.income if prev_entry and prev_entry.income is not None else None
    prev_expenses = prev_entry.expenses if prev_entry and prev_entry.expenses is not None else None
    prev_balance = (
        round((prev_income or 0) - (prev_expenses or 0), 2)
        if prev_entry else None
    )
    previous_data = {
        "month": prev_month,
        "income": prev_income,
        "expenses": prev_expenses,
        "balance": prev_balance,
    }

    def _delta_pct(current, previous):
        if previous is None or previous == 0:
            return None
        return round((current - previous) / abs(previous) * 100, 2)

    current_balance = round(income - expenses, 2)
    comparison = {
        "income_delta_pct": _delta_pct(income, prev_income),
        "expenses_delta_pct": _delta_pct(expenses, prev_expenses),
        "balance_delta_pct": _delta_pct(current_balance, prev_balance),
    }

    return jsonify({
        "current": current_data,
        "previous": previous_data,
        "comparison": comparison,
    })
