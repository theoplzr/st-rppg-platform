"""api/routes_analysis.py"""
import logging
import numpy as np
from flask import Blueprint, jsonify, request
from core.scenarios import analyze_session, analyze_roi
from core.job_queue import submit, get_job
from api.validation import reject_invalid_session

log = logging.getLogger(__name__)
bp_analysis = Blueprint("analysis", __name__)

_ERR_500 = {"error": "Internal error. Check server logs."}


@bp_analysis.post("/<session_name>")
def run_analysis(session_name):
    err = reject_invalid_session(session_name)
    if err:
        return err
    force  = request.json.get("force", False) if request.json else False
    job_id = submit(analyze_session, session_name, force=force)
    log.info("analysis submitted session=%s job=%s", session_name, job_id)
    return jsonify({"job_id": job_id, "status": "pending"}), 202


@bp_analysis.get("/<session_name>/status/<job_id>")
def job_status(session_name, job_id):
    err = reject_invalid_session(session_name)
    if err:
        return err
    job = get_job(job_id)
    if job is None:
        return jsonify({"error": "Job not found."}), 404

    if job["status"] == "done":
        result = job.get("result", {})
        result.pop("signal", None)
        return jsonify({"status": "done", "result": result})

    if job["status"] == "error":
        log.error("job %s error: %s", job_id, job.get("error"))
        return jsonify({"status": "error", "error": "Analysis failed. Check server logs."})

    return jsonify({"status": job["status"]})


@bp_analysis.get("/<session_name>")
def get_analysis(session_name):
    err = reject_invalid_session(session_name)
    if err:
        return err
    try:
        from core.session_manager import load_results
        results = load_results(session_name)
        return jsonify(results)
    except FileNotFoundError:
        return jsonify({"error": "No results found. Run analysis first."}), 404


@bp_analysis.post("/<session_name>/pixel_pos")
def pixel_pos(session_name):
    """
    Return global POS signal vs local (per-pixel) POS for a clicked map position.
    Body: { nx: float [0,1], ny: float [0,1] }
    """
    err = reject_invalid_session(session_name)
    if err:
        return err
    data = request.json or {}
    nx = float(data.get("nx", 0.5))
    ny = float(data.get("ny", 0.5))
    try:
        from core.session_manager import load_session, load_results
        from core.pos_algorithm import pos_signal
        from core.scenarios import _ANALYSIS_RESIZE

        frames, meta = load_session(session_name, resize=_ANALYSIS_RESIZE)
        fps  = float(meta.get("measured_fps", 30))
        N, H, W, _ = frames.shape

        px = int(np.clip(nx * W, 0, W - 1))
        py = int(np.clip(ny * H, 0, H - 1))

        pixel_rgb = frames[:, py, px, :]            # (N, 3)
        local_sig = pos_signal(pixel_rgb, fps)

        results    = load_results(session_name)
        global_sig = results.get("signal", {}).get("filt", [])
        time_axis  = results.get("signal", {}).get("time", [])

        return jsonify({
            "local":  local_sig.tolist(),
            "global": global_sig,
            "time":   time_axis,
            "pixel":  {"x": px, "y": py, "nx": round(nx, 3), "ny": round(ny, 3)},
            "fps":    fps,
        })
    except FileNotFoundError:
        return jsonify({"error": "Session not analyzed yet — run analysis first."}), 404
    except Exception:
        log.exception("pixel_pos failed session=%s", session_name)
        return jsonify(_ERR_500), 500


@bp_analysis.post("/<session_name>/roi")
def analyze_roi_endpoint(session_name):
    err = reject_invalid_session(session_name)
    if err:
        return err
    data = request.json or {}
    if "roi" not in data:
        return jsonify({"error": "Missing parameter 'roi'."}), 400
    roi   = tuple(data["roi"])
    label = data.get("label", "roi")
    try:
        result = analyze_roi(session_name, roi, label)
        return jsonify(result)
    except FileNotFoundError:
        return jsonify({"error": "Session not found."}), 404
    except Exception:
        log.exception("roi analysis failed session=%s", session_name)
        return jsonify(_ERR_500), 500
