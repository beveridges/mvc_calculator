import platform
from datetime import datetime
import getpass
import os
from typing import Optional, Dict, Any, List

from sbui.consoleui.email_utils import send_email
from .log_utils import (
    get_buffered_logs,
    clear_log_buffer,
    export_log_buffer_to_tempfile,
)

_LAUNCH_INFO: Optional[Dict[str, Any]] = None


def _fmt_dt(value):
    if not value:
        return "Unknown"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S UTC")
    return str(value)


def _gather_host_info():
    return {
        "user": getpass.getuser(),
        "hostname": platform.node(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "processor": platform.processor() or "Unknown",
    }


def record_launch_info(app_version: str):
    global _LAUNCH_INFO
    info = _gather_host_info()
    _LAUNCH_INFO = {
        "app_version": app_version,
        "timestamp": datetime.utcnow(),
        **info,
    }


def _format_launch_section():
    info = _LAUNCH_INFO or {}
    lines = [
        "LAUNCH INFORMATION",
        "------------------",
        f"Version: {info.get('app_version', 'Unknown')}",
        f"Timestamp: {_fmt_dt(info.get('timestamp'))}",
        f"User: {info.get('user', 'Unknown')}",
        f"Host: {info.get('hostname', 'Unknown')}",
        f"Platform: {info.get('platform', 'Unknown')}",
        f"Python: {info.get('python', 'Unknown')}",
        f"Processor: {info.get('processor', 'Unknown')}",
    ]
    return lines


def _format_close_section(app_version: str, perf_summary: Optional[Dict[str, Any]]):
    lines = [
        "",
        "CLOSE INFORMATION",
        "-----------------",
        f"Version: {app_version}",
    ]

    if not perf_summary:
        lines.append("No performance data captured.")
        return lines

    def _fmt_num(value, suffix=""):
        if value is None:
            return "n/a"
        if isinstance(value, float):
            return f"{value:.2f}{suffix}"
        return f"{value}{suffix}"

    lines.extend([
        f"Session ID: {perf_summary.get('session_id', 'n/a')}",
        f"Start: {_fmt_dt(perf_summary.get('start_time'))}",
        f"End: {_fmt_dt(perf_summary.get('end_time'))}",
        f"Duration: {_fmt_num(perf_summary.get('duration_seconds'), ' s')}",
        f"Samples captured: {perf_summary.get('sample_count', 0)}",
        "",
        "CPU usage:",
        f"  avg={_fmt_num(perf_summary.get('cpu_avg'))}%, "
        f"min={_fmt_num(perf_summary.get('cpu_min'))}%, "
        f"max={_fmt_num(perf_summary.get('cpu_max'))}%",
        "Memory usage (RSS):",
        f"  avg={_fmt_num(perf_summary.get('memory_avg'))}MB, "
        f"min={_fmt_num(perf_summary.get('memory_min'))}MB, "
        f"max={_fmt_num(perf_summary.get('memory_max'))}MB",
        "Threads:",
        f"  avg={_fmt_num(perf_summary.get('threads_avg'))}, "
        f"min={_fmt_num(perf_summary.get('threads_min'))}, "
        f"max={_fmt_num(perf_summary.get('threads_max'))}",
        "",
        f"PID: {perf_summary.get('pid', 'n/a')}",
    ])
    return lines


def send_session_summary_email(app_version: str, perf_summary: Optional[Dict[str, Any]]):
    global _LAUNCH_INFO
    lines: List[str] = []
    lines.extend(_format_launch_section())
    lines.extend(_format_close_section(app_version, perf_summary))

    buffered = get_buffered_logs()
    if buffered:
        lines.extend(["", "Telemetry log entries (excerpt):"])
        lines.extend(buffered)

    attachment_path = export_log_buffer_to_tempfile()
    attachments = [attachment_path] if attachment_path else None

    body = "\n".join(lines)
    subject = f"MVC Calculator session report ({app_version})"
    send_email(subject=subject, body=body, attachments=attachments)

    if attachment_path and os.path.exists(attachment_path):
        try:
            os.remove(attachment_path)
        except OSError:
            pass

    clear_log_buffer()
    _LAUNCH_INFO = None

