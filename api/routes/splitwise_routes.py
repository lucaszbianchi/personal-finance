from flask import Blueprint, jsonify, request
from services.splitwise_service import SplitwiseService

bp = Blueprint("splitwise", __name__)
splitwise_service = SplitwiseService()


@bp.route("/", methods=["GET"])
def get_all_splitwise():
    """Retorna todas as transações do Splitwise."""
    splitwise_entries = splitwise_service.get_all_splitwise()
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
            for entry in splitwise_entries
        ]
    )


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
