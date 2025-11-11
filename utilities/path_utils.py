# -*- coding: utf-8 -*-
"""
path_utils.py — unified, frozen-safe path resolver
Works for both PyInstaller executables and dev mode.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path

# ------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------

def is_frozen() -> bool:
    """Return True when running from a PyInstaller bundle."""
    return bool(getattr(sys, "frozen", False))


def app_root() -> Path:
    """
    Return the root directory of the application.
    - In frozen (EXE) mode: directory of the executable or its _internal folder
    - In dev mode: project root where main.py resides
    """
    if is_frozen():
        exe_dir = Path(sys.executable).resolve().parent
        internal = exe_dir / "_internal"
        return internal if internal.exists() else exe_dir

    # --- Dev mode ---
    base = Path(__file__).resolve().parent
    for _ in range(10):  # climb max 10 levels just in case
        if (base / "main.py").exists():
            return base
        if base == base.parent:
            break
        base = base.parent
    return Path.cwd()


def base_path(*parts: str) -> str:
    """
    Build a path relative to the application root.
    """
    return str(app_root().joinpath(*parts))


def resource_path(*parts: str) -> str:
    """
    Return an absolute path to a resource (usually under /resources).
    Works in both frozen and dev modes.
    """
    return str(app_root().joinpath("resources", *parts))


def writable_path(*parts: str, create: bool = False) -> str:
    """
    Same as base_path(), but optionally creates the directory.
    Use for writable outputs like logs or exports.
    """
    p = app_root().joinpath(*parts)
    if create:
        os.makedirs(p, exist_ok=True)
    return str(p)
