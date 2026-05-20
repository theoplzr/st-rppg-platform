# ST-rPPG · Wound Perfusion Platform

> Plateforme web de photopléthysmographie distante spatio-temporelle pour l'analyse de perfusion cutanée en cicatrisation
> Projet ANR · ANR-24-CE45-7356 — LCOMS Laboratory, Université de Lorraine

---

## Contexte et problématique

La cicatrisation d'une plaie dépend directement de la qualité de la vascularisation locale. Les tissus bien perfusés (granulation active) cicatrisent rapidement, tandis que les zones ischémiques ou nécrotiques stagnent. L'évaluation clinique visuelle reste subjective et ne permet pas de cartographier quantitativement la perfusion capillaire en surface.

Cette plateforme répond à cette problématique en exploitant le principe de la **rPPG (remote PhotoPlethysmoGraphy)** : une caméra standard détecte les micro-variations de réflectance cutanée induites par le flux sanguin pulsatile, sans aucun contact avec le tissu. L'approche **spatio-temporelle (ST-rPPG)** étend ce principe pixel par pixel pour produire des **cartes 2D de perfusion microcapillaire**.

---

## Algorithme central — POS (Wang et al., IEEE TBME 2017)

L'extracteur de signal rPPG implémenté est l'algorithme **POS** (*Plane-Orthogonal-to-Skin*), publié par Wang, den Brinker, Stuijk & de Haan en 2017. C'est l'état de l'art pour l'extraction rPPG en conditions d'éclairage variable.

### Principe mathématique

Le signal PPG est extrait dans un sous-espace chrominance orthogonal à la composante "peau" du spectre lumineux. Pour chaque fenêtre glissante de `l` frames :

