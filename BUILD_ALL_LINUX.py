#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

SCRIPT_ROOT = Path(__file__).resolve().parent

PORTABLE_SCRIPT = SCRIPT_ROOT / "build_linux_portable.py"
APPIMAGE_SCRIPT = SCRIPT_ROOT / "build_linux_appimage.py"
DEB_SCRIPT      = SCRIPT_ROOT / "build_linux_deb.py"

# FIXED — now uses local WSL home directory (correct)
LINUX_ROOT = Path.home() / ".linux_builds" / "MVC_CALCULATOR" / "linux_builds"
LINUX_ROOT.mkdir(parents=True, exist_ok=True)

LOG_FILE = LINUX_ROOT / f"linux_master_{datetime.now():%y.%m%d-%H%M%S}.log"

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

def main():
    print(f"\n🐧 FULL LINUX BUILD — logging to:\n{LOG_FILE}\n")

    run_step("Portable Linux Build", [sys.executable, str(PORTABLE_SCRIPT)])
    run_step("AppImage Build",      [sys.executable, str(APPIMAGE_SCRIPT)])
    run_step("DEB Package Build",   [sys.executable, str(DEB_SCRIPT)])

    print("\n✅ ALL LINUX ARTIFACTS BUILT SUCCESSFULLY\n")

if __name__ == "__main__":
    main()













# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# import sys
# import subprocess
# from pathlib import Path
# from datetime import datetime

# # Ensure UTF-8 output
# sys.stdout.reconfigure(encoding="utf-8")
# sys.stderr.reconfigure(encoding="utf-8")

# # -------------------------------------------------------------------
# # PATHS — always relative to this build folder
# # -------------------------------------------------------------------
# SCRIPT_ROOT = Path(__file__).resolve().parent

# PORTABLE_SCRIPT = SCRIPT_ROOT / "build_linux_portable.py"
# APPIMAGE_SCRIPT = SCRIPT_ROOT / "build_linux_appimage.py"
# DEB_SCRIPT      = SCRIPT_ROOT / "build_linux_deb.py"

# # -------------------------------------------------------------------
# # OUTPUT ROOT — EXACT same as Windows version
# # -------------------------------------------------------------------
# LINUX_ROOT = Path("/mnt/c/Users/Scott/Documents/.linux_builds/MVC_CALCULATOR/linux_builds")
# LINUX_ROOT.mkdir(parents=True, exist_ok=True)

# LOG_FILE = LINUX_ROOT / f"linux_master_{datetime.now():%y.%m%d-%H%M%S}.log"


# # -------------------------------------------------------------------
# # RUN STEP (with live log)
# # -------------------------------------------------------------------
# def run_step(name: str, cmd: list[str]) -> None:
    # print(f"\n========== {name} ==========")

    # with LOG_FILE.open("a", encoding="utf-8") as log:
        # log.write(f"\n[{datetime.now():%H:%M:%S}] {name}\n")
        # log.write("=" * 70 + "\n")

        # process = subprocess.Popen(
            # cmd,
            # stdout=subprocess.PIPE,
            # stderr=subprocess.STDOUT,
            # text=True
        # )

        # for line in process.stdout:
            # sys.stdout.write(line)
            # log.write(line)

        # process.wait()
        # log.write(f"\n[exit code] {process.returncode}\n")
        # log.flush()

    # if process.returncode != 0:
        # print(f"\n❌ {name} failed (exit {process.returncode})")
        # sys.exit(process.returncode)


# # -------------------------------------------------------------------
# # MAIN
# # -------------------------------------------------------------------
# def main() -> None:
    # print(f"\n🐧 FULL LINUX BUILD — logging to:\n{LOG_FILE}\n")

    # # ----------------------------------------------------------------
    # # 1) ALWAYS rebuild portable onedir
    # #    (keeps Windows + Linux version numbers identical)
    # # ----------------------------------------------------------------
    # run_step("Portable Linux Build",
             # [sys.executable, str(PORTABLE_SCRIPT)])

    # # ----------------------------------------------------------------
    # # 2) Build AppImage
    # # ----------------------------------------------------------------
    # run_step("AppImage Build",
             # [sys.executable, str(APPIMAGE_SCRIPT)])

    # # ----------------------------------------------------------------
    # # 3) Build DEB package
    # # ----------------------------------------------------------------
    # run_step("DEB Package Build",
             # [sys.executable, str(DEB_SCRIPT)])

    # print("\n✅ ALL LINUX ARTIFACTS BUILT SUCCESSFULLY\n")


# if __name__ == "__main__":
    # main()
