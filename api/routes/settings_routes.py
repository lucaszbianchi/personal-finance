"""
Módulo de rotas relacionadas às configurações do sistema.
"""

from flask import Blueprint, jsonify, request
from services.settings_service import SettingsService

bp = Blueprint("settings", __name__)
settings_service = SettingsService()


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


@bp.route("/optional-expenses-target", methods=["GET", "POST"])
def handle_optional_expenses_target():
    """Gerencia a meta mensal de gastos opcionais"""
    if request.method == "POST":
        data = request.get_json()
        if data is None or "value" not in data:
            return jsonify({"error": "Campo 'value' obrigatorio"}), 400
        try:
            settings_service.update_optional_expenses_target(float(data["value"]))
            return jsonify({"status": "success"})
        except (ValueError, TypeError) as e:
            return jsonify({"error": str(e)}), 400
    return jsonify({"value": settings_service.get_optional_expenses_target()})


@bp.route("/all", methods=["GET"])
def get_all_settings():
    """Retorna todas as configurações"""
    return jsonify(settings_service.get_all_settings())
