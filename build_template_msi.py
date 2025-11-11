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

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
APP_NAME = "MVC Calculator"
ICON_PATH = Path(base_path("resources/icons", "app.ico")).resolve()
PYI_BUILD_DIR = Path.home() / "Documents" / ".builds" / APP_NAME.lower() / "pyinstaller"
DIST_DIR = PYI_BUILD_DIR / "dist" / APP_NAME
MSI_ROOT = Path.home() / "Documents" / ".builds" / APP_NAME.lower() / "msi"
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

print(f"[OK] Using build number: {BUILDNUMBER}")

# ------------------------------------------------------------------------------
# Locate the EXE
# ------------------------------------------------------------------------------
EXE_PATH = DIST_DIR / f"{APP_NAME}.exe"
if not EXE_PATH.exists():
    print(f"[ERROR] Missing EXE at: {EXE_PATH}")
    sys.exit(1)

# ------------------------------------------------------------------------------
# Generate .wxs file for WiX
# ------------------------------------------------------------------------------
WXS_PATH = MSI_ROOT / f"{APP_NAME}.wxs"
wxs_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*" Name="{APP_NAME}" Language="1033" Version="{BUILDNUMBER}"
           Manufacturer="Moviolabs" UpgradeCode="9a1f9b7a-d0b3-4b8a-aad9-2d2b06c9a111">
    <Package InstallerVersion="500" Compressed="yes" InstallScope="perMachine" />

    <MediaTemplate />
    <Icon Id="AppIcon.ico" SourceFile="{ICON_PATH}" />
    <Property Id="ARPPRODUCTICON" Value="AppIcon.ico" />

    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFilesFolder">
        <Directory Id="INSTALLFOLDER" Name="{APP_NAME}" />
      </Directory>
    </Directory>

    <DirectoryRef Id="INSTALLFOLDER">
      <Component Id="MainExecutable" Guid="*" >
        <File Id="AppEXE" Source="{EXE_PATH}" KeyPath="yes" />
        <Shortcut Id="DesktopShortcut" Directory="DesktopFolder"
                  Name="{APP_NAME}" WorkingDirectory="INSTALLFOLDER"
                  Icon="AppIcon.ico" IconIndex="0"
                  Advertise="no" />
        <Shortcut Id="StartMenuShortcut" Directory="ProgramMenuFolder"
                  Name="{APP_NAME}" WorkingDirectory="INSTALLFOLDER"
                  Icon="AppIcon.ico" IconIndex="0"
                  Advertise="no" />
        <RemoveFile Id="RemoveShortcutDesktop" Name="{APP_NAME}.lnk"
                    On="uninstall" Directory="DesktopFolder" />
        <RemoveFile Id="RemoveShortcutMenu" Name="{APP_NAME}.lnk"
                    On="uninstall" Directory="ProgramMenuFolder" />
      </Component>
    </DirectoryRef>

    <Feature Id="DefaultFeature" Level="1">
      <ComponentRef Id="MainExecutable" />
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
    subprocess.run(["candle", f"{APP_NAME}.wxs"], check=True)
    msi_path = MSI_BUILDS / f"{APP_NAME}-{BUILDNUMBER}.msi"
    subprocess.run([
        "light", "-ext", "WixUIExtension",
        f"{APP_NAME}.wixobj", "-o", str(msi_path)
    ], check=True)
    print(f"\n✅ MSI created: {msi_path}")
except subprocess.CalledProcessError as e:
    print(f"[ERROR] WiX build failed: {e}")
    sys.exit(1)

# ------------------------------------------------------------------------------
# Create portable ZIP (from dist folder)
# ------------------------------------------------------------------------------
ZIP_PATH = MSI_BUILDS / f"{APP_NAME}-{BUILDNUMBER}-portable.zip"
if DIST_DIR.exists():
    print(f"[OK] Creating portable ZIP: {ZIP_PATH.name}")
    shutil.make_archive(str(ZIP_PATH).replace(".zip", ""), "zip", root_dir=DIST_DIR)
    print(f"✅ Portable ZIP created at: {ZIP_PATH}")
else:
    print("[WARN] No dist folder found to zip.")

# ------------------------------------------------------------------------------
# Purge old builds (keep 3 latest)
# ------------------------------------------------------------------------------
def purge_old_builds(build_dir: Path, keep: int = 3):
    builds = sorted(build_dir.glob(f"{APP_NAME}-*"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in builds[keep:]:
        if old.is_file():
            old.unlink()
            print(f"[purged] {old}")

purge_old_builds(MSI_BUILDS, keep=3)
print("\n🎉 All done — MSI + ZIP ready!")
