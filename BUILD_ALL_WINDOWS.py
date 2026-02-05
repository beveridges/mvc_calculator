#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
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
import re

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

def cleanup_old_version_directories(build_base: Path, keep: int = 3):
    """Keep only the last N version directories in the root build directory."""
    if not build_base.exists():
        return
    
    print(f"\n[CLEANUP] Cleaning up old version directories in {build_base}")
    print(f"[CLEANUP] Keeping only the last {keep} builds\n")
    
    # Find all version directories (MVC_Calculator-{version} and MVC_Calculator-oa-{version})
    version_pattern = re.compile(r"^MVC_Calculator-(\d{2}\.\d{2}-[^.]+\.\d{2}\.\d{2})$")
    oa_pattern = re.compile(r"^MVC_Calculator-oa-(\d{2}\.\d{2}-[^.]+\.\d{2}\.\d{2})$")
    version_dirs = []
    
    for item in build_base.iterdir():
        if not item.is_dir():
            continue
        # Skip special directories
        if item.name in ["pyinstaller", "temp_logs"]:
            continue
        # Check if it matches version directory pattern (licensed or OA)
        if version_pattern.match(item.name) or oa_pattern.match(item.name):
            version_dirs.append(item)
    
    if len(version_dirs) <= keep:
        print(f"[CLEANUP] Only {len(version_dirs)} version directory(ies) found, nothing to clean up")
        return
    
    # Sort by modification time (newest first)
    version_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    # Keep the newest N, delete the rest
    to_delete = version_dirs[keep:]
    kept = version_dirs[:keep]
    
    print(f"[CLEANUP] Found {len(version_dirs)} version directory(ies)")
    print(f"[CLEANUP] Keeping {len(kept)} directory(ies):")
    for vdir in kept:
        print(f"  ✓ {vdir.name}")
    
    if to_delete:
        print(f"[CLEANUP] Deleting {len(to_delete)} old directory(ies):")
        for vdir in to_delete:
            try:
                shutil.rmtree(vdir, ignore_errors=True)
                print(f"  ✓ Deleted {vdir.name}")
            except Exception as e:
                print(f"  ✗ Failed to delete {vdir.name}: {e}")
    else:
        print(f"[CLEANUP] No directories to delete")
    
    print()

def cleanup_pyinstaller_artifacts(build_base: Path):
    """Delete pyinstaller/builds, dist, and work directories after build completes."""
    pyinstaller_dir = build_base / "pyinstaller"
    if not pyinstaller_dir.exists():
        return
    
    print(f"\n[CLEANUP] Cleaning up PyInstaller artifacts in {pyinstaller_dir}\n")
    
    # Delete builds directory completely
    builds_dir = pyinstaller_dir / "builds"
    if builds_dir.exists():
        try:
            shutil.rmtree(builds_dir, ignore_errors=True)
            print(f"  ✓ Deleted {builds_dir.name}/ directory")
        except Exception as e:
            print(f"  ✗ Failed to delete {builds_dir.name}/: {e}")
    else:
        print(f"  ⊘ {builds_dir.name}/ directory does not exist")
    
    # Delete dist directory
    dist_dir = pyinstaller_dir / "dist"
    if dist_dir.exists():
        try:
            shutil.rmtree(dist_dir, ignore_errors=True)
            print(f"  ✓ Deleted {dist_dir.name}/ directory")
        except Exception as e:
            print(f"  ✗ Failed to delete {dist_dir.name}/: {e}")
    else:
        print(f"  ⊘ {dist_dir.name}/ directory does not exist")
    
    # Delete work directory
    work_dir = pyinstaller_dir / "work"
    if work_dir.exists():
        try:
            shutil.rmtree(work_dir, ignore_errors=True)
            print(f"  ✓ Deleted {work_dir.name}/ directory")
        except Exception as e:
            print(f"  ✗ Failed to delete {work_dir.name}/: {e}")
    else:
        print(f"  ⊘ {work_dir.name}/ directory does not exist")
    
    print()

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


ap = argparse.ArgumentParser(description="MVC Calculator Windows build")
ap.add_argument("-oa", "--oa", action="store_true", help="Also build Open Access (license-free) version")
args = ap.parse_args()

print(f"\n🚀 FULL WINDOWS BUILD" + (" (including OA)" if args.oa else "") + f" — logging to:\n{TEMP_LOG_FILE}\n")

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

# ------------------------------------------------------------
# 2b) OA BUILD (if -oa flag): Portable + MSI + ZIP for Open Access
# ------------------------------------------------------------
if args.oa:
    run_step("OA PyInstaller Portable Build", [sys.executable, str(PORTABLE_SCRIPT), "--onedir", "--oa"], LOG_FILE)
    run_step("OA MSI + ZIP Packaging", [sys.executable, str(MSI_SCRIPT), "--oa"], LOG_FILE)

# ------------------------------------------------------------
# 3) CLEANUP: Remove old builds and PyInstaller artifacts
# ------------------------------------------------------------
cleanup_old_version_directories(BUILD_BASE, keep=3)
cleanup_pyinstaller_artifacts(BUILD_BASE)

print("\n📦 Optional: Deploy via FTP (manual ONLY)")
print("Run: python deploy_release_ftp.py")

print("\n✅ WINDOWS BUILD COMPLETE\n")
