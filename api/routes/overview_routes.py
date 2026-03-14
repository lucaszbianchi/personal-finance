from flask import Blueprint, jsonify
from services.net_worth_service import NetWorthService

bp = Blueprint("overview", __name__)
net_worth_service = NetWorthService()


@bp.route("/net-worth", methods=["GET"])
def get_net_worth():
    """Retorna patrimonio liquido atual e historico de 12 meses."""
    return jsonify(net_worth_service.get_net_worth())


@bp.route("/partial-result", methods=["GET"])
def get_partial_result():
    """Retorna resultado parcial do mes corrente e progresso vs meta de saldo."""
    return jsonify(net_worth_service.get_partial_result())
