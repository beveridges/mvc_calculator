#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
MyApp Template — MSI + Portable ZIP Builder
--------------------------------------------------------------------------------
✓ Builds MSI installer via WiX Toolset
✓ Archives .msi and .zip to Documents/.builds/myapptemplate/msi/builds/
✓ Uses same versioning as build_template.py
================================================================================
"""

import os, sys, shutil, subprocess
from pathlib import Path
from datetime import datetime
from utilities.path_utils import base_path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
APP_DISPLAY_NAME = "MVC Calculator"
APP_BASENAME = "MVC_Calculator"
APP_KEY = "mvc_calculator"
ICON_PATH = Path(base_path("resources/icons", "icn_emg.ico")).resolve()
PYI_BUILD_DIR = Path.home() / "Documents" / ".builds" / APP_KEY / "pyinstaller"
ARCHIVE_BUILDS_DIR = PYI_BUILD_DIR / "builds"
MSI_ROOT = Path.home() / "Documents" / ".builds" / APP_KEY / "msi"
MSI_BUILDS = MSI_ROOT / "builds"
MSI_ROOT.mkdir(parents=True, exist_ok=True)
MSI_BUILDS.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------------------
# Versioning — read from utilities/version_info.py
# ------------------------------------------------------------------------------
VERSION_INFO = Path(base_path("utilities", "version_info.py"))
if not VERSION_INFO.exists():
    print("[ERROR] version_info.py not found. Run build_template.py first.")
    sys.exit(1)

BUILDNUMBER = "unknown"
for line in VERSION_INFO.read_text(encoding="utf-8").splitlines():
    if line.startswith("BUILDNUMBER"):
        BUILDNUMBER = line.split("=")[1].strip().strip('"')
        break

def wix_version_from_build(build: str) -> str:
    numeric_parts = []
    for part in build.replace("-", ".").split("."):
        if part.isdigit():
            numeric_parts.append(int(part))
        else:
            break
    while len(numeric_parts) < 4:
        numeric_parts.append(0)
    return ".".join(str(min(65534, p)) for p in numeric_parts[:4])

WIX_VERSION = wix_version_from_build(BUILDNUMBER)

print(f"[OK] Using build number: {BUILDNUMBER}")

# ------------------------------------------------------------------------------
# Determine latest archived build folder
# ------------------------------------------------------------------------------
def find_latest_build_dir(builds_root: Path) -> Path:
    if not builds_root.exists():
        print(f"[ERROR] Build archives directory missing: {builds_root}")
        sys.exit(1)
    candidates = [p for p in builds_root.iterdir() if p.is_dir()]
    if not candidates:
        print(f"[ERROR] No archived builds found in: {builds_root}")
        sys.exit(1)
    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    print(f"[OK] Using archived build: {latest.name}")
    return latest

LATEST_BUILD_DIR = find_latest_build_dir(ARCHIVE_BUILDS_DIR)

# ------------------------------------------------------------------------------
# Locate the EXE
# ------------------------------------------------------------------------------
EXE_PATH = LATEST_BUILD_DIR / f"{APP_BASENAME}.exe"
if not EXE_PATH.exists():
    exe_candidates = sorted(LATEST_BUILD_DIR.glob("*.exe"))
    if exe_candidates:
        EXE_PATH = exe_candidates[0]
        print(f"[warn] Expected EXE name not found; using {EXE_PATH.name}")
    else:
        print(f"[ERROR] Missing EXE in archived build: {LATEST_BUILD_DIR}")
        sys.exit(1)

if not EXE_PATH.exists():
    print(f"[ERROR] Missing EXE at: {EXE_PATH}")
    sys.exit(1)

# ------------------------------------------------------------------------------
# Generate .wxs file for WiX
# ------------------------------------------------------------------------------
WXS_PATH = MSI_ROOT / f"{APP_BASENAME}.wxs"
wxs_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*" Name="{APP_DISPLAY_NAME}" Language="1033" Version="{WIX_VERSION}"
           Manufacturer="Moviolabs" UpgradeCode="9a1f9b7a-d0b3-4b8a-aad9-2d2b06c9a111">
    <Package InstallerVersion="500" Compressed="yes" InstallScope="perMachine" />

    <MediaTemplate />
    <Icon Id="AppIcon.ico" SourceFile="{ICON_PATH}" />
    <Property Id="ARPPRODUCTICON" Value="AppIcon.ico" />

    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFilesFolder">
        <Directory Id="INSTALLFOLDER" Name="{APP_DISPLAY_NAME}" />
      </Directory>
      <Directory Id="ProgramMenuFolder">
        <Directory Id="ProgramMenuDir" Name="{APP_DISPLAY_NAME}" />
      </Directory>
      <Directory Id="DesktopFolder" />
    </Directory>

    <DirectoryRef Id="INSTALLFOLDER">
      <Component Id="MainExecutable" Guid="*" >
        <File Id="AppEXE" Source="{EXE_PATH}" KeyPath="yes" />
      </Component>
    </DirectoryRef>

    <DirectoryRef Id="DesktopFolder">
      <Component Id="DesktopShortcutComponent" Guid="*">
        <Shortcut Id="DesktopShortcut" Directory="DesktopFolder"
                  Name="{APP_DISPLAY_NAME}" WorkingDirectory="INSTALLFOLDER"
                  Icon="AppIcon.ico" IconIndex="0"
                  Advertise="no" />
        <RemoveFile Id="RemoveShortcutDesktop" Name="{APP_DISPLAY_NAME}.lnk"
                    On="uninstall" Directory="DesktopFolder" />
        <RegistryValue Root="HKCU" Key="Software\\Moviolabs\\{APP_BASENAME}" Name="DesktopShortcut" Type="integer" Value="1" KeyPath="yes" />
      </Component>
    </DirectoryRef>

    <DirectoryRef Id="ProgramMenuDir">
      <Component Id="ProgramMenuShortcutComponent" Guid="*">
        <Shortcut Id="StartMenuShortcut" Directory="ProgramMenuDir"
                  Name="{APP_DISPLAY_NAME}" WorkingDirectory="INSTALLFOLDER"
                  Icon="AppIcon.ico" IconIndex="0"
                  Advertise="no" />
        <RemoveFile Id="RemoveShortcutMenu" Name="{APP_DISPLAY_NAME}.lnk"
                    On="uninstall" Directory="ProgramMenuDir" />
        <RegistryValue Root="HKCU" Key="Software\\Moviolabs\\{APP_BASENAME}" Name="StartMenuShortcut" Type="integer" Value="1" KeyPath="yes" />
      </Component>
      <Component Id="ProgramMenuCleanupComponent" Guid="*">
        <RemoveFolder Id="ProgramMenuRemove" Directory="ProgramMenuDir" On="uninstall" />
        <RegistryValue Root="HKCU" Key="Software\\Moviolabs\\{APP_BASENAME}" Name="ProgramMenuCleanup" Type="integer" Value="1" KeyPath="yes" />
      </Component>
    </DirectoryRef>

    <Feature Id="DefaultFeature" Level="1">
      <ComponentRef Id="MainExecutable" />
      <ComponentRef Id="DesktopShortcutComponent" />
      <ComponentRef Id="ProgramMenuShortcutComponent" />
      <ComponentRef Id="ProgramMenuCleanupComponent" />
    </Feature>

    <UIRef Id="WixUI_InstallDir" />
    <Property Id="WIXUI_INSTALLDIR" Value="INSTALLFOLDER" />
  </Product>
</Wix>
"""
WXS_PATH.write_text(wxs_content, encoding="utf-8")
print(f"[OK] WXS file created at: {WXS_PATH}")

