"""api/validation.py — Shared input validation for API routes."""

import re
from flask import jsonify

_SESSION_NAME_RE = re.compile(r"^[a-zA-Z0-9_\-\.]{1,128}$")


def valid_session_name(name: str) -> bool:
    """Return True only for names that contain no path traversal sequences."""
    if not name or ".." in name or "/" in name or "\\" in name:
        return False
    return bool(_SESSION_NAME_RE.match(name))


def reject_invalid_session(name: str):
    """
    Return a 400 response if the session name is invalid, None otherwise.
    Usage: err = reject_invalid_session(name); if err: return err
    """
    if not valid_session_name(name):
        return jsonify({"error": "Invalid session name."}), 400
    return None
