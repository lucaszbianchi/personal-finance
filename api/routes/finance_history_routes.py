from flask import Blueprint, jsonify, request
from services.finance_history_service import FinanceHistoryService

bp = Blueprint("finance_history", __name__)
finance_history_service = FinanceHistoryService()


# Atualiza vale refeição
@bp.route("/meal-allowance", methods=["POST"])
def update_meal_allowance():
    data = request.get_json() or {}
    month = data.get("month")
    value = data.get("value")
    result = finance_history_service.update_meal_allowance(month, value)
    return jsonify(result)


# Atualiza cartão de crédito
@bp.route("/credit-card", methods=["POST"])
def update_credit_card():
    data = request.get_json() or {}
    month = data.get("month")
    current_bill = data.get("current_bill")
    future_bill = data.get("future_bill")
    result = finance_history_service.update_credit_card_info(
        month, current_bill, future_bill
    )
    return jsonify(result)


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


# Atualiza tudo de uma vez
@bp.route("/update-all", methods=["POST"])
def update_all():
    result = finance_history_service.update_all()
    return jsonify(result)


# Consulta histórico
@bp.route("/history", methods=["GET"])
def get_history():
    result = finance_history_service.get_net_worth_history()
    return jsonify(result)
