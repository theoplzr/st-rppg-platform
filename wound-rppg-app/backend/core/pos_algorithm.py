"""
core/pos_algorithm.py
─────────────────────
rPPG algorithms:
  POS   — Wang et al., IEEE TBME 2017
  CHROM — de Haan & Jeanne, IEEE TBME 2013
  LGI   — Pilz et al., CVPRW 2018

Public API
----------
pos_wang2017_raw(RGB, fps)          → raw accumulated signal (N,)
pos_signal(RGB, fps)                → raw + detrend + bandpass + Hilbert norm (N,)
pos_local(frames, fps)              → per-pixel POS (N, H, W) for spatial maps
chrom_signal(RGB, fps)              → CHROM filtered + Hilbert-normalised (N,)
chrom_filtered(RGB, fps)            → CHROM + detrend + bandpass only (amplitude preserved)
lgi_filtered(RGB, fps)              → LGI + detrend + bandpass (amplitude preserved)
lgi_signal(RGB, fps)                → LGI + Hilbert-normalised (N,)
bandpass_filter(signal, fps)        → zero-phase Butterworth bandpass
spatial_average(frames)             → temporal RGB mean (N, 3)
hr_from_signal(sig, fps)            → dominant HR in BPM (float)
"""

import math
import numpy as np
from scipy import signal as scipy_signal
from scipy.signal import butter, filtfilt


# ── Projection matrix (Wang 2017, eq. 4) ──────────────────────────────────────
_M = np.array([[0., 1., -1.],
               [-2., 1.,  1.]], dtype=np.float64)
_EPS = 1e-12


# ── Core POS — exact notebook implementation ───────────────────────────────────

def pos_wang2017_raw(RGB: np.ndarray, fps: float,
                     win_sec: float = 1.6) -> np.ndarray:
    """
    POS raw signal — Wang et al. 2017.
    RGB : (N, 3) float  →  H : (N,) float64 (accumulated, before filtering)
    """
    RGB = np.asarray(RGB, dtype=np.float64)
    N   = RGB.shape[0]
    l   = math.ceil(win_sec * fps)
    H   = np.zeros(N, dtype=np.float64)
    for n in range(l, N + 1):
        m   = n - l
        win = RGB[m:n, :]
        mu  = np.mean(win, axis=0, keepdims=True) + _EPS
        Cn  = (win / mu).T                       # (3, l)
        S   = _M @ Cn                            # (2, l)
        s0, s1 = S[0], S[1]
        alpha  = (np.std(s0) + _EPS) / (np.std(s1) + _EPS)
        h      = s0 + alpha * s1
        H[m:n] += h - np.mean(h)                # mean subtraction (eq. 7)
    return H


def pos_filtered(RGB: np.ndarray, fps: float,
                 win_sec: float = 1.6,
                 bp_low:  float = 0.70,
                 bp_high: float = 3.0) -> np.ndarray:
    """
    POS + detrend + bandpass only (NO Hilbert normalization).
    Use this for SNR / TMS / HR metrics — amplitude is preserved.
    RGB : (N, 3)  →  (N,) float32
    """
    H    = pos_wang2017_raw(RGB, fps, win_sec)
    H    = scipy_signal.detrend(H, type="linear")
    nyq  = fps / 2.0
    lo   = float(np.clip(bp_low  / nyq, 1e-6, 1 - 1e-6))
    hi   = float(np.clip(bp_high / nyq, 1e-6, 1 - 1e-6))
    b, a = scipy_signal.butter(2, [lo, hi], btype="bandpass")
    H    = scipy_signal.filtfilt(b, a, H)
    return H.astype(np.float32)


def pos_signal(RGB: np.ndarray, fps: float,
               win_sec: float = 1.6,
               bp_low:  float = 0.70,
               bp_high: float = 3.0) -> np.ndarray:
    """
    POS + detrend + bandpass + Hilbert envelope normalization.
    Use this for spatial coherence maps (uniform amplitude across pixels).
    RGB : (N, 3)  →  (N,) float32
    """
    H   = pos_filtered(RGB, fps, win_sec, bp_low, bp_high)
    env = np.abs(scipy_signal.hilbert(H)) + _EPS
    return (H / env).astype(np.float32)


