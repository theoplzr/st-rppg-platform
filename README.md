# ST-rPPG Platform

**Spatio-Temporal remote PhotoPlethysmoGraphy — Wound Perfusion Analysis**

> Research platform developed at [LCOMS](https://lcoms.univ-lorraine.fr/) — Université de Lorraine  
> ANR Project · ANR-24-CE45-7356

---

## Overview

ST-rPPG Platform is a web application for non-contact, camera-based analysis of skin perfusion in wound care. It extracts a remote PPG (rPPG) signal pixel-by-pixel from a video recording and produces spatio-temporal maps that differentiate wound tissue from healthy periwound tissue.

**Core pipeline:**
1. Video frames are loaded from an acquisition session
2. The POS algorithm (de Haan & Jeanne, IEEE TBME 2013) extracts a rPPG signal from the green channel
3. Signal quality is assessed via spectral SNR and Template Matching Score (TMS)
4. Pixel-wise FFT produces spatial maps: amplitude, phase, SNR, coherence
5. Sessions and regions of interest (ROI) can be compared to quantify perfusion differences

---

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12 · Flask 3 · NumPy · SciPy · OpenCV · Pillow |
| Frontend | Vue 3 · Vuetify 3 · Apache ECharts · Pinia · Axios |
| Deployment | Docker · Gunicorn · Nginx · Vercel · Render |

---

## Architecture

```
st-rppg-platform/
└── wound-rppg-app/
    ├── backend/
    │   ├── app.py                  # Flask application entry point
    │   ├── api/
    │   │   ├── routes_sessions.py  # Session listing and tagging
    │   │   ├── routes_analysis.py  # Async analysis pipeline
    │   │   ├── routes_scenarios.py # Multi-session comparison
    │   │   └── routes_export.py    # CSV / JSON export
    │   └── core/
    │       ├── pos_algorithm.py    # POS rPPG algorithm (de Haan & Jeanne 2013)
    │       ├── signal_quality.py   # SNR, TMS, quality score
    │       ├── spatial_maps.py     # Pixel-wise amplitude / phase / SNR / coherence maps
    │       ├── session_manager.py  # Frame loading and session I/O
    │       ├── scenarios.py        # Analysis pipeline and ROI comparison
    │       └── job_queue.py        # Async job queue (ThreadPoolExecutor)
    └── frontend/
        └── src/
            ├── views/              # Dashboard, Sessions, Analysis, Scenarios, Report
            ├── components/         # Charts (Signal, FFT, SNR, SpatialMap), UI
            └── stores/             # Pinia session store
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/sessions/` | List all sessions |
| `GET` | `/api/sessions/:session` | Session metadata |
| `POST` | `/api/sessions/:session/scenario` | Tag a session with a scenario label |
| `POST` | `/api/analysis/:session` | Submit analysis (async → returns `job_id`) |
| `GET` | `/api/analysis/:session/status/:job_id` | Poll job status |
| `GET` | `/api/analysis/:session` | Fetch cached results |
| `POST` | `/api/analysis/:session/roi` | Analyze a specific region of interest |
| `POST` | `/api/scenarios/compare/two` | Binary comparison between two sessions |
| `POST` | `/api/scenarios/compare/multiple` | Rank N sessions |
| `POST` | `/api/scenarios/compare/rois` | Wound vs. periwound ROI comparison |
| `GET` | `/api/export/:session/json` | Export full results as JSON |
| `GET` | `/api/export/:session/csv` | Export metrics + time series as CSV |

---

## Session Format

Each session is a directory placed in `backend/sessions/`:

```
sessions/
└── session_2024_01_15_143022/
    ├── frames/
    │   ├── frame_0001.png
    │   ├── frame_0002.png
    │   └── ...
    ├── metadata.json
    ├── results.json      # generated after analysis
    └── scenario.json     # generated after tagging
```

**`metadata.json` schema:**
```json
{
  "session_name": "session_2024_01_15_143022",
  "measured_fps": 30.0,
  "nb_frames": 300,
  "frame_width": 640,
  "frame_height": 480,
  "date": "2024-01-15T14:30:22"
}
```

---

## Local Setup

**Prerequisites:** Docker and Docker Compose.

```bash
# 1. Clone the repository
git clone https://github.com/theoplzr/st-rppg-platform.git
cd st-rppg-platform

# 2. Create the environment file
cp wound-rppg-app/backend/.env.example wound-rppg-app/backend/.env

# 3. Place your acquisition sessions in the sessions directory
cp -r /path/to/your/sessions/* wound-rppg-app/backend/sessions/

# 4. Start the stack
cd wound-rppg-app
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:5000/api/health |

---

## Deployment

### Backend — Render

1. Go to [render.com](https://render.com) → **New → Web Service**
2. Connect the repository, set **Root Directory** to `wound-rppg-app/backend`
3. Set **Runtime** to Docker
4. Add environment variables:

| Variable | Value |
|----------|-------|
| `FLASK_ENV` | `production` |
| `ALLOWED_ORIGINS` | `https://your-frontend.vercel.app` |

### Frontend — Vercel

1. Go to [vercel.com](https://vercel.com) → **New Project**
2. Set **Root Directory** to `wound-rppg-app/frontend`
3. Set **Framework** to Vite
4. Add environment variable:

| Variable | Value |
|----------|-------|
| `VITE_API_URL` | `https://your-backend.onrender.com/api` |

---

## Signal Quality Metrics

| Metric | Description |
|--------|-------------|
| **HR** | Heart rate estimated from the dominant FFT peak (bpm) |
| **Spectral SNR** | Peak power / out-of-band power at the HR frequency (dB) |
| **Sliding SNR** | SNR computed over a 5-second sliding window (dB) |
| **TMS** | Template Matching Score — Pearson correlation of each PPG cycle with the mean template [0, 1] |
| **Quality Score** | Composite score (0–100) weighting SNR (40 pts), TMS (40 pts), FPS (20 pts) |

---

## Spatial Maps

| Map | Description |
|-----|-------------|
| **Amplitude** | Per-pixel FFT power at the HR frequency — reflects local perfusion intensity |
| **Phase** | Per-pixel phase offset relative to the spatial median — highlights heterogeneous perfusion |
| **SNR** | Per-pixel signal-to-noise ratio (dB) |
| **Coherence** | Pearson correlation of each pixel signal with the spatial mean reference [0, 1] |

---

## References

- G. de Haan and V. Jeanne, *"Robust Pulse Rate From Chrominance-Based rPPG,"* IEEE Transactions on Biomedical Engineering, vol. 60, no. 10, pp. 2878–2886, 2013.
- A. Hmedeh et al., LCOMS Laboratory, Université de Lorraine, 2024.

---

## License

This project is part of the ANR research program ANR-24-CE45-7356.  
Contact the LCOMS laboratory for usage and collaboration inquiries.
