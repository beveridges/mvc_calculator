"""Tests for telemetry.telemetry (event logging wrapper)."""

from __future__ import annotations

import pytest

from telemetry import telemetry, log_utils


@pytest.fixture(autouse=True)
def _clear_buffer():
    log_utils.clear_log_buffer()
    yield
    log_utils.clear_log_buffer()


class TestLogEvent:
    def test_disabled_does_not_write(self, monkeypatch):
        monkeypatch.setattr(telemetry, "ENABLE_TELEMETRY", False)
        telemetry.log_event("startup", version="1.0")
        assert log_utils.get_buffered_logs() == []

    def test_enabled_writes_formatted_event(self, monkeypatch):
        monkeypatch.setattr(telemetry, "ENABLE_TELEMETRY", True)
        telemetry.log_event("startup", version="1.0", build="123")
        logs = log_utils.get_buffered_logs()
        assert any("EVENT: startup" in l and "version=1.0" in l and "build=123" in l for l in logs)


class TestLogError:
    def test_disabled_does_not_write(self, monkeypatch):
        monkeypatch.setattr(telemetry, "ENABLE_TELEMETRY", False)
        try:
            raise RuntimeError("boom")
        except RuntimeError as e:
            telemetry.log_error(e)
        assert log_utils.get_buffered_logs() == []

    def test_enabled_writes_exception_traceback(self, monkeypatch):
        monkeypatch.setattr(telemetry, "ENABLE_TELEMETRY", True)
        try:
            raise ValueError("kaboom")
        except ValueError as e:
            telemetry.log_error(e)
        logs = log_utils.get_buffered_logs()
        assert any("EXCEPTION" in l for l in logs)
        assert any("ValueError" in l and "kaboom" in l for l in logs)


class TestStartupShutdown:
    def test_startup_logs_event(self, monkeypatch):
        monkeypatch.setattr(telemetry, "ENABLE_TELEMETRY", True)
        telemetry.log_startup("26.04-alpha.01")
        assert any("EVENT: startup" in l for l in log_utils.get_buffered_logs())

    def test_shutdown_logs_event(self, monkeypatch):
        monkeypatch.setattr(telemetry, "ENABLE_TELEMETRY", True)
        telemetry.log_shutdown()
        assert any("EVENT: shutdown" in l for l in log_utils.get_buffered_logs())
