"""
Rotas relacionadas à integração com a Pluggy API.
"""

import traceback
from flask import Blueprint, jsonify, request
from requests.exceptions import HTTPError
from services.pluggy_auth_service import create_connect_token, get_item
from repositories.pluggy_item_repository import PluggyItemRepository

bp = Blueprint("pluggy", __name__)


@bp.route("/connect-token", methods=["POST"])
def get_connect_token():
    """
    Gera um connect token para uso no widget Pluggy Connect no frontend.
    Retorna { accessToken, expiresAt }.
    """
    try:
        token_data = create_connect_token()
        return jsonify(token_data)
    except Exception as e:
        traceback.print_exc()
        return (
            jsonify({"status": "error", "message": f"Erro ao gerar connect token: {e}"}),
            500,
        )


@bp.route("/items/<item_id>", methods=["GET"])
def get_item_status(item_id):
    """Retorna o status atual de um item diretamente da Pluggy API."""
    try:
        return jsonify(get_item(item_id))
    except HTTPError as e:
        status_code = e.response.status_code if e.response is not None else 500
        return jsonify({"status": "error", "message": str(e)}), status_code
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/items", methods=["GET"])
def list_items():
    """Retorna todos os itens Pluggy conectados."""
    repo = PluggyItemRepository()
    try:
        return jsonify(repo.list_all())
    finally:
        repo.close()


@bp.route("/items", methods=["POST"])
def add_item():
    """Persiste um item recém-conectado via widget."""
    data = request.get_json() or {}
    item_id = data.get("item_id")
    if not item_id:
        return jsonify({"error": "item_id é obrigatório"}), 400

    repo = PluggyItemRepository()
    try:
        alias = (data.get("alias") or "").strip() or None
        repo.upsert_item(
            item_id,
            connector_name=data.get("connector_name"),
            status=data.get("status"),
            role=data.get("role", "bank"),
            alias=alias,
        )
        return jsonify({"status": "success", "item_id": item_id})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        repo.close()


@bp.route("/items/<item_id>", methods=["PATCH"])
def update_item(item_id):
    """Atualiza o alias de um item conectado."""
    data = request.get_json() or {}
    alias = (data.get("alias") or "").strip() or None
    repo = PluggyItemRepository()
    try:
        repo.update_alias(item_id, alias)
        return jsonify({"status": "success"})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        repo.close()


@bp.route("/items/<item_id>", methods=["DELETE"])
def remove_item(item_id):
    """Remove um item conectado."""
    repo = PluggyItemRepository()
    try:
        repo.delete(item_id)
        return jsonify({"status": "success"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        repo.close()
