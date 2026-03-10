"""
Módulo de rotas relacionadas a transações bancárias.
"""

from flask import Blueprint, jsonify, request
from services.transaction_service import TransactionService
from services.category_service import CategoryService

bp = Blueprint("transactions", __name__)
transaction_service = TransactionService()
category_service = CategoryService()


def _get_category_name(category_id):
    """Helper para obter nome da categoria pelo ID."""
    if not category_id:
        return None
    category = category_service.get_category_by_id(category_id)
    return category.description if category else None


@bp.route("/bank", methods=["GET"])
def get_bank_transactions():
    """Retorna transações bancárias com filtros opcionais."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    category_id = request.args.get("category_id")

    transactions = transaction_service.get_bank_transactions(
        start_date=start_date, end_date=end_date, category_id=category_id
    )
    return jsonify(
        [
            {
                "id": t.transaction_id,
                "date": t.date,
                "description": t.description,
                "amount": t.amount,
                "category": _get_category_name(t.category_id),
                "operation_type": t.operation_type,
                "split_info": t.split_info,
                "payment_data": t.payment_data,
                "type": t.type_,
            }
            for t in transactions
        ]
    )


@bp.route("/credit", methods=["GET"])
def get_credit_transactions():
    """Retorna transações de crédito com filtros opcionais."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    category_id = request.args.get("category_id")

    transactions = transaction_service.get_credit_transactions(
        start_date=start_date, end_date=end_date, category_id=category_id
    )
    return jsonify(
        [
            {
                "id": t.transaction_id,
                "date": t.date,
                "description": t.description,
                "amount": t.amount,
                "category": _get_category_name(t.category_id),
                "status": t.status,
                "split_info": t.split_info,
            }
            for t in transactions
        ]
    )


@bp.route("/investments", methods=["GET"])
def get_investments():
    """Retorna todos os investimentos."""
    investments = transaction_service.get_investments()
    return jsonify(
        [
            {
                "id": i.investment_id,
                "name": i.name,
                "balance": i.balance,
                "type": i.type,
                "subtype": i.subtype,
                "date": i.date,
                "due_date": i.due_date,
                "issuer": i.issuer,
                "rate_type": i.rate_type,
            }
            for i in investments
        ]
    )


@bp.route("/<transaction_type>/bulk-category", methods=["PUT"])
def bulk_update_category(transaction_type):
    """Atualiza a categoria de múltiplas transações em lote."""
    data = request.get_json()
    transaction_ids = data.get("transaction_ids", [])
    category_id = data.get("category_id")  # None = remover categoria

    if transaction_type not in ["bank", "credit"]:
        return jsonify({"error": "transaction_type deve ser 'bank' ou 'credit'"}), 400
    if not transaction_ids:
        return jsonify({"error": "transaction_ids é obrigatório"}), 400

    try:
        updated = transaction_service.bulk_update_category(
            transaction_type, transaction_ids, category_id
        )
        return jsonify({"updated": updated})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/<transaction_type>/<transaction_id>/share", methods=["POST"])
def add_person_to_share_transaction(transaction_type, transaction_id):
    """Adiciona pessoas para compartilhar uma transação."""
    data = request.get_json()
    partners = data.get("partners", {})

    if not partners:
        return jsonify({"error": "partners é obrigatório"}), 400

    if transaction_type not in ["bank", "credit"]:
        return jsonify({"error": "transaction_type deve ser 'bank' ou 'credit'"}), 400

    success = transaction_service.add_person_to_share_transaction(
        transaction_type, transaction_id, partners
    )

    if success:
        return jsonify({"message": "Compartilhamento adicionado com sucesso"})
    return jsonify({"error": "Erro ao adicionar compartilhamento"}), 400


@bp.route("/<transaction_id>/settle", methods=["POST"])
def settle_up_split(transaction_id):
    """Configura uma transação como liquidação de split."""
    success = transaction_service.settle_up_split(transaction_id)

    if success:
        return jsonify({"message": "Transação configurada como liquidação com sucesso"})
    return jsonify({"error": "Erro ao configurar transação como liquidação"}), 400


