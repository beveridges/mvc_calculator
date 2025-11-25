#!/usr/bin/env python3
# Upload Windows + Linux builds to Moviolabs FTP
# ----------------------------------------------

from __future__ import annotations
import argparse
import os
import ftplib
from pathlib import Path

APP_BASENAME = "MVC_Calculator"

SOURCE_WINDOWS = Path.home() / "Documents/.builds/MVC_CALCULATOR/msi/builds"
SOURCE_LINUX   = Path.home() / "Documents/.linux_builds/MVC_CALCULATOR/linux_builds"

TARGET_DIR = "/public_html/downloads/MVC_Calculator/releases"

DEFAULT_HOST = "ftp.moviolabs.com"
PRESET_USERNAME = "moviolab"
PRESET_PASSWORD = "f2Pf3aNF-N8:9h"


def newest_windows(src: Path):
    msi = list(src.glob("MVC_Calculator-*.msi"))
    zipf = list(src.glob("MVC_Calculator-*-portable.zip"))
    if not msi or not zipf:
        raise FileNotFoundError("Windows MSI or ZIP missing")
    return (
        max(msi,  key=lambda p: p.stat().st_mtime),
        max(zipf, key=lambda p: p.stat().st_mtime)
    )


def newest_linux(src: Path):
    deb = list((src / "deb").glob("mvc-calculator_*.deb"))
    app = list((src / "appimage").glob("MVC_Calculator-*.AppImage"))
    if not deb or not app:
        raise FileNotFoundError("Linux .deb or AppImage missing")
    return (
        max(deb, key=lambda p: p.stat().st_mtime),
        max(app, key=lambda p: p.stat().st_mtime)
    )


def ensure_dir(ftp, remote):
    parts = remote.strip("/").split("/")
    for i in range(1, len(parts) + 1):
        sub = "/" + "/".join(parts[:i])
        try:
            ftp.cwd(sub)
        except ftplib.error_perm:
            ftp.mkd(sub)
            ftp.cwd(sub)


def upload(ftp, local: Path):
    print(f"[upload] {local.name}")
    with local.open("rb") as f:
        ftp.storbinary(f"STOR {local.name}", f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--user")
    parser.add_argument("--password")
    args = parser.parse_args()

    user = args.user or PRESET_USERNAME
    pw   = args.password or PRESET_PASSWORD

    print("\n📦 Locating build artifacts…")

    win_msi, win_zip = newest_windows(SOURCE_WINDOWS)
    lin_deb, lin_app = newest_linux(SOURCE_LINUX)

    print("\nFound:")
    print(" -", win_msi)
    print(" -", win_zip)
    print(" -", lin_deb)
    print(" -", lin_app)

    print("\n🔌 Connecting to FTP…")
    with ftplib.FTP(args.host) as ftp:
        ftp.login(user=user, passwd=pw)
        ensure_dir(ftp, TARGET_DIR)
        ftp.cwd(TARGET_DIR)

        for f in [win_msi, win_zip, lin_deb, lin_app]:
            upload(ftp, f)

    print("\n🌍 FTP deploy complete.\n")


if __name__ == "__main__":
    main()















# #!/usr/bin/env python3
# # Upload EXE + ZIP + DEB + AppImage to Moviolabs FTP

# from __future__ import annotations
# import argparse
# import ftplib
# import os
# from pathlib import Path

# # ==========================================
# # App name + file patterns
# # ==========================================
# APP_BASENAME = "MVC_Calculator"

# # ==========================================
# # Windows & Linux build directories
# # ==========================================
# SOURCE_WINDOWS = Path.home() / "Documents/.builds/MVC_CALCULATOR/msi/builds"
# SOURCE_LINUX = Path.home() / "Documents/.linux_builds/MVC_CALCULATOR/linux_builds"

# TARGET_DIR = "/public_html/downloads/MVC_Calculator/releases"
# DEFAULT_HOST = "ftp.moviolabs.com"

# PRESET_USERNAME = "moviolab"
# PRESET_PASSWORD = "f2Pf3aNF-N8:9h"

# # ==========================================
# # Find newest Windows build artifacts
# # ==========================================
# def newest_windows_files(src: Path):
    # msi_files = list(src.glob("MVC_Calculator-*.msi"))
    # zip_files = list(src.glob("MVC_Calculator-*-portable.zip"))

    # if not msi_files:
        # raise FileNotFoundError("No MSI found in Windows build directory.")
    # if not zip_files:
        # raise FileNotFoundError("No portable ZIP found in Windows build directory.")

    # newest_msi = max(msi_files, key=lambda p: p.stat().st_mtime)
    # newest_zip = max(zip_files, key=lambda p: p.stat().st_mtime)

    # return newest_msi, newest_zip

# # ==========================================
# # Find newest Linux build artifacts
# # ==========================================
# def newest_linux_files(src: Path):
    # deb_files = list((src / "deb").glob("mvc-calculator_*.deb"))
    # img_files = list((src / "appimage").glob("MVC_Calculator-*.AppImage"))

    # if not deb_files:
        # raise FileNotFoundError("No .deb file found in Linux deb/ folder.")
    # if not img_files:
        # raise FileNotFoundError("No AppImage file found in Linux appimage/ folder.")

    # newest_deb = max(deb_files, key=lambda p: p.stat().st_mtime)
    # newest_img = max(img_files, key=lambda p: p.stat().st_mtime)

    # return newest_deb, newest_img

# # ==========================================
# # FTP helpers
# # ==========================================
# def ensure_remote_dir(ftp, remote):
    # parts = [p for p in remote.strip("/").split("/") if p]
    # for i in range(len(parts)):
        # sub = "/" + "/".join(parts[: i + 1])
        # try:
            # ftp.cwd(sub)
        # except ftplib.error_perm:
            # ftp.mkd(sub)
            # ftp.cwd(sub)

# def upload_file(ftp, local: Path, remote_name: str):
    # print(f"[uploading] {remote_name}")
    # with local.open("rb") as f:
        # ftp.storbinary(f"STOR {remote_name}", f)
    # print(f"[ok] {remote_name}")

# # ==========================================
# # Main deploy logic
# # ==========================================
# def deploy(host, user, password):
    # print("[info] Locating build artifacts...")

    # win_msi, win_zip = newest_windows_files(SOURCE_WINDOWS)
    # lin_deb, lin_img = newest_linux_files(SOURCE_LINUX)

    # print("\n[info] Found:")
    # print(" -", win_msi)
    # print(" -", win_zip)
    # print(" -", lin_deb)
    # print(" -", lin_img)

    # print("\n[info] Connecting to FTP...")

    # with ftplib.FTP(host) as ftp:
        # ftp.login(user=user, passwd=password)
        # ensure_remote_dir(ftp, TARGET_DIR)
        # ftp.cwd(TARGET_DIR)

        # print("[info] Uploading files...")

        # for f in [win_msi, win_zip, lin_deb, lin_img]:
            # upload_file(ftp, f, f.name)

    # print("\n[done] Release upload complete.")

# # ==========================================
# # CLI
# # ==========================================
# def main():
    # parser = argparse.ArgumentParser(description="Upload release builds to Moviolabs FTP.")
    # parser.add_argument("--host", default=DEFAULT_HOST)
    # parser.add_argument("--user")
    # parser.add_argument("--password")
    # args = parser.parse_args()

    # user = args.user or PRESET_USERNAME
    # password = args.password or PRESET_PASSWORD

    # deploy(args.host, user, password)

# if __name__ == "__main__":
    # main()
