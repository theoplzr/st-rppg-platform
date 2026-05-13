"""api/routes_upload.py — Session upload endpoint (ZIP)."""
import logging
import os
import zipfile

from flask import Blueprint, jsonify, request
from core.session_manager import SESSIONS_DIR

log = logging.getLogger(__name__)
bp_upload = Blueprint("upload", __name__)

_MAX_MB = int(os.getenv("UPLOAD_MAX_MB", "500"))


# ── ZIP upload ─────────────────────────────────────────────────────────────────

def _valid_zip_structure(zf: zipfile.ZipFile) -> bool:
    names = [n for n in zf.namelist() if not n.startswith("__MACOSX/")]
    has_frames   = any("/frames/" in n and n.lower().endswith((".png", ".jpg", ".jpeg")) for n in names)
    has_metadata = any(n.endswith("metadata.json") for n in names)
    return has_frames and has_metadata


def _extract_zip(zf: zipfile.ZipFile) -> list[str]:
    extracted = set()
    for member in zf.infolist():
        if member.filename.startswith("__MACOSX/"):
            continue
        parts = member.filename.replace("\\", "/").split("/")
        if any(p in ("", "..", ".") for p in parts):
            continue
        dest = SESSIONS_DIR.joinpath(*parts)
        if member.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, open(dest, "wb") as dst:
                while chunk := src.read(1024 * 1024):
                    dst.write(chunk)
            extracted.add(parts[0])
    return list(extracted)


def _handle_zip(f) -> tuple:
    f.seek(0, os.SEEK_END)
    size_mb = f.tell() / (1024 * 1024)
    f.seek(0)
    if size_mb > _MAX_MB:
        return jsonify({"error": f"File too large ({size_mb:.1f} MB). Max: {_MAX_MB} MB."}), 413

    try:
        zf = zipfile.ZipFile(f)
    except zipfile.BadZipFile:
        return jsonify({"error": "Invalid or corrupted ZIP file."}), 400

    try:
        if not _valid_zip_structure(zf):
            return jsonify({"error": "ZIP must contain <session>/frames/<images> and <session>/metadata.json."}), 422
        sessions = _extract_zip(zf)
    except Exception:
        log.exception("ZIP extraction failed")
        return jsonify({"error": "Internal error. Check server logs."}), 500
    finally:
        zf.close()

    if not sessions:
        return jsonify({"error": "No valid session extracted from ZIP."}), 422

    log.info("ZIP uploaded: %s (%.1f MB)", sessions, size_mb)
    return jsonify({"ok": True, "sessions": sessions, "size_mb": round(size_mb, 1)}), 201


# ── Route ──────────────────────────────────────────────────────────────────────

@bp_upload.route("/", methods=["POST", "OPTIONS"])
def upload_session():
    if request.method == "OPTIONS":
        return ("", 204)

    if "file" not in request.files:
        return jsonify({"error": "Missing 'file' field in multipart form."}), 400

    f = request.files["file"]
    name = (f.filename or "").lower()

    if name.endswith(".zip"):
        return _handle_zip(f)

    if name.endswith(".avi"):
        return jsonify({
            "error": "AVI upload is not supported on this server (memory limits). "
                     "Convert your AVI locally with scripts/avi_to_session_zip.py, "
                     "then upload the resulting ZIP."
        }), 415

    return jsonify({"error": "Only .zip files are accepted."}), 400
