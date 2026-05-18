"""
core/ai_interpretation.py
─────────────────────────
Rule-based scientific interpretation of ST-rPPG analysis results.
Grounded in wound microvascular physiology and signal quality theory.

Architecture: rule-based now, LLM-augmentable later — call interpret_results()
and replace the return dict with an LLM prompt/response chain when an API key
is available (e.g. Anthropic claude-sonnet-4-6 with the structured output below
as system context).

Scientific references:
  - Wang et al. IEEE TBME 2017 (POS algorithm)
  - Bousefsaf et al. Biomedical Opt. Express 2021 (rPPG wound perfusion)
  - Wound healing: granulation (high PPG), fibrin (low), necrosis (flat)
  - SNR thresholds: >6 dB = reliable, 3-6 = acceptable, <3 = unreliable
  - HR normal range: 60-100 bpm (sinus rhythm at rest)
  - TMS >= 0.96 = clean morphology
"""

from __future__ import annotations


# ── Thresholds ─────────────────────────────────────────────────────────────────

_SNR_EXCELLENT  = 10.0   # dB
_SNR_GOOD       = 6.0
_SNR_ACCEPTABLE = 3.0
_SNR_WEAK       = 0.0

_HR_LOW   = 60.0   # bpm
_HR_HIGH  = 100.0

_TMS_CLEAN    = 0.96
_TMS_MODERATE = 0.88

# Amplitude thresholds are relative (AC/DC ratio of green reflectance after POS
# normalization) and camera/illumination-dependent — no absolute calibration exists.
_AMP_HIGH = 0.25
_AMP_MED  = 0.08

_CV_HOMO  = 0.20   # coefficient of variation (std/mean)
_CV_MIXED = 0.45


# ── SNR interpretation ─────────────────────────────────────────────────────────

def _interpret_snr(mean_snr: float) -> dict:
    if mean_snr >= _SNR_EXCELLENT:
        return {
            "level": "excellent",
            "short": f"SNR {mean_snr:.1f} dB — signal fiable",
            "text": (
                f"Le rapport signal/bruit moyen de {mean_snr:.1f} dB indique un signal rPPG "
                "de haute qualité. Les mesures de perfusion sont hautement fiables et "
                "exploitables pour une analyse clinique."
            ),
            "color": "#22d47e",
        }
    elif mean_snr >= _SNR_GOOD:
        return {
            "level": "good",
            "short": f"SNR {mean_snr:.1f} dB — signal bon",
            "text": (
                f"Le SNR moyen de {mean_snr:.1f} dB correspond à un signal de bonne qualité. "
                "Les mesures sont fiables pour une interprétation quantitative."
            ),
            "color": "#22d47e",
        }
    elif mean_snr >= _SNR_ACCEPTABLE:
        return {
            "level": "acceptable",
            "short": f"SNR {mean_snr:.1f} dB — signal acceptable",
            "text": (
                f"Le SNR de {mean_snr:.1f} dB indique un signal acceptable. "
                "Les résultats sont exploitables mais doivent être interprétés avec précaution. "
                "Vérifiez les conditions d'éclairage et l'absence d'artefacts de mouvement."
            ),
            "color": "#f59e0b",
        }
    elif mean_snr >= _SNR_WEAK:
        return {
            "level": "weak",
            "short": f"SNR {mean_snr:.1f} dB — signal faible",
            "text": (
                f"Le SNR de {mean_snr:.1f} dB indique un signal faible. "
                "Les mesures sont à la limite de la fiabilité. "
                "Améliorez l'éclairage (LED verte 530 nm recommandée) et réduisez "
                "les mouvements du patient pendant l'acquisition."
            ),
            "color": "#f59e0b",
        }
    else:
        return {
            "level": "poor",
            "short": f"SNR {mean_snr:.1f} dB — signal non fiable",
            "text": (
                f"Le SNR de {mean_snr:.1f} dB est insuffisant pour une mesure rPPG fiable. "
                "Relancez l'acquisition dans de meilleures conditions "
                "(éclairage uniforme, patient immobile, caméra stable)."
            ),
            "color": "#ef4444",
        }


# ── HR interpretation ──────────────────────────────────────────────────────────

