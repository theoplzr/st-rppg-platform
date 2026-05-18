"""
core/pos_algorithm.py
─────────────────────
POS (Plane-Orthogonal-to-Skin) rPPG algorithm.
Reference: Wang et al., IEEE TBME 2017. DOI: 10.1109/TBME.2016.2610512
Projection matrix: [[0, 1, -1], [-2, 1, 1]] — Eq. (4) of the paper.
Input  : temporal RGB signal (N, 3)
Output : rPPG signal (N,)
"""

import numpy as np
from scipy.signal import butter, filtfilt


def pos_algorithm(rgb_signal: np.ndarray, fps: float,
                  window_sec: float = 1.6) -> np.ndarray:
    """
    POS algorithm with sliding window and OLA (Overlap-Add) normalization.

    Parameters
    ----------
    rgb_signal  : (N, 3) — temporal R, G, B channel means
    fps         : sampling frequency (Hz)
    window_sec  : sliding window length (s)

    Returns
    -------
    H : (N,) — raw rPPG signal
    """
    N = len(rgb_signal)
    l = max(int(fps * window_sec), 2)

    # POS projection matrix
    P = np.array([[0, 1, -1],
                  [-2, 1,  1]], dtype=np.float64)

    H = np.zeros(N)
    W = np.zeros(N)  # accumulated weights for OLA normalization
    win = np.hanning(l)

    for n in range(l, N + 1):
        C = rgb_signal[n - l: n].T.astype(np.float64)  # (3, l)
        mu = C.mean(axis=1, keepdims=True)
        mu = np.where(mu == 0, 1e-6, mu)
        Cn = C / mu

        S = P @ Cn  # (2, l)

        std1 = S[0].std()
        std2 = S[1].std()
        alpha = std1 / (std2 + 1e-6)

        h = S[0] + alpha * S[1]
        H[n - l: n] += h * win
        W[n - l: n] += win

    # OLA normalization: divide by accumulated window weights
    W = np.where(W < 1e-8, 1.0, W)
    return H / W


def bandpass_filter(signal: np.ndarray, fps: float,
                    low_hz: float = 0.7, high_hz: float = 3.5,
                    order: int = 4) -> np.ndarray:
    """
    Zero-phase Butterworth bandpass filter [low_hz, high_hz] Hz.
    Physiological range: 0.7–3.5 Hz = 42–210 bpm.
    """
    nyq = fps / 2
    low = max(low_hz / nyq, 1e-4)
    high = min(high_hz / nyq, 1 - 1e-4)
    b, a = butter(order, [low, high], btype="band")
    return filtfilt(b, a, signal)


def spatial_average(frames: np.ndarray, mask: np.ndarray = None) -> np.ndarray:
    """
    Spatial average of video frames → temporal RGB signal (N, 3).

    Parameters
    ----------
    frames : (N, H, W, 3) float32 [0, 1]
    mask   : (H, W) bool, optional — region of interest

    Returns
    -------
    rgb : (N, 3)
    """
    N = frames.shape[0]
    if mask is not None:
        pixels = frames[:, mask, :]  # (N, n_pixels, 3)
        return pixels.mean(axis=1)
    return frames.reshape(N, -1, 3).mean(axis=1)
