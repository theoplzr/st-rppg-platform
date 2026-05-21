"""
core/spatial_maps.py
────────────────────
Pixel-wise ST-rPPG spatial map generation.

Maps computed:
  - amplitude   : per-pixel PPG power at HR frequency (single FFT)
  - phase       : per-pixel temporal phase relative to spatial median
  - snr         : Pulse3DFace sliding-window SNR (Wang/Stricker method)
  - coherence   : signed Pearson correlation local POS vs global POS
  - corr_snr    : coherence × normalized SNR  (same as dataset_builder)
"""

import numpy as np
import base64
import io
from PIL import Image


# ─── Shared FFT helper ─────────────────────────────────────────────────────────

def _green_fft(frames: np.ndarray, fps: float):
    """Windowed FFT of the green channel. Returns (fft_complex, fft_power, freq)."""
    N     = frames.shape[0]
    green = frames[:, :, :, 1].astype(np.float32)
    win   = np.hanning(N)
    fft_c = np.fft.rfft(green * win[:, None, None], axis=0)  # (F, H, W)
    fft_p = np.abs(fft_c) ** 2
    freq  = np.fft.rfftfreq(N, d=1.0 / fps)
    return fft_c, fft_p, freq


# ─── Amplitude & Phase (single-window FFT) ────────────────────────────────────

def _amplitude_from_fft(fft_power: np.ndarray, freq: np.ndarray,
                         hr_hz: float, bw: float = 0.15) -> np.ndarray:
    mask = np.abs(freq - hr_hz) < bw
    if not np.any(mask):
        return np.zeros(fft_power.shape[1:], dtype=fft_power.dtype)
    return fft_power[mask].mean(axis=0)


def _phase_from_fft(fft_complex: np.ndarray, freq: np.ndarray,
                     hr_hz: float, bw: float = 0.15) -> np.ndarray:
    mask = np.abs(freq - hr_hz) < bw
    if not np.any(mask):
        return np.zeros(fft_complex.shape[1:], dtype=np.float32)
    fft_hr = fft_complex[mask].mean(axis=0)
    phase  = np.angle(fft_hr)
    phase -= np.median(phase)
    return phase


# ─── Sliding-window SNR (Pulse3DFace / dataset_builder method) ────────────────

def _snr_sliding(local_pos: np.ndarray, fps: float, hr_hz: float,
                 window_sec: float = 10.0,
                 stride_sec: float = 2.0,
                 delta_fund: float = 6.0 / 60.0,
                 delta_harm: float = 12.0 / 60.0) -> np.ndarray:
    """
    Sliding-window SNR map — Pulse3DFace Eq. 1-2.

    SNR(dB) = 10·log10( Σ_{U=1} |Ŝ|² / Σ_{U=0} |Ŝ|² )
    U(f) = 1  iff  |f − HR| < delta_fund  OR  |f − 2·HR| < delta_harm

    local_pos : (N, H, W) per-pixel Hilbert-normalised POS signal
    Returns   : (H, W) float32 in dB
    """
    N, H, W = local_pos.shape
    win_n   = max(int(window_sec * fps), 32)
    step_n  = max(int(stride_sec * fps), 1)
    win_n   = min(win_n, N)
    starts  = list(range(0, N - win_n + 1, step_n)) or [0]

    snr_acc = np.zeros((H, W), dtype=np.float64)

    for st in starts:
        seg   = local_pos[st:st + win_n]          # (win, H, W)
        T     = seg.shape[0]
        hann  = np.hanning(T)
        freqs = np.fft.rfftfreq(T, d=1.0 / fps)
        pwr   = np.abs(np.fft.rfft(
                    seg * hann[:, None, None], axis=0)) ** 2   # (F, H, W)

        U = ((np.abs(freqs - hr_hz)       < delta_fund) |
             (np.abs(freqs - 2.0 * hr_hz) < delta_harm))      # (F,)

        p_sig   = (pwr *    U[:, None, None]).sum(axis=0)
        p_noise = (pwr * (~U)[:, None, None]).sum(axis=0)
        snr_acc += 10.0 * np.log10((p_sig + 1e-12) / (p_noise + 1e-12))

    return (snr_acc / len(starts)).astype(np.float32)


