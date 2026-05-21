"""
core/session_manager.py

Session I/O layer:
  - Load frame sequences from disk
  - Read and write metadata/results/scenario files
  - List available sessions for the frontend
"""

import base64
import cv2
import io
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from PIL import Image


SESSIONS_DIR = Path(__file__).parent.parent / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)


def load_frames(
    session_dir: Path,
    max_frames: int = None,
    resize: tuple = None,
) -> np.ndarray:
    """
    Load all frames from a session directory.

    Returns an array shaped (N, H, W, 3) as float32 in [0, 1].
    """
    frames_dir = session_dir / "frames"
    if not frames_dir.exists():
        raise FileNotFoundError(f"Frames directory not found: {frames_dir}")

    exts = (".png", ".jpg", ".jpeg", ".bmp")
    files = sorted(p for p in frames_dir.iterdir() if p.suffix.lower() in exts)

    if not files:
        raise FileNotFoundError(f"No images found in {frames_dir}")

    if max_frames:
        files = files[:max_frames]

    frames = []
    for frame_path in files:
        img = cv2.imread(str(frame_path))
        if img is None:
            continue
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        if resize:
            img = cv2.resize(img, resize)
        frames.append(img.astype(np.float32) / 255.0)

    if not frames:
        raise FileNotFoundError(f"No readable images found in {frames_dir}")

    return np.stack(frames, axis=0)


def load_metadata(session_dir: Path) -> dict:
    """Load session metadata from metadata.json or generate a fallback."""
    meta_path = session_dir / "metadata.json"
    if meta_path.exists():
        with open(meta_path) as f:
            return json.load(f)

    frames_dir = session_dir / "frames"
    n_frames = len(list(frames_dir.glob("*.png"))) + len(list(frames_dir.glob("*.jpg")))
    return {
        "session_name": session_dir.name,
        "measured_fps": 30.0,
        "nb_frames": n_frames,
        "date": datetime.now().isoformat(),
    }


def load_session(
    session_name: str,
    sessions_root: Path = None,
    max_frames: int = None,
    resize: tuple = None,
) -> tuple:
    """Load a full session (frames + metadata)."""
    root = sessions_root or SESSIONS_DIR
    session_dir = root / session_name
    if not session_dir.exists():
        raise FileNotFoundError(f"Session not found: {session_dir}")

    frames = load_frames(session_dir, max_frames=max_frames, resize=resize)
    meta = load_metadata(session_dir)
    return frames, meta


def list_sessions(sessions_root: Path = None) -> list:
    """List all available sessions with a compact metadata summary."""
    root = sessions_root or SESSIONS_DIR
    if not root.exists():
        return []

    sessions = []
    for session_dir in sorted(root.iterdir(), reverse=True):
        if not session_dir.is_dir():
            continue

        frames_dir = session_dir / "frames"
        if not frames_dir.exists():
            continue

        meta = load_metadata(session_dir)
        n_frames = len([
            p for p in frames_dir.iterdir()
            if p.suffix.lower() in (".png", ".jpg", ".jpeg")
        ])

        scenario = {}
        scenario_path = session_dir / "scenario.json"
        if scenario_path.exists():
            with open(scenario_path) as f:
                scenario = json.load(f)

        fps = meta.get("measured_fps", 0) or 0
        sessions.append({
            "name": session_dir.name,
            "date": meta.get("date", ""),
            "fps": fps,
            "nb_frames": n_frames,
            "duration_s": round(n_frames / max(fps, 1), 2),
            "resolution": f"{meta.get('frame_width', '?')}x{meta.get('frame_height', '?')}",
            "has_results": (session_dir / "results.json").exists(),
            "scenario": scenario,
        })

    return sessions


def save_results(
    session_name: str,
    results: dict,
    sessions_root: Path = None,
) -> Path:
    """Persist analysis results into results.json inside the session directory."""
    root = sessions_root or SESSIONS_DIR
    session_dir = root / session_name
    session_dir.mkdir(parents=True, exist_ok=True)

    results_path = session_dir / "results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    return results_path


def load_results(
    session_name: str,
    sessions_root: Path = None,
) -> dict:
    """Load cached analysis results from results.json."""
    root = sessions_root or SESSIONS_DIR
    results_path = root / session_name / "results.json"
    if not results_path.exists():
        raise FileNotFoundError(f"No results found for session: {session_name}")

    with open(results_path) as f:
        return json.load(f)


def save_mask(
    session_name: str,
    mask_b64: str,
    sessions_root: Path = None,
) -> Path:
    """
    Save a mask from a base64-encoded PNG.
    The PNG must be grayscale or RGBA — white pixels = wound area.
    """
    root = sessions_root or SESSIONS_DIR
    mask_path = root / session_name / "mask.png"
    mask_path.parent.mkdir(parents=True, exist_ok=True)

    img_data = base64.b64decode(mask_b64)
    img = Image.open(io.BytesIO(img_data)).convert("L")
    img.save(mask_path, format="PNG")
    return mask_path


def load_mask(
    session_name: str,
    resize: tuple = None,
    sessions_root: Path = None,
) -> np.ndarray | None:
    """
    Load mask.png for a session and return a (H, W) bool array.
    Pixels with value >= 128 are considered part of the wound.
    Returns None if no mask exists.
    """
    root = sessions_root or SESSIONS_DIR
    mask_path = root / session_name / "mask.png"
    if not mask_path.exists():
        return None

    img = Image.open(mask_path).convert("L")
    if resize:
        img = img.resize(resize, Image.NEAREST)
    return np.array(img) >= 128


def get_thumbnail(
    session_name: str,
    sessions_root: Path = None,
    size: tuple = (256, 192),
) -> str | None:
    """
    Return the first frame of a session as a base64-encoded JPEG string.
    Returns None if no frames are found.
    """
    root = sessions_root or SESSIONS_DIR
    frames_dir = root / session_name / "frames"
    if not frames_dir.exists():
        return None

    exts = (".png", ".jpg", ".jpeg", ".bmp")
    files = sorted(p for p in frames_dir.iterdir() if p.suffix.lower() in exts)
    if not files:
        return None

    img = cv2.imread(str(files[0]))
    if img is None:
        return None

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(img)
    pil.thumbnail(size, Image.LANCZOS)

    buf = io.BytesIO()
    pil.save(buf, format="JPEG", quality=75)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def save_scenario(
    session_name: str,
    label: str,
    description: str = "",
    zone: str = "",
    sessions_root: Path = None,
):
    """Persist a scenario tag next to the session."""
    root = sessions_root or SESSIONS_DIR
    scenario_path = root / session_name / "scenario.json"
    scenario_path.parent.mkdir(parents=True, exist_ok=True)

    scenario = {
        "label": label,
        "description": description,
        "zone": zone,
        "tagged_at": datetime.now().isoformat(),
    }
    with open(scenario_path, "w") as f:
        json.dump(scenario, f, indent=2)


