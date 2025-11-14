# telemetry/log_utils.py
import logging
import os
from pathlib import Path

from .config import LOG_FILENAME

def get_log_path():
    """Ensures telemetry file lives next to the executable."""
    base = Path(getattr(sys, '_MEIPASS', Path.cwd()))
    log_path = base / LOG_FILENAME
    return log_path

def get_logger():
    logger = logging.getLogger("MVC_TELEMETRY")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.FileHandler(get_log_path(), encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
