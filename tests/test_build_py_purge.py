# tests/test_build_py_purge.py
"""
Stage 4 — Unit tests for purge_old_archives()

Validates both Bernstein and MVC build.py variants.
Checks that:
 - Old archives are deleted
 - Newest 'keep' archives remain
 - Missing directory handled gracefully
"""

from __future__ import annotations
import os, time, shutil
from pathlib import Path
import importlib.util
import pytest


# ---------------------------------------------------------------------
# Fixture: dynamically import whichever build.py is defined
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
def test_purge_old_archives_removes_extra(tmp_path: Path, builder_module):
    """
    Should keep the N newest archives and remove the rest.
    """
    builds = tmp_path / "builds"
    builds.mkdir()

    # create 5 fake archives with staggered modification times
    archives = []
    for i in range(5):
        folder = builds / f"Build_{i}"
        folder.mkdir()
        (folder / "dummy.txt").write_text(str(i))
        mtime = time.time() - (1000 * (5 - i))  # older ones further back
        os.utime(folder, (mtime, mtime))
        archives.append(folder)

    func = builder_module.purge_old_archives
    func(builds, keep=3)

    # newest 3 should remain, oldest 2 deleted
    remaining = [p.name for p in builds.iterdir()]
    remaining.sort()
    assert len(remaining) == 3
    # ensure last three names (Build_2,3,4) remain
    assert all(f"Build_{i}" in remaining for i in range(2, 5))


def test_purge_old_archives_fewer_than_keep(tmp_path: Path, builder_module):
    """
    If fewer archives exist than 'keep', none should be deleted.
    """
    builds = tmp_path / "builds"
    builds.mkdir()
    for i in range(2):
        f = builds / f"B{i}"
        f.mkdir()
        (f / "file.txt").write_text("ok")

    func = builder_module.purge_old_archives
    func(builds, keep=5)

    remaining = [p.name for p in builds.iterdir()]
    assert len(remaining) == 2


def test_purge_old_archives_handles_nonexistent(tmp_path: Path, builder_module):
    """
    If builds_dir does not exist, should not raise an error.
    """
    builds = tmp_path / "does_not_exist"
    func = builder_module.purge_old_archives
    # Should simply return None without crashing
    func(builds, keep=3)
    assert not builds.exists()


def test_purge_old_archives_ignores_files(tmp_path: Path, builder_module):
    """
    Should delete plain files too (not just dirs).
    """
    builds = tmp_path / "builds"
    builds.mkdir()

    # Create 3 directories and 1 file
    for i in range(3):
        d = builds / f"Dir{i}"
        d.mkdir()
        (d / "foo.txt").write_text("data")
        mtime = time.time() - (50 * i)
        os.utime(d, (mtime, mtime))
    file_item = builds / "random.txt"
    file_item.write_text("something")
    os.utime(file_item, (time.time() - 1000, time.time() - 1000))

    func = builder_module.purge_old_archives
    func(builds, keep=2)

    remaining = [p.name for p in builds.iterdir()]
    # Two newest dirs should remain
    assert "Dir0" in remaining and "Dir1" in remaining
    # oldest (Dir2) and file removed
    assert "Dir2" not in remaining and "random.txt" not in remaining
