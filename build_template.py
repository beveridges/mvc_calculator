#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MVC_Calculator — Safe, Non-Spawning PyInstaller Build Template
--------------------------------------------------------------
- Hard recursion guard (no multiple spawn)
- UPX disabled by default
- Versioning: YY.MM-<channel>.<seq>
- Writes utilities/version_info.py
- Builds to ~/Documents/.builds/mvc_calculator/pyinstaller/{work,dist,builds}
- Archives latest build to .../builds/MVC_Calculator-<BUILDNUMBER> and (optionally) zips
"""

from __future__ import annotations
import argparse, os, re, shutil, subprocess, sys, signal, atexit
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# ============================================================
# 0) RECURSION / MULTI-SPAWN GUARD  (persistent + environment)
# ============================================================
from pathlib import Path
LOCK_FILE = Path.home() / ".ml_build_active.lock"

# Refuse to rebuild from a frozen EXE
if getattr(sys, "frozen", False):
    print("[SAFEGUARD] Refusing to rebuild from frozen EXE.")
    sys.exit(0)

# If another build process already holds the lock, abort immediately
def release_lock() -> None:
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
            print(f"[SAFEGUARD] Build lock released: {LOCK_FILE}")
    except Exception as e:
        print(f"[warn] Could not remove lock file: {e}")


if LOCK_FILE.exists():
    print("[SAFEGUARD] Another build process is already running.")
    sys.exit(0)

try:
    # Create lock file and environment marker
    LOCK_FILE.touch(exist_ok=True)
    os.environ["ML_BUILD_ACTIVE"] = "1"
    print(f"[SAFEGUARD] Build lock acquired: {LOCK_FILE}")
except Exception as e:
    print(f"[warn] Unable to create lock file: {e}")

atexit.register(release_lock)


def _sigint_handler(signum, frame):
    print("\n[warn] Build interrupted by user (Ctrl+C).")
    release_lock()
    sys.exit(130)


signal.signal(signal.SIGINT, _sigint_handler)


# ============================================================
# 1) Optional Tee logger (simple, reliable)
# ============================================================
class Tee:
    def __init__(self, log_path: Path):
        self.terminal_out = sys.__stdout__
        self.terminal_err = sys.__stderr__
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log = open(log_path, "w", encoding="utf-8")
    def write(self, message: str):
        self.terminal_out.write(message)
        self.log.write(message)
    def flush(self):
        self.terminal_out.flush()
        self.log.flush()

timestamp = datetime.now().strftime("%y.%m-%H%M%S")
project_root = Path(__file__).resolve().parent
# project_root = Path(__file__).resolve().parent.parent
logs_dir = project_root / ".build_logs"
log_file = logs_dir / f"build_{timestamp}.log"
sys.stdout = sys.stderr = Tee(log_file)
print(f"[log] Saving build output to: {log_file}\n")

# ============================================================
# 2) Environment: UPX off
# ============================================================
os.environ["PYINSTALLER_NOUPX"] = "1"
os.environ["UPX"] = "disabled"
print("[info] UPX disabled by default.\n")

try:
    from PyInstaller.__main__ import run as pyinstaller_run
except ImportError:
    print("PyInstaller not installed. Run:  pip install pyinstaller")
    sys.exit(1)

# ============================================================
# 3) Git helpers (from your working templates)
# ============================================================
def _run_git(args: list[str]) -> Optional[str]:
    try:
        return subprocess.run(["git"] + args, check=True, capture_output=True, text=True).stdout.strip()
    except Exception:
        return None

def in_git_repo() -> bool:
    return _run_git(["rev-parse", "--is-inside-work-tree"]) == "true"

def git_rev_head(short: int = 7) -> str:
    return _run_git(["rev-parse", f"--short={short}", "HEAD"]) or "unknown"

def git_latest_tag() -> str:
    return _run_git(["describe", "--tags", "--abbrev=0"]) or ""

# ============================================================
# 4) Version + archive helpers (from your working templates)
# ============================================================
def read_previous_from_file(repo_root: Path) -> Tuple[Optional[str], Optional[str]]:
    vi = repo_root / "utilities" / "version_info.py"
    if not vi.exists():
        return None, None
    try:
        text = vi.read_text(encoding="utf-8", errors="ignore")
        m_build = re.search(r'^\s*BUILDNUMBER\s*=\s*"([^"]+)"', text, re.M)
        m_ver   = re.search(r'^\s*VERSIONNUMBER\s*=\s*"([^"]+)"', text, re.M)
        return (m_build.group(1) if m_build else None,
                m_ver.group(1) if m_ver else None)
    except Exception:
        return None, None

def increment_last_segment(prev_build: str) -> str:
    parts = prev_build.split(".")
    if not parts:
        return "00"
    last = parts[-1]
    return f"{int(last)+1:0{max(2,len(last))}d}" if last.isdigit() else "00"

def archive_latest(distpath: Path, builds_dir: Path, tag: str, app_name: str | None = None) -> Optional[Path]:
    """Copy latest dist output to builds/<tag>/ (keeps onedir layout)."""
    if not distpath.exists():
        print(f"[error] dist path not found: {distpath}")
        return None
    candidates = [p for p in distpath.iterdir() if p.is_dir() or p.suffix.lower() in (".exe", ".msi")]
    if not candidates:
        print(f"[error] dist path is empty: {distpath}")
        return None
    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    dest_root = builds_dir / tag
    shutil.rmtree(dest_root, ignore_errors=True)
    dest_root.mkdir(parents=True, exist_ok=True)
    try:
        if latest.is_dir():
            shutil.copytree(latest, dest_root, dirs_exist_ok=True)
        else:
            shutil.copy2(latest, dest_root / latest.name)
        return dest_root
    except Exception as e:
        print(f"[warn] archive failed: {e}")
        return None

def purge_old_archives(builds_dir: Path, keep: int = 3):
    if not builds_dir.exists():
        return
    items = sorted(builds_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in items[keep:]:
        try:
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink(missing_ok=True)
            print(f"[purged] {p}")
        except Exception as e:
            print(f"[warn] purge failed for {p}: {e}")

def copy_tree_to_dest(src: Path, dest_root: Path, dest_rel: str):
    dest = dest_root / Path(dest_rel)
    if not src.exists():
        print(f"[skip] missing: {src}")
        return
    if src.is_file():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(src, dest)

# ============================================================
# 5) Main
# ============================================================
def main():
    ap = argparse.ArgumentParser(description="MVC_Calculator build")
    ap.add_argument("--onefile", action="store_true", help="Build single-file exe")
    ap.add_argument("--onedir", action="store_true", help="Build folder (default)")
    ap.add_argument("--purge", action="store_true", help="Remove previous dist/work before build")
    ap.add_argument("--keep", type=int, default=3, help="Number of archived builds to keep")
    ap.add_argument("--channel", default="alpha.01", help="Version channel (e.g., alpha.01)")
    ap.add_argument("--zip", dest="do_zip", action="store_true", help="Zip the archived build")
    ap.add_argument("--no-write-sysinfo", action="store_true", help="Skip writing version_info.py")
    ap.add_argument("--name", default="MVC_Calculator", help="Application name")
    ap.add_argument("--entry", default="main.py", help="Entry script path")
    args = ap.parse_args()

    entry_script = project_root / args.entry
    if not entry_script.exists():
        print(f"[error] Entry script not found: {entry_script}")
        sys.exit(2)

    # ---------- Versioning ----------
    base = datetime.now().strftime("%y.%m")
    VERSIONNUMBER = f"{base}-{args.channel}"
    prev_build, prev_version = read_previous_from_file(project_root)
    SEQ = increment_last_segment(prev_build) if prev_build and prev_version == VERSIONNUMBER else "00"
    BUILDNUMBER = f"{VERSIONNUMBER}.{SEQ}"
    GITREVHEAD = git_rev_head() if in_git_repo() else "unknown"
    GITTAG = git_latest_tag() if in_git_repo() else ""
    FRIENDLYVERSIONNAME = args.name.replace("_", " ")
    VERSIONNAME = args.name.lower().replace(" ", "")
    CONDAENVIRONMENTNAME = os.environ.get("CONDA_DEFAULT_ENV", VERSIONNAME)
    PYTHONVERSION = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    CONDAENVIRONMENTFILENAME = "environment.yml"
    RELEASENAME = GITTAG or "UNRELEASED"

    print(f"GITREVHEAD    = {GITREVHEAD}")
    print(f"GITTAG        = {GITTAG}")
    print(f"VERSIONNUMBER = {VERSIONNUMBER}")
    print(f"BUILDNUMBER   = {BUILDNUMBER}\n")

    # ---------- Write utilities/version_info.py ----------
    if not args.no_write_sysinfo:
        sysinfo_dir = project_root / "utilities"
        sysinfo_dir.mkdir(parents=True, exist_ok=True)
        sysinfo_path = sysinfo_dir / "version_info.py"
        sysinfo_txt = (
            "# Auto-generated by build_template.py — DO NOT EDIT BY HAND\n"
            f'GITREVHEAD = "{GITREVHEAD}"\n'
            f'BUILDNUMBER = "{BUILDNUMBER}"\n'
            f'VERSIONNUMBER = "{VERSIONNUMBER}"\n'
            f'FRIENDLYVERSIONNAME = "{FRIENDLYVERSIONNAME}"\n'
            f'VERSIONNAME = "{VERSIONNAME}"\n'
            f'GITTAG = "{GITTAG}"\n'
            f'CONDAENVIRONMENTNAME = "{CONDAENVIRONMENTNAME}"\n'
            f'PYTHONVERSION = "{PYTHONVERSION}"\n'
            f'CONDAENVIRONMENTFILENAME = "{CONDAENVIRONMENTFILENAME}"\n'
            f'RELEASENAME = "{RELEASENAME}"\n'
        )
        sysinfo_path.write_text(sysinfo_txt, encoding="utf-8")
        print(f"[ok] wrote {sysinfo_path}")
        
        # Update docs version and rebuild docs if they exist
        try:
            version_script = project_root / "docs_site" / "scripts" / "update_version_block.py"
            if version_script.exists():
                print("[info] Updating docs version...")
                subprocess.run([sys.executable, str(version_script)], check=False, cwd=str(project_root))
            
            # Try to rebuild docs if mkdocs is available
            docs_dir = project_root / "docs_site"
            docs_site_index = docs_dir / "site" / "index.html"
            if docs_dir.exists():
                try:
                    result = subprocess.run(
                        ["mkdocs", "build"],
                        cwd=str(docs_dir),
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    if result.returncode == 0:
                        if docs_site_index.exists():
                            print("[ok] Docs rebuilt with updated version")
                        else:
                            print("[warn] mkdocs build completed but index.html not found")
                    else:
                        print(f"[warn] Docs build failed: {result.stderr[:200]}")
                        print("[info] You may need to run 'mkdocs build' manually in docs_site/")
                except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                    print(f"[warn] mkdocs not available: {e}")
                    print("[info] Install mkdocs and run 'mkdocs build' in docs_site/ to include help files")
                # Check if docs exist even if build wasn't attempted
                if not docs_site_index.exists():
                    print("[warn] docs_site/site/index.html not found - help files will not be available in EXE")
        except Exception as e:
            print(f"[warn] Could not update docs version (non-critical): {e}")

    # ---------- PyInstaller dirs (external to project to avoid recursion) ----------
    base_build = Path.home() / "Documents" / ".builds" / "mvc_calculator" / "pyinstaller"
    workpath   = base_build / "work"
    distpath   = base_build / "dist"
    specpath   = base_build
    builds_dir = base_build / "builds"

    if args.purge:
        print("[purge] removing previous dist/work")
        shutil.rmtree(workpath, ignore_errors=True)
        shutil.rmtree(distpath, ignore_errors=True)
    for p in (specpath, workpath, distpath, builds_dir):
        p.mkdir(parents=True, exist_ok=True)
        print(f"[ok] ensured: {p}")

    # ---------- PyInstaller args ----------
    mode_flag = "--onefile" if args.onefile else "--onedir"
    datasep = ";" if os.name == "nt" else ":"
    args_pi = [
        "--noconfirm", "--clean", "--log-level=INFO", "--console",
        f"--name={args.name}",
        f"--workpath={workpath}",
        f"--distpath={distpath}",
        f"--specpath={specpath}",
        f"--paths={project_root}",
    ]
    
    # Fix missing NumPy and SciPy modules in runtime - collect ALL components
    # CRITICAL: --hidden-import alone is NOT enough! Scipy has compiled C extensions
    # that MUST be collected with --collect-all, --collect-binaries, etc.
    
    # NumPy must be collected first since SciPy depends on it
    args_pi += [
        "--collect-all", "numpy",
        "--collect-submodules", "numpy",
        "--collect-binaries", "numpy",
        "--collect-data", "numpy",
        "--hidden-import=numpy",
    ]
    
    # SciPy collection - includes compiled extensions needed for .mat file import
    args_pi += [
        "--collect-all", "scipy",
        "--collect-submodules", "scipy",
        "--collect-binaries", "scipy",
        "--collect-data", "scipy",
        "--hidden-import=scipy",
        "--hidden-import=scipy.io",
        "--hidden-import=scipy.io.matlab",
        "--hidden-import=scipy.io.matlab.mio",
        "--hidden-import=scipy.io.matlab.mio5",
        "--hidden-import=scipy.io.matlab.mio5_params",
        "--hidden-import=scipy.io.matlab.mio5_utils",
        "--hidden-import=scipy.signal",  # Used in processors.py
        "--hidden-import=scipy.sparse",
        "--hidden-import=scipy.spatial",
        "--hidden-import=scipy.stats",
    ]

    # Exclude unused PyQt5 webengine modules to prevent build errors
    args_pi += [
        "--exclude-module=PyQt5.QtWebEngine",
        "--exclude-module=PyQt5.QtWebEngineCore",
        "--exclude-module=PyQt5.QtWebEngineWidgets",
        "--collect-all", "PyQt5",
        "--collect-submodules", "PyQt5",
        "--collect-binaries", "PyQt5",
        "--collect-data", "PyQt5",
    ]

    # Data/resource folders typical for your app
    data_map = [
        (project_root / "data", "data"),
        (project_root / "config", "config"),
        (project_root / "dialogs", "dialogs"),
        (project_root / "processors", "processors"),
        (project_root / "sbui", "sbui"),
        (project_root / "uis", "uis"),
        (project_root / "utilities", "utilities"),
        (project_root / "resources", "resources"),
        (project_root / "resources" / "icons", "resources/icons"),
        (project_root / "docs_site" / "site", "docs_site/site"),
        (project_root / "sqlite", "sqlite"),
        (project_root / "reports", "reports"),
        (project_root / "_DATA_", "datos"),
        (project_root / "video", "video"),
        (project_root / "pacientes", "pacientes"),
        (project_root / "ffmpeg", "ffmpeg"),
        (project_root / "software_requerido", "software_requerido"),
    ]
    
    args_pi += [
        "--exclude-module=build_template",
        "--exclude-module=build.build_template",
        "--exclude-module=build",
    ]

    print("\n[scan] include resources:")
    for src, dest in data_map:
        print(f"  {src} → {dest} (exists={src.exists()})")
        if src.exists():
            args_pi.append(f"--add-data={str(src)}{datasep}{dest}")

    # Fixed icon path (yours). If not found, fall back to project resources.
    fixed_icon = Path(r"C:\Users\Scott\Dropbox\__PROJECTS__\MVC_CALCULATOR\resources\icons\icn_emg.ico")
    icon_path = fixed_icon if fixed_icon.exists() else (project_root / "resources" / "icons" / "icn_emg.ico")
    if icon_path.exists():
        args_pi.append(f"--icon={icon_path}")
        print(f"[ok] using icon: {icon_path}")
    else:
        print(f"[warn] icon missing at: {fixed_icon}")

    args_pi += [mode_flag, str(entry_script)]

    print("\n[run] PyInstaller args:")
    for a in args_pi:
        print(" ", a)
    try:
        pyinstaller_run(args_pi)
    except SystemExit as se:
        code = int(getattr(se, "code", 0) or 0)
        if code != 0:
            print(f"[error] PyInstaller exited with {code}")
            sys.exit(code)

    if not distpath.exists() or not any(distpath.iterdir()):
        print(f"[error] dist folder empty after build: {distpath}")
        sys.exit(3)

    # ---------- Archive ----------
    tag = f"{args.name}-{BUILDNUMBER}"
    archived_at = archive_latest(distpath, builds_dir, tag, app_name=args.name)
    if not archived_at:
        print("[error] archive step failed.")
        sys.exit(4)

    # Companion copies (ensure they’re outside the EXE too)
    for src, dest_rel in data_map:
        if src.exists():
            copy_tree_to_dest(src, archived_at, dest_rel)

    # Optional zip
    if args.do_zip:
        zip_path = shutil.make_archive(str(builds_dir / tag), "zip", root_dir=builds_dir, base_dir=tag)
        print(f"[ok] zipped archive: {zip_path}")

    purge_old_archives(builds_dir, keep=max(1, args.keep))

    print("\n✅ Done.")
    print(f"   Dist:     {distpath.resolve()}")
    print(f"   Archive:  {(builds_dir / tag).resolve()}")
    print(f"   Builds:   {builds_dir.resolve()}")
    print(f"[time] {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"[py]   {sys.executable}\n")
    
# ============================================================
# 6) Entry
# ============================================================
if __name__ == "__main__":
    # Secondary guard (refuse to build from a frozen EXE)
    if getattr(sys, "frozen", False):
        print("[SAFEGUARD] Refusing to rebuild from frozen EXE.")
        sys.exit(0)
    try:
        main()
    except KeyboardInterrupt:
        print("\n[warn] Build aborted by user.")
        raise
    finally:
        release_lock()
