import getpass
import logging
import os
import platform
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from sbui.consoleui.email_utils import send_email

logger = logging.getLogger(__name__)

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


def send_license_failure_report(error_message: str):
    """
    Send email to telemetry@moviolabs.com when license validation fails.
    Subject format: MVC Calculator authorisation report (MVC Calculator {BUILDNUMBER})
    """
    try:
        from utilities.version_info import BUILDNUMBER
    except ImportError:
        BUILDNUMBER = "unknown"

    subject = f"MVC Calculator authorisation report (MVC Calculator {BUILDNUMBER})"

    try:
        from utilities.license import get_machine_id, get_country
        hwid = get_machine_id()
        country = get_country() or "Unknown"
    except Exception:
        hwid = "unknown"
        country = "unknown"

    body = f"""License validation failed.

Error: {error_message}

Machine info:
- HWID: {hwid}
- Country: {country}
- Platform: {platform.platform()}
- Hostname: {platform.node()}
- User: {getpass.getuser()}
- Timestamp: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
"""
    send_email(subject=subject, body=body, recipient="telemetry@moviolabs.com")


def send_license_success_report(license_email: str, hwid: str, country: str):
    """
    Send email to telemetry@moviolabs.com when license validation succeeds.
    Subject format: MVC Calculator authorisation report (MVC Calculator {BUILDNUMBER}) - SUCCESS
    """
    try:
        from utilities.version_info import BUILDNUMBER
    except ImportError:
        BUILDNUMBER = "unknown"

    subject = f"MVC Calculator authorisation report (MVC Calculator {BUILDNUMBER}) - SUCCESS"

    body = f"""License validation succeeded.

Licensed email: {license_email}

Machine info:
- HWID: {hwid}
- Country: {country}
- Platform: {platform.platform()}
- Hostname: {platform.node()}
- User: {getpass.getuser()}
- Timestamp: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
"""
    send_email(subject=subject, body=body, recipient="telemetry@moviolabs.com")


def _build_preactivated_launch_report_body(entitlement: Dict[str, Any]) -> str:
    from utilities.entitlement import get_entitlement_file_path
    from utilities.license import (
        get_country,
        get_country_offline,
        get_country_online,
        get_machine_id,
        validate_license_key,
    )
    from utilities.version_info import BUILDNUMBER, VERSIONNUMBER

    lic = str(entitlement.get("license_key", "")).strip()
    ok, lic_data, err = validate_license_key(lic)
    email_in_key = lic_data.get("email", "") if ok and lic_data else ""
    country_in_key = lic_data.get("country", "") if ok and lic_data else ""
    hwid_in_key = lic_data.get("hwid", "") if ok and lic_data else ""

    combined = get_country() or "n/a"
    online = get_country_online()
    offline = get_country_offline()
    hwid = get_machine_id()
    path = get_entitlement_file_path()

    lines = [
        "MVC Calculator — preactivated bundle launch report",
        "---------------------------------------------------",
        f"Timestamp (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
        f"App version: {VERSIONNUMBER}",
        f"Build number: {BUILDNUMBER}",
        "",
        "Entitlement file:",
        f"  Path: {path}",
        f"  Exists: {path.exists()}",
        "",
        "Entitlement metadata (from JSON):",
        f"  source: {entitlement.get('source')}",
        f"  format: {entitlement.get('format')}",
        f"  issued_for: {entitlement.get('issued_for')}",
        f"  bundle_id: {entitlement.get('bundle_id')}",
        f"  issued_at_utc: {entitlement.get('issued_at_utc')}",
        f"  stored_at_utc: {entitlement.get('stored_at_utc')}",
        "",
        "Decoded license payload:",
        f"  validate_license_key ok: {ok}",
        f"  decode error: {err or 'n/a'}",
        f"  email (in key): {email_in_key}",
        f"  country (in key): {country_in_key}",
        f"  hwid (in key): {hwid_in_key}",
        "",
        "This machine:",
        f"  HWID (current): {hwid}",
        f"  get_country() (combined): {combined}",
        f"  get_country_online(): {online or 'n/a'}",
        f"  get_country_offline(): {offline or 'n/a'}",
        "",
        "Host / runtime:",
        f"  OS user: {getpass.getuser()}",
        f"  Hostname: {platform.node()}",
        f"  platform.platform(): {platform.platform()}",
        f"  Python: {platform.python_version()}",
        f"  Processor: {platform.processor() or 'Unknown'}",
        "",
        "license_key (truncated):",
    ]
    if len(lic) > 80:
        lines.append(f"  {lic[:40]}...{lic[-32:]} (len={len(lic)})")
    else:
        lines.append(f"  {lic}")
    return "\n".join(lines)


def _preactivated_launch_report_worker(entitlement: Dict[str, Any]) -> None:
    try:
        body = _build_preactivated_launch_report_body(entitlement)
        try:
            from utilities.version_info import BUILDNUMBER
        except ImportError:
            BUILDNUMBER = "unknown"
        subject = f"MVC Calculator preactivated launch ({BUILDNUMBER})"
        send_email(subject=subject, body=body, recipient="telemetry@moviolabs.com")
    except Exception:
        logger.exception("Preactivated launch report worker failed")


def schedule_preactivated_launch_report_silent(entitlement: Optional[Dict[str, Any]]) -> None:
    """
    Queue a detailed launch email for preactivated installs. Never blocks the UI thread.
    Set PREACTIVATED_LAUNCH_REPORT=0 (or false/no/off) to disable.
    """
    if not isinstance(entitlement, dict):
        return
    raw = str(os.environ.get("PREACTIVATED_LAUNCH_REPORT", "")).strip().lower()
    if raw in ("0", "false", "no", "off"):
        return
    snap = dict(entitlement)
    threading.Thread(
        target=_preactivated_launch_report_worker,
        args=(snap,),
        daemon=True,
    ).start()

