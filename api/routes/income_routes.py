from flask import Blueprint, jsonify, request

from services.income_sources_service import IncomeSourcesService

bp = Blueprint("income", __name__)
income_service = IncomeSourcesService()


@bp.route("/sources", methods=["GET"])
def get_all():
    try:
        return jsonify(income_service.get_all())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/sources", methods=["POST"])
def create():
    try:
        data = request.get_json() or {}
        record = income_service.create(data)
        return jsonify(record), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/sources/<id>", methods=["PUT"])
def update(id: str):
    try:
        data = request.get_json() or {}
        record = income_service.update(id, data)
        return jsonify(record)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/sources/<id>", methods=["DELETE"])
def delete(id: str):
    try:
        income_service.delete(id)
        return "", 204
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/sources/<id>/detail", methods=["GET"])
def get_detail(id: str):
    try:
        return jsonify(income_service.get_detail(id))
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/match-count", methods=["GET"])
def match_count():
    merchant_name = request.args.get("merchant_name", "").strip()
    if not merchant_name:
        return jsonify({"count": 0})
    amount_min = request.args.get("amount_min", type=float)
    amount_max = request.args.get("amount_max", type=float)
    next_occurrence = request.args.get("next_occurrence") or None
    frequency = request.args.get("frequency") or None
    try:
        return jsonify(income_service.count_matching(
            merchant_name, amount_min, amount_max, next_occurrence, frequency
        ))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/monthly", methods=["GET"])
def get_monthly():
    month = request.args.get("month")
    if not month:
        return jsonify({"error": "month parameter required (YYYY-MM)"}), 400
    try:
        return jsonify(income_service.get_monthly_view(month))
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
        return jsonify(income_service.get_yearly_view(int(year_str)))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
