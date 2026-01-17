from flask import Blueprint, jsonify, request
from services.splitwise_service import SplitwiseService

bp = Blueprint("splitwise", __name__)
splitwise_service = SplitwiseService()


@bp.route("/", methods=["GET"])
def get_all_splitwise():
    """Retorna todas as transações do Splitwise com informações de match."""
    splitwise_entries = splitwise_service.get_all_splitwise_with_match_info()
    return jsonify(splitwise_entries)


@bp.route("/<splitwise_id>", methods=["GET"])
def get_splitwise(splitwise_id):
    """Retorna uma transação específica do Splitwise."""
    entry = splitwise_service.get_splitwise_by_id(splitwise_id)
    if not entry:
        return jsonify({"error": "Transação não encontrada"}), 404

    return jsonify(
        {
            "id": entry.splitwise_id,
            "amount": entry.amount,
            "date": entry.date.strftime("%Y-%m-%d"),
            "description": entry.description,
            "category_id": entry.category_id,
            "transaction_id": entry.transaction_id,
        }
    )


@bp.route("/by-transaction/<transaction_id>", methods=["GET"])
def get_splitwise_by_transaction(transaction_id):
    """Retorna a transação do Splitwise vinculada a uma transação específica."""
    entry = splitwise_service.get_splitwise_by_transaction(transaction_id)
    if not entry:
        return jsonify({"error": "Transação não encontrada"}), 404

    return jsonify(
        {
            "id": entry.splitwise_id,
            "amount": entry.amount,
            "date": entry.date.strftime("%Y-%m-%d"),
            "description": entry.description,
            "category_id": entry.category_id,
            "transaction_id": entry.transaction_id,
        }
    )


@bp.route("/<splitwise_id>/link", methods=["POST"])
def link_transaction(splitwise_id):
    """Vincula uma transação ao Splitwise."""
    data = request.get_json()
    transaction_id = data.get("transaction_id")

    if not transaction_id:
        return jsonify({"error": "transaction_id é obrigatório"}), 400

    success = splitwise_service.link_transaction_to_splitwise(
        splitwise_id, transaction_id
    )
    if success:
        return jsonify({"message": "Transação vinculada com sucesso"})
    return jsonify({"error": "Erro ao vincular transação"}), 400


@bp.route("/unsettled", methods=["GET"])
def get_unsettled():
    """Retorna todas as transações do Splitwise não quitadas."""
    entries = splitwise_service.get_unsettled_splitwise()
    return jsonify(
        [
            {
                "id": entry.splitwise_id,
                "amount": entry.amount,
                "date": entry.date.strftime("%Y-%m-%d"),
                "description": entry.description,
                "category_id": entry.category_id,
                "transaction_id": entry.transaction_id,
            }
            for entry in entries
        ]
    )


@bp.route("/summary", methods=["GET"])
def get_summary():
    """Retorna um resumo das transações do Splitwise."""
    return jsonify(splitwise_service.get_splitwise_summary())


@bp.route("/auto-match", methods=["POST"])
def trigger_auto_match():
    """Executa o auto-matching manualmente para transações Splitwise."""
    try:
        results = splitwise_service.auto_match_splitwise_transactions()

        return jsonify({
            "success": True,
            "message": f"Auto-matching executado com sucesso: {results['matches_applied']} matches aplicados",
            "results": results
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erro ao executar auto-matching: {str(e)}"
        }), 500


@bp.route("/statistics", methods=["GET"])
def get_matching_statistics():
    """Retorna estatísticas de matching das transações Splitwise."""
    try:
        stats = splitwise_service.get_matching_statistics()

        return jsonify(stats)
    except Exception as e:
        return jsonify({
            "error": f"Erro ao obter estatísticas: {str(e)}"
        }), 500


@bp.route("/match-candidates/<splitwise_id>", methods=["GET"])
def get_match_candidates(splitwise_id):
    """Retorna candidatos potenciais para match de uma transação Splitwise."""
    try:
        splitwise_entry = splitwise_service.get_splitwise_by_id(splitwise_id)
        if not splitwise_entry:
            return jsonify({"error": "Transação Splitwise não encontrada"}), 404

        # Find potential match for this entry
        potential_match = splitwise_service.find_matching_transaction(splitwise_entry)

        if potential_match:
            return jsonify({
                "splitwise_entry": {
                    "id": splitwise_entry.splitwise_id,
                    "amount": splitwise_entry.amount,
                    "date": splitwise_entry.date.strftime("%Y-%m-%d"),
                    "description": splitwise_entry.description,
                },
                "potential_match": {
                    "id": potential_match.transaction_id,
                    "amount": potential_match.amount,
                    "date": potential_match.date.strftime("%Y-%m-%d"),
                    "description": potential_match.description,
                    "type": "bank" if hasattr(potential_match, 'operation_type') else "credit"
                }
            })
        else:
            return jsonify({
                "splitwise_entry": {
                    "id": splitwise_entry.splitwise_id,
                    "amount": splitwise_entry.amount,
                    "date": splitwise_entry.date.strftime("%Y-%m-%d"),
                    "description": splitwise_entry.description,
                },
                "potential_match": None,
                "message": "Nenhum candidato encontrado"
            })

    except Exception as e:
        return jsonify({
            "error": f"Erro ao buscar candidatos: {str(e)}"
        }), 500
