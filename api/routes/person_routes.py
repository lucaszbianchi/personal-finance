from flask import Blueprint, jsonify, request
from services.person_service import PersonService

bp = Blueprint("person", __name__)
person_service = PersonService()


@bp.route("/", methods=["GET"])
def list_people():
    """Lista todas as pessoas cadastradas."""
    try:
        people = person_service.get_all_people()
        return jsonify([{"id": p.person_id, "name": p.name} for p in people])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/<person_id>", methods=["GET"])
def get_person(person_id: str):
    """Retorna detalhes de uma pessoa específica."""
    try:
        person = person_service.get_person_by_id(person_id)
        if not person:
            return jsonify({"error": "Pessoa não encontrada"}), 404
        return jsonify({"id": person.person_id, "name": person.name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/", methods=["POST"])
def create_person():
    """Cria uma nova pessoa."""
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({"error": "Body inválido"}), 400

        if "id" not in data:
            return jsonify({"error": "Campo 'id' é obrigatório"}), 400

        if "name" not in data:
            return jsonify({"error": "Campo 'name' é obrigatório"}), 400

        person = person_service.create_person(data)
        return jsonify({"id": person.person_id, "name": person.name}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/<person_id>", methods=["DELETE"])
def delete_person(person_id: str):
    """Deleta uma pessoa."""
    try:
        success = person_service.delete_person(person_id)
        if success:
            return jsonify({"message": "Pessoa deletada com sucesso"})
        else:
            return jsonify({"error": "Falha ao deletar pessoa"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
