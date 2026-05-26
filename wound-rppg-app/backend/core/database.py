"""
core/database.py
────────────────
SQLite persistence layer — patients + sessions metadata.

The DB file lives inside SESSIONS_DIR (wound_rppg.db) so it is included
in the same Docker volume as the session files and persists across restarts.

Thread safety: every call opens its own connection with
check_same_thread=False + WAL journal — safe for Flask + gunicorn workers.
"""

import sqlite3
import uuid
import json
from datetime import datetime
from pathlib import Path

from .session_manager import SESSIONS_DIR

DB_PATH = SESSIONS_DIR / "wound_rppg.db"


# ─── Connection helper ────────────────────────────────────────────────────────

def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c


# ─── Schema creation (idempotent) ─────────────────────────────────────────────

def init_db():
    """Create tables if they don't exist. Called at app startup."""
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS patients (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            birth_year  INTEGER,
            sex         TEXT CHECK(sex IN ('M','F','O',NULL)),
            wound_type  TEXT,
            notes       TEXT,
            created_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sessions (
            name            TEXT PRIMARY KEY,
            patient_id      TEXT REFERENCES patients(id) ON DELETE SET NULL,
            date            TEXT,
            fps             REAL,
            nb_frames       INTEGER,
            duration_s      REAL,
            has_results     INTEGER NOT NULL DEFAULT 0,
            has_mask        INTEGER NOT NULL DEFAULT 0,
            scenario_label  TEXT,
            scenario_zone   TEXT,
            wound_id        TEXT,
            snr_db          REAL,
            hr_bpm          REAL,
            score           INTEGER,
            wound_pct       REAL,
            created_at      TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_sessions_patient  ON sessions(patient_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_wound_id ON sessions(wound_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_date     ON sessions(date);
        """)


# ─── Patient CRUD ─────────────────────────────────────────────────────────────

def create_patient(name: str, birth_year: int = None, sex: str = None,
                   wound_type: str = None, notes: str = None) -> dict:
    pid = str(uuid.uuid4())
    now = datetime.now().isoformat()
    with _conn() as c:
        c.execute(
            "INSERT INTO patients(id,name,birth_year,sex,wound_type,notes,created_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (pid, name, birth_year, sex, wound_type, notes, now),
        )
    return get_patient(pid)


def get_patient(patient_id: str) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
    return dict(row) if row else None


def list_patients() -> list:
    with _conn() as c:
        rows = c.execute(
            "SELECT p.*, COUNT(s.name) as nb_sessions "
            "FROM patients p LEFT JOIN sessions s ON s.patient_id=p.id "
            "GROUP BY p.id ORDER BY p.created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def update_patient(patient_id: str, **fields) -> dict | None:
    allowed = {"name", "birth_year", "sex", "wound_type", "notes"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return get_patient(patient_id)
    cols = ", ".join(f"{k}=?" for k in updates)
    with _conn() as c:
        c.execute(f"UPDATE patients SET {cols} WHERE id=?",
                  (*updates.values(), patient_id))
    return get_patient(patient_id)


def delete_patient(patient_id: str):
    with _conn() as c:
        c.execute("DELETE FROM patients WHERE id=?", (patient_id,))


# ─── Session metadata CRUD ────────────────────────────────────────────────────

def upsert_session(name: str, **fields) -> dict:
    """
    Insert or update a session row.  Call this:
    - after upload  (has_results=False)
    - after analysis completes (with snr_db, hr_bpm, score, etc.)
    - after scenario tag
    """
    now = datetime.now().isoformat()
    with _conn() as c:
        existing = c.execute("SELECT * FROM sessions WHERE name=?", (name,)).fetchone()
        if existing:
            allowed = {
                "patient_id", "date", "fps", "nb_frames", "duration_s",
                "has_results", "has_mask", "scenario_label", "scenario_zone",
                "wound_id", "snr_db", "hr_bpm", "score", "wound_pct",
            }
            updates = {k: v for k, v in fields.items() if k in allowed}
            if updates:
                cols = ", ".join(f"{k}=?" for k in updates)
                c.execute(f"UPDATE sessions SET {cols} WHERE name=?",
                          (*updates.values(), name))
        else:
            c.execute(
                "INSERT OR IGNORE INTO sessions"
                "(name,patient_id,date,fps,nb_frames,duration_s,"
                " has_results,has_mask,scenario_label,scenario_zone,"
                " wound_id,snr_db,hr_bpm,score,wound_pct,created_at) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    name,
                    fields.get("patient_id"),
                    fields.get("date"),
                    fields.get("fps"),
                    fields.get("nb_frames"),
                    fields.get("duration_s"),
                    int(fields.get("has_results", 0)),
                    int(fields.get("has_mask", 0)),
                    fields.get("scenario_label"),
                    fields.get("scenario_zone"),
                    fields.get("wound_id"),
                    fields.get("snr_db"),
                    fields.get("hr_bpm"),
                    fields.get("score"),
                    fields.get("wound_pct"),
                    now,
                ),
            )
    return get_session_meta(name)


def get_session_meta(name: str) -> dict | None:
    with _conn() as c:
        row = c.execute(
            "SELECT s.*, p.name as patient_name "
            "FROM sessions s LEFT JOIN patients p ON p.id=s.patient_id "
            "WHERE s.name=?", (name,)
        ).fetchone()
    return dict(row) if row else None


def list_sessions_db(patient_id: str = None, wound_id: str = None) -> list:
    query  = ("SELECT s.*, p.name as patient_name "
              "FROM sessions s LEFT JOIN patients p ON p.id=s.patient_id")
    params = []
    where  = []
    if patient_id:
        where.append("s.patient_id=?"); params.append(patient_id)
    if wound_id:
        where.append("s.wound_id=?"); params.append(wound_id)
    if where:
        query += " WHERE " + " AND ".join(where)
    query += " ORDER BY s.date DESC"
    with _conn() as c:
        rows = c.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def assign_session_to_patient(session_name: str, patient_id: str):
    with _conn() as c:
        c.execute("UPDATE sessions SET patient_id=? WHERE name=?",
                  (patient_id, session_name))


def sync_sessions_from_filesystem():
    """
    Scan SESSIONS_DIR and register any sessions not yet in the DB.
    Called at startup to ensure the DB stays in sync with the filesystem.
    """
    if not SESSIONS_DIR.exists():
        return
    for session_dir in SESSIONS_DIR.iterdir():
        if not session_dir.is_dir():
            continue
        name = session_dir.name
        frames_dir = session_dir / "frames"
        if not frames_dir.exists():
            continue

        meta_path    = session_dir / "metadata.json"
        results_path = session_dir / "results.json"
        scenario_path = session_dir / "scenario.json"
        mask_path    = session_dir / "mask.png"

        meta     = json.loads(meta_path.read_text())    if meta_path.exists()     else {}
        results  = json.loads(results_path.read_text()) if results_path.exists()  else {}
        scenario = json.loads(scenario_path.read_text()) if scenario_path.exists() else {}

        upsert_session(
            name,
            date          = meta.get("date") or results.get("meta", {}).get("date"),
            fps           = meta.get("measured_fps"),
            nb_frames     = meta.get("nb_frames"),
            duration_s    = meta.get("duration_s"),
            has_results   = int(results_path.exists()),
            has_mask      = int(mask_path.exists()),
            scenario_label = scenario.get("label"),
            scenario_zone  = scenario.get("zone"),
            wound_id       = scenario.get("wound_id"),
            snr_db         = results.get("snr", {}).get("mean_snr"),
            hr_bpm         = results.get("hr", {}).get("hr_bpm"),
            score          = results.get("quality", {}).get("score"),
            wound_pct      = results.get("wound_area", {}).get("pct"),
        )
