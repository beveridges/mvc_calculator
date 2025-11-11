# tests/test_build_py_archive.py
"""
Stage 3 — Unit tests for archive_latest()

Covers both Bernstein and MVC build.py variants.
Validates:
 - It creates builds/<tag> directory
 - Copies latest folder or .exe
 - Flattens structure
 - Cleans previous archives safely
"""

from __future__ import annotations
import os, io, shutil, time
from pathlib import Path
import importlib.util
import pytest


# ---------------------------------------------------------------------
# Helper fixture: dynamically import build.py
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
# Core test
# ---------------------------------------------------------------------
def test_archive_latest_copies_latest_folder(tmp_path: Path, builder_module):
    """
    Should copy the most recently modified folder from dist/ into builds/<tag>/.
    """
    dist = tmp_path / "dist"
    builds = tmp_path / "builds"
    dist.mkdir()
    builds.mkdir()

    # Create two mock app folders with different modification times
    old_dir = dist / "OldApp"
    new_dir = dist / "NewApp"
    old_dir.mkdir()
    new_dir.mkdir()

    # Create dummy files in each
    (old_dir / "oldfile.txt").write_text("OLD", encoding="utf-8")
    (new_dir / "newfile.txt").write_text("NEW", encoding="utf-8")

    # Manipulate modification times to force one as latest
    old_time = time.time() - 3600
    new_time = time.time()
    os.utime(old_dir, (old_time, old_time))
    os.utime(new_dir, (new_time, new_time))

    func = builder_module.archive_latest
    tag = "TestApp-25.11-alpha.01.00"

    dest = func(dist, builds, tag, app_name=None)

    # Verify returned path
    assert dest is not None and dest.exists()
    assert dest.name == tag

    # Check that NewApp content was copied, not OldApp
    contents = [p.name for p in dest.iterdir()]
    assert "newfile.txt" in contents
    assert "oldfile.txt" not in contents


def test_archive_latest_copies_single_exe(tmp_path: Path, builder_module):
    """
    Should copy newest .exe if present and not a folder.
    """
    dist = tmp_path / "dist"
    builds = tmp_path / "builds"
    dist.mkdir()
    builds.mkdir()

    exe1 = dist / "A.exe"
    exe2 = dist / "B.exe"
    exe1.write_text("EXE1", encoding="utf-8")
    exe2.write_text("EXE2", encoding="utf-8")

    # make exe2 newer
    old = time.time() - 100
    new = time.time()
    os.utime(exe1, (old, old))
    os.utime(exe2, (new, new))

    func = builder_module.archive_latest
    tag = "TestApp-25.11-alpha.01.01"

    dest = func(dist, builds, tag, app_name=None)
    assert dest is not None
    copied_files = [p.name for p in dest.iterdir()]
    assert "B.exe" in copied_files
    assert "A.exe" not in copied_files


def test_archive_latest_existing_dest_replaced(tmp_path: Path, builder_module):
    """
    Existing builds/<tag> folder should be replaced cleanly.
    """
    dist = tmp_path / "dist"
    builds = tmp_path / "builds"
    tag = "TestReplace"
    dist.mkdir()
    builds.mkdir()

    latest = dist / "App"
    latest.mkdir()
    (latest / "foo.txt").write_text("data")

    # create previous archive
    old_dest = builds / tag
    old_dest.mkdir(parents=True)
    (old_dest / "stale.txt").write_text("old")

    func = builder_module.archive_latest
    dest = func(dist, builds, tag, app_name=None)
    assert dest.exists()

    # Ensure stale file removed, new file present
    names = [p.name for p in dest.iterdir()]
    assert "foo.txt" in names
    assert "stale.txt" not in names


def test_archive_latest_returns_none_if_dist_missing(tmp_path: Path, builder_module):
    """
    Should return None if dist path does not exist.
    """
    dist = tmp_path / "does_not_exist"
    builds = tmp_path / "builds"
    tag = "TestApp-25.11-alpha.01.03"
    builds.mkdir()
    func = builder_module.archive_latest
    result = func(dist, builds, tag, app_name=None)
    assert result is None


def test_archive_latest_handles_empty_dist(tmp_path: Path, builder_module):
    """
    Should return None if dist is empty.
    """
    dist = tmp_path / "dist"
    builds = tmp_path / "builds"
    dist.mkdir()
    builds.mkdir()
    func = builder_module.archive_latest
    tag = "EmptyTest"
    result = func(dist, builds, tag, app_name=None)
    assert result is None