1. **Normalisation chrominance** — élimination de la composante DC (variation d'éclairage) :

$$C_n(t) = \frac{\text{RGB}(t)}{\mu_{\text{RGB}}}$$

1. **Projection POS** — projection sur le plan orthogonal à la peau via la matrice :

$$\mathbf{M} = \begin{pmatrix} 0 & 1 & -1 \\ -2 & 1 & 1 \end{pmatrix}$$
$$\mathbf{S} = \mathbf{M} \cdot C_n^T \quad \Rightarrow \quad h = S_1 + \alpha \cdot S_2, \quad \alpha = \frac{\sigma(S_1)}{\sigma(S_2)}$$

1. **Accumulation OLA** (*Overlap-Add*) avec soustraction de la moyenne :

$$H[m:n] \mathrel{+}= h - \bar{h}$$

### Pipeline de traitement

```text
Vidéo (N frames) ──► Moyenne spatiale (N,3) ──► POS brut ──► Detrend + Bandpass 0.7–3 Hz
                                                                        │
                                                          ┌─────────────┴──────────────┐
                                                          │                            │
                                               pos_filtered (métriques)    pos_signal (cartes)
                                                  SNR · TMS · Score         + normalisation Hilbert
```

> **Choix de conception important** : la normalisation d'enveloppe de Hilbert (`H / |hilbert(H)|`) est appliquée **uniquement** pour les cartes spatiales (amplitude uniforme entre pixels). Les métriques de qualité (SNR, TMS, score) utilisent `pos_filtered` — le signal non normalisé — pour préserver l'amplitude réelle du signal.

---

## Architecture de l'application

```text
wound-rppg-app/
├── backend/                         Python 3.12 · Flask 3 · Gunicorn
│   ├── app.py                       Point d'entrée Flask
│   ├── api/
│   │   ├── routes_analysis.py       Pipeline d'analyse (async + pixel_pos)
│   │   ├── routes_sessions.py       Gestion des sessions / upload
│   │   ├── routes_scenarios.py      Comparaisons multi-sessions
│   │   └── routes_export.py         Export CSV / JSON
│   └── core/
│       ├── pos_algorithm.py         POS Wang 2017 (pos_filtered · pos_signal · pos_local)
│       ├── signal_quality.py        SNR glissant · TMS · score composite
│       ├── spatial_maps.py          Cartes amplitude / phase / SNR / cohérence
│       ├── scenarios.py             Orchestrateur pipeline + sous-échantillonnage
│       ├── ai_interpretation.py     Interprétation scientifique rule-based
│       ├── session_manager.py       I/O sessions (frames PNG + metadata)
│       └── job_queue.py             File async (ThreadPoolExecutor)
│
└── frontend/                        Vue 3 · Vuetify 3 · Apache ECharts · Pinia
    └── src/
        ├── views/
        │   ├── Dashboard.vue        Vue d'ensemble toutes sessions
        │   ├── Sessions.vue         Gestionnaire de sessions
        │   ├── Acquire.vue          Interface d'acquisition vidéo
        │   ├── Analysis.vue         Analyse complète d'une session
        │   ├── Scenarios.vue        Comparaison multi-sessions
        │   └── Report.vue           Rapport exportable
        ├── components/
        │   ├── charts/
        │   │   ├── SignalChart.vue   Signal POS brut + filtré + pics systoliques
        │   │   ├── FFTChart.vue      Spectre de puissance + bande cardiaque
        │   │   ├── SNRChart.vue      SNR glissant + zones colorées
        │   │   └── SpatialMap.vue    Carte cliquable + comparaison POS local/global
        │   └── ui/
        │       ├── MetricCard.vue   Carte métrique animée
        │       └── QualityBadge.vue  Badge EXCELLENT / GOOD / POOR / BAD
        └── stores/session.js        Store Pinia (état global sessions)
```

### Stack technique

| Couche | Technologie |
| ----------- | ------------------------------------------------------------------ |
| Backend | Python 3.12 · Flask 3 · SciPy · NumPy · OpenCV · Pillow · Gunicorn |
| Frontend | Vue 3 · Vuetify 3 · Apache ECharts · Pinia · Vite |
| Déploiement | Docker · Docker Compose · Nginx |

---

## Fonctionnalités

### 1. Acquisition vidéo

La vue **Acquire** permet d'enregistrer une session directement depuis la caméra du navigateur (WebRTC). Les frames sont transmises au backend, stockées en PNG, et les métadonnées (FPS mesuré, résolution, horodatage) sont enregistrées automatiquement.

### 2. Gestion des sessions

La vue **Sessions** liste toutes les sessions disponibles avec leur statut d'analyse (analysé / en attente / en cours). Les sessions peuvent être :

- importées via upload d'archive ZIP (frames + metadata)
- annotées avec un **scénario clinique** (type de tissu, zone anatomique, description)
- supprimées

### 3. Analyse ST-rPPG complète

C'est le cœur de la plateforme. La vue **Analysis** déclenche le pipeline complet sur une session et affiche :

#### Métriques globales

| Métrique | Calcul | Interprétation |
| ------------------ | --------------------------------------------------------- | ----------------------- |
| **HR estimée** | Pic dominant FFT dans la bande 0.7–3.5 Hz → BPM | Fréquence cardiaque |
| **SNR glissant** | P(HR + 2HR) / P(bruit intra-bande cardiaque), fenêtre 8 s | Qualité spectrale |
| **TMS** | Corrélation de Pearson de chaque cycle PPG vs template | Cohérence morphologique |
| **Score qualité** | 0–100 pts composite (SNR + TMS + FPS) | Fiabilité globale |

**Formule du score composite** :

```text
SNR score  = clip(SNR_moyen / 8.0 × 40,  0, 40)   — 8 dB = excellent
TMS score  = clip((TMS - 0.6) / 0.4 × 40, 0, 40)  — 0.96 = propre
FPS score  = clip((FPS - 15) / 35.0 × 20, 0, 20)  — 50 fps = max
─────────────────────────────────────────────────────────────────────
EXCELLENT ≥ 70 · GOOD ≥ 50 · POOR ≥ 30 · BAD < 30
```

#### Graphiques interactifs

**Signal POS** (SignalChart) — visualisation temporelle avec :

- Signal brut POS pré-filtre (semi-transparent)
- Signal filtré 0.7–3 Hz (courbe principale)
- Pics systoliques détectés (scatter doré)
- Zoom DataZoom intégré pour l'exploration

**Spectre FFT** (FFTChart) — spectre de puissance avec :

- Mise en évidence de la bande cardiaque (0.7–3 Hz)
- Marqueur vertical à la fréquence HR estimée
- Labels doubles Hz / BPM sur l'axe des fréquences

**SNR glissant** (SNRChart) — évolution temporelle du SNR avec :

- Zones colorées : rouge (< 0 dB), orange (0–3 dB), vert (> 3 dB)
- Seuils de référence annotés (0 dB, 3 dB ✓, 6 dB ★)
- Ligne pointillée SNR moyen

**Template Matching Score** — affichage du score de cohérence morphologique et du nombre de cycles détectés.

#### Cartes spatiales ST-rPPG

Quatre cartes 2D calculées pixel par pixel via FFT de la composante verte :

| Carte | Méthode | Interprétation clinique |
| --------------- | ------------------------------------------------- | ------------------------------ |
| **Amplitude** | Puissance FFT à la fréquence HR | Intensité de perfusion locale |
| **Phase** | Phase FFT à HR, centrée sur la médiane spatiale | Délai de propagation vasculaire |
| **SNR** | P(HR + 2HR) / P(bruit) par pixel | Fiabilité pixel par pixel |
| **Cohérence** | Corrélation de Pearson signal POS local vs global | Cohérence spatiale pulsatile |

> La carte de cohérence est calculée via `pos_local` — une version vectorisée du POS appliquée pixel par pixel — et non depuis la seule composante verte, ce qui la rend plus robuste aux variations d'éclairage.

#### Comparaison POS local vs global (clic sur carte)

Un clic sur n'importe quel pixel de la carte spatiale déclenche une requête `POST /pixel_pos` qui :

1. Extrait le signal RGB du pixel sélectionné
1. Calcule son signal POS individuel (`pos_signal`)
1. Le superpose au signal global dans un graphique de comparaison
1. Affiche le coefficient de corrélation de Pearson r entre les deux signaux

Cette feature permet d'identifier visuellement les zones de forte cohérence vasculaire (r proche de 1) vs les zones d'ischémie ou de bruit (r faible).

#### Interprétation scientifique automatique

Un module rule-based génère une interprétation textuelle structurée de chaque session, couvrant :

- Qualité du signal (SNR) → fiabilité de la mesure
- Fréquence cardiaque estimée → cohérence physiologique (bradycardie / normale / tachycardie)
- Morphologie PPG (TMS) → artefacts de mouvement
- Perfusion (amplitude spatiale) → vascularisation du tissu + hétérogénéité spatiale (CV)

L'architecture est conçue pour être augmentée d'un LLM (le module expose un dict structuré prêt à être passé en contexte système à un modèle de langage).

### 4. Comparaison multi-sessions (Scénarios)

La vue **Scenarios** permet de :

- Comparer deux sessions côte à côte (métriques + cartes diff)
- Classer N sessions par score qualité décroissant
- Comparer deux ROI (wound vs periwound) sur la même session

### 5. Rapport exportable

La vue **Report** génère un rapport de synthèse de la session avec toutes les métriques, les cartes, et l'interprétation, exportable en PDF via l'impression navigateur.

### 6. Export des données

| Format | Contenu |
| -------- | -------------------------------------------------------------- |
| **CSV** | HR, SNR, TMS, score, série temporelle SNR glissant, série FFT |
| **JSON** | Résultats complets de l'analyse (structure imbriquée) |

---

## API REST

| Méthode | Endpoint | Description |
| --------- | --------------------------------------- | ------------------------------------ |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/sessions/` | Liste des sessions |
| `POST` | `/api/sessions/upload` | Upload d'une session (ZIP) |
| `POST` | `/api/sessions/:session/scenario` | Annoter une session |
| `POST` | `/api/analysis/:session` | Lancer l'analyse (async) |
| `GET` | `/api/analysis/:session/status/:job_id` | Polling statut job |
| `GET` | `/api/analysis/:session` | Résultats mis en cache |
| `POST` | `/api/analysis/:session/pixel_pos` | Signal POS d'un pixel (x, y normalisés) |
| `POST` | `/api/analysis/:session/roi` | Analyse d'une ROI |
| `POST` | `/api/scenarios/compare/two` | Comparaison binaire |
| `POST` | `/api/scenarios/compare/multiple` | Classement N sessions |
| `GET` | `/api/export/:session/csv` | Export CSV |
| `GET` | `/api/export/:session/json` | Export JSON |

---

## Déploiement local

**Prérequis** : Docker et Docker Compose.

```bash
# 1. Cloner le dépôt
git clone https://github.com/theoplzr/st-rppg-platform.git
cd st-rppg-platform/wound-rppg-app

# 2. Construire et lancer la stack
docker compose up --build
```

| Service | URL |
| ----------- | --------------------------------- |
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:5001/api/health |

Pour importer une session existante (dossier de frames PNG + `metadata.json`) :

```bash
cp -r /chemin/vers/ma-session/ wound-rppg-app/backend/sessions/
```

---

## Format des sessions

```text
sessions/
└── vid_20260515_143022/
    ├── frames/
    │   ├── frame_0001.png
    │   └── ...
    ├── metadata.json          # FPS mesuré, résolution, horodatage
    └── results.json           # généré après analyse
```

```json
{
  "session_name": "vid_20260515_143022",
  "measured_fps": 30.0,
  "nb_frames": 900,
  "frame_width": 640,
  "frame_height": 480,
  "date": "2026-05-15T14:30:22"
}
```

---

## Notes d'implémentation

### Robustesse sur vidéos longues

- **Filtre Butterworth** : les fréquences de coupure sont clampées dans `(1e-6, 1-1e-6)` avant tout appel à `scipy.signal.butter` — évite le crash `ValueError: Wn must be between 0 and 1` sur des vidéos à faible FPS.
- **FPS guard** : si `measured_fps` est absent ou incohérent (hors de [1, 240]), il est remplacé par 30 Hz.
- **Sous-échantillonnage spatial** : le calcul des cartes ST-rPPG est limité aux 300 frames centrales de la vidéo. Cela réduit le temps de calcul de `pos_local` (O(N×H×W)) de ~60 s à ~3 s sur une vidéo de 3 minutes, sans dégrader la qualité des cartes.
- **Masques FFT vides** : les fonctions `_amplitude_from_fft`, `_phase_from_fft` et `_snr_from_fft` retournent des cartes nulles (et non NaN) si aucune fréquence ne correspond à la bande HR.

### Précision du SNR

Le SNR glissant est calculé **uniquement dans la bande cardiaque** (0.7–3.0 Hz) :

```text
SNR = 10 × log10( P(HR) + P(2×HR) / P(bande 0.7–3 Hz \ {HR, 2HR}) )
```

Ce choix suit les conventions de la littérature rPPG (Bousefsaf et al., 2021) et évite d'inclure la puissance DC et respiratoire dans le dénominateur, ce qui gonflerait artificiellement le bruit et donnerait un SNR systématiquement proche de 0 dB.

### TMS — segmentation par pics

Le Template Matching Score segmente les cycles PPG à partir des **pics systoliques détectés** (`scipy.signal.find_peaks`) plutôt que par pas entier uniforme. La segmentation entière introduit une dérive de phase progressive qui fragmente les cycles longs et fait chuter le TMS artificiellement sur des signaux de bonne qualité.

---

## Références

- Wang, W., den Brinker, A. C., Stuijk, S., & de Haan, G. (2017). *Algorithmic Principles of Remote PPG.* IEEE Transactions on Biomedical Engineering, 64(7), 1479–1491.
- Bousefsaf, F., Maaoui, C., & Pruski, A. (2021). *Continuous wavelet filtering on webcam photoplethysmographic signals to remotely assess the instantaneous heart rate.* Biomedical Signal Processing and Control.
- Hmedeh, A. et al., LCOMS Laboratory, Université de Lorraine — Projet ANR-24-CE45-7356, 2024.

---

*Projet de recherche ANR-24-CE45-7356 — LCOMS, Université de Lorraine. Tout usage ou collaboration externe est soumis à accord du laboratoire.*
