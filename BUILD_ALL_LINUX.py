#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Launcher — implementation lives in ___BUILD___/BUILD_ALL_LINUX.py (repo root = cwd)."""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SCRIPT = REPO_ROOT / "___BUILD___" / "BUILD_ALL_LINUX.py"
raise SystemExit(subprocess.call([sys.executable, str(SCRIPT)] + sys.argv[1:], cwd=str(REPO_ROOT)))
