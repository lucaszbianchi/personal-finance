"""
Módulo de rotas relacionadas às configurações do sistema.
"""

from flask import Blueprint, jsonify, request
from services.settings_service import SettingsService
from services.finance_history_service import FinanceHistoryService
from datetime import datetime

bp = Blueprint("settings", __name__)
settings_service = SettingsService()
finance_history_service = FinanceHistoryService()


@bp.route("/meal-allowance", methods=["GET", "POST"])
def handle_meal_allowance():
    """Gerencia as configurações do vale refeição"""
    if request.method == "POST":
        data = request.get_json()
        if not data or "value" not in data:
            return jsonify({"error": "value é obrigatório"}), 400

        value = float(data["value"])

        settings_service.update_meal_allowance(value)

        month = data.get("month") or datetime.now().strftime("%Y-%m")
        finance_history_service.update_meal_allowance(month=month, value=value)

        return jsonify({"status": "success"})
    else:
        value = settings_service.get_meal_allowance()
        return jsonify({"value": value})


@bp.route("/credit-card", methods=["GET", "POST"])
def handle_credit_card():
    """Gerencia as datas do cartão de crédito"""
    if request.method == "POST":
        data = request.get_json()
        if not data or "closing_day" not in data or "due_day" not in data:
            return jsonify({"error": "closing_day e due_day são obrigatórios"}), 400

        try:
            settings_service.update_credit_card_dates(
                int(data["closing_day"]), int(data["due_day"])
            )
            return jsonify({"status": "success"})
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
    else:
        config = settings_service.get_credit_card_dates()
        return jsonify(config)


@bp.route("/all", methods=["GET"])
def get_all_settings():
    """Retorna todas as configurações"""
    return jsonify(settings_service.get_all_settings())