def _interpret_hr(hr_bpm: float) -> dict:
    if hr_bpm is None:
        return {
            "short": "FC non estimée",
            "text": "La fréquence cardiaque n'a pas pu être estimée (signal insuffisant).",
            "color": "#ef4444",
        }
    if _HR_LOW <= hr_bpm <= _HR_HIGH:
        return {
            "short": f"FC {hr_bpm:.0f} bpm — plage normale",
            "text": (
                f"La fréquence cardiaque estimée ({hr_bpm:.0f} bpm) est dans la plage "
                "physiologique normale (60–100 bpm au repos), "
                "cohérente avec une mesure rPPG valide."
            ),
            "color": "#22d47e",
        }
    elif hr_bpm < _HR_LOW:
        return {
            "short": f"FC {hr_bpm:.0f} bpm — bradycardie possible",
            "text": (
                f"La fréquence cardiaque estimée ({hr_bpm:.0f} bpm) est inférieure "
                "à la plage normale. Possible bradycardie ou artefact basse fréquence. "
                "Vérifiez la cohérence avec les données cliniques."
            ),
            "color": "#f59e0b",
        }
    else:
        return {
            "short": f"FC {hr_bpm:.0f} bpm — tachycardie possible",
            "text": (
                f"La fréquence cardiaque estimée ({hr_bpm:.0f} bpm) dépasse "
                "la plage normale au repos. Possible tachycardie ou artefact "
                "de mouvement haute fréquence."
            ),
            "color": "#f59e0b",
        }


# ── TMS interpretation ─────────────────────────────────────────────────────────

def _interpret_tms(tms: float, n_cycles: int) -> dict:
    if tms >= _TMS_CLEAN:
        return {
            "short": f"TMS {tms*100:.0f}% — morphologie propre",
            "text": (
                f"Le Template Matching Score ({tms*100:.1f}%, {n_cycles} cycles) "
                "indique une morphologie PPG cohérente et périodique. "
                "La forme d'onde est caractéristique d'un signal vasculaire non artefacté."
            ),
            "color": "#22d47e",
        }
    elif tms >= _TMS_MODERATE:
        return {
            "short": f"TMS {tms*100:.0f}% — morphologie modérée",
            "text": (
                f"Le TMS ({tms*100:.1f}%, {n_cycles} cycles) indique une cohérence "
                "morphologique modérée. Des irrégularités cycliques sont présentes, "
                "possiblement dues à des arythmies mineures ou des micro-mouvements."
            ),
            "color": "#f59e0b",
        }
    else:
        return {
            "short": f"TMS {tms*100:.0f}% — morphologie dégradée",
            "text": (
                f"Le TMS ({tms*100:.1f}%, {n_cycles} cycles) révèle une incohérence "
                "morphologique importante entre les cycles. Artefacts de mouvement "
                "probables ou signal insuffisamment périodique."
            ),
            "color": "#ef4444",
        }


# ── Amplitude / perfusion interpretation ───────────────────────────────────────

def _interpret_perfusion(amp_stats: dict | None) -> dict:
    if not amp_stats:
        return {
            "short": "Carte spatiale non disponible",
            "text": "Les statistiques d'amplitude spatiale ne sont pas disponibles.",
            "color": "#6e7190",
        }

    mean = amp_stats.get("mean", 0) or 0
    std  = amp_stats.get("std", 0) or 0
    cv   = std / (mean + 1e-8)

    # Perfusion level
    if mean >= _AMP_HIGH:
        perf_text = (
            f"L'amplitude rPPG moyenne ({mean:.3f}) est élevée, indiquant une bonne "
            "perfusion microvasculaire. Le tissu répond fortement au signal cardiaque — "
            "caractéristique d'un tissu de granulation actif ou d'une peau saine."
        )
        perf_color = "#22d47e"
        perf_short = "Perfusion élevée — tissu vascularisé"
    elif mean >= _AMP_MED:
        perf_text = (
            f"L'amplitude rPPG moyenne ({mean:.3f}) indique une perfusion modérée. "
            "Tissu partiellement vascularisé — compatible avec une phase transitoire "
            "de cicatrisation (fibrine en résorption, néo-vascularisation débutante)."
        )
        perf_color = "#f59e0b"
        perf_short = "Perfusion modérée — vascularisation partielle"
    else:
        perf_text = (
            f"L'amplitude rPPG moyenne ({mean:.3f}) est faible. "
            "La réponse microvasculaire est limitée — compatible avec du tissu fibrineux, "
            "nécrotique ou une zone d'ischémie. "
            "Corrélation avec l'examen clinique recommandée."
        )
        perf_color = "#ef4444"
        perf_short = "Perfusion faible — ischémie possible"

    # Spatial heterogeneity
    if cv < _CV_HOMO:
        hetero_text = (
            "La carte spatiale est homogène (CV < 20%) — perfusion uniforme sur la zone analysée."
        )
        hetero_short = "Carte homogène"
    elif cv < _CV_MIXED:
        hetero_text = (
            f"La carte présente une hétérogénéité modérée (CV = {cv*100:.0f}%), "
            "suggérant des zones de perfusion différentielle — typique des marges de plaie "
            "où coexistent tissu sain et tissu lésé."
        )
        hetero_short = "Hétérogénéité modérée"
    else:
        hetero_text = (
            f"La carte est fortement hétérogène (CV = {cv*100:.0f}%). "
            "Co-existence probable de zones nécrotiques (amplitude faible) et de zones "
            "périphériques vascularisées (amplitude élevée) — "
            "cartographie différentielle wound/peri-wound recommandée."
        )
        hetero_short = "Forte hétérogénéité spatiale"

    return {
        "short": perf_short,
        "text": perf_text + " " + hetero_text,
        "heterogeneity_short": hetero_short,
        "color": perf_color,
        "mean": round(mean, 4),
        "cv": round(cv, 3),
    }


