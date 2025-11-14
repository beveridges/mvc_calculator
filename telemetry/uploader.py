# telemetry/uploader.py

import requests
from .config import UPLOAD_ENABLED, UPLOAD_ENDPOINT, LOG_FILENAME
from pathlib import Path

def upload_logs():
    """Uploads log file to remote server."""
    if not UPLOAD_ENABLED or not UPLOAD_ENDPOINT:
        return False

    log_path = Path(LOG_FILENAME)
    if not log_path.exists():
        return False

    files = {"file": open(log_path, "rb")}
    r = requests.post(UPLOAD_ENDPOINT, files=files)

    return r.status_code == 200
