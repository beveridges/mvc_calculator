"""Tests for sbui.consoleui.console_redirector."""

from __future__ import annotations

import sys

import pytest

pytestmark = pytest.mark.requires_qt


class TestEmittingStream:
    def test_non_empty_write_emits_signal(self, qapp):
        from sbui.consoleui.console_redirector import EmittingStream

        captured = []
        stream = EmittingStream()
        stream.text_written.connect(captured.append)
        stream.write("hello")
        qapp.processEvents()
        assert captured == ["hello"]

    def test_empty_write_is_ignored(self, qapp):
        from sbui.consoleui.console_redirector import EmittingStream

        captured = []
        stream = EmittingStream()
        stream.text_written.connect(captured.append)
        stream.write("   \n")
        qapp.processEvents()
        assert captured == []

    def test_flush_is_safe(self, qapp):
        from sbui.consoleui.console_redirector import EmittingStream
        EmittingStream().flush()  # should not raise


class TestRedirectStdout:
    def test_replaces_sys_stdout_with_signal(self, qapp):
        from sbui.consoleui.console_redirector import redirect_stdout

        captured = []
        original_stdout = sys.stdout
        try:
            stream = redirect_stdout(captured.append)
            assert sys.stdout is stream
            sys.stdout.write("piped-text")
            qapp.processEvents()
            assert captured == ["piped-text"]
        finally:
            sys.stdout = original_stdout
