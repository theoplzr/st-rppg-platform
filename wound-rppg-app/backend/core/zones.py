"""
core/zones.py
─────────────
Zone-based ST-rPPG analysis.

Instead of per-pixel analysis (noisy, 64×64 = 4096 independent signals),
the observed region is divided into a configurable grid of zones.
Each zone averages its pixels before computing POS — giving a much more
robust signal per region while preserving spatial information.

Public API
----------
compute_zone_grid(frames, fps, n_rows, n_cols, mask, hr_hz)
    → dict with per-zone metrics + comparison arrays

zone_signals_for_display(frames, fps, n_rows, n_cols, mask)
    → per-zone filtered signals for frontend chart comparison
"""

import numpy as np
from scipy.signal import find_peaks

from .pos_algorithm import (
    pos_wang2017_raw, pos_filtered, spatial_average,
)
from .signal_quality import estimate_hr_fft, compute_snr_sliding

_EPS = 1e-8


def _zone_slices(H: int, W: int, n_rows: int, n_cols: int):
    """Generate (row_idx, col_idx, row_slice, col_slice) for each zone."""
    row_edges = np.linspace(0, H, n_rows + 1, dtype=int)
    col_edges = np.linspace(0, W, n_cols + 1, dtype=int)
    for r in range(n_rows):
        for c in range(n_cols):
            yield r, c, slice(row_edges[r], row_edges[r+1]), slice(col_edges[c], col_edges[c+1])


def compute_zone_grid(
    frames: np.ndarray,
    fps: float,
    n_rows: int = 4,
    n_cols: int = 4,
    mask: np.ndarray = None,
    hr_hz: float = None,
) -> dict:
    """
    Divide the frame into n_rows × n_cols zones and compute per-zone metrics.

    Parameters
    ----------
    frames  : (N, H, W, 3) float32 [0,1]
    fps     : frames per second
    n_rows  : number of zone rows  (default 4)
    n_cols  : number of zone columns (default 4)
    mask    : (H, W) bool — if provided, zones with < 10% valid pixels are skipped
    hr_hz   : dominant heart-rate frequency; if None, estimated per zone

    Returns
    -------
    dict with:
      zones   : list of zone dicts (r, c, hr_bpm, snr_db, amplitude, tms, n_pixels, active)
      grid_snr       : (n_rows, n_cols) SNR values
      grid_amplitude : (n_rows, n_cols) amplitude values
      grid_hr        : (n_rows, n_cols) HR bpm values
      n_rows, n_cols
    """
    N, H, W, _ = frames.shape
    zones = []

    grid_snr  = np.full((n_rows, n_cols), np.nan, dtype=np.float32)
    grid_amp  = np.full((n_rows, n_cols), np.nan, dtype=np.float32)
    grid_hr   = np.full((n_rows, n_cols), np.nan, dtype=np.float32)

    for r, c, rs, cs in _zone_slices(H, W, n_rows, n_cols):
        zone_frames = frames[:, rs, cs, :]           # (N, zh, zw, 3)
        zh, zw      = zone_frames.shape[1], zone_frames.shape[2]
        n_px_total  = zh * zw

        # Mask filtering
        zone_mask = mask[rs, cs] if mask is not None else None
        if zone_mask is not None:
            n_valid = int(zone_mask.sum())
            if n_valid < max(4, int(0.10 * n_px_total)):
                zones.append(_empty_zone(r, c))
                continue
        else:
            n_valid = n_px_total

        # Spatial average within zone (respecting mask)
        rgb = spatial_average(zone_frames, mask=zone_mask)    # (N, 3)

        # Signal
        try:
            raw    = pos_wang2017_raw(rgb, fps)
            filt   = pos_filtered(rgb, fps)
        except Exception:
            zones.append(_empty_zone(r, c))
            continue

        # HR
        hr_info = estimate_hr_fft(filt, fps)
        zone_hr = hr_info.get("hr_hz") or (hr_hz or 1.2)
        hr_bpm  = hr_info.get("hr_bpm") or round(zone_hr * 60, 1)

        # SNR
        snr_info = compute_snr_sliding(filt, fps, zone_hr)
        snr_db   = snr_info.get("mean_snr", 0.0)

        # Amplitude: RMS of filtered signal
        amplitude = float(np.sqrt(np.mean(filt ** 2)))

        # TMS: simple correlation of signal halves as a morphology proxy
        half = len(filt) // 2
        if half > 10:
            r1, r2 = filt[:half], filt[half:half*2]
            from scipy.stats import pearsonr
            try:
                tms_val = float(pearsonr(r1, r2)[0])
            except Exception:
                tms_val = 0.0
        else:
            tms_val = 0.0

        grid_snr[r, c] = snr_db
        grid_amp[r, c] = amplitude
        grid_hr[r, c]  = hr_bpm

        zones.append({
            "r":         r,
            "c":         c,
            "id":        r * n_cols + c,
            "hr_bpm":    round(hr_bpm, 1),
            "snr_db":    round(snr_db, 2),
            "amplitude": round(amplitude, 5),
            "tms":       round(tms_val, 3),
            "n_pixels":  n_valid,
            "active":    True,
            "signal":    (filt / (np.abs(filt).max() + _EPS)).tolist(),
        })

    return {
        "zones":          zones,
        "n_rows":         n_rows,
        "n_cols":         n_cols,
        "grid_snr":       _nan_to_none(grid_snr),
        "grid_amplitude": _nan_to_none(grid_amp),
        "grid_hr":        _nan_to_none(grid_hr),
        "fps":            fps,
    }


def _empty_zone(r: int, c: int) -> dict:
    return {"r": r, "c": c, "id": r * 100 + c, "active": False,
            "hr_bpm": None, "snr_db": None, "amplitude": None,
            "tms": None, "n_pixels": 0, "signal": []}


def _nan_to_none(arr: np.ndarray) -> list:
    """Convert 2D numpy array to nested list, replacing NaN with None."""
    return [
        [None if np.isnan(v) else round(float(v), 3) for v in row]
        for row in arr
    ]


def zone_surface_3d(frames: np.ndarray, fps: float,
                    n_rows: int = 8, n_cols: int = 8,
                    mask: np.ndarray = None,
                    hr_hz: float = None) -> dict:
    """
    High-resolution zone grid for 3D surface plot.
    Uses a finer grid (default 8×8) to give smooth surface relief.

    Returns:
      x_labels, y_labels : axis tick labels
      surface_amplitude  : (n_rows, n_cols) amplitude values (Z axis)
      surface_snr        : (n_rows, n_cols) SNR values (colour axis)
    """
    result = compute_zone_grid(frames, fps, n_rows, n_cols, mask, hr_hz)

    amp_grid = result["grid_amplitude"]   # (n_rows, n_cols) nested list
    snr_grid = result["grid_snr"]

    # Build ECharts surface3D data: [[xi, yi, amp, snr], ...]
    data = []
    for r_idx, row in enumerate(amp_grid):
        for c_idx, amp in enumerate(row):
            snr = snr_grid[r_idx][c_idx]
            if amp is None:
                amp, snr = 0.0, -20.0
            data.append([c_idx, r_idx, round(amp, 5), round(snr if snr else 0.0, 2)])

    return {
        "data":    data,
        "n_rows":  n_rows,
        "n_cols":  n_cols,
        "x_range": [0, n_cols - 1],
        "y_range": [0, n_rows - 1],
    }
