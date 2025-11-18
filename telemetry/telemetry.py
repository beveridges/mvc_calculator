# telemetry/telemetry.py
import traceback
from .config import ENABLE_TELEMETRY
from .log_utils import get_logger

logger = get_logger()

def log_event(event_name: str, **kwargs):
    if not ENABLE_TELEMETRY:
        return
    param_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"EVENT: {event_name} {param_str}")

def log_error(error: Exception):
    if not ENABLE_TELEMETRY:
        return
    logger.error("EXCEPTION:")
    logger.error("".join(
        traceback.format_exception(type(error), error, error.__traceback__)
    ))

def log_startup(version: str):
    log_event("startup", version=version)

def log_shutdown():
    log_event("shutdown")
