"""
core/pdf_report.py
──────────────────
Generate a clinical PDF report for a single ST-rPPG session.

Uses reportlab (already in requirements.txt).
Fonts: Helvetica (built-in, no external files needed).
"""

import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.platypus import Image as RLImage
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import base64


# ── Colour palette ─────────────────────────────────────────────────────────────
_ACCENT  = colors.HexColor("#e8622a")
_TEAL    = colors.HexColor("#06b6d4")
_GREEN   = colors.HexColor("#22d47e")
_WARN    = colors.HexColor("#f59e0b")
_DANGER  = colors.HexColor("#ef4444")
_BG      = colors.HexColor("#0a0a12")
_SURFACE = colors.HexColor("#14141e")
_BORDER  = colors.HexColor("#252535")
_TEXT    = colors.HexColor("#e8e8f0")
_MUTED   = colors.HexColor("#7070a0")
_WHITE   = colors.white

PAGE_W, PAGE_H = A4


def _styles():
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("h1", fontName="Helvetica-Bold",
                             fontSize=18, textColor=_TEXT,
                             spaceAfter=4, spaceBefore=0),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold",
                             fontSize=11, textColor=_ACCENT,
                             spaceAfter=4, spaceBefore=10),
        "h3": ParagraphStyle("h3", fontName="Helvetica-Bold",
                             fontSize=9, textColor=_TEXT,
                             spaceAfter=2, spaceBefore=6),
        "body": ParagraphStyle("body", fontName="Helvetica",
                               fontSize=9, textColor=_TEXT,
                               spaceAfter=3, leading=14),
        "small": ParagraphStyle("small", fontName="Helvetica",
                                fontSize=7.5, textColor=_MUTED,
                                spaceAfter=2),
        "mono": ParagraphStyle("mono", fontName="Courier",
                               fontSize=8, textColor=_TEAL,
                               spaceAfter=2),
        "center": ParagraphStyle("center", fontName="Helvetica",
                                 fontSize=9, textColor=_TEXT,
                                 alignment=TA_CENTER, spaceAfter=2),
    }


def _hr(width=None):
    return HRFlowable(width=width or "100%", thickness=0.5,
                      color=_BORDER, spaceAfter=6, spaceBefore=4)


def _metric_table(rows, col_widths=None):
    """Build a small 2-column metric table."""
    col_widths = col_widths or [5 * cm, 9 * cm]
    tbl = Table(rows, colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ("FONTNAME",    (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR",  (0, 0), (0, -1),  _MUTED),
        ("TEXTCOLOR",  (1, 0), (1, -1),  _TEXT),
        ("FONTNAME",   (1, 0), (1, -1),  "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [_SURFACE, _BG]),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("GRID",       (0, 0), (-1, -1), 0.3, _BORDER),
        ("ROUNDEDCORNERS", [4]),
    ]))
    return tbl


def _algo_table(result: dict):
    """POS / CHROM / LGI comparison table."""
    hr  = result.get("hr", {})
    chrom = result.get("chrom", {})
    lgi   = result.get("lgi", {})
    snr   = result.get("snr", {})

    def _fmt(v, unit=""):
        return f"{v}{unit}" if v is not None else "—"

    rows = [
        ["Algorithme", "HR estimée", "SNR moyen"],
        ["POS (Wang 2017)",   _fmt(hr.get("hr_bpm"), " bpm"),    _fmt(snr.get("mean_snr"), " dB")],
        ["CHROM (de Haan 2013)", _fmt(chrom.get("hr_bpm"), " bpm"), _fmt(chrom.get("snr_db"), " dB")],
        ["LGI (Pilz 2018)",   _fmt(lgi.get("hr_bpm"), " bpm"),   _fmt(lgi.get("snr_db"), " dB")],
    ]
    tbl = Table(rows, colWidths=[6 * cm, 4.5 * cm, 4.5 * cm])
    tbl.setStyle(TableStyle([
        ("FONTNAME",     (0, 0), (-1, 0),   "Helvetica-Bold"),
        ("FONTNAME",     (0, 1), (-1, -1),  "Helvetica"),
        ("FONTSIZE",     (0, 0), (-1, -1),  8.5),
        ("TEXTCOLOR",   (0, 0), (-1, 0),   _MUTED),
        ("TEXTCOLOR",   (1, 1), (-1, -1),  _ACCENT),
        ("BACKGROUND",  (0, 0), (-1, 0),   _SURFACE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_BG, _SURFACE]),
        ("TOPPADDING",   (0, 0), (-1, -1),  4),
        ("BOTTOMPADDING",(0, 0), (-1, -1),  4),
        ("LEFTPADDING",  (0, 0), (-1, -1),  8),
        ("GRID",        (0, 0), (-1, -1),   0.3, _BORDER),
        ("ALIGN",       (1, 0), (-1, -1),   "CENTER"),
    ]))
    return tbl


