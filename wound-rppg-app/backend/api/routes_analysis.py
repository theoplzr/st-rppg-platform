"""api/routes_analysis.py"""
import logging
import numpy as np
from flask import Blueprint, jsonify, request
from core.scenarios import analyze_session, analyze_roi, timeline, analyze_dual_roi
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


@bp_analysis.post("/batch")
def run_batch_analysis():
    """
    Body: { sessions: ["s1", "s2", ...], force: false }
    Submits one background job per session and returns a list of job_ids.
    """
    data     = request.json or {}
    sessions = data.get("sessions", [])
    force    = data.get("force", False)
    if not sessions:
        return jsonify({"error": "Missing 'sessions' list."}), 400

    jobs = []
    for name in sessions:
        err = reject_invalid_session(name)
        if err:
            jobs.append({"session": name, "error": "invalid name"})
            continue
        job_id = submit(analyze_session, name, force=force)
        jobs.append({"session": name, "job_id": job_id, "status": "pending"})
        log.info("batch job submitted session=%s job=%s", name, job_id)

    return jsonify({"jobs": jobs}), 202


@bp_analysis.post("/<session_name>/dual_roi")
def dual_roi_endpoint(session_name):
    """
    Compare wound ROI vs healthy ROI.
    Body: { roi_wound: [x,y,w,h], roi_healthy: [x,y,w,h] }
    """
    err = reject_invalid_session(session_name)
    if err:
        return err
    data = request.json or {}
    if "roi_wound" not in data or "roi_healthy" not in data:
        return jsonify({"error": "Missing roi_wound or roi_healthy."}), 400
    try:
        result = analyze_dual_roi(
            session_name,
            tuple(data["roi_wound"]),
            tuple(data["roi_healthy"]),
        )
        return jsonify(result)
    except FileNotFoundError:
        return jsonify({"error": "Session not found."}), 404
    except Exception:
        log.exception("dual_roi failed session=%s", session_name)
        return jsonify(_ERR_500), 500


@bp_analysis.post("/<session_name>/auto_segment")
def auto_segment_endpoint(session_name):
    """
    Run Otsu auto-segmentation on the amplitude map from the last analysis.
    Returns mask_b64, pct, n_pixels — user can then apply it as the mask.
    """
    err = reject_invalid_session(session_name)
    if err:
        return err
    try:
        from core.session_manager import load_results
        from core.spatial_maps import auto_segment_mask
        import base64, cv2

        results = load_results(session_name)
        amp_b64 = results.get("maps", {}).get("amplitude")
        if not amp_b64:
            return jsonify({"error": "No amplitude map — run analysis first."}), 400

        raw  = base64.b64decode(amp_b64.split(",")[-1])
        arr  = np.frombuffer(raw, np.uint8)
        img  = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return jsonify({"error": "Could not decode amplitude map."}), 500

        amp_float = img.astype(np.float32) / 255.0
        seg = auto_segment_mask(amp_float)
        return jsonify(seg)
    except FileNotFoundError:
        return jsonify({"error": "No results — run analysis first."}), 404
    except Exception:
        log.exception("auto_segment failed session=%s", session_name)
        return jsonify(_ERR_500), 500


@bp_analysis.get("/timeline")
def get_timeline():
    """
    Query params:
      zone      — filter by zone
      label     — filter by scenario label
      wound_id  — filter by wound_id (takes priority over zone/label)
    """
    zone      = request.args.get("zone")
    label     = request.args.get("label")
    wound_id  = request.args.get("wound_id")
    try:
        result = timeline(zone=zone, label=label, wound_id=wound_id)
        return jsonify(result)
    except Exception:
        log.exception("timeline failed zone=%s label=%s wound_id=%s", zone, label, wound_id)
        return jsonify(_ERR_500), 500


@bp_analysis.post("/<session_name>/zones")
def zone_analysis_endpoint(session_name):
    """
    Zone-based analysis — divides frame into N×M zones.
    Query params: n_rows (default 4), n_cols (default 4), surface (bool)
    Optional body: { hr_hz: float }
    Returns zones[] + grid_snr/amplitude/hr + optional surface3d data.
    """
    err = reject_invalid_session(session_name)
    if err:
        return err
    n_rows  = request.args.get("n_rows", 4, type=int)
    n_cols  = request.args.get("n_cols", 4, type=int)
    surface = request.args.get("surface", "false").lower() == "true"
    data    = request.json or {}
    hr_hz   = data.get("hr_hz")
    try:
        from core.session_manager import load_session, load_results
        from core.scenarios import _ANALYSIS_RESIZE
        from core.zones import compute_zone_grid, zone_surface_3d

        frames, meta = load_session(session_name, resize=_ANALYSIS_RESIZE)
        fps = float(meta.get("measured_fps", 30))

        # Try to load existing mask
        mask = None
        try:
            res  = load_results(session_name)
            maps = res.get("maps", {})
            if maps.get("mask"):
                import base64, cv2
                raw  = base64.b64decode(maps["mask"].split(",")[-1])
                arr  = np.frombuffer(raw, np.uint8)
                gray = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
                if gray is not None:
                    _, H, W, _ = frames.shape
                    gray = cv2.resize(gray, (W, H), interpolation=cv2.INTER_NEAREST)
                    mask = gray > 127
        except Exception:
            pass

        result = compute_zone_grid(frames, fps, n_rows=n_rows, n_cols=n_cols,
                                   mask=mask, hr_hz=hr_hz)
        if surface:
            n_surf = min(max(n_rows, n_cols) * 2, 12)
            result["surface3d"] = zone_surface_3d(frames, fps, n_rows=n_surf, n_cols=n_surf,
                                                  mask=mask, hr_hz=hr_hz)
        return jsonify(result)
    except FileNotFoundError:
        return jsonify({"error": "Session not found."}), 404
    except Exception:
        log.exception("zone analysis failed session=%s", session_name)
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
