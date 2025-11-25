#!/usr/bin/env python3
# MASTER LINUX BUILD — MVC Calculator
# -----------------------------------
# Builds:
#   ✔ AppImage
#   ✔ .deb package
#   (✘ Portable Linux build — DISABLED BY DEFAULT)

import subprocess
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent

# Sub-builders
APPIMAGE = ROOT / "build_linux_appimage.py"
DEB      = ROOT / "build_linux_deb.py"

# Linux build root (Windows-mapped path)
WIN_ROOT = Path("/mnt/c/Users/Scott/Documents/.linux_builds/MVC_CALCULATOR/linux_builds")
LOG_FILE = WIN_ROOT / f"linux_master_{datetime.now():%y.%m%d-%H%M%S}.log"
WIN_ROOT.mkdir(parents=True, exist_ok=True)

def run_step(name, cmd):
    print(f"\n========== {name} ==========")
    with LOG_FILE.open("a", encoding="utf-8") as log:
        log.write(f"\n[{datetime.now():%H:%M:%S}] {name}\n")
        log.write("=" * 70 + "\n")

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True)

        for line in proc.stdout:
            sys.stdout.write(line)
            log.write(line)

        proc.wait()
        log.write(f"\n[exit code] {proc.returncode}\n")
        log.flush()

    if proc.returncode != 0:
        print(f"\n❌ {name} failed (exit {proc.returncode})")
        sys.exit(proc.returncode)

print(f"\n🐧 FULL LINUX BUILD — logging to:\n{LOG_FILE}\n")

# ------------------------------------------------------------
# 1) SKIP PORTABLE ALWAYS — USER WILL BUILD IT MANUALLY IF WANTED
# ------------------------------------------------------------
print("[INFO] Portable Linux build DISABLED by default.")
print("[INFO] If you want portable Linux: run build_linux_portable.py manually.\n")

# ------------------------------------------------------------
# 2) Build AppImage
# ------------------------------------------------------------
run_step("AppImage Build", [sys.executable, str(APPIMAGE)])

# ------------------------------------------------------------
# 3) Build .deb
# ------------------------------------------------------------
run_step("DEB Package Build", [sys.executable, str(DEB)])

print("\n✅ ALL LINUX ARTIFACTS BUILT SUCCESSFULLY\n")

















# #!/usr/bin/env python3
# # MASTER LINUX BUILD — MVC Calculator
# # -----------------------------------
# # Builds:
# #   ✔ Portable Linux onedir (if missing)
# #   ✔ AppImage
# #   ✔ .deb package

# import subprocess
# import sys
# from pathlib import Path
# from datetime import datetime

# ROOT = Path(__file__).resolve().parent

# PORTABLE = ROOT / "build_linux_portable.py"
# APPIMAGE = ROOT / "build_linux_appimage.py"
# DEB      = ROOT / "build_linux_deb.py"

# WIN_ROOT = Path("/mnt/c/Users/Scott/Documents/.linux_builds/MVC_CALCULATOR/linux_builds")
# PYINSTALLER_OUT = WIN_ROOT / "pyinstaller"

# LOG_FILE = WIN_ROOT / f"linux_master_{datetime.now():%y.%m%d-%H%M%S}.log"
# WIN_ROOT.mkdir(parents=True, exist_ok=True)

# def run_step(name, cmd):
    # print(f"\n========== {name} ==========")
    # with LOG_FILE.open("a", encoding="utf-8") as log:
        # log.write(f"\n[{datetime.now():%H:%M:%S}] {name}\n")
        # log.write("=" * 70 + "\n")

        # proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                # stderr=subprocess.STDOUT, text=True)

        # for line in proc.stdout:
            # sys.stdout.write(line)
            # log.write(line)

        # proc.wait()
        # log.write(f"\n[exit code] {proc.returncode}\n")
        # log.flush()

    # if proc.returncode != 0:
        # print(f"\n❌ {name} failed (exit {proc.returncode})")
        # sys.exit(proc.returncode)

# print(f"\n🐧 FULL LINUX BUILD — logging to:\n{LOG_FILE}\n")

