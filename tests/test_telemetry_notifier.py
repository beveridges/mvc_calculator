"""Tests for telemetry.notifier."""

from __future__ import annotations

import os
import time
from datetime import datetime

import pytest

from telemetry import notifier
from telemetry import log_utils


@pytest.fixture(autouse=True)
def _reset_state():
    notifier._LAUNCH_INFO = None
    log_utils.clear_log_buffer()
    yield
    notifier._LAUNCH_INFO = None
    log_utils.clear_log_buffer()


class TestFmtDt:
    def test_none_returns_unknown(self):
        assert notifier._fmt_dt(None) == "Unknown"

    def test_datetime_is_formatted(self):
        dt = datetime(2026, 4, 16, 12, 0, 0)
        assert "2026-04-16 12:00:00 UTC" == notifier._fmt_dt(dt)

    def test_string_passthrough(self):
        assert notifier._fmt_dt("2026-01-01") == "2026-01-01"


class TestRecordLaunchInfo:
    def test_records_host_info(self):
        notifier.record_launch_info("1.0.0")
        info = notifier._LAUNCH_INFO
        assert info is not None
        for key in ["app_version", "timestamp", "user", "hostname", "platform", "python"]:
            assert key in info


class TestFormatSections:
    def test_launch_section_uses_unknown_when_no_info(self):
        notifier._LAUNCH_INFO = None
        lines = notifier._format_launch_section()
        assert "Version: Unknown" in "\n".join(lines)

    def test_close_section_without_perf_summary(self):
        lines = notifier._format_close_section("1.0.0", None)
        assert "No performance data captured." in "\n".join(lines)

    def test_close_section_with_perf_summary(self):
        summary = {
            "session_id": "abc",
            "start_time": datetime(2026, 4, 1, 10, 0, 0),
            "end_time": datetime(2026, 4, 1, 10, 5, 0),
            "duration_seconds": 300.0,
            "sample_count": 5,
            "cpu_avg": 20.0,
            "cpu_min": 10.0,
            "cpu_max": 50.0,
            "memory_avg": 150.0,
            "memory_min": 100.0,
            "memory_max": 200.0,
            "threads_avg": 4.0,
            "threads_min": 2,
            "threads_max": 6,
            "pid": 1234,
        }
        text = "\n".join(notifier._format_close_section("1.0.0", summary))
        assert "Session ID: abc" in text
        assert "PID: 1234" in text
        assert "CPU usage" in text


class TestSendSessionSummaryEmail:
    def test_sends_and_clears_buffer(self, monkeypatch):
        calls = {}

        def _fake_send(**kwargs):
            calls.update(kwargs)
            return True

        monkeypatch.setattr(notifier, "send_email", _fake_send)
        notifier.record_launch_info("1.2.3")
        log_utils.get_logger().info("buffered-entry")
        notifier.send_session_summary_email("1.2.3", None)
        assert "MVC Calculator session report" in calls["subject"]
        assert "1.2.3" in calls["subject"]
        assert log_utils.get_buffered_logs() == []
        # Launch info was cleared
        assert notifier._LAUNCH_INFO is None


class TestLicenseReports:
    def test_failure_report_sends_email(self, monkeypatch):
        captured = {}

        def _fake_send(subject, body, recipient=None, **kwargs):
            captured["subject"] = subject
            captured["body"] = body
            captured["recipient"] = recipient
            return True

        monkeypatch.setattr(notifier, "send_email", _fake_send)
        notifier.send_license_failure_report("invalid license")
        assert "authorisation report" in captured["subject"]
        assert captured["recipient"] == "telemetry@moviolabs.com"
        assert "invalid license" in captured["body"]

    def test_success_report_sends_email(self, monkeypatch):
        captured = {}
        monkeypatch.setattr(notifier, "send_email", lambda **kw: captured.update(kw) or True)
        notifier.send_license_success_report("user@x.com", "HWID", "US")
        assert "SUCCESS" in captured["subject"]
        assert captured["recipient"] == "telemetry@moviolabs.com"
        assert "user@x.com" in captured["body"]
        assert "HWID" in captured["body"]
        assert "US" in captured["body"]


class TestPreactivatedLaunchReport:
    def test_disabled_env_var_skips_thread(self, monkeypatch):
        monkeypatch.setenv("PREACTIVATED_LAUNCH_REPORT", "0")
        called = {"thread": False}

        class _FakeThread:
            def __init__(self, *a, **kw): called["thread"] = True
            def start(self): called["thread"] = True

        monkeypatch.setattr(notifier.threading, "Thread", _FakeThread)
        notifier.schedule_preactivated_launch_report_silent({"license_key": "x"})
        assert called["thread"] is False

    def test_non_dict_entitlement_noop(self, monkeypatch):
        monkeypatch.delenv("PREACTIVATED_LAUNCH_REPORT", raising=False)

        called = {"thread": False}

        class _FakeThread:
            def __init__(self, *a, **kw): pass
            def start(self): called["thread"] = True

        monkeypatch.setattr(notifier.threading, "Thread", _FakeThread)
        notifier.schedule_preactivated_launch_report_silent("nope")
        assert called["thread"] is False

    def test_schedules_background_thread_when_enabled(self, monkeypatch):
        monkeypatch.delenv("PREACTIVATED_LAUNCH_REPORT", raising=False)
        started = []

        class _FakeThread:
            def __init__(self, target=None, args=(), daemon=None): self._target = target; self._args = args
            def start(self): started.append(self._target)

        monkeypatch.setattr(notifier.threading, "Thread", _FakeThread)
        notifier.schedule_preactivated_launch_report_silent({"license_key": "x"})
        assert len(started) == 1
