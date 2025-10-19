from flask import Blueprint, jsonify, request
from services.person_service import PersonService

bp = Blueprint("person", __name__)
person_service = PersonService()


@bp.route("/", methods=["GET"])
def list_people():
    """Lista todas as pessoas cadastradas."""
    try:
        people = person_service.get_all_people()
        return jsonify(
            [
                {
                    "id": p.person_id,
                    "name": p.name,
                    "is_partner": p.is_partner(),
                    "settled_up": p.settled_up(),
                }
                for p in people
            ]
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/<person_id>", methods=["GET"])
def get_person(person_id: str):
    """Retorna detalhes de uma pessoa específica."""
    try:
        person = person_service.get_person_by_id(person_id)
        if not person:
            return jsonify({"error": "Pessoa não encontrada"}), 404
        return jsonify(
            {
                "id": person.person_id,
                "name": person.name,
                "is_partner": person.is_partner(),
                "settled_up": person.settled_up(),
                "split_info": person.split_info,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/<person_id>/partner", methods=["POST"])
def set_partner(person_id: str):
    """Define uma pessoa como parceira."""
    try:
        person_service.set_partner(person_id)
        return jsonify({"message": "Pessoa definida como parceira com sucesso"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/<person_id>/settled", methods=["POST"])
def mark_settled(person_id: str):
    """Marca uma pessoa como quitada (settled up)."""
    try:
        person_service.mark_settled(person_id)
        return jsonify({"message": "Pessoa marcada como quitada com sucesso"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/partners/pending", methods=["GET"])
def list_pending_partners():
    """Lista parceiros com pendências."""
    try:
        pending = person_service.get_partners_pending_settlement()
        return jsonify(
            [
                {
                    "id": p.person_id,
                    "name": p.name,
                    "is_partner": p.is_partner(),
                    "settled_up": p.settled_up(),
                    "split_info": p.split_info,
                }
                for p in pending
            ]
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/<person_id>/split-info", methods=["PATCH"])
def update_split_info(person_id: str):
    """Atualiza parcialmente o split_info de uma pessoa."""
    try:
        split_info = request.get_json()
        if not split_info or not isinstance(split_info, dict):
            return jsonify({"error": "Body inválido"}), 400

        person_service.update_split_info(person_id, split_info)
        return jsonify({"message": "Split info atualizado com sucesso"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
