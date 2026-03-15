from flask import Blueprint, jsonify, request
from services.cash_flow_service import CashFlowService, current_ym

bp = Blueprint("cash_flow", __name__)
cash_flow_service = CashFlowService()


@bp.route("", methods=["GET"])
def get_cash_flow():
    try:
        window = int(request.args.get("window", 3))
    except (ValueError, TypeError):
        return jsonify({"error": "window must be 3 or 6"}), 400
    end_month = request.args.get("end_month") or current_ym()
    if window not in (3, 6):
        return jsonify({"error": "window must be 3 or 6"}), 400
    return jsonify(cash_flow_service.get_cash_flow(window, end_month))
