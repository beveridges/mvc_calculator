#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
import subprocess
from pathlib import Path

from utilities.version_info import BUILDNUMBER  # same as Windows build

APP_NAME = "MVC_Calculator"
VERSION = BUILDNUMBER  # e.g. "25.11-alpha.01.72"

# ROOT = Path("/mnt/c/Users/Scott/Documents/.linux_builds/MVC_CALCULATOR/linux_builds")
ROOT = Path.home() / ".linux_builds" / "MVC_CALCULATOR" / "linux_builds"
PORTABLE = ROOT / "pyinstaller"
APPDIR = ROOT / "appimage" / "AppDir"
OUTFILE = ROOT / f"{APP_NAME}-{VERSION}-x86_64.AppImage"


def create_structure() -> None:
    print("[INFO] Creating AppDir structure...")
    if APPDIR.exists():
        shutil.rmtree(APPDIR)

    (APPDIR / "usr/bin").mkdir(parents=True, exist_ok=True)
    (APPDIR / "usr/share/icons").mkdir(parents=True, exist_ok=True)
    (APPDIR / "usr/share/applications").mkdir(parents=True, exist_ok=True)


def copy_files() -> None:
    print("[INFO] Copying portable build...")
    # Copy the PyInstaller onedir into /usr/bin/MVC_Calculator
    target = APPDIR / "usr/bin" / APP_NAME
    shutil.copytree(PORTABLE, target)

    # Icon: use your existing PNG
    icon_src = Path("resources/icons/icn_emg.png")
    icon_dest = APPDIR / "usr/share/icons" / f"{APP_NAME}.png"
    shutil.copy(icon_src, icon_dest)


def create_desktop() -> None:
    print("[INFO] Writing .desktop file...")

    exec_path = f"/usr/bin/{APP_NAME}/{APP_NAME}"

    desktop_file = APPDIR / "usr/share/applications" / f"{APP_NAME}.desktop"
    desktop_file.write_text(
        f"""[Desktop Entry]
Type=Application
Name={APP_NAME}
Exec={exec_path}
Icon={APP_NAME}
Categories=Science;Utility;
Terminal=false
""".strip()
    )


def build_appimage() -> None:
    print("[INFO] Building AppImage...")
    subprocess.run(
        ["appimagetool", str(APPDIR), str(OUTFILE)],
        check=True,
    )


def main() -> None:
    create_structure()
    copy_files()
    create_desktop()
    build_appimage()
    print(f"[DONE] AppImage created: {OUTFILE}")


if __name__ == "__main__":
    main()















# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# import os
# import shutil
# import subprocess
# from pathlib import Path

# APP_NAME = "MVC_Calculator"
# VERSION = "1.0.0"

# ROOT = Path("/mnt/c/Users/Scott/Documents/.linux_builds/MVC_CALCULATOR/linux_builds")
# PORTABLE = ROOT / "pyinstaller"
# APPDIR = ROOT / "appimage" / "AppDir"
# OUTFILE = ROOT / f"{APP_NAME}-x86_64.AppImage"


# def create_structure():
    # print("[INFO] Creating AppDir structure...")
    # if APPDIR.exists():
        # shutil.rmtree(APPDIR)
    # (APPDIR / "usr/bin").mkdir(parents=True, exist_ok=True)
    # (APPDIR / "usr/share/icons").mkdir(parents=True, exist_ok=True)
    # (APPDIR / "usr/share/applications").mkdir(parents=True, exist_ok=True)


# def copy_files():
    # print("[INFO] Copying portable build...")
    # target = APPDIR / "usr/bin" / APP_NAME
    # shutil.copytree(PORTABLE, target)


# def create_desktop():
    # print("[INFO] Writing .desktop file...")

    # desktop_file = APPDIR / "usr/share/applications" / f"{APP_NAME}.desktop"

    # desktop_file.write_text(f"""
    # [Desktop Entry]
    # Type=Application
    # Name={APP_NAME}
    # Exec=/usr/bin/{APP_NAME}/{APP_NAME}
    # Icon={APP_NAME}
    # Categories=Utility;
    # """.strip())

    # # Copy icon (use your PNG)
    # icon_src = Path("resources/icons/icn_emg.png")
    # icon_dest = APPDIR / "usr/share/icons" / f"{APP_NAME}.png"
    # shutil.copy(icon_src, icon_dest)


# def build_appimage():
    # print("[INFO] Building AppImage...")

    # subprocess.run([
        # "appimagetool",
        # str(APPDIR),
        # str(OUTFILE)
    # ], check=True)


# def main():
    # create_structure()
    # copy_files()
    # create_desktop()
    # build_appimage()
    # print(f"[DONE] AppImage created: {OUTFILE}")


# if __name__ == "__main__":
    # main()




















# # # build_linux_appimage.py
# # import os
# # import shutil
# # import subprocess
# # from pathlib import Path

# # APP_NAME = "MVC_Calculator"
# # VERSION = "1.0.0"

# # ROOT = Path("/mnt/c/Users/Scott/Documents/.linux_builds/MVC_CALCULATOR/linux_builds")
# # PORTABLE = ROOT / "pyinstaller"
# # APPDIR = ROOT / "appimage" / "AppDir"
# # OUTFILE = ROOT / f"{APP_NAME}-x86_64.AppImage"

# # def create_structure():
    # # print("[INFO] Creating AppDir structure...")
    # # if APPDIR.exists():
        # # shutil.rmtree(APPDIR)
    # # (APPDIR / "usr/bin").mkdir(parents=True)
    # # (APPDIR / "usr/share/icons/hicolor/256x256/apps").mkdir(parents=True)
    # # (APPDIR / "usr/share/applications").mkdir(parents=True)

# # def copy_files():
    # # print("[INFO] Copying portable build...")
    # # shutil.copytree(PORTABLE, APPDIR / "usr/bin" / APP_NAME)

    # # shutil.copy("resources/icons/icn_emg.png",
                # # APPDIR / "usr/share/icons/hicolor/256x256/apps/mvc-calculator.png")

# # def create_desktop():
    # # desktop = APPDIR / "usr/share/applications/mvc-calculator.desktop"
    # # desktop.write_text(f"""
# # [Desktop Entry]
# # Type=Application
# # Name=MVC Calculator
# # Exec=/{APP_NAME}
# # Icon=mvc-calculator
# # Categories=Science;Utility;
# # Terminal=false
# # """)

# # def build_appimage():
    # # print("[INFO] Building AppImage...")
    # # subprocess.run([
        # # "appimagetool", str(APPDIR), str(OUTFILE)
    # # ], check=True)

# # def main():
    # # create_structure()
    # # copy_files()
    # # create_desktop()
    # # build_appimage()
    # # print(f"[DONE] AppImage created: {OUTFILE}")

# # if __name__ == "__main__":
    # # main()
