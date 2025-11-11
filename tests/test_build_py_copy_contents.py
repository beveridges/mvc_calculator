# tests/test_build_py_copy_contents.py
"""
Stage 5 — Unit tests for copy_contents()

Validates both Bernstein and MVC build.py variants.
Ensures:
 - Files and folders copy correctly
 - Existing destination is overwritten
 - Single-file copy works
 - Missing source handled gracefully
"""

from __future__ import annotations
import os, shutil
from pathlib import Path
import importlib.util
import pytest


# ---------------------------------------------------------------------
# Fixture: dynamically import build.py (Bernstein / MVC)
# ---------------------------------------------------------------------
@pytest.fixture(params=["BERNSTEIN_BUILD", "MVC_BUILD"])
def builder_module(request):
    path = os.environ.get(request.param)
    if not path:
        pytest.skip(f"{request.param} not set")
    spec = importlib.util.spec_from_file_location(request.param.lower(), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------
# Core tests
# ---------------------------------------------------------------------
def test_copy_contents_directory_to_directory(tmp_path: Path, builder_module):
    """Copies an entire directory recursively."""
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    sub = src / "subdir"
    sub.mkdir(parents=True)
    (src / "a.txt").write_text("AAA")
    (sub / "b.txt").write_text("BBB")

    func = builder_module.copy_contents
    func(src, dst)

    # Verify structure replicated
    assert (dst / "a.txt").exists()
    assert (dst / "subdir" / "b.txt").exists()
    assert (dst / "a.txt").read_text() == "AAA"


def test_copy_contents_overwrites_existing_destination(tmp_path: Path, builder_module):
    """Destination folder should be replaced if already exists."""
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "new.txt").write_text("fresh")
    dst.mkdir()
    (dst / "old.txt").write_text("stale")

    func = builder_module.copy_contents
    func(src, dst)

    names = [p.name for p in dst.iterdir()]
    # old file removed, new file present
    assert "new.txt" in names and "old.txt" not in names


def test_copy_contents_single_file(tmp_path: Path, builder_module):
    """Handles case where src is a single file."""
    src = tmp_path / "onefile.txt"
    dst = tmp_path / "copy/onefile.txt"
    src.write_text("hello world")

    func = builder_module.copy_contents
    func(src, dst)

    assert dst.exists()
    assert dst.read_text() == "hello world"


def test_copy_contents_missing_source_returns_gracefully(tmp_path: Path, builder_module):
    """If src does not exist, should not crash."""
    src = tmp_path / "nope"
    dst = tmp_path / "dest"
    func = builder_module.copy_contents
    func(src, dst)
    assert not dst.exists()  # nothing should be created


def test_copy_contents_preserves_file_contents(tmp_path: Path, builder_module):
    """All file data should be preserved after copy."""
    src = tmp_path / "src"
    src.mkdir()
    content = "This is some important content.\nLine2\nLine3"
    (src / "data.txt").write_text(content, encoding="utf-8")

    dst = tmp_path / "dst"
    func = builder_module.copy_contents
    func(src, dst)

    new_data = (dst / "data.txt").read_text(encoding="utf-8")
    assert new_data == content
