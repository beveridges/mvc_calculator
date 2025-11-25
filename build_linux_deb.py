#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
import subprocess
from pathlib import Path

from utilities.version_info import BUILDNUMBER  # same as Windows build

APP_ID = "mvc-calculator"          # Debian package name
DISPLAY_NAME = "MVC Calculator"    # Human-readable
VERSION = BUILDNUMBER              # e.g. "25.11-alpha.01.72"

# ROOT = Path("/mnt/c/Users/Scott/Documents/.linux_builds/MVC_CALCULATOR/linux_builds")
ROOT = Path.home() / ".linux_builds" / "MVC_CALCULATOR" / "linux_builds"
PORTABLE = ROOT / "pyinstaller"
DEBROOT = ROOT / "deb" / f"{APP_ID}_{VERSION}_amd64"
OUTFILE = ROOT / f"{APP_ID}_{VERSION}_amd64.deb"


def create_structure() -> None:
    print("[INFO] Creating DEB structure...")

    if DEBROOT.exists():
        shutil.rmtree(DEBROOT)

    (DEBROOT / "DEBIAN").mkdir(parents=True, exist_ok=True)
    (DEBROOT / "usr/bin").mkdir(parents=True, exist_ok=True)
    (DEBROOT / "usr/share/applications").mkdir(parents=True, exist_ok=True)
    (DEBROOT / "usr/share/icons/hicolor/256x256/apps").mkdir(parents=True, exist_ok=True)


def copy_files() -> None:
    print("[INFO] Copying portable build...")

    # Place full PyInstaller onedir inside /usr/bin/MVC_Calculator
    bin_dir_name = DISPLAY_NAME.replace(" ", "_")  # "MVC_Calculator"
    target = DEBROOT / "usr/bin" / bin_dir_name
    shutil.copytree(PORTABLE, target)

    # Icon
    icon_src = Path("resources/icons/icn_emg.png")
    icon_dest = DEBROOT / "usr/share/icons/hicolor/256x256/apps/mvc-calculator.png"
    shutil.copy(icon_src, icon_dest)


def write_control() -> None:
    print("[INFO] Writing control file...")

    control = f"""Package: {APP_ID}
Version: {VERSION}
Section: utils
Priority: optional
Architecture: amd64
Depends: python3
Maintainer: MVCCalculator <dev@moviolabs.com>
Description: {DISPLAY_NAME}
 MVC Calculator packaged for Linux.
"""

    control_file = DEBROOT / "DEBIAN" / "control"
    control_file.write_text(control)


def write_desktop() -> None:
    print("[INFO] Writing .desktop entry...")

    bin_dir_name = DISPLAY_NAME.replace(" ", "_")  # "MVC_Calculator"
    exec_path = f"/usr/bin/{bin_dir_name}/{bin_dir_name}"

    desktop_data = f"""[Desktop Entry]
Type=Application
Name={DISPLAY_NAME}
Exec={exec_path}
Icon=mvc-calculator
Categories=Science;Utility;
Terminal=false
"""

    desktop_file = DEBROOT / "usr/share/applications" / f"{APP_ID}.desktop"
    desktop_file.write_text(desktop_data)


def build_deb() -> None:
    print("[INFO] Building .deb package...")
    subprocess.run(
        ["dpkg-deb", "--build", str(DEBROOT), str(OUTFILE)],
        check=True,
    )


def main() -> None:
    create_structure()
    copy_files()
    write_control()
    write_desktop()
    build_deb()
    print(f"[DONE] DEB created: {OUTFILE}")


if __name__ == "__main__":
    main()
