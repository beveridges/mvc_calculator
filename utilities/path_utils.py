# -*- coding: utf-8 -*-
"""
Created on Tue Jun 10 13:00:35 2025

@author: Scott
"""

# utilities/path_utils.py
from __future__ import annotations
import os
from pathlib import Path
import sys, time

# Always resolve from where main.py resides
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(BASE_DIR, 'main.py')):
    BASE_DIR = os.path.dirname(BASE_DIR)


def base_path(*parts):
    return os.path.join(BASE_DIR, *parts)


def resource_path(*parts):
    return os.path.join(BASE_DIR, 'resources', *parts)



def is_frozen() -> bool:
    """True when running from a PyInstaller bundle (exe)."""
    return bool(getattr(sys, "frozen", False))

def app_root() -> Path:
    if is_frozen():
        exe_dir = Path(sys.executable).resolve().parent
        # If we're inside PyInstaller onefile/onedir (_internal layout)
        internal = exe_dir / "_internal"
        if internal.exists():
            return internal
        return exe_dir
    return Path(__file__).resolve().parent.parent


def base_path(*parts: str) -> str:
    """
    Build a path relative to app_root(). Use for bundled **resources** as well as
    writable folders (we keep them next to the exe in frozen mode).
    """
    return str(app_root().joinpath(*parts))

def writable_path(*parts: str, create: bool = False) -> str:
    """
    Same as base_path(), but optionally creates the directory for you.
    Use for outputs like exports, logs, etc.
    """
    p = app_root().joinpath(*parts)
    if create:
        os.makedirs(p, exist_ok=True)
    return str(p)

