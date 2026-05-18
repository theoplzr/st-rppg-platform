"""
core/signal_quality.py
──────────────────────
rPPG signal quality metrics:
  - Heart rate estimation (FFT)
  - Sliding SNR
  - TMS (Template Matching Score)
  - Global quality score
"""

import numpy as np
from scipy.signal import find_peaks, welch
from scipy.stats import pearsonr


# ─── Heart rate estimation ─────────────────────────────────────────────────────

def estimate_hr_fft(signal: np.ndarray, fps: float,
                    low_hz: float = 0.7, high_hz: float = 3.5) -> dict:
    """
    Heart rate estimation via FFT: dominant peak in the physiological range.
    Returns hr_bpm, hr_hz, peak_power, snr_spectral, freq, fft arrays.
    """
    N = len(signal)
    win = np.hanning(N)
    fft = np.abs(np.fft.rfft(signal * win))
    freq = np.fft.rfftfreq(N, d=1.0 / fps)

    mask = (freq >= low_hz) & (freq <= high_hz)
    freq_hr = freq[mask]
    fft_hr = fft[mask]

    if len(fft_hr) == 0:
        return {"hr_bpm": None, "hr_hz": None, "peak_power": 0,
                "freq": freq.tolist(), "fft": fft.tolist()}

    idx_peak = np.argmax(fft_hr)
    hr_hz = float(freq_hr[idx_peak])
    hr_bpm = hr_hz * 60

    # Spectral SNR: peak power / total power outside the peak band
    bw = 0.1
    mask_sig = np.abs(freq - hr_hz) < bw
    p_sig = (fft ** 2)[mask_sig].sum()
    p_tot = (fft ** 2).sum()
    snr_spectral = 10 * np.log10(p_sig / (p_tot - p_sig + 1e-12))

    return {
        "hr_bpm":       round(hr_bpm, 1),
        "hr_hz":        round(hr_hz, 4),
        "peak_power":   float(fft_hr[idx_peak]),
        "snr_spectral": round(snr_spectral, 2),
        "freq":         freq.tolist(),
        "fft":          fft.tolist(),
        "freq_hr":      freq_hr.tolist(),
        "fft_hr":       fft_hr.tolist(),
    }


# ─── Sliding SNR ───────────────────────────────────────────────────────────────

