import json
import numpy as np
from pathlib import Path

from .pos_algorithm import (
    pos_wang2017_raw, pos_filtered, pos_signal, spatial_average,
    chrom_filtered, chrom_signal,
    lgi_filtered,
)
from .signal_quality import full_quality_report
from .spatial_maps import (
    compute_all_maps, maps_to_base64_dict, roi_stats,
    dc_map, amplitude_normalized,
)
from .ai_interpretation import interpret_results
from .session_manager import (
    load_session,
    load_mask,
    load_results,
    save_results,
    SESSIONS_DIR,
)

# 64×64 = balance qualité signal / usage mémoire Render
_ANALYSIS_RESIZE = (64, 64)


def _round_or_zero(value, digits=2):
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return 0


def _compute_healing_score(snr_db: float, amplitude: float,
                           wound_pct: float = None) -> dict:
    """
    Composite perfusion/healing score 0–100.
    Components:
      SNR    — up to 40 pts  (SNR ≥ 10 dB = full score)
      Amp    — up to 35 pts  (RMS amplitude ≥ 0.035 = full score)
      Coverage — up to 25 pts (wound mask ≥ 25% of frame = full score; 15 if unknown)
    """
    s_snr  = float(np.clip((snr_db / 10.0) * 40.0, 0.0, 40.0))
    s_amp  = float(np.clip((amplitude / 0.035) * 35.0, 0.0, 35.0))
    if wound_pct is not None:
        s_cov = float(np.clip((wound_pct / 25.0) * 25.0, 0.0, 25.0))
    else:
        s_cov = 15.0   # neutral when no mask
    total = round(s_snr + s_amp + s_cov, 1)
    if total >= 75:
        label, color = "Bonne perfusion", "#22d47e"
    elif total >= 45:
        label, color = "Perfusion modérée", "#f59e0b"
    else:
        label, color = "Perfusion faible", "#ef4444"
    return {
        "score":   total,
        "label":   label,
        "color":   color,
        "s_snr":   round(s_snr, 1),
        "s_amp":   round(s_amp, 1),
        "s_cov":   round(s_cov, 1),
    }


def _load_scenario(session_name: str, sessions_root: Path = None) -> dict:
    root = sessions_root or SESSIONS_DIR
    scenario_path = root / session_name / "scenario.json"
    if not scenario_path.exists():
        return {}
    with open(scenario_path) as f:
        return json.load(f)


def _result_summary(session_name: str, result: dict, sessions_root: Path = None) -> dict:
    quality = result.get("quality", {})
    hr      = result.get("hr", {})
    snr     = result.get("snr", {})
    tms     = result.get("tms", {})
    return {
        "name":     session_name,
        "scenario": _load_scenario(session_name, sessions_root=sessions_root),
        "fps":      _round_or_zero(result.get("fps"), 2),
        "hr_bpm":   _round_or_zero(hr.get("hr_bpm"), 1),
        "snr_db":   _round_or_zero(snr.get("mean_snr"), 2),
        "tms":      _round_or_zero(tms.get("tms"), 4),
        "score":    int(quality.get("score", 0) or 0),
        "label":    quality.get("label", "UNKNOWN"),
        "color":    quality.get("color", "#9ca3af"),
        "date":     result.get("meta", {}).get("date", ""),
    }


