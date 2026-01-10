"""
Módulo de rotas relacionadas à importação de dados.
"""

from flask import Blueprint, jsonify
from pluggy_api import PluggyAPI

bp = Blueprint("import", __name__)


@bp.route("/data", methods=["POST"])
def import_data():
    """Importa todos os dados das APIs externas usando o novo fluxo direto."""
    try:
        api = PluggyAPI()
        api.fetch_and_store_data_to_db()

        return jsonify(
            {
                "status": "success",
                "message": "Dados importados com sucesso via novo fluxo",
            }
        )
    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": f"Erro ao importar dados: {str(e)}"}
            ),
            500,
        )
