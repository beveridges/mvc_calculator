"""Smoke tests for top-level helpers defined in main.py.

These tests exercise the small module-level utilities (update_splash,
warmup_matplotlib_cache, handle_uncaught_exception) without instantiating the
full ApplicationWindow, which requires a real UI file and connected services.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from unittest.mock import MagicMock

import pytest

pytestmark = [pytest.mark.requires_qt, pytest.mark.requires_numpy, pytest.mark.requires_scipy]


@pytest.fixture(scope="module")
def main_module(qapp):
    import importlib
    # Reset existing import so that module-level initialisation re-runs.
    if "main" in sys.modules:
        del sys.modules["main"]
    return importlib.import_module("main")


class TestWarmupMatplotlibCache:
    def test_does_nothing_when_frozen(self, main_module, monkeypatch):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        # Replace subprocess.Popen so we can confirm it is never called.
        mock_popen = MagicMock()
        monkeypatch.setattr(main_module.subprocess, "Popen", mock_popen)
        main_module.warmup_matplotlib_cache()
        mock_popen.assert_not_called()

    def test_spawns_subprocess_when_not_frozen(self, main_module, monkeypatch):
        monkeypatch.setattr(sys, "frozen", False, raising=False)
        mock_popen = MagicMock()
        monkeypatch.setattr(main_module.subprocess, "Popen", mock_popen)
        main_module.warmup_matplotlib_cache()
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        assert "matplotlib" in args[0][-1]

    def test_silently_swallows_subprocess_errors(self, main_module, monkeypatch):
        monkeypatch.setattr(sys, "frozen", False, raising=False)

        def _boom(*a, **kw):
            raise OSError("no fork")

        monkeypatch.setattr(main_module.subprocess, "Popen", _boom)
        # Must not raise
        main_module.warmup_matplotlib_cache()


class TestUpdateSplash:
    def test_none_splash_is_noop(self, main_module):
        main_module.update_splash(None, "loading", 50)  # must not raise

    def test_delegates_to_splash(self, main_module):
        splash = MagicMock()
        main_module.update_splash(splash, "initialising", 42)
        splash.showMessage.assert_called_once()
        # First positional arg should contain our message and percent.
        message_arg = splash.showMessage.call_args[0][0]
        assert "initialising" in message_arg
        assert "42" in message_arg


class TestHandleUncaughtException:
    def test_logs_critical(self, main_module, caplog):
        try:
            raise RuntimeError("boom")
        except RuntimeError:
            exc_type, value, tb = sys.exc_info()

        with caplog.at_level(logging.CRITICAL, logger="root"):
            main_module.handle_uncaught_exception(exc_type, value, tb)

        assert any("Uncaught exception" in r.getMessage() for r in caplog.records)