# # ------------------------------------------------------------
# # 1) Ensure portable exists
# # ------------------------------------------------------------
# if not PYINSTALLER_OUT.exists():
    # print("\n[INFO] No portable Linux build detected.")
    # print("[INFO] Auto-building portable Linux version…")
    # run_step("Portable Linux Build", [sys.executable, str(PORTABLE)])
# else:
    # print("[OK] Portable build detected.")

# # ------------------------------------------------------------
# # 2) Build AppImage
# # ------------------------------------------------------------
# run_step("AppImage Build", [sys.executable, str(APPIMAGE)])

# # ------------------------------------------------------------
# # 3) Build .deb
# # ------------------------------------------------------------
# run_step("DEB Package Build", [sys.executable, str(DEB)])

# print("\n✅ ALL LINUX ARTIFACTS BUILT SUCCESSFULLY\n")



















# # #!/usr/bin/env python3
# # """
# # Master Linux Builder for MVC Calculator
# # =======================================

# # Builds:
  # # ✔ AppImage
  # # ✔ .deb package
  # # (✘ Portable build — included but DISABLED by default)

# # Output is placed inside:

  # # /mnt/c/Users/Scott/Documents/.linux_builds/MVC_CALCULATOR/linux_builds/

# # Windows path:
  # # C:\Users\Scott\Documents\.linux_builds\MVC_CALCULATOR\linux_builds\
# # """

# # import os
# # import shutil
# # import subprocess
# # from pathlib import Path

# # # ------------------------------------------------------------
# # # CONFIGURATION
# # # ------------------------------------------------------------

# # APP_NAME = "MVC_Calculator"
# # DEB_NAME = "mvc-calculator"
# # VERSION = "1.0.0"

# # WIN_ROOT = Path("/mnt/c/Users/Scott/Documents/.linux_builds/MVC_CALCULATOR/linux_builds")
# # PYINSTALLER_OUT = WIN_ROOT / "pyinstaller"
# # APPIMAGE_OUTFILE = WIN_ROOT / f"{APP_NAME}-x86_64.AppImage"
# # DEB_ROOT = WIN_ROOT / "deb" / f"{DEB_NAME}_{VERSION}_amd64"
# # DEB_OUTFILE = WIN_ROOT / f"{DEB_NAME}_{VERSION}_amd64.deb"

# # ICON = "resources/icons/icn_emg.png"


# # # ------------------------------------------------------------
# # # UTIL: RUN
# # # ------------------------------------------------------------
# # def run_cmd(cmd):
    # # print(f"[CMD] {' '.join(cmd)}")
    # # subprocess.run(cmd, check=True)


# # # ------------------------------------------------------------
# # # STEP 1 — Portable (PyInstaller)
# # # Disabled unless user explicitly enables it
# # # ------------------------------------------------------------
# # def build_portable():
    # # print("\n=== BUILDING PORTABLE LINUX EXECUTABLE (PyInstaller) ===\n")

    # # shutil.rmtree("build", ignore_errors=True)
    # # shutil.rmtree("dist", ignore_errors=True)

    # # run_cmd([
        # # "pyinstaller",
        # # "--noconfirm",
        # # "--clean",
        # # "--name", APP_NAME,
        # # "--icon", ICON,
        # # "--add-data", "resources:resources",
        # # "main.py"
    # # ])

    # # print("[INFO] Copying to:", PYINSTALLER_OUT)
    # # shutil.rmtree(PYINSTALLER_OUT, ignore_errors=True)
    # # shutil.copytree(Path("dist") / APP_NAME, PYINSTALLER_OUT)

    # # print("[DONE] Portable build completed.\n")


