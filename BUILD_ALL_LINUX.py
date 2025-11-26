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

# Get version number
VERSION_INFO = SCRIPT_ROOT / "utilities" / "version_info.py"
BUILDNUMBER = "unknown"
if VERSION_INFO.exists():
    for line in VERSION_INFO.read_text(encoding="utf-8").splitlines():
        if line.startswith("BUILDNUMBER"):
            BUILDNUMBER = line.split("=")[1].strip().strip('"')
            break

# Uses local WSL home directory (correct)
LINUX_ROOT = Path.home() / ".linux_builds" / "MVC_CALCULATOR" / "linux_builds"
LINUX_ROOT.mkdir(parents=True, exist_ok=True)

LOG_FILE = LINUX_ROOT / f"linux_master_{datetime.now():%y.%m%d-%H%M%S}.log"

# Windows versioned directory (where Linux builds will be copied)
WIN_BUILD_BASE = Path("/mnt/c/Users/Scott/Documents/.builds/mvc_calculator")
WIN_VERSION_DIR = WIN_BUILD_BASE / f"MVC_Calculator-{BUILDNUMBER}"
WIN_BUILDFILES_DIR = WIN_VERSION_DIR / "buildfiles"


def run_step(name: str, cmd: list[str]):
    print(f"\n========== {name} ==========")

    with LOG_FILE.open("a", encoding="utf-8") as log:
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
def copy_to_windows():
    WIN_VERSION_DIR.mkdir(parents=True, exist_ok=True)
    WIN_BUILDFILES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n[INFO] Copying Linux build artifacts to Windows versioned directory:\n{WIN_VERSION_DIR}\n")

    # Copy DEB and AppImage to version directory (main artifacts)
    for item in LINUX_ROOT.iterdir():
        if item.suffix in [".deb", ".AppImage"]:
            dest = WIN_VERSION_DIR / item.name
            shutil.copy(item, dest)
            print(f"  ✓ Copied {item.name} to version directory")

    # Copy portable build and other files to buildfiles
    for item in LINUX_ROOT.iterdir():
        if item.name == "pyinstaller" or (item.is_file() and item.suffix not in [".deb", ".AppImage"]):
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
    print(f"\n🐧 FULL LINUX BUILD — logging to:\n{LOG_FILE}\n")

    run_step("Portable Linux Build", [sys.executable, str(PORTABLE_SCRIPT)])
    run_step("AppImage Build",      [sys.executable, str(APPIMAGE_SCRIPT)])
    run_step("DEB Package Build",   [sys.executable, str(DEB_SCRIPT)])

    print("\n✅ ALL LINUX ARTIFACTS BUILT SUCCESSFULLY\n")


if __name__ == "__main__":
    main()
    copy_to_windows()

