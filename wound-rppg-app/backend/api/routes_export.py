"""api/routes_export.py"""
import csv
import io
import json
import logging
from flask import Blueprint, jsonify, send_file
from core.session_manager import load_results
from api.validation import reject_invalid_session

log = logging.getLogger(__name__)
bp_export = Blueprint("export", __name__)

_ERR_500 = {"error": "Internal error. Check server logs."}


@bp_export.get("/<session_name>/json")
def export_json(session_name):
    err = reject_invalid_session(session_name)
    if err:
        return err
    try:
        results = load_results(session_name)
        buf = io.BytesIO(json.dumps(results, indent=2).encode())
        buf.seek(0)
        return send_file(buf, mimetype="application/json",
                         download_name=f"{session_name}_results.json",
                         as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "Results not found."}), 404
    except Exception:
        log.exception("export_json failed session=%s", session_name)
        return jsonify(_ERR_500), 500


@bp_export.get("/<session_name>/csv")
def export_csv(session_name):
    """
    Full CSV export with four sections:
      [metrics]     — scalar values (HR, SNR, TMS, quality score)
      [signal]      — filtered and raw signal over the time axis
      [snr_sliding] — sliding SNR (time, snr_db)
      [fft]         — power spectrum (freq_hz, power)
    """
    err = reject_invalid_session(session_name)
    if err:
        return err
    try:
        results = load_results(session_name)
    except FileNotFoundError:
        return jsonify({"error": "Results not found."}), 404
    except Exception:
        log.exception("export_csv load failed session=%s", session_name)
        return jsonify(_ERR_500), 500

    hr   = results.get("hr",      {})
    snr  = results.get("snr",     {})
    tms  = results.get("tms",     {})
    qual = results.get("quality", {})
    sig  = results.get("signal",  {})

    buf = io.StringIO()
    w   = csv.writer(buf)

    # ── Scalar metrics ───────────────────────────────────────────────────────
    w.writerow(["[metrics]"])
    w.writerow(["metric", "value"])
    w.writerow(["session",       session_name])
    w.writerow(["hr_bpm",        hr.get("hr_bpm")])
    w.writerow(["hr_hz",         hr.get("hr_hz")])
    w.writerow(["snr_mean_db",   snr.get("mean_snr")])
    w.writerow(["snr_min_db",    snr.get("min_snr")])
    w.writerow(["snr_std_db",    snr.get("std_snr")])
    w.writerow(["tms",           tms.get("tms")])
    w.writerow(["tms_is_clean",  tms.get("is_clean")])
    w.writerow(["tms_n_cycles",  tms.get("n_cycles")])
    w.writerow(["quality_score", qual.get("score")])
    w.writerow(["quality_label", qual.get("label")])
    w.writerow(["fps",           results.get("fps")])
    w.writerow(["n_frames",      results.get("n_frames")])
    w.writerow([])

    # ── Temporal signal (filtered + raw) ─────────────────────────────────────
    t_axis   = sig.get("time",  [])
    sig_filt = sig.get("filt",  [])
    sig_raw  = sig.get("raw",   [])
    peaks    = set(sig.get("peaks", []))

    if t_axis:
        w.writerow(["[signal]"])
        w.writerow(["time_s", "signal_filtered", "signal_raw", "is_peak"])
        for i, t in enumerate(t_axis):
            w.writerow([
                round(t, 4),
                round(sig_filt[i], 6) if i < len(sig_filt) else "",
                round(sig_raw[i],  6) if i < len(sig_raw)  else "",
                1 if i in peaks else 0,
            ])
        w.writerow([])

    # ── Sliding SNR ───────────────────────────────────────────────────────────
    snr_times  = snr.get("time", [])
    snr_values = snr.get("snr",  [])

    if snr_times:
        w.writerow(["[snr_sliding]"])
        w.writerow(["time_s", "snr_db"])
        for t, s in zip(snr_times, snr_values):
            w.writerow([round(t, 3), round(s, 3)])
        w.writerow([])

    # ── Power spectrum ────────────────────────────────────────────────────────
    freq_all = hr.get("freq", [])
    fft_all  = hr.get("fft",  [])

    if freq_all:
        w.writerow(["[fft]"])
        w.writerow(["freq_hz", "power"])
        for f, p in zip(freq_all, fft_all):
            w.writerow([round(f, 4), round(p, 6)])
        w.writerow([])

    buf.seek(0)
    out = io.BytesIO(buf.getvalue().encode("utf-8"))
    return send_file(out, mimetype="text/csv",
                     download_name=f"{session_name}_metrics.csv",
                     as_attachment=True)


@bp_export.get("/<session_name>/pdf")
def export_pdf(session_name):
    """Generate and download a clinical PDF report for the session."""
    err = reject_invalid_session(session_name)
    if err:
        return err
    try:
        from core.pdf_report import generate_pdf
        results = load_results(session_name)
        pdf_bytes = generate_pdf(session_name, results)
        buf = io.BytesIO(pdf_bytes)
        buf.seek(0)
        return send_file(
            buf,
            mimetype="application/pdf",
            download_name=f"{session_name}_report.pdf",
            as_attachment=True,
        )
    except FileNotFoundError:
        return jsonify({"error": "Results not found — run analysis first."}), 404
    except Exception:
        log.exception("export_pdf failed session=%s", session_name)
        return jsonify(_ERR_500), 500
