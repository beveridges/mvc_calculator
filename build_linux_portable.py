#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import shutil
import subprocess
from pathlib import Path

APP_NAME = "MVC_Calculator"
ICON = "resources/icons/icn_emg.png"

# Output directory (WINDOWS PATH mirrored into WSL)
OUT_DIR = Path("/mnt/c/Users/Scott/Documents/.linux_builds/MVC_CALCULATOR/linux_builds/pyinstaller")


def run():
    print("[INFO] Cleaning build dirs...")
    shutil.rmtree("build", ignore_errors=True)
    shutil.rmtree("dist", ignore_errors=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("[INFO] Running PyInstaller...")

    # Use the current Python executable and run PyInstaller as a module
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--name", APP_NAME,
        "--icon", ICON,
        "--add-data", "resources:resources",
        "main.py",
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print("❌ PyInstaller failed with exit code:", e.returncode)
        sys.exit(e.returncode)

    dist_dir = Path("dist") / APP_NAME

    if not dist_dir.exists():
        print(f"❌ Expected dist directory not found: {dist_dir}")
        sys.exit(1)

    print("[INFO] Copying result to output folder...")
    shutil.rmtree(OUT_DIR, ignore_errors=True)
    shutil.copytree(dist_dir, OUT_DIR)

    print("\n[DONE] Portable Linux build created:")
    print(OUT_DIR)


if __name__ == "__main__":
    run()














# # build_linux_portable.py
# import os
# import shutil
# from pathlib import Path
# import subprocess

# APP_NAME = "MVC_Calculator"
# ICON = "resources/icons/icn_emg.png"

# # Output directory (WINDOWS PATH mirrored into WSL)
# OUT_DIR = Path("/mnt/c/Users/Scott/Documents/.linux_builds/MVC_CALCULATOR/linux_builds/pyinstaller")


# def run():
    # out_dir = Path("/mnt/c/Users/Scott/Documents/.linux_builds/MVC_CALCULATOR/linux_builds/pyinstaller")
    # dist_dir = Path("dist") / APP_NAME

    # print("[INFO] Cleaning build dirs...")
    # shutil.rmtree("build", ignore_errors=True)
    # shutil.rmtree("dist", ignore_errors=True)
    # out_dir.mkdir(parents=True, exist_ok=True)

    # print("[INFO] Running PyInstaller...")
    # subprocess.run([
        # "pyinstaller",
        # "--noconfirm",
        # "--clean",
        # "--name", APP_NAME,
        # "--icon", ICON,
        # "--add-data", "resources:resources",
        # "main.py"
    # ], check=True)

    # print("[INFO] Copying result to output folder...")
    # shutil.rmtree(out_dir, ignore_errors=True)
    # shutil.copytree(dist_dir, out_dir)

    # print("[DONE] Portable Linux build created:")
    # print(out_dir)

# if __name__ == "__main__":
    # run()
