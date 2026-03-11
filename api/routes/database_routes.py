import traceback
from flask import Blueprint, jsonify, current_app
from services.database_service import reset_and_reseed

bp = Blueprint("database", __name__)


@bp.route("/reset", methods=["POST"])
def reset_database():
    if not current_app.debug:
        return jsonify({"status": "error", "message": "Disponível apenas em modo debug"}), 403
    try:
        reset_and_reseed()
        return jsonify({"status": "success", "message": "Banco de dados resetado com sucesso"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500
