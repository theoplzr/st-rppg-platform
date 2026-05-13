"""api/routes_sessions.py"""
import logging
from flask import Blueprint, jsonify, request
from core.session_manager import list_sessions, save_scenario, load_metadata, SESSIONS_DIR
from api.validation import reject_invalid_session

log = logging.getLogger(__name__)
bp_sessions = Blueprint("sessions", __name__)

_ERR_500 = {"error": "Internal error. Check server logs."}


@bp_sessions.get("/")
def get_sessions():
    try:
        return jsonify(list_sessions())
    except Exception:
        log.exception("list_sessions failed")
        return jsonify(_ERR_500), 500


@bp_sessions.post("/<session_name>/scenario")
def tag_scenario(session_name):
    err = reject_invalid_session(session_name)
    if err:
        return err
    data = request.json or {}
    try:
        save_scenario(
            session_name,
            label=data.get("label", ""),
            description=data.get("description", ""),
            zone=data.get("zone", ""),
        )
        log.info("scenario tagged session=%s label=%s", session_name, data.get("label"))
        return jsonify({"ok": True})
    except FileNotFoundError:
        return jsonify({"error": "Session not found."}), 404
    except Exception:
        log.exception("tag_scenario failed session=%s", session_name)
        return jsonify(_ERR_500), 500


@bp_sessions.get("/<session_name>")
def get_session(session_name):
    err = reject_invalid_session(session_name)
    if err:
        return err
    try:
        meta = load_metadata(SESSIONS_DIR / session_name)
        return jsonify(meta)
    except Exception:
        log.exception("get_session failed session=%s", session_name)
        return jsonify(_ERR_500), 500
