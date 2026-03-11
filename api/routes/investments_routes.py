from flask import Blueprint, jsonify
from services.investment_service import InvestmentService

bp = Blueprint("investments", __name__)


@bp.route("/", methods=["GET"])
def get_investments():
    service = InvestmentService()
    investments = service.get_investments()
    return jsonify([{
        "id": i.investment_id,
        "name": i.name,
        "type": i.type,
        "subtype": i.subtype,
        "amount": i.amount,
        "balance": i.balance,
        "date": i.date,
        "due_date": i.due_date,
        "issuer": i.issuer,
        "rate_type": i.rate_type,
    } for i in investments])


@bp.route("/history", methods=["GET"])
def get_investment_history():
    service = InvestmentService()
    return jsonify(service.get_investment_history())
