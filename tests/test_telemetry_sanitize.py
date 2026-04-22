"""Tests for telemetry.sanitize."""

from __future__ import annotations

import getpass
import socket
from pathlib import Path

from telemetry import sanitize


class TestSanitizeText:
    def test_redacts_username(self, monkeypatch):
        monkeypatch.setattr(sanitize.getpass, "getuser", lambda: "alice")
        out = sanitize.sanitize_text("user alice was here")
        assert "alice" not in out
        assert "<USER>" in out

    def test_redacts_hostname(self, monkeypatch):
        monkeypatch.setattr(sanitize.socket, "gethostname", lambda: "laptop-01")
        out = sanitize.sanitize_text("host laptop-01 is online")
        assert "laptop-01" not in out
        assert "<HOST>" in out

    def test_redacts_home_path(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sanitize.Path, "home", classmethod(lambda cls: tmp_path))
        out = sanitize.sanitize_text(f"path is {tmp_path}/file.txt")
        assert str(tmp_path) not in out
        assert "<HOME>" in out

    def test_redacts_windows_user_path(self):
        out = sanitize.sanitize_text(r"C:\Users\bob\Documents\x.txt")
        assert r"C:\Users\bob" not in out
        assert r"C:\Users\<USER>" in out

    def test_redacts_linux_home(self):
        out = sanitize.sanitize_text("/home/carol/project/file.py")
        assert "/home/carol" not in out
        assert "/home/<USER>" in out

    def test_redacts_mac_users_path(self):
        out = sanitize.sanitize_text("/Users/dave/doc.md")
        assert "/Users/dave" not in out
        assert "/Users/<USER>" in out
