"""Routes for automation rules."""

from flask import Blueprint, jsonify, request
from services.automation_service import AutomationService

bp = Blueprint("automations", __name__)
automation_service = AutomationService()


@bp.get("/")
def list_rules():
    return jsonify(automation_service.list_rules())


@bp.post("/")
def create_rule():
    try:
        rule = automation_service.create_rule(request.get_json() or {})
        return jsonify(rule), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.get("/<int:rule_id>")
def get_rule(rule_id: int):
    try:
        return jsonify(automation_service.get_rule(rule_id))
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@bp.put("/<int:rule_id>")
def update_rule(rule_id: int):
    try:
        rule = automation_service.update_rule(rule_id, request.get_json() or {})
        return jsonify(rule)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.delete("/<int:rule_id>")
def delete_rule(rule_id: int):
    try:
        automation_service.delete_rule(rule_id)
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@bp.post("/preview")
def preview_matches():
    try:
        body = request.get_json() or {}
        matches = automation_service.preview_matches(body.get("conditions", []))
        return jsonify(matches)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.post("/<int:rule_id>/apply")
def apply_rule(rule_id: int):
    try:
        result = automation_service.apply_rule(rule_id)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@bp.patch("/<int:rule_id>/toggle")
def toggle_rule(rule_id: int):
    body = request.get_json() or {}
    if "enabled" not in body:
        return jsonify({"error": "enabled field is required"}), 400
    try:
        rule = automation_service.toggle_enabled(rule_id, bool(body["enabled"]))
        return jsonify(rule)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
