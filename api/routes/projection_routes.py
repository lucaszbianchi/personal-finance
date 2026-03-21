from flask import Blueprint, jsonify, request

from services.projection_service import ProjectionService

bp = Blueprint("projection", __name__)
projection_service = ProjectionService()


@bp.route("", methods=["GET"])
def get_projection():
    months = request.args.get("months", 12, type=int)
    return jsonify(projection_service.get_projection(months))


@bp.route("/assumptions", methods=["GET"])
def get_assumptions():
    return jsonify(projection_service.get_assumptions())
