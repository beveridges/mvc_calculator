#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import shutil
import subprocess
import re
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
    
    if not VERSION_INFO.exists():
        print(f"❌ ERROR: version_info.py not found at {VERSION_INFO}")
        print(f"   Make sure you've run BUILD_ALL_WINDOWS.py first!")
        return BUILDNUMBER
    
    # Force read from disk (bypass any Python import cache)
    # Read fresh each time to get the latest version (after Windows builds increment it)
    try:
        content = VERSION_INFO.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("BUILDNUMBER"):
                BUILDNUMBER = line.split("=")[1].strip().strip('"')
                break
    except Exception as e:
        print(f"❌ ERROR: Could not read version_info.py: {e}")
        return BUILDNUMBER
    
    # Clear any Python bytecode cache for this module
    import py_compile
    import os
    pyc_file = VERSION_INFO.with_suffix('.pyc')
    if pyc_file.exists():
        try:
            pyc_file.unlink()
        except:
            pass
    
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
# CLEANUP OLD BUILDS - KEEP ONLY CURRENT AND PREVIOUS
# --------------------------------------------------------------
def cleanup_old_builds(current_buildnumber: str):
    """Remove old build files, keeping only current and previous builds."""
    print(f"\n[INFO] Cleaning up old builds in {LINUX_ROOT}")
    print(f"[INFO] Keeping: current ({current_buildnumber}) and previous build only\n")
    
    # Version pattern: e.g., "25.11-alpha.01.80"
    VERSION_PATTERN = re.compile(r"(\d{2}\.\d{2}-alpha\.\d{2}\.\d{2})")
    
    # Find all versions in the directory
    versions_found = set()
    files_by_version = {}
    
    for item in LINUX_ROOT.iterdir():
        if not item.is_file():
            continue
        
        # Skip temp_logs and other non-build files
        if item.name == "temp_logs" or item.suffix.lower() not in [".deb", ".appimage"]:
            continue
        
        # Extract version from filename
        match = VERSION_PATTERN.search(item.name)
        if match:
            version = match.group(1)
            versions_found.add(version)
            if version not in files_by_version:
                files_by_version[version] = []
            files_by_version[version].append(item)
    
    if not versions_found:
        print(f"  [INFO] No versioned build files found to clean up")
        return
    
    # Sort versions (newest first)
    sorted_versions = sorted(versions_found, reverse=True)
    
    # Determine which versions to keep
    # Keep the two newest versions (current build + previous build)
    # Since cleanup runs after builds complete, current_buildnumber should be the newest
    keep_versions = sorted_versions[:2] if len(sorted_versions) >= 2 else sorted_versions
    
    print(f"  [INFO] Found {len(versions_found)} version(s): {sorted_versions}")
    print(f"  [INFO] Keeping versions: {keep_versions}")
    
    # Delete files from versions not in keep list
    deleted_count = 0
    for version, files in files_by_version.items():
        if version not in keep_versions:
            print(f"  [CLEANUP] Removing files for version {version}:")
            for file in files:
                try:
                    file.unlink()
                    print(f"    ✓ Deleted {file.name}")
                    deleted_count += 1
                except Exception as e:
                    print(f"    ❌ Failed to delete {file.name}: {e}")
    
    if deleted_count > 0:
        print(f"\n  [INFO] Cleanup complete: removed {deleted_count} file(s)")
    else:
        print(f"\n  [INFO] No files to clean up (only current/previous builds present)")


# --------------------------------------------------------------
# COPY RESULTING FILES TO WINDOWS DIRECTORY
# --------------------------------------------------------------
def copy_to_windows(buildnumber: str, oa_mode: bool = False):
    """Copy Linux build artifacts to Windows versioned directory"""
    if oa_mode:
        WIN_VERSION_DIR = WIN_BUILD_BASE / f"MVC_Calculator-oa-{buildnumber}"
    else:
        WIN_VERSION_DIR = WIN_BUILD_BASE / f"MVC_Calculator-{buildnumber}"
    WIN_BUILDFILES_DIR = WIN_VERSION_DIR / "buildfiles"
    
    WIN_VERSION_DIR.mkdir(parents=True, exist_ok=True)
    WIN_BUILDFILES_DIR.mkdir(parents=True, exist_ok=True)

    build_type = "OA" if oa_mode else "licensed"
    print(f"\n[INFO] Copying Linux {build_type} build artifacts to:\n{WIN_VERSION_DIR}\n")
    print(f"[INFO] Filtering files for version: {buildnumber}\n")

    # Copy DEB and AppImage to version directory (main artifacts)
    # OA: copy *-oa* files; licensed: copy files without -oa
    copied_count = 0
    for item in LINUX_ROOT.iterdir():
        if item.is_file():
            suffix_lower = item.suffix.lower()
            if suffix_lower in [".deb", ".appimage"]:
                has_oa = "-oa" in item.name or "mvc-calculator-oa" in item.name
                version_match = buildnumber in item.name
                if version_match and (has_oa if oa_mode else not has_oa):
                    dest = WIN_VERSION_DIR / item.name
                    shutil.copy(item, dest)
                    print(f"  ✓ Copied {item.name} to version directory")
                    copied_count += 1
    
    if copied_count == 0:
        print(f"  ⚠️  Warning: No matching build files found for version {buildnumber}")
        print(f"     Checked directory: {LINUX_ROOT}")
        print(f"     Looking for files containing: {buildnumber}")

    # Copy portable build to buildfiles (licensed only; OA dir just gets DEB/AppImage)
    if not oa_mode:
        for item in LINUX_ROOT.iterdir():
            if item.name == "temp_logs":
                continue
            suffix_lower = item.suffix.lower() if item.is_file() else ""
            if suffix_lower in [".deb", ".appimage"]:
                continue
            if item.name == "pyinstaller" and item.is_dir():
                dest = WIN_BUILDFILES_DIR / item.name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
                print(f"  ✓ Copied {item.name} to buildfiles")
                break

    print("[INFO] Copy complete.\n")



