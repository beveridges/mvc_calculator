#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# MASTER WINDOWS BUILD — MVC Calculator
# --------------------------------------
# Runs:
#   ✔ build_windows_portable.py  (ALWAYS rebuild PyInstaller onedir)
#   ✔ build_windows_msi.py       (MSI + ZIP)
#   (FTP upload remains manual)

import subprocess
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent

# Correct builder scripts
PORTABLE_SCRIPT = ROOT / "build_windows_portable.py"
MSI_SCRIPT      = ROOT / "build_windows_msi.py"

# Build base directory (version directory will be created after portable build)
BUILD_BASE = Path.home() / "Documents" / ".builds" / "mvc_calculator"
BUILD_BASE.mkdir(parents=True, exist_ok=True)

# Temporary log location (will move to version directory after we know the build number)
TEMP_LOG_DIR = BUILD_BASE / "temp_logs"
TEMP_LOG_DIR.mkdir(parents=True, exist_ok=True)
TEMP_LOG_FILE = TEMP_LOG_DIR / f"windows_master_{datetime.now():%y.%m%d-%H%M%S}.log"

def read_build_number():
    """Read BUILDNUMBER from utilities/version_info.py"""
    VERSION_INFO = ROOT / "utilities" / "version_info.py"
    BUILDNUMBER = "unknown"
    if VERSION_INFO.exists():
        for line in VERSION_INFO.read_text(encoding="utf-8").splitlines():
            if line.startswith("BUILDNUMBER"):
                BUILDNUMBER = line.split("=")[1].strip().strip('"')
                break
    return BUILDNUMBER

def run_step(name, cmd, log_file):
    print(f"\n========== {name} ==========")
    with log_file.open("a", encoding="utf-8") as log:
        log.write(f"\n[{datetime.now():%H:%M:%S}] {name}\n")
        log.write("=" * 70 + "\n")

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        for line in proc.stdout:
            print(line, end="")
            log.write(line)

        proc.wait()
        log.write(f"\n[exit code] {proc.returncode}\n")
        log.flush()

    if proc.returncode != 0:
        print(f"\n❌ {name} failed (exit {proc.returncode})")
        sys.exit(proc.returncode)


print(f"\n🚀 FULL WINDOWS BUILD — logging to:\n{TEMP_LOG_FILE}\n")

# ------------------------------------------------------------
# 1) ALWAYS REBUILD PYINSTALLER PORTABLE ONEDIR
#    (This will increment the build number)
# ------------------------------------------------------------
run_step("PyInstaller Portable Build", [sys.executable, str(PORTABLE_SCRIPT)], TEMP_LOG_FILE)

# ------------------------------------------------------------
# Read the build number AFTER portable build (it was incremented)
# ------------------------------------------------------------
BUILDNUMBER = read_build_number()
VERSION_DIR = BUILD_BASE / f"MVC_Calculator-{BUILDNUMBER}"
BUILDFILES_DIR = VERSION_DIR / "buildfiles"
VERSION_DIR.mkdir(parents=True, exist_ok=True)
BUILDFILES_DIR.mkdir(parents=True, exist_ok=True)

# Move log file to the correct version directory
LOG_FILE = BUILDFILES_DIR / TEMP_LOG_FILE.name
if TEMP_LOG_FILE.exists():
    shutil.move(str(TEMP_LOG_FILE), str(LOG_FILE))
    print(f"\n📁 Build output directory: {VERSION_DIR}")
    print(f"   - MSI and ZIP will be created in: {VERSION_DIR}")
    print(f"   - Build artifacts will be in: {BUILDFILES_DIR}")
    print(f"   - Log file moved to: {LOG_FILE}\n")

# ------------------------------------------------------------
# 2) BUILD MSI + ZIP FROM THE PORTABLE BUILD
#    (Files are created directly in versioned directory structure)
# ------------------------------------------------------------
run_step("MSI + ZIP Packaging", [sys.executable, str(MSI_SCRIPT)], LOG_FILE)

print("\n📦 Optional: Deploy via FTP (manual ONLY)")
print("Run: python deploy_release_ftp.py")

print("\n✅ WINDOWS BUILD COMPLETE\n")
