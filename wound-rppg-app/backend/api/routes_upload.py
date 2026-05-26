"""api/routes_upload.py — Session upload endpoint (ZIP or AVI)."""
import json
import logging
import os
import re
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import cv2
from flask import Blueprint, jsonify, request
from core.session_manager import SESSIONS_DIR
from core.database import upsert_session

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
    # Sync to DB
    for sname in sessions:
        try:
            meta_path = SESSIONS_DIR / sname / "metadata.json"
            meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
            upsert_session(sname, date=meta.get("date"), fps=meta.get("measured_fps"),
                           nb_frames=meta.get("nb_frames"))
        except Exception:
            log.warning("DB sync skipped for %s", sname)
    return jsonify({"ok": True, "sessions": sessions, "size_mb": round(size_mb, 1)}), 201


# ── AVI upload ─────────────────────────────────────────────────────────────────

def _handle_avi(f, filename: str) -> tuple:
    stem = re.sub(r"[^\w\-]", "_", Path(filename).stem)
    session_name = f"{stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_dir = SESSIONS_DIR / session_name
    frames_dir  = session_dir / "frames"
    tmp_path    = None

    try:
        # Stream AVI to a temp file (may be several GB — avoid loading into RAM)
        with tempfile.NamedTemporaryFile(suffix=".avi", delete=False) as tmp:
            tmp_path = tmp.name
            shutil.copyfileobj(f.stream, tmp)

        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            return jsonify({"error": "Cannot open AVI file — file may be corrupt."}), 400

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

        frames_dir.mkdir(parents=True, exist_ok=True)

        idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            cv2.imwrite(str(frames_dir / f"frame_{idx:05d}.png"), frame)
            idx += 1
        cap.release()

        if idx == 0:
            shutil.rmtree(session_dir, ignore_errors=True)
            return jsonify({"error": "AVI contains no readable frames."}), 422

        meta = {
            "session_name": session_name,
            "measured_fps": round(fps, 3),
            "nb_frames":    idx,
            "date":         datetime.now().isoformat(),
            "source":       "avi",
        }
        (session_dir / "metadata.json").write_text(json.dumps(meta, indent=2))

        size_mb = os.path.getsize(tmp_path) / (1024 * 1024)
        log.info("AVI converted: %s — %d frames @ %.1f fps (%.1f MB)", session_name, idx, fps, size_mb)
        try:
            upsert_session(session_name, date=meta["date"], fps=fps, nb_frames=idx)
        except Exception:
            log.warning("DB sync skipped for %s", session_name)
        return jsonify({"ok": True, "sessions": [session_name], "size_mb": round(size_mb, 1)}), 201

    except Exception:
        log.exception("AVI conversion failed")
        shutil.rmtree(session_dir, ignore_errors=True)
        return jsonify({"error": "AVI conversion failed. Check server logs."}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


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
        return _handle_avi(f, f.filename)

    return jsonify({"error": "Only .zip and .avi files are accepted."}), 400
