"""
core/signal_quality.py
──────────────────────
rPPG signal quality metrics:
  - Heart rate estimation (FFT)
  - Sliding SNR
  - TMS (Template Matching Score)
  - Respiratory rate from green channel
  - HRV (SDNN, RMSSD, pNN50)
  - Motion artifact detection (inter-frame diff)
  - STFT spectrogram
  - Global quality score
"""

import numpy as np
from scipy.signal import find_peaks, welch, stft as scipy_stft, butter, filtfilt
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

_BP_LOW  = 0.7   # cardiac band lower bound (Hz)
_BP_HIGH = 3.0   # cardiac band upper bound (Hz)


def compute_snr_sliding(signal: np.ndarray, fps: float,
                        hr_hz: float,
                        window_sec: float = 8.0,
                        step_sec: float = 1.0,
                        bw: float = 0.2) -> dict:
    """
    Sliding-window SNR — P(HR + 2HR) / P(cardiac band noise).
    Noise is measured ONLY within the cardiac band [0.7, 3.0] Hz so that
    out-of-band content (DC, respiration) does not artificially inflate noise.
    window_sec=8 gives ≥10 cardiac cycles per window for stable spectral estimate.
    """
    win_n  = max(int(window_sec * fps), 32)
    step_n = max(int(step_sec   * fps), 1)
    N = len(signal)
    snr_values = []
    time_axis  = []

    for start in range(0, N - win_n + 1, step_n):
        seg  = signal[start: start + win_n]
        pwr  = np.abs(np.fft.rfft(seg * np.hanning(win_n))) ** 2
        freq = np.fft.rfftfreq(win_n, d=1.0 / fps)

        # Restrict to cardiac band
        band     = (freq >= _BP_LOW) & (freq <= _BP_HIGH)
        pwr_band = pwr[band]
        frq_band = freq[band]
        if pwr_band.size < 3:
            continue

        # Signal bins: HR fundamental + 2nd harmonic
        mask_sig = np.zeros(pwr_band.size, dtype=bool)
        for k in [1, 2]:
            mask_sig |= (np.abs(frq_band - k * hr_hz) < bw)

        p_sig   = pwr_band[mask_sig].sum()
        p_noise = pwr_band[~mask_sig].sum()
        if p_noise < 1e-12:
            continue
        snr = 10.0 * np.log10(p_sig / p_noise)
        snr_values.append(round(float(snr), 3))
        time_axis.append(round((start + win_n // 2) / fps, 3))

    snr_arr = np.array(snr_values) if snr_values else np.array([0.0])
    return {
        "snr":      snr_values,
        "time":     time_axis,
        "mean_snr": round(float(snr_arr.mean()), 2),
        "min_snr":  round(float(snr_arr.min()),  2),
        "std_snr":  round(float(snr_arr.std()),  2),
    }


# ─── Template Matching Score ───────────────────────────────────────────────────

def compute_tms(signal: np.ndarray, fps: float,
                hr_hz: float) -> dict:
    """
    Template Matching Score (TMS): morphological consistency of PPG cycles.
    Cycles are segmented between consecutive detected peaks (avoids integer
    cycle-length drift). Each cycle is resampled to 100 pts then Pearson-
    correlated with the mean template.
    """
    if hr_hz is None or hr_hz <= 0:
        return {"tms": 0.0, "is_clean": False, "n_cycles": 0}

    # Expected samples between peaks ± 40% tolerance
    expected = fps / hr_hz
    min_dist = int(expected * 0.60)

    peaks, _ = find_peaks(signal, distance=min_dist, height=0)
    if len(peaks) < 3:
        # Fallback: uniform segmentation with float step (no drift)
        step = fps / hr_hz                       # exact float step
        starts = np.arange(0, len(signal) - step, step)
        peaks_fb = np.round(starts).astype(int)
        peaks = peaks_fb[peaks_fb + int(step) < len(signal)]
        if len(peaks) < 2:
            return {"tms": 0.0, "is_clean": False, "n_cycles": 0}

    n_points = 100
    cycles = []
    for i in range(len(peaks) - 1):
        seg = signal[peaks[i]: peaks[i + 1]]
        if len(seg) < 4:
            continue
        x_old = np.linspace(0, 1, len(seg))
        x_new = np.linspace(0, 1, n_points)
        cycles.append(np.interp(x_new, x_old, seg))

    if len(cycles) < 2:
        return {"tms": 0.0, "is_clean": False, "n_cycles": 0}

    cycles   = np.array(cycles)
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


# ─── Respiratory rate ──────────────────────────────────────────────────────────

def estimate_respiratory_rate(rgb_signal: np.ndarray, fps: float,
                               low_hz: float = 0.15,
                               high_hz: float = 0.50) -> dict:
    """
    Estimate respiratory rate from the low-frequency component of the green
    channel.  Typical range: 0.15–0.50 Hz (9–30 breaths/min).
    rgb_signal : (N, 3) mean RGB per frame
    """
    if rgb_signal is None or rgb_signal.ndim != 2:
        return {"rr_bpm": None, "rr_hz": None}

    g = rgb_signal[:, 1].astype(np.float64)
    g -= g.mean()

    nyq = fps / 2.0
    lo  = max(low_hz  / nyq, 1e-4)
    hi  = min(high_hz / nyq, 1 - 1e-4)
    b, a = butter(3, [lo, hi], btype="bandpass")
    try:
        g_resp = filtfilt(b, a, g)
    except Exception:
        return {"rr_bpm": None, "rr_hz": None}

    N    = len(g_resp)
    win  = np.hanning(N)
    fft  = np.abs(np.fft.rfft(g_resp * win)) ** 2
    freq = np.fft.rfftfreq(N, d=1.0 / fps)
    mask = (freq >= low_hz) & (freq <= high_hz)
    if not np.any(mask):
        return {"rr_bpm": None, "rr_hz": None}

    rr_hz  = float(freq[mask][np.argmax(fft[mask])])
    rr_bpm = round(rr_hz * 60.0, 1)
    return {
        "rr_bpm": rr_bpm,
        "rr_hz":  round(rr_hz, 4),
        "signal": g_resp.tolist(),
    }


# ─── HRV — Heart Rate Variability ─────────────────────────────────────────────

def compute_hrv(signal_filt: np.ndarray, fps: float, hr_hz: float) -> dict:
    """
    HRV from detected PPG peaks: SDNN, RMSSD, pNN50.
    Requires at least 5 peaks for meaningful estimates.
    """
    if hr_hz is None or hr_hz <= 0:
        return {"sdnn_ms": None, "rmssd_ms": None, "pnn50": None, "n_peaks": 0}

    min_dist = int(fps / hr_hz * 0.6)
    norm = signal_filt / (np.abs(signal_filt).max() + 1e-8)
    peaks, _ = find_peaks(norm, distance=min_dist, height=0.15)

    if len(peaks) < 5:
        return {"sdnn_ms": None, "rmssd_ms": None, "pnn50": None, "n_peaks": len(peaks)}

    rr_s    = np.diff(peaks) / fps              # RR intervals in seconds
    rr_ms   = rr_s * 1000.0                     # convert to ms

    sdnn    = float(np.std(rr_ms))
    rmssd   = float(np.sqrt(np.mean(np.diff(rr_ms) ** 2)))
    pnn50   = float(100.0 * np.sum(np.abs(np.diff(rr_ms)) > 50) / len(rr_ms))

    return {
        "sdnn_ms":  round(sdnn,  1),
        "rmssd_ms": round(rmssd, 1),
        "pnn50":    round(pnn50, 1),
        "n_peaks":  len(peaks),
        "rr_ms":    rr_ms.tolist(),
    }


# ─── Motion artifact detection ────────────────────────────────────────────────

def detect_motion_artifacts(frames: np.ndarray,
                             threshold_sigma: float = 2.5) -> dict:
    """
    Detect motion-corrupted frames via inter-frame absolute difference on the
    green channel.  Frames whose diff > mean + threshold_sigma × std are flagged.

    frames : (N, H, W, 3) float32 [0, 1]
    Returns: bad_frames (list of int indices), pct_bad, severity label,
             diff_signal for display.
    """
    if frames.ndim != 4 or frames.shape[0] < 2:
        return {"bad_frames": [], "pct_bad": 0.0, "severity": "none", "diff": []}

    green   = frames[:, :, :, 1]                        # (N, H, W)
    diff    = np.abs(np.diff(green, axis=0)).mean(axis=(1, 2))   # (N-1,)
    mu, sigma = diff.mean(), diff.std()
    thr     = mu + threshold_sigma * sigma

    bad_idx = np.where(diff > thr)[0].tolist()          # frame index (0-based)
    pct_bad = round(100.0 * len(bad_idx) / len(diff), 1)

    if pct_bad == 0:
        severity = "none"
    elif pct_bad < 5:
        severity = "low"
    elif pct_bad < 15:
        severity = "moderate"
    else:
        severity = "high"

    return {
        "bad_frames": bad_idx,
        "n_bad":      len(bad_idx),
        "pct_bad":    pct_bad,
        "severity":   severity,
        "threshold":  round(float(thr), 6),
        "diff":       diff.tolist(),
    }


# ─── STFT Spectrogram ─────────────────────────────────────────────────────────

def compute_stft(signal_filt: np.ndarray, fps: float,
                 nperseg_sec: float = 8.0,
                 noverlap_ratio: float = 0.875,
                 max_hz: float = 4.0) -> dict:
    """
    Short-Time Fourier Transform of the POS signal.
    Returns time/freq/power arrays downsampled for JSON transfer.

    nperseg_sec=8 → 8-second window (same as SNR window, ~10 cycles at 75 bpm).
    noverlap_ratio=0.875 → 87.5% overlap for smooth time resolution.
    """
    nperseg  = min(int(nperseg_sec * fps), len(signal_filt))
    noverlap = int(nperseg * noverlap_ratio)
    nfft     = max(nperseg, 256)

    f, t, Zxx = scipy_stft(
        signal_filt.astype(np.float64),
        fs=fps,
        window="hann",
        nperseg=nperseg,
        noverlap=noverlap,
        nfft=nfft,
    )

    # Keep only cardiac-relevant frequencies (0.3 – max_hz Hz)
    freq_mask = (f >= 0.3) & (f <= max_hz)
    f_crop = f[freq_mask]
    power  = np.abs(Zxx[freq_mask]) ** 2

    # Log-scale power, clip for display
    log_power = 10.0 * np.log10(power + 1e-12)
    p2, p98   = np.percentile(log_power, 2), np.percentile(log_power, 98)
    log_norm  = np.clip((log_power - p2) / (p98 - p2 + 1e-8), 0.0, 1.0)

    return {
        "time":     [round(float(v), 3) for v in t],
        "freq":     [round(float(v), 4) for v in f_crop],
        "power":    log_norm.tolist(),
    }


# ─── Global quality score ──────────────────────────────────────────────────────

def quality_score(mean_snr: float, tms: float, fps: float) -> dict:
    """
    Composite quality score (0–100) combining SNR, TMS, and frame rate.
    Returns label, color, score, and actionable recommendations.
    """
    # SNR (cardiac-band):  0..8 dB  → 0..40 pts  (0 dB = weak but detectable, 8 dB = excellent)
    # TMS:                0.6..1.0 → 0..40 pts  (0.96 kept for is_clean flag)
    # FPS:               15..50   → 0..20 pts
    snr_score = min(max(mean_snr / 8.0 * 40, 0), 40)
    tms_score = min(max((tms - 0.6) / 0.4 * 40, 0), 40)
    fps_score = min(max((fps - 15)  / 35.0 * 20, 0), 20)

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


# ─── Bootstrap confidence intervals ──────────────────────────────────────────

def bootstrap_ci(signal_filt: np.ndarray, fps: float,
                 win_sec: float = 8.0,
                 n_boot: int = 60,
                 ci_pct: float = 95.0) -> dict | None:
    """
    Window-bootstrap CI for HR estimation.
    Estimates HR from n_boot random sub-windows of the signal and returns
    mean ± confidence interval, which reflects temporal HR stability.
    """
    L       = len(signal_filt)
    win_len = min(int(win_sec * fps), L)
    if win_len < 32 or L < win_len:
        return None

    rng      = np.random.default_rng(0)
    boot_hrs = []
    for _ in range(n_boot):
        start = int(rng.integers(0, L - win_len + 1))
        win   = signal_filt[start: start + win_len]
        info  = estimate_hr_fft(win, fps)
        hr    = info.get("hr_bpm")
        if hr:
            boot_hrs.append(hr)

    if len(boot_hrs) < 5:
        return None

    alpha = (100.0 - ci_pct) / 2.0
    hrs   = np.array(boot_hrs)
    return {
        "hr_mean":   round(float(hrs.mean()), 1),
        "hr_std":    round(float(hrs.std()),  1),
        "hr_ci_lo":  round(float(np.percentile(hrs, alpha)),         1),
        "hr_ci_hi":  round(float(np.percentile(hrs, 100.0 - alpha)), 1),
        "n_windows": len(boot_hrs),
        "ci_pct":    ci_pct,
    }


# ─── Full quality report ───────────────────────────────────────────────────────

def full_quality_report(signal_raw: np.ndarray,
                        signal_filt: np.ndarray,
                        fps: float,
                        rgb_signal: np.ndarray = None,
                        frames: np.ndarray = None) -> dict:
    """
    Full quality report from the filtered POS signal.
    Returns a JSON-serializable dict.
    """
    hr_info   = estimate_hr_fft(signal_filt, fps)
    hr_hz     = hr_info.get("hr_hz") or 1.2

    snr_info  = compute_snr_sliding(signal_filt, fps, hr_hz)
    tms_info  = compute_tms(signal_filt, fps, hr_hz)
    qual      = quality_score(snr_info["mean_snr"], tms_info["tms"], fps)
    hrv_info  = compute_hrv(signal_filt, fps, hr_hz)
    stft_info = compute_stft(signal_filt, fps)
    ci_info   = bootstrap_ci(signal_filt, fps)

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
        "hrv":     hrv_info,
        "stft":    stft_info,
        "hr_ci":   ci_info,
        "signal": {
            "raw":   raw_norm,
            "filt":  sig_norm,
            "time":  t_axis,
            "peaks": peaks.tolist(),
        },
    }

    if rgb_signal is not None:
        report["respiration"] = estimate_respiratory_rate(rgb_signal, fps)
        for ch, name in enumerate(["R", "G", "B"]):
            ch_sig  = rgb_signal[:, ch].astype(float)
            ch_norm = (ch_sig - ch_sig.mean()) / (ch_sig.std() + 1e-8)
            report[f"rgb_{name}"] = ch_norm.tolist()

    if frames is not None:
        report["motion"] = detect_motion_artifacts(frames)

    return report
