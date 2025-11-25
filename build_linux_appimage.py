# build_linux_appimage.py
import os
import shutil
import subprocess
from pathlib import Path

APP_NAME = "MVC_Calculator"
VERSION = "1.0.0"

ROOT = Path("/mnt/c/Users/Scott/Documents/.linux_builds/MVC_CALCULATOR/linux_builds")
PORTABLE = ROOT / "pyinstaller"
APPDIR = ROOT / "appimage" / "AppDir"
OUTFILE = ROOT / f"{APP_NAME}-x86_64.AppImage"

def create_structure():
    print("[INFO] Creating AppDir structure...")
    if APPDIR.exists():
        shutil.rmtree(APPDIR)
    (APPDIR / "usr/bin").mkdir(parents=True)
    (APPDIR / "usr/share/icons/hicolor/256x256/apps").mkdir(parents=True)
    (APPDIR / "usr/share/applications").mkdir(parents=True)

def copy_files():
    print("[INFO] Copying portable build...")
    shutil.copytree(PORTABLE, APPDIR / "usr/bin" / APP_NAME)

    shutil.copy("resources/icons/icn_emg.png",
                APPDIR / "usr/share/icons/hicolor/256x256/apps/mvc-calculator.png")

def create_desktop():
    desktop = APPDIR / "usr/share/applications/mvc-calculator.desktop"
    desktop.write_text(f"""
[Desktop Entry]
Type=Application
Name=MVC Calculator
Exec=/{APP_NAME}
Icon=mvc-calculator
Categories=Science;Utility;
Terminal=false
""")

def build_appimage():
    print("[INFO] Building AppImage...")
    subprocess.run([
        "appimagetool", str(APPDIR), str(OUTFILE)
    ], check=True)

def main():
    create_structure()
    copy_files()
    create_desktop()
    build_appimage()
    print(f"[DONE] AppImage created: {OUTFILE}")

if __name__ == "__main__":
    main()
