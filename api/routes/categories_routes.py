"""
Módulo de rotas relacionadas a categorias.
"""

from flask import Blueprint, jsonify, request
from services.category_service import CategoryService

bp = Blueprint("categories", __name__)
category_service = CategoryService()


@bp.route("/", methods=["GET"])
def list_categories():
    """Lista todas as categorias."""
    try:
        categories = category_service.get_all_categories()
        return jsonify([{"id": cat.id, "name": cat.name} for cat in categories])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/", methods=["POST"])
def create_category():
    """Cria uma nova categoria."""
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({"error": "Body inválido"}), 400

        if "name" not in data:
            return jsonify({"error": "Campo 'name' é obrigatório"}), 400

        types = data.get("types")
        category = category_service.create_category(data["name"], types)
        return (
            jsonify(
                {"id": category.id, "name": category.name}
            ),
            201,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/<category_name>", methods=["DELETE"])
def delete_category(category_name: str):
    """Deleta uma categoria."""
    try:
        category_service.delete_category(category_name)
        return jsonify({"message": "Categoria deletada com sucesso"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/edit", methods=["POST"])
def edit_category():
    """Edita o nome de uma categoria."""
    try:
        data = request.get_json()
        if not data or "old_name" not in data or "new_name" not in data:
            return (
                jsonify({"error": "Campos 'old_name' e 'new_name' são obrigatórios"}),
                400,
            )

        success = category_service.edit_category(data["old_name"], data["new_name"])
        if success:
            return jsonify({"message": "Categoria atualizada com sucesso"})
        return jsonify({"error": "Falha ao atualizar categoria"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/unify", methods=["POST"])
def unify_categories():
    """Unifica múltiplas categorias em uma só."""
    try:
        data = request.get_json()
        if not data or "categories" not in data or "target" not in data:
            return (
                jsonify({"error": "Campos 'categories' e 'target' são obrigatórios"}),
                400,
            )

        if not isinstance(data["categories"], list):
            return jsonify({"error": "Campo 'categories' deve ser uma lista"}), 400

        success = category_service.unify_categories(data["categories"], data["target"])
        if success:
            return jsonify({"message": "Categorias unificadas com sucesso"})
        return jsonify({"error": "Falha ao unificar categorias"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
