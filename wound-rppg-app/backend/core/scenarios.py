import json
import numpy as np
from pathlib import Path

from .pos_algorithm import pos_wang2017_raw, pos_filtered, pos_signal, spatial_average
from .signal_quality import full_quality_report
from .spatial_maps import compute_all_maps, maps_to_base64_dict, roi_stats
from .ai_interpretation import interpret_results
from .session_manager import (
    load_session,
    load_results,
    save_results,
    SESSIONS_DIR,
)

# 128x128 = compromise between signal quality and Render memory usage
_ANALYSIS_RESIZE = (64, 64)


def _round_or_zero(value, digits=2):
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return 0


def _load_scenario(session_name: str, sessions_root: Path = None) -> dict:
    root = sessions_root or SESSIONS_DIR
    scenario_path = root / session_name / "scenario.json"
    if not scenario_path.exists():
        return {}

    with open(scenario_path) as f:
        return json.load(f)


def _result_summary(session_name: str, result: dict, sessions_root: Path = None) -> dict:
    quality = result.get("quality", {})
    hr = result.get("hr", {})
    snr = result.get("snr", {})
    tms = result.get("tms", {})

    return {
        "name": session_name,
        "scenario": _load_scenario(session_name, sessions_root=sessions_root),
        "fps": _round_or_zero(result.get("fps"), 2),
        "hr_bpm": _round_or_zero(hr.get("hr_bpm"), 1),
        "snr_db": _round_or_zero(snr.get("mean_snr"), 2),
        "tms": _round_or_zero(tms.get("tms"), 4),
        "score": int(quality.get("score", 0) or 0),
        "label": quality.get("label", "UNKNOWN"),
        "color": quality.get("color", "#9ca3af"),
    }


def analyze_session(session_name: str, sessions_root: Path = None, force: bool = False) -> dict:
    root = sessions_root or SESSIONS_DIR

    if not force:
        try:
            return load_results(session_name, sessions_root=root)
        except FileNotFoundError:
            pass

    frames, meta = load_session(session_name, sessions_root=root, resize=_ANALYSIS_RESIZE)
    fps = float(meta.get("measured_fps", 30))
    if not (1.0 <= fps <= 240.0):
        fps = 30.0

    rgb       = spatial_average(frames)
    raw       = pos_wang2017_raw(rgb, fps)
    filt_bp   = pos_filtered(rgb, fps)   # detrend + bandpass — for metrics
    filt_norm = pos_signal(rgb, fps)     # + Hilbert norm — for spatial maps

    report = full_quality_report(raw, filt_bp, fps, rgb_signal=rgb)

    hr_hz = report["hr"]["hr_hz"] or 1.2

    # Subsample to at most 300 frames for spatial maps (prevents 30-60 s compute on 3-min videos)
    _MAP_MAX_FRAMES = 300
    n_total = len(frames)
    if n_total > _MAP_MAX_FRAMES:
        center     = n_total // 2
        half       = _MAP_MAX_FRAMES // 2
        map_frames = frames[center - half: center + half]
        map_signal = filt_norm[center - half: center + half]
    else:
        map_frames = frames
        map_signal = filt_norm

    maps = compute_all_maps(map_frames, fps, hr_hz, filt_signal=map_signal)
    maps_b64 = maps_to_base64_dict(maps, size=(256, 256))

    amp_stats = roi_stats(maps["amplitude"])
    results = {
        "session_name": session_name,
        "meta": meta,
        "fps": fps,
        "n_frames": len(frames),
        **report,
        "maps": maps_b64,
        "amp_stats": amp_stats,
        "interpretation": interpret_results({**report, "amp_stats": amp_stats}),
    }

    save_results(session_name, results, sessions_root=root)
    return results


def compare_two(session_a: str, session_b: str, sessions_root: Path = None) -> dict:
    root = sessions_root or SESSIONS_DIR
    result_a = analyze_session(session_a, sessions_root=root)
    result_b = analyze_session(session_b, sessions_root=root)

    summary_a = _result_summary(session_a, result_a, sessions_root=root)
    summary_b = _result_summary(session_b, result_b, sessions_root=root)

    return {
        "session_a": summary_a,
        "session_b": summary_b,
        "diff": {
            "hr_bpm": round(summary_b["hr_bpm"] - summary_a["hr_bpm"], 1),
            "snr_db": round(summary_b["snr_db"] - summary_a["snr_db"], 2),
            "score": summary_b["score"] - summary_a["score"],
        },
        "maps_a": result_a.get("maps", {}),
        "maps_b": result_b.get("maps", {}),
    }


def compare_multiple(session_names: list, sessions_root: Path = None) -> dict:
    root = sessions_root or SESSIONS_DIR
    ranking = []

    for session_name in session_names:
        result = analyze_session(session_name, sessions_root=root)
        ranking.append(_result_summary(session_name, result, sessions_root=root))

    ranking.sort(
        key=lambda item: (item["score"], item["snr_db"], item["tms"]),
        reverse=True,
    )

    return {"ranking": ranking, "n": len(ranking)}


def analyze_roi(
    session_name: str,
    roi: tuple,
    label: str = "roi",
    sessions_root: Path = None,
) -> dict:
    root = sessions_root or SESSIONS_DIR
    frames, meta = load_session(session_name, sessions_root=root, resize=_ANALYSIS_RESIZE)
    fps = float(meta.get("measured_fps", 30))

    x, y, w, h = roi
    roi_frames = frames[:, y:y + h, x:x + w, :]

    rgb     = spatial_average(roi_frames)
    raw     = pos_wang2017_raw(rgb, fps)
    filt_bp = pos_filtered(rgb, fps)

    report = full_quality_report(raw, filt_bp, fps, rgb_signal=rgb)
    report["roi"] = {"x": x, "y": y, "w": w, "h": h}
    report["label"] = label
    return report


