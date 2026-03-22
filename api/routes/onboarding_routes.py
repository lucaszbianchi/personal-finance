import traceback

from flask import Blueprint, jsonify, request

from pluggy_api import PluggyAPI
from services.finance_history_service import FinanceHistoryService
from services.onboarding_service import OnboardingService

bp = Blueprint("onboarding", __name__)
onboarding_service = OnboardingService()


@bp.route("/status", methods=["GET"])
def get_status():
    return jsonify(onboarding_service.get_status())


@bp.route("/credentials", methods=["POST"])
def save_credentials():
    data = request.get_json() or {}
    try:
        onboarding_service.save_credentials(
            client_id=data.get("client_id", ""),
            client_secret=data.get("client_secret", ""),
            splitwise_account_name=data.get("splitwise_account_name"),
        )
        return jsonify({"status": "success"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/restart", methods=["POST"])
def restart():
    return jsonify(onboarding_service.restart())


@bp.route("/full-sync", methods=["POST"])
def full_sync():
    """Executa sync completo: non_recent + recent + rebuild finance_history."""
    try:
        api = PluggyAPI()

        summary_non_recent = api.fetch_and_store_data_to_db(import_type="non_recent")
        summary_recent = api.fetch_and_store_data_to_db(import_type="recent")

        fh_service = FinanceHistoryService()
        rebuild_result = fh_service.rebuild_all_months()

        onboarding_service.mark_complete()

        combined = {
            "status": "success",
            "non_recent": summary_non_recent,
            "recent": summary_recent,
            "rebuild": rebuild_result,
        }
        return jsonify(combined)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500
