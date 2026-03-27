"""
Módulo de rotas relacionadas a categorias.
"""

from datetime import date

from flask import Blueprint, jsonify, request
from services.category_service import CategoryService
from services.category_visualization_service import CategoryVisualizationService

bp = Blueprint("categories", __name__)
category_service = CategoryService()
category_viz_service = CategoryVisualizationService()


@bp.route("/expense-history", methods=["GET"])
def expense_history():
    """Retorna histórico de gastos por categoria para gráfico de linhas."""
    try:
        months = int(request.args.get("months", 6))
        return jsonify(category_viz_service.get_expense_history(months))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/distribution", methods=["GET"])
def expense_distribution():
    """Retorna distribuição hierárquica de gastos para gráfico Sankey."""
    try:
        month = request.args.get("month", date.today().strftime("%Y-%m"))
        return jsonify(category_viz_service.get_expense_distribution(month))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/", methods=["GET"])
def list_categories():
    """Lista todas as categorias com contagem de transações."""
    try:
        categories = category_service.get_all_categories()
        return jsonify(categories)
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

        name = data["name"]
        category = category_service.create_category(
            name,
            description_translated=data.get("description_translated", name),
            parent_id=data.get("parent_id"),
            parent_description=data.get("parent_description"),
        )
        return (
            jsonify(
                {"id": category.id, "description": category.description}
            ),
            201,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/<category_id>/fields", methods=["PATCH"])
def update_category_fields(category_id: str):
    """Atualiza campos diretos de uma categoria (description_translated, parent_id, parent_description)."""
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({"error": "Body inválido"}), 400

        category_service.update_category_fields(
            category_id,
            description_translated=data.get("description_translated"),
            parent_id=data.get("parent_id"),
            parent_description=data.get("parent_description"),
            expense_type=data.get("expense_type"),
        )
        return jsonify({"message": "Campos atualizados com sucesso"})
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
