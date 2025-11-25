# build_linux_deb.py
import os
import shutil
import subprocess
from pathlib import Path

APP_NAME = "mvc-calculator"
DISPLAY_NAME = "MVC Calculator"
VERSION = "1.0.0"

ROOT = Path("/mnt/c/Users/Scott/Documents/.linux_builds/MVC_CALCULATOR/linux_builds")
PORTABLE = ROOT / "pyinstaller"
DEBROOT = ROOT / "deb" / f"{APP_NAME}_{VERSION}_amd64"
OUTFILE = ROOT / f"{APP_NAME}_{VERSION}_amd64.deb"

def create_structure():
    print("[INFO] Creating DEB structure...")
    if DEBROOT.exists():
        shutil.rmtree(DEBROOT)

    (DEBROOT / "DEBIAN").mkdir(parents=True)
    (DEBROOT / "opt/mvc-calculator").mkdir(parents=True)
    (DEBROOT / "usr/share/applications").mkdir(parents=True)
    (DEBROOT / "usr/share/icons/hicolor/256x256/apps").mkdir(parents=True)

def copy_files():
    print("[INFO] Copying portable build...")
    shutil.copytree(PORTABLE, DEBROOT / "opt/mvc-calculator/MVC_Calculator")

    shutil.copy("resources/icons/icn_emg.png",
                DEBROOT / "usr/share/icons/hicolor/256x256/apps/mvc-calculator.png")

def write_control():
    print("[INFO] Writing control file...")
    control = DEBROOT / "DEBIAN/control"
    control.write_text(f"""
Package: {APP_NAME}
Version: {VERSION}
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Moviolabs
Description: MVC Calculator for Linux
""")

def write_desktop():
    desktop = DEBROOT / "usr/share/applications/mvc-calculator.desktop"
    desktop.write_text(f"""
[Desktop Entry]
Type=Application
Name={DISPLAY_NAME}
Exec=/opt/mvc-calculator/MVC_Calculator/MVC_Calculator
Icon=mvc-calculator
Categories=Science;Utility;
Terminal=false
""")

def build_deb():
    print("[INFO] Building .deb package...")
    subprocess.run(["dpkg-deb", "--build", str(DEBROOT), str(OUTFILE)], check=True)

def main():
    create_structure()
    copy_files()
    write_control()
    write_desktop()
    build_deb()
    print(f"[DONE] DEB created: {OUTFILE}")

if __name__ == "__main__":
    main()
