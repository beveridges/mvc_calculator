# build_linux_portable.py
import os
import shutil
from pathlib import Path
import subprocess

APP_NAME = "MVC_Calculator"
ICON = "resources/icons/icn_emg.png"

# Output directory (WINDOWS PATH mirrored into WSL)
/mnt/c/Users/Scott/Documents/.linux_builds/MVC_CALCULATOR/linux_builds/pyinstaller

def run():
    out_dir = Path("/mnt/c/Users/Scott/Documents/.linux_builds/MVC_CALCULATOR/linux_builds/pyinstaller")
    dist_dir = Path("dist") / APP_NAME

    print("[INFO] Cleaning build dirs...")
    shutil.rmtree("build", ignore_errors=True)
    shutil.rmtree("dist", ignore_errors=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[INFO] Running PyInstaller...")
    subprocess.run([
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--name", APP_NAME,
        "--icon", ICON,
        "--add-data", "resources:resources",
        "main.py"
    ], check=True)

    print("[INFO] Copying result to output folder...")
    shutil.rmtree(out_dir, ignore_errors=True)
    shutil.copytree(dist_dir, out_dir)

    print("[DONE] Portable Linux build created:")
    print(out_dir)

if __name__ == "__main__":
    run()