# ------------------------------------------------------------------------------
# Run WiX (candle + light)
# ------------------------------------------------------------------------------
os.chdir(MSI_ROOT)
try:
    subprocess.run(["candle", f"{APP_BASENAME}.wxs"], check=True)
    msi_path = MSI_BUILDS / f"{APP_BASENAME}-{BUILDNUMBER}.msi"
    cab_path = MSI_BUILDS / "cab1.cab"
    if cab_path.exists():
        try:
            cab_path.unlink()
        except PermissionError:
            os.chmod(cab_path, 0o666)
            cab_path.unlink(missing_ok=True)
    if msi_path.exists():
        try:
            msi_path.unlink()
        except PermissionError:
            os.chmod(msi_path, 0o666)
            msi_path.unlink(missing_ok=True)
    subprocess.run([
        "light", "-ext", "WixUIExtension",
        f"{APP_BASENAME}.wixobj", "-o", str(msi_path)
    ], check=True)
    print(f"\n✅ MSI created: {msi_path}")
except subprocess.CalledProcessError as e:
    print(f"[ERROR] WiX build failed: {e}")
    sys.exit(1)

# ------------------------------------------------------------------------------
# Create portable ZIP (from dist folder)
# ------------------------------------------------------------------------------
ZIP_PATH = MSI_BUILDS / f"{APP_BASENAME}-{BUILDNUMBER}-portable.zip"
zip_base = ZIP_PATH.with_suffix("")
if LATEST_BUILD_DIR.exists():
    print(f"[OK] Creating portable ZIP from {LATEST_BUILD_DIR.name}: {ZIP_PATH.name}")
    shutil.make_archive(str(zip_base), "zip", root_dir=LATEST_BUILD_DIR.parent, base_dir=LATEST_BUILD_DIR.name)
    print(f"✅ Portable ZIP created at: {ZIP_PATH}")
else:
    print("[WARN] No archived build folder found to zip.")

# ------------------------------------------------------------------------------
# Purge old builds (keep 3 latest)
# ------------------------------------------------------------------------------
def purge_old_builds(build_dir: Path, keep: int = 3):
    builds = sorted(build_dir.glob(f"{APP_BASENAME}-*"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in builds[keep:]:
        if old.is_file():
            old.unlink()
            print(f"[purged] {old}")

purge_old_builds(MSI_BUILDS, keep=3)
print("\n🎉 All done — MSI + ZIP ready!")