# # # ------------------------------------------------------------
# # # STEP 2 — AppImage
# # # ------------------------------------------------------------
# # def build_appimage():
    # # print("\n=== BUILDING APPIMAGE ===\n")

    # # APPDIR = WIN_ROOT / "appimage" / "AppDir"

    # # if APPDIR.exists():
        # # shutil.rmtree(APPDIR)

    # # # Create structure
    # # (APPDIR / "usr/bin").mkdir(parents=True)
    # # (APPDIR / "usr/share/applications").mkdir(parents=True)
    # # (APPDIR / "usr/share/icons/hicolor/256x256/apps").mkdir(parents=True)

    # # # Copy PyInstaller build
    # # print("[INFO] Copying application files...")
    # # shutil.copytree(PYINSTALLER_OUT, APPDIR / "usr/bin" / APP_NAME)

    # # shutil.copy(ICON, APPDIR / "usr/share/icons/hicolor/256x256/apps/mvc-calculator.png")

    # # # Desktop entry
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

    # # print("[INFO] Running appimagetool...")
    # # run_cmd([
        # # "appimagetool",
        # # str(APPDIR),
        # # str(APPIMAGE_OUTFILE)
    # # ])

    # # print("[DONE] AppImage created:", APPIMAGE_OUTFILE, "\n")


# # # ------------------------------------------------------------
# # # STEP 3 — Debian .deb package
# # # ------------------------------------------------------------
# # def build_deb():
    # # print("\n=== BUILDING .DEB PACKAGE ===\n")

    # # if DEB_ROOT.exists():
        # # shutil.rmtree(DEB_ROOT)

    # # (DEB_ROOT / "DEBIAN").mkdir(parents=True)
    # # (DEB_ROOT / "opt/mvc-calculator").mkdir(parents=True)
    # # (DEB_ROOT / "usr/share/applications").mkdir(parents=True)
    # # (DEB_ROOT / "usr/share/icons/hicolor/256x256/apps").mkdir(parents=True)

    # # print("[INFO] Copying application files...")
    # # shutil.copytree(PYINSTALLER_OUT, DEB_ROOT / "opt/mvc-calculator/MVC_Calculator")

    # # shutil.copy(ICON, DEB_ROOT / "usr/share/icons/hicolor/256x256/apps/mvc-calculator.png")

    # # # control file
    # # (DEB_ROOT / "DEBIAN/control").write_text(f"""
# # Package: {DEB_NAME}
# # Version: {VERSION}
# # Section: utils
# # Priority: optional
# # Architecture: amd64
# # Maintainer: Moviolabs
# # Description: MVC Calculator for Linux
# # """)

    # # # desktop entry
    # # (DEB_ROOT / "usr/share/applications/mvc-calculator.desktop").write_text(f"""
# # [Desktop Entry]
# # Type=Application
# # Name=MVC Calculator
# # Exec=/opt/mvc-calculator/MVC_Calculator/MVC_Calculator
# # Icon=mvc-calculator
# # Categories=Science;Utility;
# # Terminal=false
# # """)

    # # print("[INFO] Building .deb...")
    # # run_cmd(["dpkg-deb", "--build", str(DEB_ROOT), str(DEB_OUTFILE)])

    # # print("[DONE] DEB created:", DEB_OUTFILE, "\n")


# # # ------------------------------------------------------------
# # # MAIN
# # # ------------------------------------------------------------
# # def main():

    # # print("\n===================================")
    # # print("  BUILD ALL LINUX ARTIFACTS")
    # # print("===================================\n")

    # # print(f"[INFO] Output directory: {WIN_ROOT}")

    # # # ------------------------------------------------------------
    # # # Portable Linux build — DISABLED BY DEFAULT
    # # # ------------------------------------------------------------
    # # # build_portable()   # ← UNCOMMENT to enable

    # # print("[SKIPPED] Portable Linux build (PyInstaller)")

    # # # Ensure portable exists before continuing
    # # if not PYINSTALLER_OUT.exists():
        # # print("\n❌ ERROR: Portable build missing.")
        # # print("You must enable build_portable() ONCE to generate it:")
        # # print("\n1) Edit build_all_linux.py")
        # # print("2) Uncomment:")
        # # print("       build_portable()")
        # # print("3) Run:")
        # # print("       python build_all_linux.py\n")
        # # return

    # # build_appimage()
    # # build_deb()

    # # print("\n=== ALL LINUX BUILDS COMPLETED SUCCESSFULLY ===\n")


# # if __name__ == "__main__":
    # # main()
