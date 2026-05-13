import logging
from flask import Blueprint, jsonify, request
from core.scenarios import compare_two, compare_multiple
from api.validation import reject_invalid_session

log = logging.getLogger(__name__)
bp_scenarios = Blueprint("scenarios", __name__)

MAX_COMPARE_SESSIONS = 5 

@bp_scenarios.post("/compare/two")
def compare_two_endpoint():
    data = request.json or {}
    session_a = data.get("session_a")
    session_b = data.get("session_b")

    if not session_a or not session_b:
        return jsonify({"error": "Parameters 'session_a' and 'session_b' are required."}), 400

    err = reject_invalid_session(session_a)
    if err:
        return err

    err = reject_invalid_session(session_b)
    if err:
        return err

    try:
        result = compare_two(session_a, session_b)
        return jsonify(result)
    except FileNotFoundError:
        return jsonify({"error": "Session(s) non analysée(s)."}), 404
    except Exception:
        log.exception("Erreur comparaison binaire")
        return jsonify({"error": "Erreur interne"}), 500

@bp_scenarios.post("/compare/multiple")
def compare_multiple_endpoint():
    data = request.json or {}
    sessions = data.get("sessions", [])

    if not isinstance(sessions, list) or len(sessions) < 2:
        return jsonify({"error": "At least two sessions are required."}), 400

    if len(sessions) > MAX_COMPARE_SESSIONS:
        return jsonify({"error": f"Maximum {MAX_COMPARE_SESSIONS} sessions autorisées."}), 400

    for session_name in sessions:
        err = reject_invalid_session(session_name)
        if err:
            return err

    try:
        result = compare_multiple(sessions)
        return jsonify(result)
    except Exception:
        log.exception("Erreur comparaison multiple")
        return jsonify({"error": "Erreur interne"}), 500
