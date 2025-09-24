#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Combined builder:
- Computes/writes utilities/system_info.py (unless --no-write-sysinfo)
- Runs PyInstaller with all artifacts under ./.build/pyinstaller/
- Archives newest dist to ./.build/pyinstaller/builds/<AppName-<BUILDNUMBER>>/ (FLAT)
- Copies _DATA_/ → datos/ and video/ → videos/ into that archive root
- (Optional) Zips the archive folder when --zip is passed
- Purges older archives, keeping latest N (default 3)

Usage:
  python build.py                     # onedir (recommended)
  python build.py --onefile           # single exe
  python build.py --purge             # clean previous dist/work
  python build.py --keep 3            # keep latest 3 archives (default)
  python build.py --name MotusHombro
  python build.py --no-write-sysinfo
  python build.py --zip               # also create a .zip of the archive
"""

from __future__ import annotations
import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# ---------- PyInstaller entry ----------
try:
    from PyInstaller.__main__ import run as pyinstaller_run
except ImportError:
    print("PyInstaller isn't installed. Run:  pip install pyinstaller")
    sys.exit(1)

# ---------- Git helpers ----------
def _run_git(args: list[str]) -> Optional[str]:
    try:
        out = subprocess.run(["git"] + args, check=True, capture_output=True, text=True).stdout.strip()
        return out
    except Exception:
        return None

def in_git_repo() -> bool:
    return _run_git(["rev-parse", "--is-inside-work-tree"]) == "true"

def git_rev_head(short: int = 7) -> str:
    return _run_git(["rev-parse", f"--short={short}", "HEAD"]) or "unknown"

def git_latest_tag() -> str:
    return _run_git(["describe", "--tags", "--abbrev=0"]) or ""

# ---------- Previous build reader ----------
def read_previous_from_import(repo_root: Path) -> Tuple[Optional[str], Optional[str]]:
    try:
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        import importlib
        prev_mod = importlib.import_module("utilities.system_info")
        prev_build = getattr(prev_mod, "BUILDNUMBER", None)
        prev_version = getattr(prev_mod, "VERSIONNUMBER", None)
        if isinstance(prev_build, str) and isinstance(prev_version, str):
            return prev_build, prev_version
    except Exception:
        pass
    return None, None

def read_previous_from_file(repo_root: Path) -> Tuple[Optional[str], Optional[str]]:
    sysinfo_path = repo_root / "utilities" / "version_info.py"
    if not sysinfo_path.exists():
        return None, None
    try:
        text = sysinfo_path.read_text(encoding="utf-8", errors="ignore")
        m_build = re.search(r'^\s*BUILDNUMBER\s*=\s*"([^"]+)"', text, re.M)
        m_version = re.search(r'^\s*VERSIONNUMBER\s*=\s*"([^"]+)"', text, re.M)
        prev_build = m_build.group(1) if m_build else None
        prev_version = m_version.group(1) if m_version else None
        return prev_build, prev_version
    except Exception:
        return None, None

def read_previous_build_info(repo_root: Path) -> Tuple[Optional[str], Optional[str]]:
    prev_build, prev_version = read_previous_from_import(repo_root)
    if prev_build and prev_version:
        return prev_build, prev_version
    return read_previous_from_file(repo_root)

def increment_last_segment(prev_build: str) -> Tuple[str, int]:
    parts = prev_build.split(".")
    if not parts:
        return "00", 0
    last = parts[-1]
    if not last.isdigit():
        return "00", 0
    width = max(2, len(last))
    nxt = int(last) + 1
    return f"{nxt:0{width}d}", nxt

   
def detect_conda_env_info(project_root: Path) -> Tuple[str, str, str]:
    """
    Returns (env_name, python_version, env_file_path_relative_to_project_root_or_empty).
    env_name from CONDA_DEFAULT_ENV or last segment of CONDA_PREFIX.
    env_file: first existing among:
      environment.yml/.yaml, <env>.yml/.yaml, conda.yml/.yaml in project root.
    """
    env_name = os.environ.get("CONDA_DEFAULT_ENV", "").strip()
    if not env_name:
        prefix = os.environ.get("CONDA_PREFIX", "").strip()
        if prefix:
            env_name = Path(prefix).name
    if not env_name:
        env_name = "unknown"

    pyver = ".".join(map(str, sys.version_info[:3]))

    candidates = [
        project_root / "environment.yml",
        project_root / "environment.yaml",
        project_root / f"{env_name}.yml",
        project_root / f"{env_name}.yaml",
        project_root / "conda.yml",
        project_root / "conda.yaml",
    ]

    env_file = ""
    for c in candidates:
        if c.exists():
            try:
                # make it relative to the repo root (project_root)
                env_file = os.path.relpath(c.resolve(), start=project_root.resolve())
            except Exception:
                env_file = str(c)
            break

    return env_name, pyver, env_file


# ---------- Archiving & purge ----------
def archive_latest(distpath: Path, builds_dir: Path, tag: str, app_name: str | None = None) -> Optional[Path]:
    """
    Copy newest build from dist/ into builds/{tag}/, FLATTENING the onedir layout:
      dist/<AppName>/...  →  builds/{tag}/(all files here, no extra folder)
    If onefile, the single exe is copied into builds/{tag}/ directly.
    """
    if not distpath.exists():
        return None

    if app_name and (distpath / app_name).exists():
        latest = distpath / app_name
    else:
        items = list(distpath.iterdir())
        if not items:
            return None
        latest = max(items, key=lambda p: p.stat().st_mtime)

    dest_root = builds_dir / tag
    if dest_root.exists():
        shutil.rmtree(dest_root, ignore_errors=True)
    dest_root.mkdir(parents=True, exist_ok=True)

    try:
        if latest.is_dir():
            for item in latest.iterdir():
                src = item
                dst = dest_root / item.name
                if src.is_dir():
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
        else:
            shutil.copy2(latest, dest_root / latest.name)
        return dest_root
    except Exception as e:
        print(f"[warn] archive failed: {e}")
        return None

def purge_old_archives(builds_dir: Path, keep: int = 3) -> None:
    if not builds_dir.exists():
        return
    items = [p for p in builds_dir.iterdir()]
    items.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for p in items[keep:]:
        try:
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink(missing_ok=True)
            print(f"[purged] {p}")
        except Exception as e:
            print(f"[warn] purge failed for {p}: {e}")

def copy_contents(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return
    if dst.exists():
        shutil.rmtree(dst, ignore_errors=True)
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        s = item
        d = dst / item.name
        if s.is_dir():
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

# ---------- Main ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--onefile", action="store_true", help="Build single-file exe")
    ap.add_argument("--onedir", action="store_true", help="Build folder (default)")
    ap.add_argument("--purge", action="store_true", help="Remove previous dist/work before build")
    ap.add_argument("--keep", type=int, default=3, help="How many archived builds to keep (default 3)")
    ap.add_argument("--name", default="MotusHombro", help="Application name")
    ap.add_argument("--no-write-sysinfo", action="store_true", help="Skip writing utilities/system_info.py")
    ap.add_argument("--entry", default="main.py", help="Entry script (default: main.py)")
    ap.add_argument("--channel", default="alpha.01", help="Version channel (default: alpha.01)")
    ap.add_argument("--version-base", default=None, help="Override YY.MM (e.g., 25.09); default = now")
    ap.add_argument("--zip", dest="do_zip", action="store_true", help="Also create a .zip of the archive")
    args = ap.parse_args()

    project_root = Path(__file__).resolve().parent
    entry_script = project_root / args.entry
    if not entry_script.exists():
        print(f"[error] Entry script not found: {entry_script}")
        sys.exit(2)

    # ----- Version/build info -----
    base = args.version_base or datetime.now().strftime("%y.%m")
    VERSIONNUMBER = f"{base}-{args.channel}"
    VERSIONNAME = f"MOTUS.Hombro.{VERSIONNUMBER}"
    FRIENDLYVERSIONNAME = "MOTUS Hombro"

    if in_git_repo():
        GITREVHEAD = git_rev_head(7)
        GITTAG = git_latest_tag()
        repo_root = Path(_run_git(["rev-parse", "--show-toplevel"]) or project_root)
    else:
        GITREVHEAD = "unknown"
        GITTAG = ""
        repo_root = project_root

    prev_build, prev_version = read_previous_build_info(repo_root)
    SEQ = increment_last_segment(prev_build)[0] if (prev_build and prev_version == VERSIONNUMBER) else "00"
    BUILDNUMBER = f"{VERSIONNUMBER}.{SEQ}"

    # ----- Conda / Python info -----
    CONDAENVIRONMENTNAME, PYTHONVERSION, CONDAENVIRONMENTFILENAME = detect_conda_env_info(project_root)

    print(f"GITREVHEAD            = {GITREVHEAD}")
    print(f"BUILDNUMBER           = {BUILDNUMBER}")
    print(f"VERSIONNUMBER         = {VERSIONNUMBER}")
    print(f"VERSIONNAME           = {VERSIONNAME}")
    print(f"FRIENDLYVERSIONNAME   = {FRIENDLYVERSIONNAME}")
    print(f"GITTAG                = {GITTAG}")
    print(f"CONDAENVIRONMENTNAME  = {CONDAENVIRONMENTNAME}")
    print(f"PYTHONVERSION         = {PYTHONVERSION}")
    print(f"CONDAENVIRONMENTFILENAME  = {CONDAENVIRONMENTFILENAME or '(not found)'}")

    # ----- Write utilities/version_info.py -----
    if not args.no_write_sysinfo:
        def dq(s: str) -> str:
            # double-quote-safe literal
            s = s or ""
            return s.replace("\\", "\\\\").replace('"', '\\"')

        sysinfo_dir = repo_root / "utilities"
        sysinfo_dir.mkdir(parents=True, exist_ok=True)
        sysinfo_path = sysinfo_dir / "version_info.py"
        sysinfo_path.write_text(
            "# Auto-generated by build.py — DO NOT EDIT BY HAND\n"
            f'GITREVHEAD = "{dq(GITREVHEAD)}"\n'
            f'BUILDNUMBER = "{dq(BUILDNUMBER)}"\n'
            f'VERSIONNUMBER = "{dq(VERSIONNUMBER)}"\n'
            f'FRIENDLYVERSIONNAME = "{dq(FRIENDLYVERSIONNAME)}"\n'
            f'VERSIONNAME = "{dq(VERSIONNAME)}"\n'
            f'GITTAG = "{dq(GITTAG)}"\n'
            f'CONDAENVIRONMENTNAME = "{dq(CONDAENVIRONMENTNAME)}"\n'
            f'PYTHONVERSION = "{dq(PYTHONVERSION)}"\n'
            f'CONDAENVIRONMENTFILENAME = "{dq(CONDAENVIRONMENTFILENAME)}"\n',
            encoding="utf-8",
        )
        print(f"Wrote {sysinfo_path}")
    
    # ----- PyInstaller paths -----
    base_build = project_root / ".build" / "pyinstaller"
    workpath   = base_build / "work"
    distpath   = base_build / "dist"
    specpath   = base_build
    builds_dir = base_build / "builds"

    if args.purge:
        shutil.rmtree(workpath, ignore_errors=True)
        shutil.rmtree(distpath, ignore_errors=True)

    base_build.mkdir(parents=True, exist_ok=True)
    builds_dir.mkdir(parents=True, exist_ok=True)

    mode_flag = "--onefile" if args.onefile else "--onedir"
    datasep = ";" if os.name == "nt" else ":"

    # ----- Data mapping (kept inside app for base_path to resolve) -----
    data_map = [
        (project_root / "reports" / "templates",       "reports/templates"),
        (project_root / "reports" / "generated",       "reports/generated"),
        (project_root / "sqlite" / "bmcdatabase.db",   "sqlite/bmcdatabase.db"),
        (project_root / "ffmpeg",                      "ffmpeg"),
        (project_root / "software_requerido",          "software_requerido"),
        (project_root / "ayuda",                       "ayuda"),
        (project_root / "video",                       "video"),
        (project_root / "pacientes",                   "pacientes"),
        (project_root / "_DATA_",                      "datos"),          
        (project_root / "templates",                   "templates"),
        (project_root / "uis", "uis"),
        (project_root / "resources" / "icons",         "resources/icons"),    
        (project_root / "resources",                   "resources"),
    ]

    args_pi = [
        "--noconfirm", "--clean",
        f"--name={args.name}",
        f"--workpath={workpath}",
        f"--distpath={distpath}",
        f"--specpath={specpath}",
        mode_flag,
        str(entry_script),
    ]
    for src, dest in data_map:
        if not src.exists():
            print(f"[warn] missing data: {src}")
            continue
        args_pi.insert(-1, f"--add-data={src}{datasep}{dest}")
        
        
    icon_path = project_root / "resources" / "icons" / "B_trans.png"
    if icon_path.exists():
        args_pi.insert(-1, f"--icon={icon_path}")
    else:
        print(f"[warn] icon not found: {icon_path}")


    print("\nRunning PyInstaller with:\n  " + "\n  ".join(args_pi))
    pyinstaller_run(args_pi)

    # ----- Archive this build (FLAT) -----
    tag = f"{args.name}-{BUILDNUMBER}"
    archived_at = archive_latest(distpath, builds_dir, tag, app_name=args.name)
    if not archived_at:
        print("[warn] nothing archived (dist empty?)")
        return

    # ----- EXTRA CONTENT in archive root -----
    copy_contents(project_root / "_DATA_", archived_at / "datos")   # _DATA_/ → datos/
    copy_contents(project_root / "video",   archived_at / "videos") # video/  → videos/

    # ----- Optional Zip -----
    zip_path = ""
    if args.do_zip:
        zip_base = builds_dir / tag
        zip_path = shutil.make_archive(str(zip_base), "zip", root_dir=builds_dir, base_dir=tag)
        print(f"Zipped archive: {zip_path}")

    # ----- Purge older archives (dirs and zips), keep latest N -----
    purge_old_archives(builds_dir, keep=max(1, int(args.keep)))

    print("\n✅ Done."
          f"\n   Dist:     {distpath.resolve()}"
          f"\n   Archive:  {archived_at.resolve()}"
          f"\n   Zip:      {zip_path or '(skipped)'}"
          f"\n   Builds:   {builds_dir.resolve()} (keeping {args.keep})")

if __name__ == "__main__":
    main()