@bp.route("/<transaction_id>/settle/category", methods=["POST"])
def add_category_to_settle_up(transaction_id):
    """Adiciona uma categoria a uma transação de liquidação."""
    data = request.get_json()
    category_id = data.get("category_id")

    if not category_id:
        return jsonify({"error": "category_id é obrigatório"}), 400

    success = transaction_service.add_category_to_settle_up_transaction(
        transaction_id, category_id
    )

    if success:
        return jsonify({"message": "Categoria adicionada com sucesso"})
    return jsonify({"error": "Erro ao adicionar categoria"}), 400


@bp.route("/check-split-settle", methods=["GET"])
def check_split_settle():
    """Verifica o estado atual dos splits e settle ups."""
    result = transaction_service.check_split_settle_up()
    return jsonify(result)


@bp.route("/bank", methods=["POST"])
def create_bank_transaction():
    """Cria uma nova transação bancária."""
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({"error": "Body inválido"}), 400

        if "id" not in data:
            return jsonify({"error": "Campo 'id' é obrigatório"}), 400

        if "description" not in data:
            return jsonify({"error": "Campo 'description' é obrigatório"}), 400

        if "amount" not in data:
            return jsonify({"error": "Campo 'amount' é obrigatório"}), 400

        if "date" not in data:
            return jsonify({"error": "Campo 'date' é obrigatório"}), 400

        transaction = transaction_service.create_bank_transaction(data)
        return (
            jsonify(
                {
                    "id": transaction.transaction_id,
                    "date": transaction.date,
                    "description": transaction.description,
                    "amount": transaction.amount,
                    "category": _get_category_name(transaction.category_id),
                    "operation_type": transaction.operation_type,
                    "split_info": transaction.split_info,
                    "payment_data": transaction.payment_data,
                    "type": transaction.type_,
                }
            ),
            201,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/credit", methods=["POST"])
def create_credit_transaction():
    """Cria uma nova transação de cartão de crédito."""
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({"error": "Body inválido"}), 400

        if "id" not in data:
            return jsonify({"error": "Campo 'id' é obrigatório"}), 400

        if "description" not in data:
            return jsonify({"error": "Campo 'description' é obrigatório"}), 400

        if "amount" not in data:
            return jsonify({"error": "Campo 'amount' é obrigatório"}), 400

        if "date" not in data:
            return jsonify({"error": "Campo 'date' é obrigatório"}), 400

        transaction = transaction_service.create_credit_transaction(data)
        return (
            jsonify(
                {
                    "id": transaction.transaction_id,
                    "date": transaction.date,
                    "description": transaction.description,
                    "amount": transaction.amount,
                    "category": _get_category_name(transaction.category_id),
                    "status": transaction.status,
                }
            ),
            201,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/bank/<transaction_id>", methods=["DELETE"])
def delete_bank_transaction(transaction_id: str):
    """Deleta uma transação bancária."""
    try:
        success = transaction_service.delete_bank_transaction(transaction_id)
        if success:
            return jsonify({"message": "Transação bancária deletada com sucesso"})
        else:
            return jsonify({"error": "Falha ao deletar transação bancária"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/credit/<transaction_id>", methods=["DELETE"])
def delete_credit_transaction(transaction_id: str):
    """Deleta uma transação de cartão de crédito."""
    try:
        success = transaction_service.delete_credit_transaction(transaction_id)
        if success:
            return jsonify({"message": "Transação de crédito deletada com sucesso"})
        else:
            return jsonify({"error": "Falha ao deletar transação de crédito"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/operation-types", methods=["GET"])
def get_operation_types():
    """Retorna lista de tipos de operação únicos das transações bancárias."""
    try:
        operation_types = transaction_service.get_operation_types()
        return jsonify({"operation_types": operation_types})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
