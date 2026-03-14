from flask import Blueprint, jsonify, request
from datetime import date
from dateutil.relativedelta import relativedelta
from services.finance_summary_service import FinanceSummaryService
from services.spending_pace_service import SpendingPaceService
from services.net_worth_service import NetWorthService

bp = Blueprint("dashboard", __name__)
finance_summary_service = FinanceSummaryService()
spending_pace_service = SpendingPaceService()
net_worth_service = NetWorthService()


@bp.route("/data", methods=["GET"])
def get_dashboard_data():
    """
    Retorna dados consolidados para o Dashboard:
    - current_month: métricas do mês atual (do finance_history)
    - category_breakdown: gastos por categoria do mês atual
    - history: últimos 12 meses do finance_history
    """
    current_date = date.today().replace(day=1)
    month = current_date.strftime("%Y-%m")
    start_date = current_date.strftime("%Y-%m-%d")
    end_date = (current_date + relativedelta(months=1)).strftime("%Y-%m-%d")

    # Gastos por categoria do mês atual
    category_breakdown = finance_summary_service.get_category_expenses(start_date, end_date)

    # Métricas do mês atual do finance_history
    cutoff = (current_date - relativedelta(months=11)).strftime("%Y-%m")
    current_entry, all_history = finance_summary_service.get_history_data(month, cutoff)

    current_month = {
        "income": current_entry.income if current_entry else None,
        "expenses": current_entry.expenses if current_entry else None,
        "balance": round(
            (current_entry.income or 0) - (current_entry.expenses or 0), 2
        ) if current_entry else None,
        "credit_card_bill": current_entry.credit_card_bill if current_entry else None,
        "total_cash": current_entry.total_cash if current_entry else None,
    }

    # Histórico dos últimos 12 meses
    history = [
        {
            "month": e.month,
            "income": e.income,
            "expenses": e.expenses,
            "investments": e.total_cash,
        }
        for e in all_history
        if e.month >= cutoff
    ]
    history.sort(key=lambda x: x["month"])

    return jsonify({
        "current_month": current_month,
        "category_breakdown": category_breakdown,
        "history": history,
    })


@bp.route("/net-worth", methods=["GET"])
def get_net_worth():
    """Retorna patrimonio liquido atual e historico de 12 meses."""
    return jsonify(net_worth_service.get_net_worth())


@bp.route("/partial-result", methods=["GET"])
def get_partial_result():
    """Retorna resultado parcial do mes corrente e progresso vs meta de saldo."""
    return jsonify(net_worth_service.get_partial_result())


@bp.route("/spending-pace", methods=["GET"])
def get_spending_pace():
    month_param = request.args.get("month")
    if month_param:
        try:
            date.fromisoformat(f"{month_param}-01")
        except ValueError:
            return jsonify({"error": "Invalid month format. Use YYYY-MM"}), 400
        month = month_param
    else:
        month = date.today().strftime("%Y-%m")
    return jsonify(spending_pace_service.get_spending_pace(month))
