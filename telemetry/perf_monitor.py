# telemetry/perf_monitor.py

import psutil
import time
import threading
from uuid import uuid4
from datetime import datetime
from typing import Optional, Dict, Any

from .log_utils import get_logger
from .config import PERF_SAMPLE_INTERVAL, ENABLE_TELEMETRY

logger = get_logger()

session_id = None  # anonymous session ID, new each run
_stop_event = threading.Event()
_thread = None
_summary_data: Dict[str, Any] = {}


def _reset_summary():
    return {
        "session_id": session_id,
        "start_time": None,
        "end_time": None,
        "duration_seconds": 0.0,
        "sample_count": 0,
        "cpu_total": 0.0,
        "cpu_min": None,
        "cpu_max": None,
        "memory_total": 0.0,
        "memory_min": None,
        "memory_max": None,
        "threads_total": 0,
        "threads_min": None,
        "threads_max": None,
        "pid": None,
    }


def _ensure_summary():
    global _summary_data
    if not _summary_data:
        _summary_data = _reset_summary()


def _update_summary(cpu, memory, threads, pid):
    _ensure_summary()
    data = _summary_data
    data["sample_count"] += 1
    data["cpu_total"] += cpu
    data["memory_total"] += memory
    data["threads_total"] += threads
    data["cpu_min"] = cpu if data["cpu_min"] is None else min(data["cpu_min"], cpu)
    data["cpu_max"] = cpu if data["cpu_max"] is None else max(data["cpu_max"], cpu)
    data["memory_min"] = memory if data["memory_min"] is None else min(data["memory_min"], memory)
    data["memory_max"] = memory if data["memory_max"] is None else max(data["memory_max"], memory)
    data["threads_min"] = threads if data["threads_min"] is None else min(data["threads_min"], threads)
    data["threads_max"] = threads if data["threads_max"] is None else max(data["threads_max"], threads)
    data["end_time"] = datetime.utcnow()
    data["pid"] = pid
    if data["start_time"]:
        data["duration_seconds"] = (data["end_time"] - data["start_time"]).total_seconds()


def _finalize_summary():
    if not _summary_data:
        return None

    data = _summary_data.copy()
    if data["sample_count"]:
        data["cpu_avg"] = data["cpu_total"] / data["sample_count"]
        data["memory_avg"] = data["memory_total"] / data["sample_count"]
        data["threads_avg"] = data["threads_total"] / data["sample_count"]
    else:
        data["cpu_avg"] = None
        data["memory_avg"] = None
        data["threads_avg"] = None

    if data["start_time"] and not data["end_time"]:
        data["end_time"] = datetime.utcnow()
        data["duration_seconds"] = (data["end_time"] - data["start_time"]).total_seconds()

    # Remove internal totals before returning
    for key in ("cpu_total", "memory_total", "threads_total"):
        data.pop(key, None)

    return data


def sample_performance():
    if not ENABLE_TELEMETRY:
        return

    process = psutil.Process()
    _ensure_summary()
    _summary_data["pid"] = process.pid

    while not _stop_event.is_set():
        try:
            cpu = psutil.cpu_percent(interval=None)
            memory = process.memory_info().rss / (1024 * 1024)  # MB
            threads = process.num_threads()

            logger.info(
                f"PERF: cpu={cpu} mem={memory:.2f}MB threads={threads} session={session_id}"
            )
            _update_summary(cpu, memory, threads, process.pid)

        except Exception as e:
            logger.error(f"PERF_ERROR: {repr(e)}")

        if _stop_event.wait(PERF_SAMPLE_INTERVAL):
            break


def start_performance_monitor():
    """Start background thread."""
    global _thread, session_id, _summary_data
    if not ENABLE_TELEMETRY:
        return
    if _thread and _thread.is_alive():
        return

    session_id = str(uuid4())
    _stop_event.clear()
    _summary_data = _reset_summary()
    _summary_data["session_id"] = session_id
    _summary_data["start_time"] = datetime.utcnow()
    _thread = threading.Thread(target=sample_performance, daemon=True)
    _thread.start()


def stop_performance_monitor(timeout: float = 1.0) -> Optional[Dict[str, Any]]:
    """Signal the background thread to stop and return summary data."""
    global _thread, _summary_data
    _stop_event.set()
    if _thread and _thread.is_alive():
        _thread.join(timeout=timeout)
    _thread = None
    summary = _finalize_summary()
    _summary_data = {}
    return summary


def get_session_id() -> Optional[str]:
    return session_id