def pos_local(RGB_tensor: np.ndarray, fps: float,
              win_sec: float = 1.6,
              bp_low:  float = 0.70,
              bp_high: float = 3.0) -> np.ndarray:
    """
    Vectorised per-pixel POS + detrend + bandpass + Hilbert normalization.
    RGB_tensor : (N, H, W, 3) float  →  (N, H, W) float32
    """
    RGB_tensor = np.asarray(RGB_tensor, dtype=np.float64)
    N, Hi, Wi, _ = RGB_tensor.shape
    l = math.ceil(win_sec * fps)
    if N < l:
        return np.zeros((N, Hi, Wi), dtype=np.float32)

    Hb = np.zeros((N, Hi, Wi), dtype=np.float64)
    for m in range(N - l + 1):
        win   = RGB_tensor[m:m + l]                                # (l, Hi, Wi, 3)
        mu    = np.mean(win, axis=0, keepdims=True) + _EPS
        Cn    = win / mu                                           # (l, Hi, Wi, 3)
        S     = np.einsum("ij,lhwj->ilhw", _M, Cn)                # (2, l, Hi, Wi)
        s0, s1 = S[0], S[1]
        alpha = (np.std(s0, axis=0, keepdims=True) + _EPS) / \
                (np.std(s1, axis=0, keepdims=True) + _EPS)
        h     = s0 + alpha * s1
        Hb[m:m + l] += h - np.mean(h, axis=0, keepdims=True)

    Hb   = scipy_signal.detrend(Hb, axis=0, type="linear")
    nyq  = fps / 2.0
    lo   = float(np.clip(bp_low  / nyq, 1e-6, 1 - 1e-6))
    hi   = float(np.clip(bp_high / nyq, 1e-6, 1 - 1e-6))
    b, a = scipy_signal.butter(2, [lo, hi], btype="bandpass")
    Hb   = scipy_signal.filtfilt(b, a, Hb, axis=0)
    env  = np.abs(scipy_signal.hilbert(Hb, axis=0)) + _EPS
    return (Hb / env).astype(np.float32)


# ── CHROM — de Haan & Jeanne, IEEE TBME 2013 ──────────────────────────────────

def chrom_filtered(RGB: np.ndarray, fps: float,
                   win_sec: float = 1.6,
                   bp_low:  float = 0.70,
                   bp_high: float = 3.0) -> np.ndarray:
    """
    CHROM raw signal with detrend + bandpass (amplitude preserved).
    Uses chrominance channels to separate blood-volume pulse from illumination.

    Xs = 3R − 2G
    Ys = 1.5R + G − 1.5B
    alpha = std(Xs) / std(Ys)  (per sliding window)
    H += Xs − alpha·Ys
    """
    RGB = np.asarray(RGB, dtype=np.float64)
    N   = RGB.shape[0]
    l   = max(math.ceil(win_sec * fps), 4)
    H   = np.zeros(N, dtype=np.float64)

    for m in range(N - l + 1):
        win = RGB[m:m + l, :]
        mu  = win.mean(axis=0, keepdims=True) + _EPS
        Cn  = win / mu                                  # (l, 3)
        R, G, B = Cn[:, 0], Cn[:, 1], Cn[:, 2]
        Xs = 3.0 * R - 2.0 * G
        Ys = 1.5 * R + G - 1.5 * B
        alpha  = (np.std(Xs) + _EPS) / (np.std(Ys) + _EPS)
        h      = Xs - alpha * Ys
        H[m:m + l] += h - h.mean()

    H    = scipy_signal.detrend(H, type="linear")
    nyq  = fps / 2.0
    lo   = float(np.clip(bp_low  / nyq, 1e-6, 1 - 1e-6))
    hi   = float(np.clip(bp_high / nyq, 1e-6, 1 - 1e-6))
    b, a = scipy_signal.butter(2, [lo, hi], btype="bandpass")
    H    = scipy_signal.filtfilt(b, a, H)
    return H.astype(np.float32)


def chrom_signal(RGB: np.ndarray, fps: float,
                 win_sec: float = 1.6,
                 bp_low:  float = 0.70,
                 bp_high: float = 3.0) -> np.ndarray:
    """CHROM + Hilbert envelope normalization (for spatial coherence maps)."""
    H   = chrom_filtered(RGB, fps, win_sec, bp_low, bp_high)
    env = np.abs(scipy_signal.hilbert(H)) + _EPS
    return (H / env).astype(np.float32)


