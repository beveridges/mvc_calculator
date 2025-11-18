# telemetry/log_utils.py
import logging
import tempfile
import os
from collections import deque
from typing import List, Optional

_LOG_BUFFER = deque(maxlen=2048)


class _InMemoryHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
        except Exception:
            msg = record.getMessage()
        _LOG_BUFFER.append(msg)


def get_logger():
    logger = logging.getLogger("MVC_TELEMETRY")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = _InMemoryHandler()
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def get_buffered_logs() -> List[str]:
    return list(_LOG_BUFFER)


def clear_log_buffer():
    _LOG_BUFFER.clear()


def get_log_path():
    """Maintained for backwards compatibility; no on-disk log is stored."""
    return None


def export_log_buffer_to_tempfile() -> Optional[str]:
    """
    Write the buffered telemetry log to a temporary file and
    return the path so it can be attached to an email.
    """
    if not _LOG_BUFFER:
        return None

    fd, path = tempfile.mkstemp(prefix="mvc_telemetry_", suffix=".log", text=True)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write("\n".join(_LOG_BUFFER))
    return path
