"""Tests for telemetry.perf_monitor."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

pytest.importorskip("psutil", reason="perf_monitor requires psutil")

from telemetry import perf_monitor  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch):
    # Ensure each test starts with a clean module state.
    perf_monitor._stop_event.clear()
    perf_monitor._thread = None
    perf_monitor._summary_data = {}
    perf_monitor.session_id = None
    yield
    perf_monitor._stop_event.set()
    perf_monitor._thread = None
    perf_monitor._summary_data = {}
    perf_monitor.session_id = None


class TestResetSummary:
    def test_reset_summary_structure(self):
        perf_monitor.session_id = "abc"
        data = perf_monitor._reset_summary()
        assert data["session_id"] == "abc"
        for k in ("cpu_total", "memory_total", "threads_total", "sample_count"):
            assert data[k] == 0 or data[k] == 0.0


class TestUpdateSummary:
    def test_first_sample_sets_min_max(self):
        perf_monitor._summary_data = perf_monitor._reset_summary()
        perf_monitor._summary_data["start_time"] = datetime.utcnow() - timedelta(seconds=1)
        perf_monitor._update_summary(cpu=25.0, memory=128.0, threads=5, pid=1234)
        data = perf_monitor._summary_data
        assert data["sample_count"] == 1
        assert data["cpu_min"] == data["cpu_max"] == 25.0
        assert data["memory_min"] == data["memory_max"] == 128.0
        assert data["threads_min"] == data["threads_max"] == 5
        assert data["pid"] == 1234
        assert data["duration_seconds"] >= 0

    def test_multiple_samples_update_min_max(self):
        perf_monitor._summary_data = perf_monitor._reset_summary()
        perf_monitor._summary_data["start_time"] = datetime.utcnow()
        perf_monitor._update_summary(10.0, 100.0, 3, 1)
        perf_monitor._update_summary(50.0, 200.0, 7, 1)
        perf_monitor._update_summary(30.0, 150.0, 5, 1)
        data = perf_monitor._summary_data
        assert data["sample_count"] == 3
        assert data["cpu_min"] == 10.0
        assert data["cpu_max"] == 50.0
        assert data["memory_min"] == 100.0
        assert data["memory_max"] == 200.0
        assert data["threads_min"] == 3
        assert data["threads_max"] == 7


class TestFinalizeSummary:
    def test_returns_none_when_empty(self):
        perf_monitor._summary_data = {}
        assert perf_monitor._finalize_summary() is None

    def test_averages_and_cleans_internal_fields(self):
        perf_monitor._summary_data = perf_monitor._reset_summary()
        perf_monitor._summary_data["start_time"] = datetime.utcnow()
        perf_monitor._update_summary(10.0, 100.0, 2, 1)
        perf_monitor._update_summary(30.0, 200.0, 4, 1)
        result = perf_monitor._finalize_summary()
        assert result["cpu_avg"] == 20.0
        assert result["memory_avg"] == 150.0
        assert result["threads_avg"] == 3.0
        # Internal totals removed
        for key in ("cpu_total", "memory_total", "threads_total"):
            assert key not in result

    def test_zero_samples_avg_none(self):
        perf_monitor._summary_data = perf_monitor._reset_summary()
        perf_monitor._summary_data["start_time"] = datetime.utcnow()
        result = perf_monitor._finalize_summary()
        assert result["cpu_avg"] is None


class TestLifecycle:
    def test_start_is_noop_when_telemetry_disabled(self, monkeypatch):
        monkeypatch.setattr(perf_monitor, "ENABLE_TELEMETRY", False)
        perf_monitor.start_performance_monitor()
        assert perf_monitor._thread is None

    def test_stop_returns_none_after_noop_start(self, monkeypatch):
        monkeypatch.setattr(perf_monitor, "ENABLE_TELEMETRY", False)
        perf_monitor.start_performance_monitor()
        assert perf_monitor.stop_performance_monitor() is None

    def test_get_session_id_initially_none(self):
        assert perf_monitor.get_session_id() is None

    def test_start_then_stop_captures_summary(self, monkeypatch):
        """Even with a mocked sampler, start/stop should set session id and return a dict."""
        monkeypatch.setattr(perf_monitor, "ENABLE_TELEMETRY", True)
        # Replace sample_performance with a no-op that waits on the stop event.
        called = {"ran": False}

        def _fake_sampler():
            called["ran"] = True
            # Block briefly on the stop event; stop_performance_monitor sets it.
            perf_monitor._stop_event.wait(timeout=2)

        monkeypatch.setattr(perf_monitor, "sample_performance", _fake_sampler)
        perf_monitor.start_performance_monitor()
        assert perf_monitor.get_session_id() is not None
        summary = perf_monitor.stop_performance_monitor(timeout=2.0)
        assert summary is not None
        assert summary["session_id"] == perf_monitor.get_session_id() or summary["session_id"] is not None
        assert called["ran"] is True
