"""Tests for telemetry.config."""

from __future__ import annotations

import importlib
import sys


def _reload_with_env(env):
    import os
    saved = {k: os.environ.get(k) for k in env}
    try:
        for k, v in env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        if "telemetry.config" in sys.modules:
            del sys.modules["telemetry.config"]
        return importlib.import_module("telemetry.config")
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class TestTelemetryConfig:
    def test_disabled_by_default_in_source_mode(self):
        mod = _reload_with_env({"TELEMETRY": None})
        # Not frozen in the test environment, so telemetry is off.
        assert mod.RUNNING_FROZEN is False
        assert mod.ENABLE_TELEMETRY is False

    def test_env_forces_enabled(self):
        mod = _reload_with_env({"TELEMETRY": "1"})
        assert mod.ENABLE_TELEMETRY is True

    def test_env_forces_disabled(self):
        mod = _reload_with_env({"TELEMETRY": "0"})
        assert mod.ENABLE_TELEMETRY is False

    def test_env_false_word_disables(self):
        mod = _reload_with_env({"TELEMETRY": "false"})
        assert mod.ENABLE_TELEMETRY is False

    def test_perf_sample_interval_is_positive_int(self):
        mod = _reload_with_env({"TELEMETRY": "0"})
        assert isinstance(mod.PERF_SAMPLE_INTERVAL, int)
        assert mod.PERF_SAMPLE_INTERVAL > 0
