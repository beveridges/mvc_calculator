"""Tests for telemetry.log_utils."""

from __future__ import annotations

import logging
import os

from telemetry import log_utils


class TestLoggerAndBuffer:
    def setup_method(self):
        log_utils.clear_log_buffer()

    def test_get_logger_returns_configured_singleton(self):
        logger = log_utils.get_logger()
        assert logger is log_utils.get_logger()
        assert logger.level == logging.INFO
        assert logger.propagate is False
        assert any(isinstance(h, log_utils._InMemoryHandler) for h in logger.handlers)

    def test_messages_go_into_buffer(self):
        logger = log_utils.get_logger()
        logger.info("hello-buffer")
        logs = log_utils.get_buffered_logs()
        assert any("hello-buffer" in line for line in logs)

    def test_clear_buffer(self):
        log_utils.get_logger().info("some-entry")
        assert log_utils.get_buffered_logs()
        log_utils.clear_log_buffer()
        assert log_utils.get_buffered_logs() == []

    def test_get_log_path_is_none(self):
        assert log_utils.get_log_path() is None

    def test_export_log_buffer_to_tempfile_empty_returns_none(self):
        log_utils.clear_log_buffer()
        assert log_utils.export_log_buffer_to_tempfile() is None

    def test_export_log_buffer_to_tempfile_writes_entries(self):
        logger = log_utils.get_logger()
        logger.info("export-me")
        path = log_utils.export_log_buffer_to_tempfile()
        try:
            assert path is not None
            assert os.path.exists(path)
            contents = open(path, encoding="utf-8").read()
            assert "export-me" in contents
        finally:
            if path and os.path.exists(path):
                os.remove(path)

    def test_emit_handles_broken_record(self):
        """Ensure the in-memory handler tolerates a record that fails formatting."""
        handler = log_utils._InMemoryHandler()

        class _BadRecord:
            def getMessage(self):
                return "fallback-msg"

            levelno = 20
            levelname = "INFO"

        # Force exception during format()
        log_utils.clear_log_buffer()
        handler.emit(_BadRecord())  # should not raise
        assert any("fallback-msg" in line for line in log_utils.get_buffered_logs())
