from flask import Blueprint, jsonify, request
from services.bills_service import BillsService

bp = Blueprint("bills", __name__)
bills_service = BillsService()


@bp.route("/monthly", methods=["GET"])
def get_monthly():
    month = request.args.get("month")
    if not month:
        return jsonify({"error": "month required"}), 400
    try:
        return jsonify(bills_service.get_monthly(month))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/history", methods=["GET"])
def get_history():
    return jsonify(bills_service.get_history())
