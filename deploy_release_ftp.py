#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Push latest build artifacts (MSI + portable ZIP) to Moviolabs FTP release folder.

Usage:
    python deploy_release_ftp.py --user <ftp_user> --password <ftp_password>

Defaults:
    - Source directory: C:/Users/<user>/Documents/.builds/mvc_calculator/msi/builds
    - Target directory on FTP: /public_html/downloads/MVC_Calculator/releases

The script selects the most recent `MVC_Calculator-*.msi` and matching
`MVC_Calculator-*-portable.zip` from the source directory and uploads them.
"""

from __future__ import annotations

import argparse
import ftplib
import getpass
import os
import sys
from pathlib import Path
from typing import Tuple, Optional, List

# ===============================================================================================
APP_BASENAME = "MVC_Calculator"
SOURCE_ROOT = Path.home() / "Documents" / ".builds" / "mvc_calculator" / "msi" / "builds"
TARGET_DIR = "/public_html/downloads/MVC_Calculator/releases"
DEFAULT_HOST = "ftp.moviolabs.com"
PRESET_USERNAME: str = "moviolab"
PRESET_PASSWORD: str = "f2Pf3aNF-N8:9h"  

PASSWORD FOR 
imm.qtm.machine
Nc)D6J(Fs1q+t=&x
# ===============================================================================================


def newest_release_pair(source_dir: Path) -> Tuple[Path, Path]:
    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    msi_files: List[Path] = sorted(source_dir.glob(f"{APP_BASENAME}-*.msi"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not msi_files:
        raise FileNotFoundError(f"No MSI files found in {source_dir}")

    latest_msi = msi_files[0]
    build_tag = latest_msi.stem.replace(f"{APP_BASENAME}-", "")
    zip_candidate = source_dir / f"{APP_BASENAME}-{build_tag}-portable.zip"

    if not zip_candidate.exists():
        raise FileNotFoundError(f"Portable ZIP not found for build '{build_tag}': {zip_candidate}")

    return latest_msi, zip_candidate


def ensure_remote_dir(ftp: ftplib.FTP, remote_path: str) -> None:
    parts = [p for p in remote_path.strip("/").split("/") if p]
    for idx in range(len(parts)):
        sub_path = "/" + "/".join(parts[: idx + 1])
        try:
            ftp.cwd(sub_path)
        except ftplib.error_perm:
            ftp.mkd(sub_path)
            ftp.cwd(sub_path)


def upload_file(ftp: ftplib.FTP, local_path: Path, remote_path: str) -> None:
    with local_path.open("rb") as fh:
        ftp.storbinary(f"STOR {remote_path}", fh)


def deploy(host: str, username: str, password: str, source_dir: Path = SOURCE_ROOT, remote_dir: str = TARGET_DIR) -> Tuple[Path, Path]:
    msi_path, zip_path = newest_release_pair(source_dir)

    print(f"[info] Uploading:")
    print(f"  - {msi_path.name}")
    print(f"  - {zip_path.name}")
    print(f"[info] FTP host: {host}")
    print(f"[info] Remote dir: {remote_dir}")

    with ftplib.FTP(host) as ftp:
        ftp.login(user=username, passwd=password)
        ensure_remote_dir(ftp, remote_dir)
        ftp.cwd(remote_dir)

        upload_file(ftp, msi_path, msi_path.name)
        print(f"[ok] Uploaded {msi_path.name}")

        upload_file(ftp, zip_path, zip_path.name)
        print(f"[ok] Uploaded {zip_path.name}")

    print("[done] Release artifacts uploaded successfully.")
    return msi_path, zip_path


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload latest MVC Calculator build to Moviolabs FTP.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="FTP host (default: ftp.moviolabs.com)")
    parser.add_argument("--user", help="FTP username")
    parser.add_argument("--password", help="FTP password (prompted if omitted)")
    parser.add_argument("--source", type=Path, default=SOURCE_ROOT, help="Source directory containing MSI/ZIP builds")
    parser.add_argument("--remote-dir", default=TARGET_DIR, help="Remote FTP directory to upload to")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)

    username = args.user or PRESET_USERNAME or input("FTP username: ").strip()
    password = args.password or PRESET_PASSWORD or getpass.getpass("FTP password: ")

    try:
        deploy(
            host=args.host,
            username=username,
            password=password,
            source_dir=args.source,
            remote_dir=args.remote_dir,
        )
    except Exception as exc:
        print(f"[error] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()