# ─── Coherence (signed Pearson corr, local POS vs global) ─────────────────────

def _coherence_from_pos(frames: np.ndarray, fps: float,
                        ref_signal: np.ndarray = None) -> np.ndarray:
    """
    Signed Pearson correlation of each pixel's POS signal against the global
    POS reference. Returns values in [−1, 1].
    """
    from .pos_algorithm import pos_local

    pos_maps = pos_local(frames, fps)          # (N, H, W)
    N, H, W  = pos_maps.shape

    if ref_signal is not None:
        ref = np.asarray(ref_signal, dtype=np.float32)[:N]
    else:
        ref = pos_maps.mean(axis=(1, 2))

    ref      = ref - ref.mean()
    ref_std  = ref.std() + 1e-8

    pos_c    = pos_maps - pos_maps.mean(axis=0, keepdims=True)
    px_std   = pos_c.std(axis=0) + 1e-8

    coh = np.tensordot(ref, pos_c.reshape(N, -1), axes=[[0], [0]])
    coh = coh.reshape(H, W) / (N * ref_std * px_std)
    return np.clip(coh, -1.0, 1.0).astype(np.float32)


# ─── corr_snr = coherence × SNR_normalized  (dataset_builder formula) ─────────

def _corr_snr(corr_map: np.ndarray, snr_map: np.ndarray) -> np.ndarray:
    """
    corr_snr = corr_map × snr_norm
    snr_norm is SNR_linear clipped to [0,1] via robust percentile scaling
    (same formula as dataset_builder_v2_k.ipynb).
    """
    snr_lin  = 10.0 ** (snr_map.astype(np.float32) / 10.0)
    valid    = snr_lin[np.isfinite(snr_lin)]
    if len(valid) < 2:
        return corr_map.copy()
    p2, p98  = np.percentile(valid, 2), np.percentile(valid, 98)
    snr_norm = np.clip((snr_lin - p2) / (p98 - p2 + 1e-8), 0.0, 1.0)
    return (corr_map * snr_norm).astype(np.float32)


# ─── All maps in one pass ──────────────────────────────────────────────────────

def compute_all_maps(frames: np.ndarray, fps: float,
                     hr_hz: float,
                     filt_signal: np.ndarray = None) -> dict:
    """
    Compute all ST-rPPG spatial maps.

    Parameters
    ----------
    frames      : (N, H, W, 3) float32 in [0, 1]
    fps         : frames per second
    hr_hz       : dominant heart-rate frequency in Hz
    filt_signal : (N,) global POS signal used as coherence reference

    Returns dict with keys: amplitude, phase, snr, coherence, corr_snr, shape.
    """
    # --- single-pass FFT for amplitude + phase ---
    fft_c, fft_p, freq = _green_fft(frames, fps)
    amp   = _amplitude_from_fft(fft_p, freq, hr_hz)
    phase = _phase_from_fft(fft_c, freq, hr_hz)

    # --- per-pixel POS for sliding SNR + coherence (shared computation) ---
    from .pos_algorithm import pos_local
    local_pos = pos_local(frames, fps)          # (N, H, W)

    snr = _snr_sliding(local_pos, fps, hr_hz)
    coh = _coherence_signed(local_pos, filt_signal)
    cs  = _corr_snr(coh, snr)

    return {
        "amplitude":  amp,
        "phase":      phase,
        "snr":        snr,
        "coherence":  coh,
        "corr_snr":   cs,
        "shape":      list(amp.shape),
    }