def analyze_session(session_name: str, sessions_root: Path = None,
                    force: bool = False) -> dict:
    root = sessions_root or SESSIONS_DIR

    if not force:
        try:
            return load_results(session_name, sessions_root=root)
        except FileNotFoundError:
            pass

    frames, meta = load_session(session_name, sessions_root=root,
                                resize=_ANALYSIS_RESIZE)
    fps = float(meta.get("measured_fps", 30))
    if not (1.0 <= fps <= 240.0):
        fps = 30.0

    # ── Charge le masque si l'utilisateur en a défini un ──────────────────────
    mask_2d = load_mask(session_name, resize=_ANALYSIS_RESIZE,
                        sessions_root=root)   # (H, W) bool  ou  None

    # ── Applique le masque : zéro les pixels hors zone ─────────────────────────
    masked_frames = frames
    if mask_2d is not None:
        masked_frames = frames.copy()
        masked_frames[:, ~mask_2d, :] = 0.0   # hors masque → noir (RGB=0)

    # ── Signal global (moyenne spatiale sur zone masquée) ─────────────────────
    rgb       = spatial_average(masked_frames, mask=mask_2d)
    raw       = pos_wang2017_raw(rgb, fps)
    filt_bp   = pos_filtered(rgb, fps)    # pour les métriques (amplitude préservée)
    filt_norm = pos_signal(rgb, fps)      # normalisé Hilbert pour les cartes

    report = full_quality_report(raw, filt_bp, fps,
                                 rgb_signal=rgb, frames=masked_frames)
    hr_hz  = report["hr"]["hr_hz"] or 1.2

    # ── CHROM + LGI algorithm comparison ─────────────────────────────────────
    from .signal_quality import estimate_hr_fft, compute_snr_sliding

    def _algo_metrics(sig_bp):
        _hr  = estimate_hr_fft(sig_bp, fps)
        _snr = compute_snr_sliding(sig_bp, fps, _hr.get("hr_hz") or hr_hz)
        _max = float(np.abs(sig_bp).max()) + 1e-8
        return {
            "hr_bpm": _hr.get("hr_bpm"),
            "snr_db": _snr.get("mean_snr"),
            "signal": (sig_bp / _max).tolist(),
        }

    report["chrom"] = _algo_metrics(chrom_filtered(rgb, fps))
    report["lgi"]   = _algo_metrics(lgi_filtered(rgb, fps))

    # ── Composite healing score ───────────────────────────────────────────────
    _snr_val  = report.get("snr", {}).get("mean_snr") or 0.0
    _amp_val  = float(np.sqrt(np.mean(filt_bp ** 2)))   # RMS amplitude
    _wpct     = None
    if mask_2d is not None:
        _wpct = 100.0 * int(mask_2d.sum()) / max(int(mask_2d.size), 1)
    report["healing_score"] = _compute_healing_score(_snr_val, _amp_val, _wpct)

    # ── Sous-échantillonnage pour les cartes spatiales (max 300 frames) ───────
    _MAP_MAX_FRAMES = 300
    n_total = len(masked_frames)
    if n_total > _MAP_MAX_FRAMES:
        center     = n_total // 2
        half       = _MAP_MAX_FRAMES // 2
        map_frames = masked_frames[center - half: center + half]
        map_signal = filt_norm[center - half: center + half]
    else:
        map_frames = masked_frames
        map_signal = filt_norm

    maps     = compute_all_maps(map_frames, fps, hr_hz, filt_signal=map_signal)
    dc       = dc_map(map_frames)
    maps["dc"]             = dc
    maps["amp_normalized"] = amplitude_normalized(maps["amplitude"], dc)
    maps_b64 = maps_to_base64_dict(maps, size=(256, 256))

    amp_stats = roi_stats(maps["amplitude"])

    # ── Wound area from mask ──────────────────────────────────────────────────
    wound_area = None
    if mask_2d is not None:
        n_wound = int(mask_2d.sum())
        n_total = int(mask_2d.size)
        wound_area = {
            "pixels":  n_wound,
            "total":   n_total,
            "pct":     round(100.0 * n_wound / max(n_total, 1), 2),
        }

    results = {
        "session_name": session_name,
        "meta":         meta,
        "fps":          fps,
        "n_frames":     len(frames),
        "has_mask":     mask_2d is not None,
        "wound_area":   wound_area,
        **report,
        "maps":         maps_b64,
        "amp_stats":    amp_stats,
        "interpretation": interpret_results({**report, "amp_stats": amp_stats}),
    }

    save_results(session_name, results, sessions_root=root)
    return results


def compare_two(session_a: str, session_b: str,
                sessions_root: Path = None) -> dict:
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
            "score":  summary_b["score"] - summary_a["score"],
        },
        "maps_a": result_a.get("maps", {}),
        "maps_b": result_b.get("maps", {}),
    }


def compare_multiple(session_names: list, sessions_root: Path = None) -> dict:
    root    = sessions_root or SESSIONS_DIR
    ranking = []
    for session_name in session_names:
        result = analyze_session(session_name, sessions_root=root)
        ranking.append(_result_summary(session_name, result, sessions_root=root))
    ranking.sort(key=lambda x: (x["score"], x["snr_db"], x["tms"]), reverse=True)
    return {"ranking": ranking, "n": len(ranking)}


