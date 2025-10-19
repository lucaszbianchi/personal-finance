"""
Módulo de rotas relacionadas ao dashboard e resumos financeiros.
"""

from flask import Blueprint, jsonify, request
from services.finance_summary_service import FinanceSummaryService

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