def _coherence_signed(local_pos: np.ndarray,
                      ref_signal: np.ndarray = None) -> np.ndarray:
    """
    Signed Pearson correlation of pre-computed per-pixel POS vs reference.
    Avoids recomputing pos_local when it's already available.
    """
    N, H, W = local_pos.shape

    if ref_signal is not None:
        ref = np.asarray(ref_signal, dtype=np.float32)[:N]
    else:
        ref = local_pos.mean(axis=(1, 2))

    ref     = ref - ref.mean()
    ref_std = ref.std() + 1e-8

    pos_c   = local_pos - local_pos.mean(axis=0, keepdims=True)
    px_std  = pos_c.std(axis=0) + 1e-8

    coh = np.tensordot(ref, pos_c.reshape(N, -1), axes=[[0], [0]])
    coh = coh.reshape(H, W) / (N * ref_std * px_std)
    return np.clip(coh, -1.0, 1.0).astype(np.float32)


# ─── Base64 PNG export ─────────────────────────────────────────────────────────

COLORMAPS = {
    "perfusion": [
        (13, 17, 23),
        (26, 58, 92),
        (0, 200, 255),
        (126, 231, 135),
        (240, 136, 62),
        (248, 81, 73),
    ],
    "phase": [
        (0, 0, 139),
        (0, 100, 255),
        (200, 200, 200),
        (255, 100, 0),
        (139, 0, 0),
    ],
    "snr": [
        (248, 81, 73),
        (240, 136, 62),
        (200, 200, 200),
        (0, 200, 255),
        (126, 231, 135),
    ],
    "coherence": [
        (139, 0, 0),
        (240, 136, 62),
        (200, 200, 200),
        (0, 200, 255),
        (13, 17, 80),
    ],
    "corr_snr": [
        (13, 17, 23),
        (26, 58, 92),
        (0, 200, 255),
        (126, 231, 135),
        (248, 81, 73),
    ],
}


def _apply_colormap(data: np.ndarray, cmap_name: str = "perfusion") -> np.ndarray:
    colors = np.array(COLORMAPS[cmap_name], dtype=np.float32)
    n = len(colors)
    d_min, d_max = float(data.min()), float(data.max())
    if d_max - d_min < 1e-8:
        normalized = np.zeros_like(data, dtype=np.float32)
    else:
        normalized = ((data - d_min) / (d_max - d_min)).astype(np.float32)
    indices  = normalized * (n - 1)
    idx_low  = np.floor(indices).astype(int).clip(0, n - 2)
    idx_high = (idx_low + 1).clip(0, n - 1)
    frac     = (indices - idx_low)[..., np.newaxis]
    rgb = (1 - frac) * colors[idx_low] + frac * colors[idx_high]
    return rgb.astype(np.uint8)


def map_to_base64(data: np.ndarray, cmap_name: str = "perfusion",
                  size: tuple = None) -> str:
    rgb = _apply_colormap(data, cmap_name)
    img = Image.fromarray(rgb, mode="RGB")
    if size:
        img = img.resize(size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def maps_to_base64_dict(maps: dict, size: tuple = (256, 256)) -> dict:
    cmap_names = {
        "amplitude": "perfusion",
        "phase":     "phase",
        "snr":       "snr",
        "coherence": "coherence",
        "corr_snr":  "corr_snr",
    }
    return {
        key: map_to_base64(maps[key], cmap, size)
        for key, cmap in cmap_names.items()
        if key in maps
    }


# ─── ROI statistics ────────────────────────────────────────────────────────────

def roi_stats(amp_map: np.ndarray, roi: tuple = None) -> dict:
    data = amp_map[roi[1]:roi[1]+roi[3], roi[0]:roi[0]+roi[2]] if roi else amp_map
    return {
        "mean":   round(float(data.mean()),   4),
        "std":    round(float(data.std()),    4),
        "max":    round(float(data.max()),    4),
        "min":    round(float(data.min()),    4),
        "median": round(float(np.median(data)), 4),
    }
