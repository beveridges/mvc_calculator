"""Tests for utilities.path_utils."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from utilities import path_utils


class TestIsFrozen:
    def test_reports_false_when_not_frozen(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", False, raising=False)
        assert path_utils.is_frozen() is False

    def test_reports_true_when_frozen(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        assert path_utils.is_frozen() is True


class TestAppRoot:
    def test_dev_mode_finds_main_py(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", False, raising=False)
        root = path_utils.app_root()
        assert (root / "main.py").exists()

    def test_frozen_mode_returns_internal_when_present(self, tmp_path, monkeypatch):
        exe_dir = tmp_path / "app"
        internal = exe_dir / "_internal"
        internal.mkdir(parents=True)
        exe = exe_dir / "app.exe"
        exe.write_text("")
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", str(exe), raising=False)
        assert path_utils.app_root() == internal

    def test_frozen_mode_returns_exe_dir_without_internal(self, tmp_path, monkeypatch):
        exe_dir = tmp_path / "app"
        exe_dir.mkdir()
        exe = exe_dir / "app.exe"
        exe.write_text("")
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", str(exe), raising=False)
        assert path_utils.app_root() == exe_dir


class TestBasePath:
    def test_joins_parts_under_app_root(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", False, raising=False)
        result = Path(path_utils.base_path("foo", "bar.txt"))
        assert result.name == "bar.txt"
        assert "foo" in result.parts


class TestResourcePath:
    def test_prefixes_resources(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", False, raising=False)
        result = Path(path_utils.resource_path("icons", "x.png"))
        assert "resources" in result.parts
        assert result.name == "x.png"


class TestWritablePath:
    def test_creates_directory_when_requested(self, tmp_path, monkeypatch):
        monkeypatch.setattr(path_utils, "app_root", lambda: tmp_path)
        p = path_utils.writable_path("newdir", create=True)
        assert os.path.isdir(p)

    def test_does_not_create_without_flag(self, tmp_path, monkeypatch):
        monkeypatch.setattr(path_utils, "app_root", lambda: tmp_path)
        p = path_utils.writable_path("not-created")
        assert not os.path.isdir(p)
