"""
core/spatial_maps.py
────────────────────
Pixel-wise ST-rPPG spatial map generation:
  - Amplitude map
  - Phase map
  - SNR map
  - Coherence map
  - Base64 PNG export for the API

The green-channel FFT is computed once in compute_all_maps and shared
across all four maps, avoiding redundant computation on (N, H, W) arrays.
"""

import numpy as np
import base64
import io
from PIL import Image


# ─── Shared FFT helper ─────────────────────────────────────────────────────────

def _green_fft(frames: np.ndarray, fps: float):
    """
    Compute the windowed FFT of the green channel once.
    Returns (fft_complex, fft_power, freq).
    """
    N = frames.shape[0]
    green = frames[:, :, :, 1].astype(np.float32)
    win   = np.hanning(N)
    fft_c = np.fft.rfft(green * win[:, None, None], axis=0)  # (F, H, W) complex
    fft_p = np.abs(fft_c) ** 2                                # (F, H, W) power
    freq  = np.fft.rfftfreq(N, d=1.0 / fps)
    return fft_c, fft_p, freq


# ─── Individual map builders (accept pre-computed FFT) ─────────────────────────

def _amplitude_from_fft(fft_power: np.ndarray, freq: np.ndarray,
                         hr_hz: float, bw: float = 0.15) -> np.ndarray:
    mask = np.abs(freq - hr_hz) < bw
    if not np.any(mask):
        return np.zeros(fft_power.shape[1:], dtype=fft_power.dtype)
    return fft_power[mask].mean(axis=0)  # (H, W)


def _phase_from_fft(fft_complex: np.ndarray, freq: np.ndarray,
                     hr_hz: float, bw: float = 0.15) -> np.ndarray:
    mask = np.abs(freq - hr_hz) < bw
    if not np.any(mask):
        return np.zeros(fft_complex.shape[1:], dtype=np.float32)
    fft_hr = fft_complex[mask].mean(axis=0)  # (H, W) complex
    phase  = np.angle(fft_hr)
    phase -= np.median(phase)               # center relative to spatial median
    return phase


def _snr_from_fft(fft_power: np.ndarray, freq: np.ndarray,
                   hr_hz: float, bw: float = 0.15) -> np.ndarray:
    mask_sig = np.zeros(len(freq), dtype=bool)
    for k in [1, 2]:
        mask_sig |= (np.abs(freq - k * hr_hz) < bw)
    if not np.any(mask_sig):
        return np.full(fft_power.shape[1:], -30.0, dtype=np.float32)
    p_sig   = fft_power[mask_sig].sum(axis=0)
    p_noise = fft_power[~mask_sig].sum(axis=0)
    return 10 * np.log10((p_sig + 1e-12) / (p_noise + 1e-12))


def _coherence_from_pos(frames: np.ndarray, fps: float,
                        ref_signal: np.ndarray = None) -> np.ndarray:
    """
    POS-based coherence map: Pearson correlation of each pixel's per-pixel POS
    signal (pos_local) against the global POS reference signal.
    """
    from .pos_algorithm import pos_local

    pos_maps = pos_local(frames, fps)           # (N, H, W) Hilbert-normalised
    N, H, W  = pos_maps.shape

    if ref_signal is not None:
        ref = np.asarray(ref_signal, dtype=np.float32)[:N]
    else:
        ref = pos_maps.mean(axis=(1, 2))

    ref     = ref - ref.mean()
    ref_std = ref.std() + 1e-8

    pos_c  = pos_maps - pos_maps.mean(axis=0, keepdims=True)  # (N, H, W)
    px_std = pos_c.std(axis=0) + 1e-8                         # (H, W)

    coh = np.tensordot(ref, pos_c.reshape(N, -1), axes=[[0], [0]])
    coh = coh.reshape(H, W) / (N * ref_std * px_std)
    return np.clip(np.abs(coh), 0, 1)


# ─── All maps in a single FFT pass ────────────────────────────────────────────

def compute_all_maps(frames: np.ndarray, fps: float,
                     hr_hz: float,
                     filt_signal: np.ndarray = None) -> dict:
    """
    Compute all ST-rPPG spatial maps.
    filt_signal: global pos_signal output used as coherence reference.
    """
    fft_c, fft_p, freq = _green_fft(frames, fps)

    amp   = _amplitude_from_fft(fft_p, freq, hr_hz)
    phase = _phase_from_fft(fft_c, freq, hr_hz)
    snr   = _snr_from_fft(fft_p, freq, hr_hz)
    coh   = _coherence_from_pos(frames, fps, ref_signal=filt_signal)

    return {
        "amplitude": amp,
        "phase":     phase,
        "snr":       snr,
        "coherence": coh,
        "shape":     list(amp.shape),
    }


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
        (13, 17, 23),
        (26, 58, 92),
        (0, 200, 255),
        (126, 231, 135),
    ],
}


def _apply_colormap(data: np.ndarray, cmap_name: str = "perfusion") -> np.ndarray:
    """Apply a custom colormap to a normalized 2D array via linear interpolation."""
    colors = np.array(COLORMAPS[cmap_name], dtype=np.float32)
    n = len(colors)

    d_min, d_max = data.min(), data.max()
    if d_max - d_min < 1e-8:
        normalized = np.zeros_like(data)
    else:
        normalized = (data - d_min) / (d_max - d_min)

    indices  = normalized * (n - 1)
    idx_low  = np.floor(indices).astype(int).clip(0, n - 2)
    idx_high = (idx_low + 1).clip(0, n - 1)
    frac     = (indices - idx_low)[..., np.newaxis]

    rgb = (1 - frac) * colors[idx_low] + frac * colors[idx_high]
    return rgb.astype(np.uint8)


def map_to_base64(data: np.ndarray, cmap_name: str = "perfusion",
                  size: tuple = None) -> str:
    """Convert a 2D map to a base64-encoded PNG string."""
    rgb = _apply_colormap(data, cmap_name)
    img = Image.fromarray(rgb, mode="RGB")
    if size:
        img = img.resize(size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def maps_to_base64_dict(maps: dict, size: tuple = (256, 256)) -> dict:
    """Convert all spatial maps to base64 PNG strings for the API response."""
    cmap_names = {
        "amplitude": "perfusion",
        "phase":     "phase",
        "snr":       "snr",
        "coherence": "coherence",
    }
    return {
        key: map_to_base64(maps[key], cmap, size)
        for key, cmap in cmap_names.items()
        if key in maps
    }


# ─── ROI statistics ────────────────────────────────────────────────────────────

def roi_stats(amp_map: np.ndarray,
              roi: tuple = None) -> dict:
    """
    Amplitude statistics over a region of interest.
    roi = (x, y, w, h); if None, statistics are computed over the full map.
    """
    if roi:
        x, y, w, h = roi
        data = amp_map[y:y+h, x:x+w]
    else:
        data = amp_map

    return {
        "mean":   round(float(data.mean()), 4),
        "std":    round(float(data.std()), 4),
        "max":    round(float(data.max()), 4),
        "min":    round(float(data.min()), 4),
        "median": round(float(np.median(data)), 4),
    }
