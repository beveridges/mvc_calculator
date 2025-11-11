#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MASTER BUILD SCRIPT — MVC Calculator
------------------------------------
Full release pipeline:
  1️⃣ Run build_template.py (PyInstaller)
  2️⃣ Run build_template_msi.py (MSI + ZIP)
  3️⃣ Run release_to_github.py (GitHub upload)

Keeps same version name (from utilities/version_info.py).
Logs all steps under:
  C:\\Users\\Scott\\Documents\\.builds\\mvc_calculator\\master_build_YY.MMDD-HHMMSS.log
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================
PROJECT_NAME = "MVC_Calculator"
ROOT = Path(__file__).resolve().parent
BUILD_SCRIPT = ROOT / "build_template.py"
MSI_SCRIPT = ROOT / "build_template_msi.py"
RELEASE_SCRIPT = ROOT / "release_to_github.py"
VERSION_FILE = ROOT / "utilities" / "version_info.py"
LOG_DIR = Path.home() / "Documents" / ".builds" / PROJECT_NAME.lower()
LOG_FILE = LOG_DIR / f"master_build_{datetime.now():%y.%m%d-%H%M%S}.log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def run_step(name: str, cmd: list[str]) -> int:
    """Run subprocess, streaming and logging output."""
    print(f"\n========== {name} ==========")
    print(" ".join(cmd))
    with LOG_FILE.open("a", encoding="utf-8") as log:
        log.write(f"\n[{datetime.now():%H:%M:%S}] {name}\n")
        log.write("=" * 70 + "\n")
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            sys.stdout.write(line)
            log.write(line)
        proc.wait()
        log.write(f"\n[exit code] {proc.returncode}\n")
        log.flush()
    return proc.returncode


def read_buildnumber() -> str:
    """Read BUILDNUMBER from version_info.py."""
    if not VERSION_FILE.exists():
        return "unknown"
    for line in VERSION_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("BUILDNUMBER"):
            return line.split("=")[1].strip().strip('"')
    return "unknown"


# ============================================================
# MAIN SEQUENCE
# ============================================================
def main():
    print(f"\n🚀 MASTER BUILD: {PROJECT_NAME}")
    print(f"📄 Log file → {LOG_FILE}\n")

    # STEP 1 — PyInstaller build
    code1 = run_step("PyInstaller Build", [sys.executable, str(BUILD_SCRIPT), "--onedir"])
    if code1 != 0:
        print(f"\n❌ PyInstaller failed (exit code {code1})")
        sys.exit(code1)

    # STEP 2 — Get build number for reference
    build_number = read_buildnumber()
    print(f"\n[OK] Using version tag: {build_number}\n")

    # STEP 3 — MSI + ZIP
    code2 = run_step("MSI + ZIP Packaging", [sys.executable, str(MSI_SCRIPT)])
    if code2 != 0:
        print(f"\n❌ MSI packaging failed (exit code {code2})")
        sys.exit(code2)

    # STEP 4 — GitHub Release
    code3 = run_step("GitHub Release", [sys.executable, str(RELEASE_SCRIPT)])
    if code3 != 0:
        print(f"\n❌ GitHub release failed (exit code {code3})")
        sys.exit(code3)

    print("\n✅ ALL STEPS COMPLETED SUCCESSFULLY")
    print(f"   Version: {build_number}")
    print(f"   Log saved at: {LOG_FILE}")


# ============================================================
# ENTRY
# ============================================================
if __name__ == "__main__":
    main()
