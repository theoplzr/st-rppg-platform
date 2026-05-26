"""api/routes_patients.py — Patient management endpoints."""
import logging
from flask import Blueprint, jsonify, request
from core.database import (
    create_patient, get_patient, list_patients, update_patient,
    delete_patient, assign_session_to_patient, list_sessions_db,
)
from api.validation import reject_invalid_session

log = logging.getLogger(__name__)
bp_patients = Blueprint("patients", __name__)
_ERR_500 = {"error": "Internal error. Check server logs."}


@bp_patients.get("/")
def get_patients():
    try:
        return jsonify(list_patients())
    except Exception:
        log.exception("list_patients failed")
        return jsonify(_ERR_500), 500


@bp_patients.post("/")
def post_patient():
    data = request.json or {}
    if not data.get("name"):
        return jsonify({"error": "Field 'name' is required."}), 400
    try:
        patient = create_patient(
            name       = data["name"],
            birth_year = data.get("birth_year"),
            sex        = data.get("sex"),
            wound_type = data.get("wound_type"),
            notes      = data.get("notes"),
        )
        log.info("patient created id=%s name=%s", patient["id"], patient["name"])
        return jsonify(patient), 201
    except Exception:
        log.exception("create_patient failed")
        return jsonify(_ERR_500), 500


@bp_patients.get("/<patient_id>")
def get_patient_detail(patient_id):
    patient = get_patient(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found."}), 404
    sessions = list_sessions_db(patient_id=patient_id)
    return jsonify({**patient, "sessions": sessions})


@bp_patients.patch("/<patient_id>")
def patch_patient(patient_id):
    data = request.json or {}
    try:
        patient = update_patient(patient_id, **data)
        if not patient:
            return jsonify({"error": "Patient not found."}), 404
        return jsonify(patient)
    except Exception:
        log.exception("update_patient failed id=%s", patient_id)
        return jsonify(_ERR_500), 500


@bp_patients.delete("/<patient_id>")
def del_patient(patient_id):
    if not get_patient(patient_id):
        return jsonify({"error": "Patient not found."}), 404
    delete_patient(patient_id)
    log.info("patient deleted id=%s", patient_id)
    return jsonify({"ok": True})


@bp_patients.post("/<patient_id>/sessions/<session_name>")
def attach_session(patient_id, session_name):
    """Link an existing session to a patient."""
    err = reject_invalid_session(session_name)
    if err:
        return err
    if not get_patient(patient_id):
        return jsonify({"error": "Patient not found."}), 404
    try:
        assign_session_to_patient(session_name, patient_id)
        log.info("session %s assigned to patient %s", session_name, patient_id)
        return jsonify({"ok": True})
    except Exception:
        log.exception("assign_session failed")
        return jsonify(_ERR_500), 500
