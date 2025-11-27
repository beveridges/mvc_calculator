#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

SCRIPT_ROOT = Path(__file__).resolve().parent

PORTABLE_SCRIPT = SCRIPT_ROOT / "build_linux_portable.py"
APPIMAGE_SCRIPT = SCRIPT_ROOT / "build_linux_appimage.py"
DEB_SCRIPT      = SCRIPT_ROOT / "build_linux_deb.py"

# Uses local WSL home directory (correct)
LINUX_ROOT = Path.home() / ".linux_builds" / "MVC_CALCULATOR" / "linux_builds"
LINUX_ROOT.mkdir(parents=True, exist_ok=True)

# Temporary log location (will move to version directory after we know the build number)
TEMP_LOG_DIR = LINUX_ROOT / "temp_logs"
TEMP_LOG_DIR.mkdir(parents=True, exist_ok=True)
TEMP_LOG_FILE = TEMP_LOG_DIR / f"linux_master_{datetime.now():%y.%m%d-%H%M%S}.log"

# Windows build base (version directory will be determined after reading build number)
WIN_BUILD_BASE = Path("/mnt/c/Users/Scott/Documents/.builds/mvc_calculator")

def read_build_number():
    """Read BUILDNUMBER from utilities/version_info.py (reads fresh each time)"""
    VERSION_INFO = SCRIPT_ROOT / "utilities" / "version_info.py"
    BUILDNUMBER = "unknown"
    if VERSION_INFO.exists():
        # Read fresh each time to get the latest version (after Windows builds increment it)
        for line in VERSION_INFO.read_text(encoding="utf-8").splitlines():
            if line.startswith("BUILDNUMBER"):
                BUILDNUMBER = line.split("=")[1].strip().strip('"')
                break
    return BUILDNUMBER


def run_step(name: str, cmd: list[str], log_file: Path):
    print(f"\n========== {name} ==========")

    with log_file.open("a", encoding="utf-8") as log:
        log.write(f"\n[{datetime.now():%H:%M:%S}] {name}\n")
        log.write("=" * 70 + "\n")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        for line in process.stdout:
            sys.stdout.write(line)
            log.write(line)

        process.wait()
        log.write(f"\n[exit code] {process.returncode}\n")
        log.flush()

    if process.returncode != 0:
        print(f"\n❌ {name} failed (exit {process.returncode})")
        sys.exit(process.returncode)


# --------------------------------------------------------------
# COPY RESULTING FILES TO WINDOWS DIRECTORY
# --------------------------------------------------------------
def copy_to_windows(buildnumber: str):
    """Copy Linux build artifacts to Windows versioned directory"""
    WIN_VERSION_DIR = WIN_BUILD_BASE / f"MVC_Calculator-{buildnumber}"
    WIN_BUILDFILES_DIR = WIN_VERSION_DIR / "buildfiles"
    
    WIN_VERSION_DIR.mkdir(parents=True, exist_ok=True)
    WIN_BUILDFILES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n[INFO] Copying Linux build artifacts to Windows versioned directory:\n{WIN_VERSION_DIR}\n")
    print(f"[INFO] Filtering files for version: {buildnumber}\n")
    
    # Diagnostic: List all files in LINUX_ROOT to help debug
    print(f"[DEBUG] Files found in {LINUX_ROOT}:")
    for item in sorted(LINUX_ROOT.iterdir()):
        if item.is_file():
            print(f"  - {item.name} (suffix: {item.suffix})")
    print()

    # Copy DEB and AppImage to version directory (main artifacts)
    # Only copy files that match the current build number
    copied_count = 0
    for item in LINUX_ROOT.iterdir():
        if item.is_file():
            # Check file extension (case-insensitive for AppImage)
            suffix_lower = item.suffix.lower()
            if suffix_lower in [".deb", ".appimage"]:
                # Check if file name contains the build number
                if buildnumber in item.name:
                    dest = WIN_VERSION_DIR / item.name
                    shutil.copy(item, dest)
                    print(f"  ✓ Copied {item.name} to version directory")
                    copied_count += 1
                else:
                    print(f"  ⊘ Skipped {item.name} (version mismatch, expected {buildnumber})")
    
    if copied_count == 0:
        print(f"  ⚠️  Warning: No matching build files found for version {buildnumber}")
        print(f"     Checked directory: {LINUX_ROOT}")
        print(f"     Looking for files containing: {buildnumber}")

    # Copy portable build and other files to buildfiles
    # Skip main artifacts (.deb, .AppImage) which are already copied above
    for item in LINUX_ROOT.iterdir():
        # Skip temp_logs directory and main artifacts (already copied above)
        if item.name == "temp_logs":
            continue
        # Skip .deb and .AppImage files (case-insensitive) - already copied to version directory
        suffix_lower = item.suffix.lower() if item.is_file() else ""
        if suffix_lower in [".deb", ".appimage"]:
            continue
        if item.name == "pyinstaller" or (item.is_file() and suffix_lower not in [".deb", ".appimage"]):
            dest = WIN_BUILDFILES_DIR / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy(item, dest)
            print(f"  ✓ Copied {item.name} to buildfiles")

    print("[INFO] Copy complete.\n")



def main():
    print(f"\n🐧 FULL LINUX BUILD — logging to:\n{TEMP_LOG_FILE}\n")
    print("[INFO] Reading version from utilities/version_info.py (should match Windows build)\n")

    # Run all Linux builds
    run_step("Portable Linux Build", [sys.executable, str(PORTABLE_SCRIPT)], TEMP_LOG_FILE)
    run_step("AppImage Build",      [sys.executable, str(APPIMAGE_SCRIPT)], TEMP_LOG_FILE)
    run_step("DEB Package Build",   [sys.executable, str(DEB_SCRIPT)], TEMP_LOG_FILE)

    print("\n✅ ALL LINUX ARTIFACTS BUILT SUCCESSFULLY\n")
    
    # Read build number AFTER builds complete (Windows builds have already incremented it)
    BUILDNUMBER = read_build_number()
    print(f"[INFO] Using build number: {BUILDNUMBER}\n")
    
    # Set up version directory structure
    WIN_VERSION_DIR = WIN_BUILD_BASE / f"MVC_Calculator-{BUILDNUMBER}"
    WIN_BUILDFILES_DIR = WIN_VERSION_DIR / "buildfiles"
    WIN_BUILDFILES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Move log file to the correct version directory
    LOG_FILE = WIN_BUILDFILES_DIR / TEMP_LOG_FILE.name
    if TEMP_LOG_FILE.exists():
        shutil.move(str(TEMP_LOG_FILE), str(LOG_FILE))
        print(f"📁 Build output directory: {WIN_VERSION_DIR}")
        print(f"   - DEB and AppImage will be copied to: {WIN_VERSION_DIR}")
        print(f"   - Build artifacts will be in: {WIN_BUILDFILES_DIR}")
        print(f"   - Log file moved to: {LOG_FILE}\n")
    
    # Copy files to Windows versioned directory
    copy_to_windows(BUILDNUMBER)


if __name__ == "__main__":
    main()

