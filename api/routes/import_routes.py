"""
Módulo de rotas relacionadas à importação de dados.
"""

import traceback
from flask import Blueprint, jsonify
from pluggy_api import PluggyAPI

bp = Blueprint("import", __name__)


@bp.route("/data", methods=["POST"])
def import_data():
    """Importa todos os dados das APIs externas usando o novo fluxo direto."""
    try:
        api = PluggyAPI()
        summary = api.fetch_and_store_data_to_db()

        return jsonify(
            {
                "status": "success",
                "message": "Dados importados com sucesso",
                "counts": summary,
            }
        )
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
