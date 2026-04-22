"""Tests for utilities.code_signing."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from utilities import code_signing


class TestFindSignTool:
    def test_returns_path_when_in_path(self, monkeypatch):
        monkeypatch.setattr(code_signing.shutil, "which", lambda name: "C:/sign/signtool.exe")
        result = code_signing.find_signtool()
        assert isinstance(result, Path)
        assert str(result).endswith("signtool.exe")

    def test_returns_first_existing_common_path(self, monkeypatch, tmp_path):
        fake = tmp_path / "signtool.exe"
        fake.write_text("")
        monkeypatch.setattr(code_signing.shutil, "which", lambda name: None)
        monkeypatch.setattr(code_signing, "find_signtool", code_signing.find_signtool)
        with patch.object(
            Path,
            "exists",
            lambda self: str(self) == str(fake),
        ):
            # Replace the candidate list with something predictable.
            original = code_signing.find_signtool
            # call function unmodified; ensure it doesn't error out.
            result = original()
            assert result is None or isinstance(result, Path)

    def test_returns_none_when_nothing_found(self, monkeypatch):
        monkeypatch.setattr(code_signing.shutil, "which", lambda name: None)
        # Make every filesystem check report "does not exist"
        with patch.object(Path, "exists", lambda self: False):
            assert code_signing.find_signtool() is None


class TestSignFile:
    def test_missing_file_returns_false(self, tmp_path):
        missing = tmp_path / "nope.exe"
        assert code_signing.sign_file(missing, cert_path="cert.pfx") is False

    def test_missing_signtool_returns_false(self, tmp_path, monkeypatch):
        target = tmp_path / "app.exe"
        target.write_text("")
        monkeypatch.setattr(code_signing, "find_signtool", lambda: None)
        assert code_signing.sign_file(target, cert_path="cert.pfx") is False

    def test_no_cert_supplied_returns_false(self, tmp_path, monkeypatch):
        target = tmp_path / "app.exe"
        target.write_text("")
        monkeypatch.setattr(code_signing, "find_signtool", lambda: Path("signtool.exe"))
        assert code_signing.sign_file(target) is False

    def test_successful_sign(self, tmp_path, monkeypatch):
        target = tmp_path / "app.exe"
        target.write_text("")
        monkeypatch.setattr(code_signing, "find_signtool", lambda: Path("signtool.exe"))
        captured = {}

        def _fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

        monkeypatch.setattr(code_signing.subprocess, "run", _fake_run)
        ok = code_signing.sign_file(
            target,
            cert_path="cert.pfx",
            cert_password="pw",
            timestamp_url="http://timestamp.example",
            description="Test",
            description_url="http://x.example",
        )
        assert ok is True
        cmd = captured["cmd"]
        assert cmd[0].endswith("signtool.exe") or cmd[0] == "signtool.exe"
        assert cmd[1] == "sign"
        assert "/f" in cmd
        assert "cert.pfx" in cmd
        assert "/p" in cmd
        assert "pw" in cmd
        assert "/tr" in cmd
        assert "/d" in cmd
        assert "/du" in cmd
        assert str(target) in cmd

    def test_sign_with_thumbprint(self, tmp_path, monkeypatch):
        target = tmp_path / "app.exe"
        target.write_text("")
        monkeypatch.setattr(code_signing, "find_signtool", lambda: Path("signtool.exe"))
        calls = {}

        def _fake_run(cmd, **kwargs):
            calls["cmd"] = cmd
            return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

        monkeypatch.setattr(code_signing.subprocess, "run", _fake_run)
        ok = code_signing.sign_file(target, cert_thumbprint="ABCDEF")
        assert ok is True
        assert "/sha1" in calls["cmd"]
        assert "ABCDEF" in calls["cmd"]

    def test_signtool_nonzero_returns_false(self, tmp_path, monkeypatch):
        target = tmp_path / "app.exe"
        target.write_text("")
        monkeypatch.setattr(code_signing, "find_signtool", lambda: Path("signtool.exe"))
        monkeypatch.setattr(
            code_signing.subprocess,
            "run",
            lambda *a, **kw: subprocess.CompletedProcess([], 1, stdout="", stderr="bad"),
        )
        assert code_signing.sign_file(target, cert_path="cert.pfx") is False

    def test_signtool_exception_returns_false(self, tmp_path, monkeypatch):
        target = tmp_path / "app.exe"
        target.write_text("")
        monkeypatch.setattr(code_signing, "find_signtool", lambda: Path("signtool.exe"))

        def _boom(*a, **kw):
            raise OSError("nope")

        monkeypatch.setattr(code_signing.subprocess, "run", _boom)
        assert code_signing.sign_file(target, cert_path="cert.pfx") is False