# ── Global narrative ───────────────────────────────────────────────────────────

def _global_narrative(snr_i: dict, hr_i: dict, tms_i: dict, perf_i: dict,
                       quality_score: int, quality_label: str) -> str:
    levels = [snr_i.get("level", ""), tms_i.get("level", "")]
    is_reliable = all(l in ("excellent", "good", "acceptable") for l in levels)

    if quality_score >= 70:
        opening = (
            "Cette session présente un signal ST-rPPG de haute qualité. "
            "Les mesures sont exploitables pour une analyse clinique quantitative."
        )
    elif quality_score >= 50:
        opening = (
            "Cette session présente un signal de qualité correcte. "
            "Les résultats sont interprétables avec les précautions d'usage."
        )
    elif quality_score >= 30:
        opening = (
            "La qualité du signal est limitée. "
            "Les résultats ne doivent être utilisés qu'à titre indicatif."
        )
    else:
        opening = (
            "Le signal est de mauvaise qualité. "
            "Relancez l'acquisition avant toute interprétation clinique."
        )

    if is_reliable:
        context = (
            "Dans le cadre du projet Wound-rPPG (ANR-24-CE45-7356), ce type de signal "
            "permet de cartographier la perfusion microcapillaire en surface de plaie "
            "sans contact. Les cartes d'amplitude rPPG constituent un proxy non-invasif "
            "de l'activité vasculaire locale."
        )
    else:
        context = (
            "Avant interprétation clinique, améliorez les conditions d'acquisition : "
            "éclairage uniforme (LED verte recommandée), immobilisation du patient, "
            "caméra fixe, durée minimum 30 s à 25+ FPS."
        )

    return f"{opening} {context}"


# ── Main entry point ───────────────────────────────────────────────────────────

def interpret_results(result: dict) -> dict:
    """
    Generate a scientific interpretation of an ST-rPPG analysis result.

    Input : dict from analyze_session() — must contain 'hr', 'snr', 'tms',
            'quality', 'amp_stats' keys.
    Output: structured interpretation dict — JSON-serializable, display-ready.

    To upgrade to LLM: pass the structured fields as context to an Anthropic
    API call (claude-sonnet-4-6) and replace the text fields with the response.
    """
    snr_val  = (result.get("snr") or {}).get("mean_snr", -99)
    hr_val   = (result.get("hr") or {}).get("hr_bpm")
    tms_val  = (result.get("tms") or {}).get("tms", 0)
    n_cycles = (result.get("tms") or {}).get("n_cycles", 0)
    quality  = result.get("quality") or {}
    amp_stats = result.get("amp_stats")

    snr_i  = _interpret_snr(snr_val)
    hr_i   = _interpret_hr(hr_val)
    tms_i  = _interpret_tms(tms_val, n_cycles)
    perf_i = _interpret_perfusion(amp_stats)

    narrative = _global_narrative(
        snr_i, hr_i, tms_i, perf_i,
        quality.get("score", 0),
        quality.get("label", "UNKNOWN"),
    )

    return {
        "narrative": narrative,
        "signal_quality": snr_i,
        "heart_rate":     hr_i,
        "morphology":     tms_i,
        "perfusion":      perf_i,
        "method":         "rule-based",
        "algorithm":      "POS — Wang et al., IEEE TBME 2017",
        "project":        "ANR-24-CE45-7356 · Wound-rPPG · LCOMS",
    }
