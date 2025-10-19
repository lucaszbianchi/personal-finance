"""
Módulo de rotas relacionadas à importação de dados.
"""

from flask import Blueprint, jsonify
from fetch_data import FetchData

bp = Blueprint("import", __name__)


@bp.route("/import-data", methods=["POST"])
def import_data():
    """Importa todos os dados das APIs externas."""
    try:
        fetch_data = FetchData()
        fetch_data.execute()

        return jsonify(
            {
                "status": "success",
                "message": "Dados importados com sucesso",
            }
        )
    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": f"Erro ao importar dados: {str(e)}"}
            ),
            500,
        )
