from flask import Blueprint, jsonify, request
from services.finance_history_service import FinanceHistoryService

bp = Blueprint("finance_history", __name__)
finance_history_service = FinanceHistoryService()


# Atualiza patrimônio líquido
@bp.route("/net-worth", methods=["POST"])
def update_net_worth():
    result = finance_history_service.update_net_worth()
    return jsonify(result)


# Atualiza fluxo de caixa
@bp.route("/cash-flow", methods=["POST"])
def update_cash_flow():
    data = request.get_json() or {}
    month = data.get("month")
    income = data.get("income")
    expenses = data.get("expenses")
    result = finance_history_service.update_cash_flow(month, income, expenses)
    return jsonify(result)


# Consulta histórico
@bp.route("/history", methods=["GET"])
def get_history():
    result = finance_history_service.get_net_worth_history()
    return jsonify(result)


# Backfill income/expenses para todos os meses com transacoes
@bp.route("/rebuild", methods=["POST"])
def rebuild_history():
    result = finance_history_service.rebuild_all_months()
    return jsonify(result)
