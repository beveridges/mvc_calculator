"""Tests for sbui.consoleui.console_output (QPlainTextEdit handler + dialog + SBConsoleOutput)."""

from __future__ import annotations

import logging

import pytest

pytestmark = pytest.mark.requires_qt


@pytest.fixture
def plain_text_edit(qapp):
    from PyQt5.QtWidgets import QPlainTextEdit
    return QPlainTextEdit()


class TestQtPlainTextEditHandler:
    def test_emit_appends_formatted_text(self, qapp, plain_text_edit):
        from sbui.consoleui.console_output import QtPlainTextEditHandler

        handler = QtPlainTextEditHandler(plain_text_edit, formatter=logging.Formatter("%(message)s"))
        record = logging.LogRecord("t", logging.INFO, "", 0, "hello-log", None, None)
        handler.emit(record)
        qapp.processEvents()
        assert "hello-log" in plain_text_edit.toPlainText()

    def test_emit_handles_duck_typed_target(self, qapp):
        from sbui.consoleui.console_output import QtPlainTextEditHandler

        class _Duck:
            def __init__(self):
                self.lines = []

            def appendPlainText(self, line):
                self.lines.append(line)

        target = _Duck()
        handler = QtPlainTextEditHandler(target, formatter=logging.Formatter("%(message)s"))
        record = logging.LogRecord("t", logging.INFO, "", 0, "duck", None, None)
        handler.emit(record)
        assert target.lines == ["duck"]

    def test_emit_removes_handler_when_widget_deleted(self, qapp):
        from sbui.consoleui.console_output import QtPlainTextEditHandler

        class _Boom:
            def appendPlainText(self, *a, **kw):
                raise RuntimeError("deleted")

            def verticalScrollBar(self):
                raise RuntimeError("deleted")

        boom = _Boom()
        # PyQt's isinstance check needs a real QPlainTextEdit to call the fast path;
        # passing a duck will take the else branch, which also handles RuntimeError.
        handler = QtPlainTextEditHandler(boom, formatter=logging.Formatter("%(message)s"))
        root = logging.getLogger()
        root.addHandler(handler)
        try:
            record = logging.LogRecord("t", logging.INFO, "", 0, "x", None, None)
            handler.emit(record)  # should not raise
            assert handler not in root.handlers
        finally:
            if handler in root.handlers:
                root.removeHandler(handler)


class TestSendLogDialog:
    def test_get_message_returns_empty_by_default(self, qapp):
        from sbui.consoleui.console_output import SendLogDialog

        dlg = SendLogDialog()
        assert dlg.get_message() == ""

    def test_get_message_returns_user_text(self, qapp):
        from sbui.consoleui.console_output import SendLogDialog

        dlg = SendLogDialog()
        dlg.message_edit.setPlainText("hello message")
        assert dlg.get_message() == "hello message"


@pytest.fixture
def _patched_redirect(monkeypatch):
    """SBConsoleOutput replaces sys.stdout in its constructor; neutralise that for tests."""
    from sbui.consoleui import console_output
    monkeypatch.setattr(console_output, "redirect_stdout", lambda *_a, **_k: None)


class TestSBConsoleOutput:
    def test_send_log_returns_false_when_no_logfile(self, qapp, plain_text_edit, _patched_redirect):
        from sbui.consoleui.console_output import SBConsoleOutput

        console = SBConsoleOutput(target=plain_text_edit)
        assert console.send_log() is False

    def test_send_log_returns_false_when_logfile_missing(
        self, qapp, plain_text_edit, tmp_path, _patched_redirect
    ):
        from sbui.consoleui.console_output import SBConsoleOutput

        console = SBConsoleOutput(
            target=plain_text_edit, logfile=str(tmp_path / "nope.log")
        )
        assert console.send_log() is False

    def test_constructor_applies_style_to_target(self, qapp, plain_text_edit, _patched_redirect):
        from sbui.consoleui.console_output import SBConsoleOutput

        custom_style = "QPlainTextEdit { color: red; }"
        SBConsoleOutput(target=plain_text_edit, style=custom_style)
        assert "color: red" in plain_text_edit.styleSheet()