def compute_snr_sliding(signal: np.ndarray, fps: float,
                        hr_hz: float,
                        window_sec: float = 5.0,
                        step_sec: float = 1.0,
                        bw: float = 0.15) -> dict:
    """
    Sliding-window SNR computed over window_sec-second segments.
    SNR = 10 * log10(P_signal / P_noise)
    P_signal covers HR and 2nd harmonic ± bw Hz.
    """
    win_n = int(window_sec * fps)
    step_n = int(step_sec * fps)
    N = len(signal)
    snr_values = []
    time_axis = []

    for start in range(0, N - win_n + 1, step_n):
        seg = signal[start: start + win_n]
        fft = np.abs(np.fft.rfft(seg * np.hanning(win_n))) ** 2
        freq = np.fft.rfftfreq(win_n, d=1.0 / fps)

        mask_sig = np.zeros(len(freq), dtype=bool)
        for k in [1, 2]:
            mask_sig |= (np.abs(freq - k * hr_hz) < bw)

        p_sig = fft[mask_sig].sum()
        p_noise = fft[~mask_sig].sum()
        snr = 10 * np.log10(p_sig / (p_noise + 1e-12))
        snr_values.append(round(float(snr), 3))
        time_axis.append(round((start + win_n // 2) / fps, 3))

    snr_arr = np.array(snr_values)
    return {
        "snr":      snr_values,
        "time":     time_axis,
        "mean_snr": round(float(snr_arr.mean()), 2) if len(snr_arr) else 0,
        "min_snr":  round(float(snr_arr.min()), 2) if len(snr_arr) else 0,
        "std_snr":  round(float(snr_arr.std()), 2) if len(snr_arr) else 0,
    }


# ─── Template Matching Score ───────────────────────────────────────────────────

def compute_tms(signal: np.ndarray, fps: float,
                hr_hz: float) -> dict:
    """
    Template Matching Score (TMS): measures morphological consistency of PPG cycles.
    Each cycle is resampled to 100 points and correlated with the mean template.
    Returns tms in [0, 1] and is_clean flag (threshold: 0.96).
    """
    if hr_hz is None or hr_hz <= 0:
        return {"tms": 0.0, "is_clean": False, "n_cycles": 0}

    cycle_len = int(fps / hr_hz)
    if cycle_len < 3:
        return {"tms": 0.0, "is_clean": False, "n_cycles": 0}

    n_points = 100
    cycles = []

    for start in range(0, len(signal) - cycle_len, cycle_len):
        cycle = signal[start: start + cycle_len]
        # Resample to n_points via linear interpolation
        x_old = np.linspace(0, 1, len(cycle))
        x_new = np.linspace(0, 1, n_points)
        cycle_resampled = np.interp(x_new, x_old, cycle)
        cycles.append(cycle_resampled)

    if len(cycles) < 2:
        return {"tms": 0.0, "is_clean": False, "n_cycles": 0}

    cycles = np.array(cycles)
    template = cycles.mean(axis=0)

    correlations = []
    for c in cycles:
        if c.std() < 1e-8 or template.std() < 1e-8:
            continue
        r, _ = pearsonr(c, template)
        correlations.append(r)

    if not correlations:
        return {"tms": 0.0, "is_clean": False, "n_cycles": 0}

    tms = float(np.mean(correlations))
    return {
        "tms":      round(tms, 4),
        "is_clean": tms >= 0.96,
        "n_cycles": len(cycles),
    }


# ─── Global quality score ──────────────────────────────────────────────────────

def quality_score(mean_snr: float, tms: float, fps: float) -> dict:
    """
    Composite quality score (0–100) combining SNR, TMS, and frame rate.
    Returns label, color, score, and actionable recommendations.
    """
    # Each component linearly scaled to its contribution ceiling.
    # SNR bounds align with ai_interpretation thresholds: 0..10 dB → 0..40 pts.
    snr_score = min(max(mean_snr / 10.0 * 40, 0), 40)    # SNR 0..10 dB → 0..40
    tms_score = min(max((tms - 0.8) / 0.2 * 40, 0), 40)  # TMS 0.8..1.0  → 0..40
    fps_score = min(max((fps - 15) / 35 * 20, 0), 20)     # FPS 15..50    → 0..20

    score = int(snr_score + tms_score + fps_score)

    if score >= 70:
        label, color = "EXCELLENT", "#7ee787"
    elif score >= 50:
        label, color = "GOOD", "#00c8ff"
    elif score >= 30:
        label, color = "POOR", "#f0883e"
    else:
        label, color = "BAD", "#f85149"

    recommendations = []
    if mean_snr < 0:
        recommendations.append("Vérifiez l'éclairage (LEDs vertes recommandées)")
        recommendations.append("Réduisez les artefacts de mouvement")
    if tms < 0.96:
        recommendations.append("Morphologie du signal instable — stabilisez la caméra")
    if fps < 25:
        recommendations.append("Fréquence d'images insuffisante (minimum 25 Hz)")

    return {
        "score":           score,
        "label":           label,
        "color":           color,
        "recommendations": recommendations,
    }


# ─── Full quality report ───────────────────────────────────────────────────────

def full_quality_report(signal_raw: np.ndarray,
                        signal_filt: np.ndarray,
                        fps: float,
                        rgb_signal: np.ndarray = None) -> dict:
    """
    Full quality report from the filtered POS signal.
    Returns a JSON-serializable dict.
    """
    hr_info  = estimate_hr_fft(signal_filt, fps)
    hr_hz    = hr_info.get("hr_hz") or 1.2

    snr_info = compute_snr_sliding(signal_filt, fps, hr_hz)
    tms_info = compute_tms(signal_filt, fps, hr_hz)
    qual     = quality_score(snr_info["mean_snr"], tms_info["tms"], fps)

    # Peak detection on normalized signal
    peaks, _ = find_peaks(signal_filt / (np.abs(signal_filt).max() + 1e-8),
                          distance=int(fps * 0.4), height=0.2)

    # Normalize signals to [-1, 1] for display
    sig_max  = np.abs(signal_filt).max() + 1e-8
    sig_norm = (signal_filt / sig_max).tolist()
    raw_norm = (signal_raw / (np.abs(signal_raw).max() + 1e-8)).tolist()

    t_axis = (np.arange(len(signal_filt)) / fps).tolist()

    report = {
        "hr":      hr_info,
        "snr":     snr_info,
        "tms":     tms_info,
        "quality": qual,
        "signal": {
            "raw":   raw_norm,
            "filt":  sig_norm,
            "time":  t_axis,
            "peaks": peaks.tolist(),
        },
    }

    if rgb_signal is not None:
        for ch, name in enumerate(["R", "G", "B"]):
            ch_sig  = rgb_signal[:, ch].astype(float)
            ch_norm = (ch_sig - ch_sig.mean()) / (ch_sig.std() + 1e-8)
            report[f"rgb_{name}"] = ch_norm.tolist()

    return report
