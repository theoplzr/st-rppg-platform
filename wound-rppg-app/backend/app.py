"""
app.py — Flask API Wound-rPPG
"""

import os
import logging
from flask import Flask, request
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
log = logging.getLogger(__name__)

from api.routes_sessions  import bp_sessions
from api.routes_analysis  import bp_analysis
from api.routes_scenarios import bp_scenarios
from api.routes_export    import bp_export
from api.routes_upload    import bp_upload

app = Flask(__name__)

_raw_origins = os.getenv("ALLOWED_ORIGINS", "")
_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]
_allow_all_origins = not _origins

CORS(
    app,
    resources={r"/api/*": {"origins": _origins or "*"}},
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    max_age=86400,
)
log.info("CORS origins: %s", _origins)


def _origin_is_allowed(origin: str) -> bool:
    if not origin:
        return False
    return _allow_all_origins or origin in _origins


@app.after_request
def add_cors_headers(response):
    """
    Force CORS headers on API responses, including error/preflight paths.
    This makes deploy-time misconfigurations much easier to diagnose from the browser.
    """
    if not request.path.startswith("/api/"):
        return response

    origin = request.headers.get("Origin")
    if _origin_is_allowed(origin):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Max-Age"] = "86400"

    return response


@app.route("/api", methods=["OPTIONS"])
@app.route("/api/<path:_path>", methods=["OPTIONS"])
def api_preflight(_path=""):
    return ("", 204)

app.register_blueprint(bp_sessions,  url_prefix="/api/sessions")
app.register_blueprint(bp_analysis,  url_prefix="/api/analysis")
app.register_blueprint(bp_scenarios, url_prefix="/api/scenarios")
app.register_blueprint(bp_export,    url_prefix="/api/export")
app.register_blueprint(bp_upload,    url_prefix="/api/upload")


@app.route("/api/health")
def health():
    return {"status": "ok", "version": "1.1.0"}


if __name__ == "__main__":
    _debug = os.getenv("FLASK_ENV", "production") == "development"
    app.run(debug=_debug, host="0.0.0.0", port=5000)
