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

# Get version number
VERSION_INFO = ROOT / "utilities" / "version_info.py"
BUILDNUMBER = "unknown"
if VERSION_INFO.exists():
    for line in VERSION_INFO.read_text(encoding="utf-8").splitlines():
        if line.startswith("BUILDNUMBER"):
            BUILDNUMBER = line.split("=")[1].strip().strip('"')
            break

# Versioned build directory
BUILD_BASE = Path.home() / "Documents" / ".builds" / "mvc_calculator"
VERSION_DIR = BUILD_BASE / f"MVC_Calculator-{BUILDNUMBER}"
BUILDFILES_DIR = VERSION_DIR / "buildfiles"
VERSION_DIR.mkdir(parents=True, exist_ok=True)
BUILDFILES_DIR.mkdir(parents=True, exist_ok=True)

# Logging
LOG_FILE = BUILDFILES_DIR / f"windows_master_{datetime.now():%y.%m%d-%H%M%S}.log"

def run_step(name, cmd):
    print(f"\n========== {name} ==========")
    with LOG_FILE.open("a", encoding="utf-8") as log:
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


def organize_build_files():
    """Move build artifacts to versioned directory structure."""
    print(f"\n📁 Organizing build files to: {VERSION_DIR}")
    
    # MSI builds directory (where MSI and ZIP are created)
    MSI_BUILDS = BUILD_BASE / "msi" / "builds"
    
    # Move MSI and ZIP files to version directory
    for pattern in [f"MVC_Calculator-{BUILDNUMBER}.msi", f"MVC_Calculator-{BUILDNUMBER}-portable.zip"]:
        source = MSI_BUILDS / pattern
        if source.exists():
            dest = VERSION_DIR / pattern
            shutil.move(str(source), str(dest))
            print(f"  ✓ Moved {pattern} to version directory")
    
    # Move other build files to buildfiles subdirectory
    # Move MSI build artifacts (wixobj, wxs, etc.)
    MSI_ROOT = BUILD_BASE / "msi"
    for item in MSI_ROOT.iterdir():
        if item.is_file() and item.suffix in [".wixobj", ".wxs", ".wixpdb"]:
            dest = BUILDFILES_DIR / item.name
            shutil.move(str(item), str(dest))
            print(f"  ✓ Moved {item.name} to buildfiles")
    
    # Move MSI build directory contents (cabs, etc.) to buildfiles
    if MSI_BUILDS.exists():
        for item in MSI_BUILDS.iterdir():
            if item.name not in [f"MVC_Calculator-{BUILDNUMBER}.msi", f"MVC_Calculator-{BUILDNUMBER}-portable.zip"]:
                dest = BUILDFILES_DIR / item.name
                if item.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.move(str(item), str(dest))
                else:
                    shutil.move(str(item), str(dest))
                print(f"  ✓ Moved {item.name} to buildfiles")
    
    print(f"✅ Build files organized\n")

print(f"\n🚀 FULL WINDOWS BUILD — logging to:\n{LOG_FILE}\n")
print(f"📁 Build output directory: {VERSION_DIR}\n")

# ------------------------------------------------------------
# 1) ALWAYS REBUILD PYINSTALLER PORTABLE ONEDIR
# ------------------------------------------------------------
run_step("PyInstaller Portable Build", [sys.executable, str(PORTABLE_SCRIPT)])

# ------------------------------------------------------------
# 2) BUILD MSI + ZIP FROM THE PORTABLE BUILD
# ------------------------------------------------------------
run_step("MSI + ZIP Packaging", [sys.executable, str(MSI_SCRIPT)])

# ------------------------------------------------------------
# 3) ORGANIZE BUILD FILES INTO VERSIONED DIRECTORY
# ------------------------------------------------------------
organize_build_files()

print("\n📦 Optional: Deploy via FTP (manual ONLY)")
print("Run: python deploy_release_ftp.py")

print("\n✅ WINDOWS BUILD COMPLETE\n")