def _b64_to_rl_image(b64_data_uri: str, width_cm: float) -> RLImage | None:
    """Convert a base64 data URI to a ReportLab Image flowable."""
    try:
        _, b64 = b64_data_uri.split(",", 1)
        raw  = base64.b64decode(b64)
        buf  = io.BytesIO(raw)
        img  = RLImage(buf, width=width_cm * cm)
        return img
    except Exception:
        return None


def generate_pdf(session_name: str, result: dict) -> bytes:
    """
    Generate a PDF report for a session and return it as bytes.

    Parameters
    ----------
    session_name : str
    result       : dict — the full analysis result (from load_results or analyze_session)
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    S = _styles()
    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("ST-rPPG WOUND PLATFORM", S["small"]))
    story.append(Paragraph(f"Rapport d'analyse — {session_name}", S["h1"]))
    meta = result.get("meta", {})
    date_str = meta.get("date", "")
    if date_str:
        try:
            date_str = datetime.fromisoformat(date_str).strftime("%d/%m/%Y %H:%M")
        except Exception:
            pass
    story.append(Paragraph(
        f"Session : <font color='#e8622a'><b>{session_name}</b></font> · "
        f"Date : {date_str} · "
        f"Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        S["small"],
    ))
    story.append(_hr())

    # ── Quality badge ─────────────────────────────────────────────────────────
    qual = result.get("quality", {})
    heal = result.get("healing_score", {})
    q_score = qual.get("score", "—")
    q_label = qual.get("label", "—")
    h_score = heal.get("score", "—") if heal else "—"
    h_label = heal.get("label", "—") if heal else "—"

    badge_rows = [
        ["Score qualité signal", str(q_score), q_label],
        ["Score perfusion",      str(h_score), h_label],
    ]
    badge_tbl = Table(badge_rows, colWidths=[5.5 * cm, 3 * cm, 6.5 * cm])
    badge_tbl.setStyle(TableStyle([
        ("FONTNAME",    (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("FONTNAME",   (1, 0), (1, -1),  "Helvetica-Bold"),
        ("FONTSIZE",   (1, 0), (1, -1),  14),
        ("TEXTCOLOR",  (0, 0), (0, -1),  _MUTED),
        ("TEXTCOLOR",  (1, 0), (1, -1),  _ACCENT),
        ("TEXTCOLOR",  (2, 0), (2, -1),  _GREEN),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [_SURFACE, _BG]),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("GRID",       (0, 0), (-1, -1),  0.3, _BORDER),
    ]))
    story.append(badge_tbl)
    story.append(Spacer(1, 10))

    # ── Section 1 — Métriques principales ─────────────────────────────────────
    story.append(Paragraph("1. Métriques principales", S["h2"]))
    hr    = result.get("hr", {})
    snr   = result.get("snr", {})
    tms   = result.get("tms", {})
    hrv   = result.get("hrv", {})
    resp  = result.get("respiration", {})
    mot   = result.get("motion", {})
    ci    = result.get("hr_ci", {})
    wa    = result.get("wound_area", {})

    main_rows = [
        ["Fréquence cardiaque",   f"{hr.get('hr_bpm', '—')} bpm"],
        ["SNR moyen",             f"{snr.get('mean_snr', '—')} dB"],
        ["TMS (morphologie)",     f"{round((tms.get('tms') or 0)*100, 1)} %"],
        ["Fréquence respiratoire", f"{resp.get('rr_bpm', '—')} rpm"],
        ["Artefacts mouvement",   f"{mot.get('pct_bad', '—')} %  [{mot.get('severity', '—')}]"],
        ["FPS réel",              f"{round(result.get('fps', 0), 1)} Hz"],
        ["Frames",                str(result.get("n_frames", "—"))],
        ["Surface de plaie",      f"{wa.get('pct', '—')} % ({wa.get('pixels', '—')} px)" if wa else "—"],
    ]
    if ci:
        main_rows.append([
            "IC HR (95%)",
            f"{ci.get('hr_ci_lo', '—')}–{ci.get('hr_ci_hi', '—')} bpm  (σ={ci.get('hr_std', '—')} bpm)",
        ])

    story.append(_metric_table(main_rows))
    story.append(Spacer(1, 8))

    # ── Section 2 — HRV ───────────────────────────────────────────────────────
    if hrv and hrv.get("sdnn_ms") is not None:
        story.append(Paragraph("2. Variabilité de la fréquence cardiaque (HRV)", S["h2"]))
        hrv_rows = [
            ["SDNN",   f"{hrv.get('sdnn_ms', '—')} ms"],
            ["RMSSD",  f"{hrv.get('rmssd_ms', '—')} ms"],
            ["pNN50",  f"{hrv.get('pnn50', '—')} %"],
            ["Pics détectés", str(hrv.get("n_peaks", "—"))],
        ]
        story.append(_metric_table(hrv_rows))
        story.append(Spacer(1, 8))

    # ── Section 3 — Comparaison algorithmes ───────────────────────────────────
    story.append(Paragraph("3. Comparaison algorithmes rPPG", S["h2"]))
    story.append(_algo_table(result))
    story.append(Spacer(1, 8))

    # ── Section 4 — Cartes spatiales ──────────────────────────────────────────
    maps = result.get("maps", {})
    if maps:
        story.append(Paragraph("4. Cartes spatiales ST-rPPG", S["h2"]))
        map_pairs = [
            ("amplitude",     "Amplitude PPG"),
            ("snr",           "SNR spatial"),
            ("dc",            "Illumination DC"),
            ("amp_normalized","Perfusion normalisée"),
        ]
        img_row = []
        for key, label in map_pairs:
            b64 = maps.get(key)
            if b64:
                img = _b64_to_rl_image(b64, 4.0)
                if img:
                    img_row.append([img, Paragraph(label, S["center"])])
        if img_row:
            # 2 maps per row
            for i in range(0, len(img_row), 2):
                chunk = img_row[i:i + 2]
                while len(chunk) < 2:
                    chunk.append(["", ""])
                row_data = [[chunk[0][0], chunk[1][0]],
                            [chunk[0][1], chunk[1][1]]]
                img_tbl = Table(row_data, colWidths=[7 * cm, 7 * cm])
                img_tbl.setStyle(TableStyle([
                    ("ALIGN",  (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING",    (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]))
                story.append(img_tbl)
        story.append(Spacer(1, 8))

    # ── Section 5 — Interprétation ────────────────────────────────────────────
    interp = result.get("interpretation", {})
    if interp:
        story.append(Paragraph("5. Interprétation automatique", S["h2"]))
        narr = interp.get("narrative", "")
        if narr:
            story.append(Paragraph(narr, S["body"]))
        for key, label in [
            ("signal_quality", "Qualité signal"),
            ("heart_rate",     "Fréquence cardiaque"),
            ("morphology",     "Morphologie PPG"),
            ("perfusion",      "Perfusion"),
        ]:
            item = interp.get(key, {})
            if item and item.get("short"):
                story.append(Paragraph(
                    f"<b>{label}</b> : {item['short']}", S["small"]
                ))
        story.append(Spacer(1, 8))

    # ── Recommendations ───────────────────────────────────────────────────────
    recs = qual.get("recommendations", [])
    if recs:
        story.append(Paragraph("Recommandations", S["h3"]))
        for r in recs:
            story.append(Paragraph(f"• {r}", S["small"]))
        story.append(Spacer(1, 6))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(_hr())
    story.append(Paragraph(
        "ST-rPPG Platform · LCOMS · Université de Lorraine · ANR-24-CE45-7356  "
        "— Rapport généré automatiquement à des fins de recherche.",
        S["small"],
    ))

    doc.build(story)
    return buf.getvalue()