def analyze_roi(session_name: str, roi: tuple, label: str = "roi",
                sessions_root: Path = None) -> dict:
    root   = sessions_root or SESSIONS_DIR
    frames, meta = load_session(session_name, sessions_root=root,
                                resize=_ANALYSIS_RESIZE)
    fps = float(meta.get("measured_fps", 30))
    x, y, w, h = roi
    roi_frames  = frames[:, y:y + h, x:x + w, :]
    rgb         = spatial_average(roi_frames)
    raw         = pos_wang2017_raw(rgb, fps)
    filt_bp     = pos_filtered(rgb, fps)
    report      = full_quality_report(raw, filt_bp, fps, rgb_signal=rgb)
    report["roi"]   = {"x": x, "y": y, "w": w, "h": h}
    report["label"] = label
    return report


def analyze_dual_roi(session_name: str,
                     roi_wound: tuple, roi_healthy: tuple,
                     sessions_root: Path = None) -> dict:
    """
    Compare wound ROI vs healthy skin ROI side-by-side.
    roi_wound / roi_healthy : (x, y, w, h) in analysis-resize coordinates.
    Returns both reports + perfusion ratio (wound_amp / healthy_amp).
    """
    root = sessions_root or SESSIONS_DIR
    frames, meta = load_session(session_name, sessions_root=root,
                                resize=_ANALYSIS_RESIZE)
    fps = float(meta.get("measured_fps", 30))

    def _roi_report(roi):
        x, y, w, h = roi
        roi_f  = frames[:, y:y + h, x:x + w, :]
        rgb    = spatial_average(roi_f)
        raw    = pos_wang2017_raw(rgb, fps)
        filt   = pos_filtered(rgb, fps)
        return full_quality_report(raw, filt, fps, rgb_signal=rgb)

    rep_wound   = _roi_report(roi_wound)
    rep_healthy = _roi_report(roi_healthy)

    amp_w = rep_wound.get("amp_stats", {}).get("mean", 0) or \
            float(np.abs(np.array(rep_wound["signal"]["filt"])).mean())
    amp_h = rep_healthy.get("amp_stats", {}).get("mean", 0) or \
            float(np.abs(np.array(rep_healthy["signal"]["filt"])).mean())

    ratio = round(amp_w / (amp_h + 1e-8), 3)

    return {
        "wound":         {**rep_wound,   "roi": dict(zip("xywh", roi_wound))},
        "healthy":       {**rep_healthy, "roi": dict(zip("xywh", roi_healthy))},
        "perfusion_ratio": ratio,
        "hr_diff_bpm": round(
            (rep_wound["hr"].get("hr_bpm") or 0) -
            (rep_healthy["hr"].get("hr_bpm") or 0), 1
        ),
        "snr_diff_db": round(
            (rep_wound["snr"].get("mean_snr") or 0) -
            (rep_healthy["snr"].get("mean_snr") or 0), 2
        ),
    }


def timeline(zone: str = None, label: str = None,
             wound_id: str = None,
             sessions_root: Path = None) -> dict:
    """
    Retourne l'évolution temporelle des métriques pour un groupe de sessions.
    Groupe par wound_id (prioritaire), sinon par zone + label.
    """
    root     = sessions_root or SESSIONS_DIR
    points   = []

    for session_dir in sorted(root.iterdir()):
        if not session_dir.is_dir():
            continue
        results_path = session_dir / "results.json"
        scenario_path = session_dir / "scenario.json"
        if not results_path.exists():
            continue

        scenario = {}
        if scenario_path.exists():
            with open(scenario_path) as f:
                scenario = json.load(f)

        # Filtre
        if wound_id:
            if scenario.get("wound_id") != wound_id:
                continue
        else:
            if zone  and scenario.get("zone")  != zone:
                continue
            if label and scenario.get("label") != label:
                continue

        with open(results_path) as f:
            r = json.load(f)

        points.append({
            "name":       session_dir.name,
            "date":       r.get("meta", {}).get("date", ""),
            "snr_db":     _round_or_zero(r.get("snr", {}).get("mean_snr"), 2),
            "hr_bpm":     _round_or_zero(r.get("hr", {}).get("hr_bpm"), 1),
            "tms":        _round_or_zero(r.get("tms", {}).get("tms"), 4),
            "score":      int(r.get("quality", {}).get("score", 0) or 0),
            "amp_mean":   _round_or_zero(r.get("amp_stats", {}).get("mean"), 4),
            "wound_pct":  _round_or_zero(r.get("wound_area", {}).get("pct") if r.get("wound_area") else None, 2),
            "rr_bpm":     _round_or_zero(r.get("respiration", {}).get("rr_bpm"), 1),
            "has_mask":   bool(r.get("has_mask", False)),
            "scenario":   scenario,
        })

    points.sort(key=lambda p: p["date"])
    return {"points": points, "n": len(points)}
