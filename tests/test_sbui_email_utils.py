"""Tests for sbui.consoleui.email_utils."""

from __future__ import annotations

import smtplib
import types

import pytest

from sbui.consoleui import email_utils


class _FakeSMTP:
    """Minimal SMTP_SSL stand-in that records what happened."""

    def __init__(self, server, port, context=None, timeout=None):
        self.server = server
        self.port = port
        self.context = context
        self.timeout = timeout
        self.logged_in = False
        self.sent = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def login(self, sender, password):
        self.logged_in = True

    def sendmail(self, sender, recipient, body):
        self.sent.append((sender, recipient, body))


class TestSendEmail:
    def test_successful_send(self, monkeypatch):
        fake = {}

        def _factory(*args, **kwargs):
            f = _FakeSMTP(*args, **kwargs)
            fake["obj"] = f
            return f

        monkeypatch.setattr(email_utils.smtplib, "SMTP_SSL", _factory)
        ok = email_utils.send_email("subject", "body")
        assert ok is True
        assert fake["obj"].logged_in is True
        sender, recipient, body = fake["obj"].sent[0]
        assert "subject" in body

    def test_missing_attachment_is_skipped(self, monkeypatch, tmp_path):
        def _factory(*args, **kwargs):
            return _FakeSMTP(*args, **kwargs)

        monkeypatch.setattr(email_utils.smtplib, "SMTP_SSL", _factory)
        ok = email_utils.send_email(
            "subject",
            "body",
            attachments=[str(tmp_path / "does_not_exist.txt")],
        )
        assert ok is True

    def test_existing_attachment_is_included(self, monkeypatch, tmp_path):
        path = tmp_path / "note.txt"
        path.write_text("hello", encoding="utf-8")

        captured = {}

        class _CapturingSMTP(_FakeSMTP):
            def sendmail(self, sender, recipient, body):
                captured["body"] = body
                super().sendmail(sender, recipient, body)

        monkeypatch.setattr(email_utils.smtplib, "SMTP_SSL", _CapturingSMTP)
        ok = email_utils.send_email("subject", "body", attachments=[str(path)])
        assert ok is True
        assert "note.txt" in captured["body"]

    def test_smtp_failure_returns_false(self, monkeypatch):
        def _factory(*args, **kwargs):
            raise smtplib.SMTPException("nope")

        monkeypatch.setattr(email_utils.smtplib, "SMTP_SSL", _factory)
        ok = email_utils.send_email("subject", "body")
        assert ok is False


class TestEmailFile:
    def test_file_missing_returns_false(self, tmp_path):
        missing = tmp_path / "nope.log"
        assert email_utils.email_file(str(missing)) is False

    def test_sends_existing_file(self, monkeypatch, tmp_path):
        log_file = tmp_path / "log.log"
        log_file.write_text("content", encoding="utf-8")
        calls = {}

        def _fake_send(**kwargs):
            calls.update(kwargs)
            return True

        monkeypatch.setattr(email_utils, "send_email", _fake_send)
        ok = email_utils.email_file(str(log_file))
        assert ok is True
        assert calls["attachments"] == [str(log_file)]
        assert "Session Log" in calls["subject"]