# ── LGI — Pilz et al., CVPRW 2018 ─────────────────────────────────────────────

def lgi_filtered(RGB: np.ndarray, fps: float,
                 win_sec: float = 1.6,
                 bp_low:  float = 0.70,
                 bp_high: float = 3.0) -> np.ndarray:
    """
    LGI — Local Group Invariance (Pilz et al. 2018).
    Separates rPPG from illumination using PCA on normalised RGB windows.

    For each window: normalise by channel mean → covariance → project onto
    the second eigenvector (first = illumination, second = blood-volume pulse).
    Robust for darker skin tones compared to POS / CHROM.
    """
    RGB = np.asarray(RGB, dtype=np.float64)
    N   = RGB.shape[0]
    l   = max(math.ceil(win_sec * fps), 4)
    H   = np.zeros(N, dtype=np.float64)

    for m in range(N - l + 1):
        win = RGB[m:m + l, :]
        mu  = win.mean(axis=0, keepdims=True) + _EPS
        Cn  = win / mu                              # channel normalisation
        Cc  = Cn - Cn.mean(axis=0, keepdims=True)  # mean-centre
        cov = (Cc.T @ Cc) / l                       # 3×3 covariance
        _, evec = np.linalg.eigh(cov)              # eigenvalues ascending
        # evec[:,2] = largest (illumination), evec[:,1] = 2nd (pulse)
        h = Cc @ evec[:, 1]
        H[m:m + l] += h - h.mean()

    H    = scipy_signal.detrend(H, type="linear")
    nyq  = fps / 2.0
    lo   = float(np.clip(bp_low  / nyq, 1e-6, 1 - 1e-6))
    hi   = float(np.clip(bp_high / nyq, 1e-6, 1 - 1e-6))
    b, a = scipy_signal.butter(2, [lo, hi], btype="bandpass")
    H    = scipy_signal.filtfilt(b, a, H)
    return H.astype(np.float32)


def lgi_signal(RGB: np.ndarray, fps: float,
               win_sec: float = 1.6,
               bp_low:  float = 0.70,
               bp_high: float = 3.0) -> np.ndarray:
    """LGI + Hilbert envelope normalisation (uniform amplitude for spatial maps)."""
    H   = lgi_filtered(RGB, fps, win_sec, bp_low, bp_high)
    env = np.abs(scipy_signal.hilbert(H)) + _EPS
    return (H / env).astype(np.float32)


# ── HR estimation ──────────────────────────────────────────────────────────────

def hr_from_signal(sig: np.ndarray, fps: float,
                   hr_min: float = 30., hr_max: float = 200.) -> float:
    """Dominant frequency in [hr_min, hr_max] BPM → BPM."""
    freqs = np.fft.rfftfreq(len(sig), d=1.0 / fps)
    pwr   = np.abs(np.fft.rfft(sig.astype(np.float64))) ** 2
    mask  = (freqs >= hr_min / 60.) & (freqs <= hr_max / 60.)
    if not np.any(mask):
        return 60.
    return float(freqs[mask][np.argmax(pwr[mask])] * 60.)


# ── Helpers (kept for backward compatibility) ──────────────────────────────────

def bandpass_filter(signal: np.ndarray, fps: float,
                    low_hz: float = 0.7, high_hz: float = 3.5,
                    order: int = 4) -> np.ndarray:
    """Zero-phase Butterworth bandpass [low_hz, high_hz] Hz."""
    nyq  = fps / 2
    low  = max(low_hz  / nyq, 1e-4)
    high = min(high_hz / nyq, 1 - 1e-4)
    b, a = butter(order, [low, high], btype="band")
    return filtfilt(b, a, signal)


def spatial_average(frames: np.ndarray, mask: np.ndarray = None) -> np.ndarray:
    """
    Spatial average of video frames → temporal RGB signal (N, 3).
    frames : (N, H, W, 3) float32 [0, 1]
    """
    N = frames.shape[0]
    if mask is not None:
        pixels = frames[:, mask, :]          # (N, n_pixels, 3)
        return pixels.mean(axis=1)
    return frames.reshape(N, -1, 3).mean(axis=1)


# Backward-compatible alias
pos_algorithm = pos_wang2017_raw
