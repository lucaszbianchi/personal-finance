"""
Módulo de rotas relacionadas à importação de dados.
"""

import traceback
from flask import Blueprint, jsonify, request
from pluggy_api import PluggyAPI
from repositories.rate_limit_repository import RateLimitRepository

bp = Blueprint("import", __name__)


@bp.route("/data", methods=["POST"])
def import_data():
    """Importa todos os dados das APIs externas usando o novo fluxo direto."""
    try:
        body = request.get_json(silent=True) or {}
        import_type = body.get("import_type", "recent")
        if import_type not in ("recent", "non_recent"):
            return jsonify({"status": "error", "message": "import_type inválido"}), 400
        item_id = body.get("item_id") or None

        api = PluggyAPI()
        summary = api.fetch_and_store_data_to_db(import_type=import_type, item_id=item_id)

        response_body = {
            "status": "success",
            "message": "Dados importados com sucesso",
            "counts": summary,
        }

        if import_type == "non_recent":
            usage = next(
                (u for u in summary.get("rate_limit_usage", []) if u["call_type"] == "non_recent"),
                None,
            )
            # Avisa quando remaining <= 1 (última chamada disponível ou limite já atingido),
            # pois com apenas 4 chamadas/mês o usuário precisa de feedback imediato após cada uso.
            if usage and usage["remaining"] <= 1:
                remaining = usage["remaining"]
                limit = usage["limit_value"]
                used = usage["count"]
                if remaining == 0:
                    response_body["rate_limit_warning"] = (
                        f"Limite de sincronizações históricas atingido: {used} de {limit} usadas este mês."
                    )
                else:
                    response_body["rate_limit_warning"] = (
                        f"Você usou {used} de {limit} sincronizações históricas deste mês. Resta {remaining}."
                    )

        return jsonify(response_body)
    except Exception as e:
        error_message = str(e)
        traceback.print_exc()
        print(f"Error in /import/data: {error_message}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Erro ao importar dados: {error_message}",
                }
            ),
            500,
        )


@bp.route("/rate-limit-usage", methods=["GET"])
def rate_limit_usage():
    """Retorna o resumo de uso de rate-limit do mês atual."""
    item_id = request.args.get("item_id") or None
    repo = RateLimitRepository()
    try:
        usage = repo.get_usage_summary(item_id=item_id)
        return jsonify({"status": "success", "usage": usage})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        repo.close()
