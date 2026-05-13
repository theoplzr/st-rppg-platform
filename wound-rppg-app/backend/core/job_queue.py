import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

_executor = ThreadPoolExecutor(max_workers=1)
_jobs: dict[str, dict] = {}
_lock = threading.Lock()

def _run(job_id: str, fn, *args, **kwargs):
    with _lock:
        _jobs[job_id]["status"] = "running"
    try:
        result = fn(*args, **kwargs)
        with _lock:
            _jobs[job_id].update({
                "status": "done",
                "result": result,
                "finished_at": datetime.utcnow().isoformat(),
            })
    except Exception as e:
        with _lock:
            _jobs[job_id].update({
                "status": "error",
                "error": str(e),
                "finished_at": datetime.utcnow().isoformat(),
            })

def submit(fn, *args, **kwargs) -> str:
    job_id = str(uuid.uuid4())
    with _lock:
        _jobs[job_id] = {"status": "pending", "submitted_at": datetime.utcnow().isoformat()}
    _executor.submit(_run, job_id, fn, *args, **kwargs)
    return job_id

def get_job(job_id: str) -> dict | None:
    with _lock:
        return dict(_jobs.get(job_id, {})) or None