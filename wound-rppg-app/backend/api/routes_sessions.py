"""api/routes_sessions.py"""
import logging
from flask import Blueprint, jsonify, request
from core.session_manager import (
    list_sessions, save_scenario, load_metadata,
    save_mask, load_mask, get_thumbnail, SESSIONS_DIR,
)
from api.validation import reject_invalid_session

log = logging.getLogger(__name__)
bp_sessions = Blueprint("sessions", __name__)

_ERR_500 = {"error": "Internal error. Check server logs."}


@bp_sessions.get("/")
def get_sessions():
    try:
        sessions = list_sessions()
        try:
            from core.database import list_sessions_db
            db_index = {r["name"]: r for r in list_sessions_db()}
            for s in sessions:
                db = db_index.get(s["name"], {})
                s["patient_id"]     = db.get("patient_id")
                s["patient_name"]   = db.get("patient_name")
                s["score"]          = db.get("score")
                s["snr_db"]         = db.get("snr_db")
                s["hr_bpm"]         = db.get("hr_bpm")
                s["wound_pct"]      = db.get("wound_pct")
                s["wound_id"]       = db.get("wound_id")
                s["scenario_label"] = db.get("scenario_label") or s.get("scenario", {}).get("label")
                s["has_mask"]       = bool(db.get("has_mask", 0))
        except Exception:
            log.warning("DB enrichment skipped in list_sessions")
        return jsonify(sessions)
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


@bp_sessions.get("/<session_name>/thumbnail")
def get_session_thumbnail(session_name):
    err = reject_invalid_session(session_name)
    if err:
        return err
    try:
        thumb = get_thumbnail(session_name)
        if thumb is None:
            return jsonify({"error": "No frames found."}), 404
        return jsonify({"thumbnail": thumb})
    except Exception:
        log.exception("thumbnail failed session=%s", session_name)
        return jsonify(_ERR_500), 500


@bp_sessions.post("/<session_name>/mask")
def save_session_mask(session_name):
    """
    Body: { mask: "<base64-encoded PNG>" }
    The PNG should be grayscale — white = wound area.
    """
    err = reject_invalid_session(session_name)
    if err:
        return err
    data = request.json or {}
    mask_b64 = data.get("mask", "")
    if not mask_b64:
        return jsonify({"error": "Missing 'mask' field."}), 400
    try:
        save_mask(session_name, mask_b64)
        log.info("mask saved session=%s", session_name)
        return jsonify({"ok": True})
    except Exception:
        log.exception("save_mask failed session=%s", session_name)
        return jsonify(_ERR_500), 500


@bp_sessions.delete("/<session_name>/mask")
def delete_session_mask(session_name):
    err = reject_invalid_session(session_name)
    if err:
        return err
    import os
    mask_path = SESSIONS_DIR / session_name / "mask.png"
    if mask_path.exists():
        os.remove(mask_path)
        log.info("mask deleted session=%s", session_name)
    try:
        from core.database import upsert_session
        upsert_session(session_name, has_mask=0)
    except Exception:
        pass
    return jsonify({"ok": True})


@bp_sessions.get("/<session_name>/mask")
def get_session_mask(session_name):
    """Returns whether a mask exists and its base64 PNG if it does."""
    err = reject_invalid_session(session_name)
    if err:
        return err
    mask_path = SESSIONS_DIR / session_name / "mask.png"
    if not mask_path.exists():
        return jsonify({"has_mask": False})
    import base64
    with open(mask_path, "rb") as f:
        mask_b64 = base64.b64encode(f.read()).decode("utf-8")
    return jsonify({"has_mask": True, "mask": mask_b64})