def main():
    ap = argparse.ArgumentParser(description="MVC Calculator Linux build")
    ap.add_argument("-oa", "--oa", action="store_true", help="Also build Open Access (license-free) version")
    args = ap.parse_args()

    print(f"\n🐧 FULL LINUX BUILD" + (" (including OA)" if args.oa else "") + f" — logging to:\n{TEMP_LOG_FILE}\n")
    
    # Read build number BEFORE builds (Windows builds have already incremented it)
    # This ensures we use the correct version and can verify it before building
    VERSION_INFO_FILE = SCRIPT_ROOT / "utilities" / "version_info.py"
    print(f"[INFO] Reading version from: {VERSION_INFO_FILE}")
    
    # Show file modification time to help debug sync issues
    if VERSION_INFO_FILE.exists():
        import time
        mtime = VERSION_INFO_FILE.stat().st_mtime
        mtime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))
        print(f"[INFO] File last modified: {mtime_str}")
    
    BUILDNUMBER = read_build_number()
    print(f"[INFO] Build number read: {BUILDNUMBER}")
    print(f"[INFO] ⚠️  VERIFY: This should match the Windows build number (v80)!")
    print(f"[INFO] If this is wrong:")
    print(f"   1. Make sure you've run BUILD_ALL_WINDOWS.py first")
    print(f"   2. Check that version_info.py is synced between Windows and WSL")
    print(f"   3. Try: git pull (if version_info.py is committed)")
    print()
    
    # Verify the build number is reasonable (not "unknown")
    if BUILDNUMBER == "unknown":
        print(f"❌ ERROR: Could not read build number from version_info.py")
        print(f"   File location: {SCRIPT_ROOT / 'utilities' / 'version_info.py'}")
        print(f"   Make sure you've run BUILD_ALL_WINDOWS.py first!")
        sys.exit(1)
    
    # Clear Python cache files to force fresh imports in build scripts
    import glob
    cache_pattern = str(SCRIPT_ROOT / "utilities" / "__pycache__" / "version_info*.pyc")
    for pyc_file in glob.glob(cache_pattern):
        try:
            Path(pyc_file).unlink()
            print(f"[INFO] Cleared cache file: {Path(pyc_file).name}")
        except:
            pass
    
    # Check if this looks like an old version (less than expected)
    # This is a safety check - user should verify manually
    try:
        version_parts = BUILDNUMBER.split(".")
        if len(version_parts) >= 4:
            build_seq = int(version_parts[-1])
            if build_seq < 80:  # Adjust this threshold as needed
                print(f"⚠️  WARNING: Build number {BUILDNUMBER} seems low.")
                print(f"   Expected v80 or higher. Verify this is correct!")
                print(f"   If this is wrong, the build scripts will use the wrong version!\n")
    except:
        pass
    
    print()

    # Run licensed Linux builds
    run_step("Portable Linux Build", [sys.executable, str(PORTABLE_SCRIPT)], TEMP_LOG_FILE)
    run_step("AppImage Build",      [sys.executable, str(APPIMAGE_SCRIPT)], TEMP_LOG_FILE)
    run_step("DEB Package Build",   [sys.executable, str(DEB_SCRIPT)], TEMP_LOG_FILE)

    # Run OA builds if requested
    if args.oa:
        run_step("OA Portable Linux Build", [sys.executable, str(PORTABLE_SCRIPT), "--oa"], TEMP_LOG_FILE)
        run_step("OA AppImage Build",      [sys.executable, str(APPIMAGE_SCRIPT), "--oa"], TEMP_LOG_FILE)
        run_step("OA DEB Package Build",   [sys.executable, str(DEB_SCRIPT), "--oa"], TEMP_LOG_FILE)

    print("\n✅ ALL LINUX ARTIFACTS BUILT SUCCESSFULLY\n")
    
    # Re-read build number to confirm (should be the same)
    BUILDNUMBER_FINAL = read_build_number()
    if BUILDNUMBER_FINAL != BUILDNUMBER:
        print(f"⚠️  WARNING: Build number changed during build!")
        print(f"   Started with: {BUILDNUMBER}")
        print(f"   Ended with: {BUILDNUMBER_FINAL}")
        BUILDNUMBER = BUILDNUMBER_FINAL
    
    print(f"[INFO] Using build number: {BUILDNUMBER}\n")
    
    # Clean up old builds (keep only current and previous)
    cleanup_old_builds(BUILDNUMBER)
    
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
    
    # Copy licensed files to Windows versioned directory
    copy_to_windows(BUILDNUMBER, oa_mode=False)

    # Copy OA files if built
    if args.oa:
        copy_to_windows(BUILDNUMBER, oa_mode=True)


if __name__ == "__main__":
    main()

