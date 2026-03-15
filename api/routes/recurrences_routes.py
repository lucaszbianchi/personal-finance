from flask import Blueprint, jsonify, request

from services.recurrences_service import RecurrencesService

bp = Blueprint("recurrences", __name__)
recurrences_service = RecurrencesService()


@bp.route("", methods=["GET"])
def get_all():
    try:
        return jsonify(recurrences_service.get_all())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("", methods=["POST"])
def create():
    try:
        data = request.get_json() or {}
        record = recurrences_service.create(data)
        return jsonify(record), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/match-count", methods=["GET"])
def match_count():
    merchant_name = request.args.get("merchant_name", "").strip()
    if not merchant_name:
        return jsonify({"count": 0})
    amount_min = request.args.get("amount_min", type=float)
    amount_max = request.args.get("amount_max", type=float)
    try:
        return jsonify(recurrences_service.count_matching(merchant_name, amount_min, amount_max))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/<id>/detail", methods=["GET"])
def get_detail(id: str):
    try:
        return jsonify(recurrences_service.get_detail(id))
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/<id>", methods=["PUT"])
def update(id: str):
    try:
        data = request.get_json() or {}
        record = recurrences_service.update(id, data)
        return jsonify(record)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/<id>", methods=["DELETE"])
def delete(id: str):
    try:
        recurrences_service.delete(id)
        return "", 204
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/<id>/toggle-unavoidable", methods=["PATCH"])
def toggle_unavoidable(id: str):
    try:
        record = recurrences_service.toggle_unavoidable(id)
        return jsonify(record)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/monthly", methods=["GET"])
def get_monthly():
    month = request.args.get("month")
    if not month:
        return jsonify({"error": "month parameter required (YYYY-MM)"}), 400
    try:
        return jsonify(recurrences_service.get_monthly_view(month))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/yearly", methods=["GET"])
def get_yearly():
    year_str = request.args.get("year")
    if not year_str or not year_str.isdigit():
        return jsonify({"error": "year parameter required (YYYY)"}), 400
    try:
        return jsonify(recurrences_service.get_yearly_view(int(year_str)))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/installments", methods=["GET"])
def get_installments():
    month = request.args.get("month")
    if not month:
        return jsonify({"error": "month parameter required (YYYY-MM)"}), 400
    try:
        return jsonify(recurrences_service.get_installments(month))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
