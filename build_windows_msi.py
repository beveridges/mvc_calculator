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
from collections import defaultdict
from pathlib import Path
from datetime import datetime
from utilities.path_utils import base_path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

OA_MODE = "--oa" in sys.argv or "-oa" in sys.argv

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
APP_DISPLAY_NAME = "MVC Calculator"
APP_BASENAME = "MVC_Calculator"
APP_KEY = "mvc_calculator"
ICON_PATH = Path(base_path("resources/icons", "icn_emg.ico")).resolve()
BANNER_IMAGE_PATH = Path(base_path("resources/icons", "MSI_INSTALLER_BANNER.png")).resolve()
DIALOG_IMAGE_PATH = Path(base_path("resources/icons", "MSI_INSTALLER_DIALOG_IMAGE_LARGE_B_W.png")).resolve()
PYI_BUILD_DIR = Path.home() / "Documents" / ".builds" / APP_KEY / "pyinstaller"
ARCHIVE_BUILDS_DIR = PYI_BUILD_DIR / "builds"
BUILD_BASE = Path.home() / "Documents" / ".builds" / APP_KEY

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

# Create versioned directory structure
VERSION_DIR = BUILD_BASE / (f"MVC_Calculator-oa-{BUILDNUMBER}" if OA_MODE else f"MVC_Calculator-{BUILDNUMBER}")
BUILDFILES_DIR = VERSION_DIR / "buildfiles"
VERSION_DIR.mkdir(parents=True, exist_ok=True)
BUILDFILES_DIR.mkdir(parents=True, exist_ok=True)

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

MSI_BASENAME = f"{APP_BASENAME}-oa-{BUILDNUMBER}" if OA_MODE else f"{APP_BASENAME}-{BUILDNUMBER}"
print(f"[OK] Using build number: {BUILDNUMBER}" + (" (OA mode)" if OA_MODE else ""))

# ------------------------------------------------------------------------------
# Determine latest archived build folder
# ------------------------------------------------------------------------------
def find_latest_build_dir(builds_root: Path) -> Path:
    print(f"[DEBUG] Looking for builds in: {builds_root}")
    print(f"[DEBUG] Path exists: {builds_root.exists()}")
    print(f"[DEBUG] Path is absolute: {builds_root.is_absolute()}")
    
    if not builds_root.exists():
        print(f"[ERROR] Build archives directory missing: {builds_root}")
        print(f"[DEBUG] Parent directory exists: {builds_root.parent.exists()}")
        if builds_root.parent.exists():
            print(f"[DEBUG] Parent directory contents:")
            try:
                for item in builds_root.parent.iterdir():
                    print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")
            except Exception as e:
                print(f"  [ERROR] Could not list parent directory: {e}")
        sys.exit(1)
    
    print(f"[DEBUG] Scanning for build directories...")
    candidates = [p for p in builds_root.iterdir() if p.is_dir()]
    print(f"[DEBUG] Found {len(candidates)} candidate directories")
    
    if candidates:
        print(f"[DEBUG] Candidate directories:")
        for cand in sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[:10]:
            mtime = datetime.fromtimestamp(cand.stat().st_mtime)
            print(f"  - {cand.name} (modified: {mtime})")
    
    if not candidates:
        print(f"[ERROR] No archived builds found in: {builds_root}")
        print(f"[DEBUG] Directory contents:")
        try:
            all_items = list(builds_root.iterdir())
            if all_items:
                for item in all_items:
                    print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")
            else:
                print(f"  (directory is empty)")
        except Exception as e:
            print(f"  [ERROR] Could not list directory: {e}")
        print(f"[INFO] You may need to run build_windows_portable.py first to create a PyInstaller build")
        sys.exit(1)
    
    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    mtime = datetime.fromtimestamp(latest.stat().st_mtime)
    print(f"[OK] Using archived build: {latest.name} (modified: {mtime})")
    return latest

if OA_MODE:
    OA_BUILD_DIR = ARCHIVE_BUILDS_DIR / f"MVC_Calculator-oa-{BUILDNUMBER}"
    if not OA_BUILD_DIR.exists():
        print(f"[ERROR] OA build not found: {OA_BUILD_DIR}")
        print(f"[INFO] Run build_windows_portable.py --onedir --oa first")
        sys.exit(1)
    LATEST_BUILD_DIR = OA_BUILD_DIR
    print(f"[OK] Using OA archived build: {LATEST_BUILD_DIR.name}")
else:
    LATEST_BUILD_DIR = find_latest_build_dir(ARCHIVE_BUILDS_DIR)
print(f"[DEBUG] LATEST_BUILD_DIR resolved to: {LATEST_BUILD_DIR}")
print(f"[DEBUG] LATEST_BUILD_DIR exists: {LATEST_BUILD_DIR.exists()}")

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
# Helpers for WiX generation
# ------------------------------------------------------------------------------
def sanitize_identifier(text: str) -> str:
    """Convert text to valid WiX identifier"""
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in text)
    if not cleaned:
        cleaned = "item"
    if cleaned[0].isdigit():
        cleaned = f"_{cleaned}"
    return cleaned

def unique_id(base: str, used: set) -> str:
    """Generate unique ID by appending counter if needed"""
    candidate = base
    counter = 2
    while candidate in used:
        candidate = f"{base}_{counter}"
        counter += 1
    used.add(candidate)
    return candidate

def collect_files(build_dir: Path):
    """Collect all files from build directory"""
    return [p for p in build_dir.rglob("*") if p.is_file()]

# ------------------------------------------------------------------------------
# Generate .wxs file for WiX
# ------------------------------------------------------------------------------
build_files = collect_files(LATEST_BUILD_DIR)
print(f"[INFO] Enumerating all files in {LATEST_BUILD_DIR}...")
print(f"[DEBUG] EXE path: {EXE_PATH}")

# Build directory structure using Path objects
dir_children: dict[Path, set[Path]] = defaultdict(set)
files_in_dir: dict[Path, list[Path]] = defaultdict(list)

for file_path in build_files:
    rel_parts = file_path.relative_to(LATEST_BUILD_DIR).parts
    parent = Path()
    for part in rel_parts[:-1]:
        current = parent / part
        dir_children[parent].add(current)
        parent = current
    files_in_dir[parent].append(file_path)

# Generate unique directory IDs
dir_ids: dict[Path, str] = {Path(): "INSTALLFOLDER"}
used_directory_ids = {"INSTALLFOLDER"}

def get_directory_id(path: Path) -> str:
    """Get or create unique directory ID for a path"""
    if path in dir_ids:
        return dir_ids[path]
    base = f"INSTALLFOLDER_{sanitize_identifier('_'.join(path.parts))}" if path.parts else "INSTALLFOLDER"
    dir_id = unique_id(base, used_directory_ids)
    dir_ids[path] = dir_id
    return dir_id

# Track component and file IDs
component_ids: list[str] = []
file_ids_used: set[str] = set()
component_ids_used: set[str] = set()

def build_directory_xml(path: Path, indent: str = "        ") -> list[str]:
    """Recursively build directory XML with files"""
    lines: list[str] = []
    dir_id = get_directory_id(path)
    name_attr = f" Name=\"{APP_DISPLAY_NAME}\"" if path == Path() else f" Name=\"{path.name}\""
    lines.append(f"{indent}<Directory Id=\"{dir_id}\"{name_attr}>")
    
    # Add files in this directory
    for file_path in sorted(files_in_dir[path], key=lambda p: p.name):
        rel_parts = file_path.relative_to(LATEST_BUILD_DIR).parts
        sanitized_rel = sanitize_identifier("_".join(rel_parts))
        
        # Special handling for main EXE
        if file_path == EXE_PATH:
            comp_id = "MainExecutable"
            file_id = "AppEXE"
            # Only add MainExecutable once to component_ids
            if comp_id not in component_ids_used:
                component_ids_used.add(comp_id)
                # Don't add to component_ids here - it's already in Feature as hardcoded
        else:
            comp_id = unique_id(f"Cmp_{sanitized_rel}", component_ids_used)
            file_id = unique_id(f"File_{sanitized_rel}", file_ids_used)
            component_ids.append(comp_id)
        
        source_path = str(file_path).replace("/", "\\")
        lines.append(f"{indent}  <Component Id=\"{comp_id}\" Guid=\"*\">")
        lines.append(f"{indent}    <File Id=\"{file_id}\" Source=\"{source_path}\" KeyPath=\"yes\" />")
        lines.append(f"{indent}  </Component>")
    
    # Recursively add child directories
    for child in sorted(dir_children[path], key=lambda p: p.name.lower()):
        lines.extend(build_directory_xml(child, indent + "  "))
    
    lines.append(f"{indent}</Directory>")
    return lines

directory_tree_xml = "\n".join(build_directory_xml(Path()))

print(f"[DEBUG] Generated components for {len(component_ids)} files")
print(f"[DEBUG] Total directories: {len(dir_ids)}")
print(f"[DEBUG] Total components: {len(component_ids)}")

# Generate ComponentRef list (exclude hardcoded ones)
hardcoded_component_ids = {"MainExecutable", "DesktopShortcutComponent", "ProgramMenuShortcutComponent", "ProgramMenuCleanupComponent"}
component_ids_filtered = [cid for cid in component_ids if cid not in hardcoded_component_ids]
component_refs_xml = "\n".join(
    f"      <ComponentRef Id=\"{cid}\" />" for cid in component_ids_filtered
)

# ------------------------------------------------------------------------------
# Generate .wxs file for WiX
# ------------------------------------------------------------------------------
# Check for license file
LICENSE_RTF = Path(base_path("resources", "LICENSE.rtf")).resolve()
if not LICENSE_RTF.exists():
    print(f"[WARN] License file not found at {LICENSE_RTF}")
    print(f"       Creating default license file...")
    LICENSE_RTF.parent.mkdir(parents=True, exist_ok=True)

WXS_PATH = BUILDFILES_DIR / f"{APP_BASENAME}.wxs"
license_file_xml = ""
if LICENSE_RTF.exists():
    license_file_xml = f'    <WixVariable Id="WixUILicenseRtf" Value="{str(LICENSE_RTF).replace(chr(92), "/")}" />\n'
    print(f"[OK] License file found: {LICENSE_RTF}")

# Add banner and dialog bitmaps for installer UI
logo_banner_xml = ""
logo_dialog_xml = ""
if BANNER_IMAGE_PATH.exists():
    # Banner bitmap (shown at top of installer dialogs - must be exactly 493x58 pixels)
    # Format: 24-bit BMP or PNG (BMP recommended for best compatibility)
    logo_banner_xml = f'    <WixVariable Id="WixUIBannerBmp" Value="{str(BANNER_IMAGE_PATH).replace(chr(92), "/")}" />\n'
    print(f"[OK] Banner image found: {BANNER_IMAGE_PATH}")
else:
    print(f"[WARN] Banner image not found at {BANNER_IMAGE_PATH}")

if DIALOG_IMAGE_PATH.exists():
    # Dialog bitmap (shown on left side of installer dialogs)
    # NOTE: WixUI_Mondo expects 493x312 pixels, but some sources say 164x314
    # If image is stretching, try resizing to 493x312 pixels
    # PNG format is supported by WiX (24-bit RGB recommended, no alpha channel)
    logo_dialog_xml = f'    <WixVariable Id="WixUIDialogBmp" Value="{str(DIALOG_IMAGE_PATH).replace(chr(92), "/")}" />\n'
    print(f"[OK] Dialog image found: {DIALOG_IMAGE_PATH}")
    print(f"[INFO] If dialog image is stretching, ensure it's exactly 493x312 pixels (WixUI_Mondo standard)")
else:
    print(f"[WARN] Dialog image not found at {DIALOG_IMAGE_PATH}")

wxs_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*" Name="{APP_DISPLAY_NAME}" Language="1033" Version="{WIX_VERSION}"
           Manufacturer="Moviolabs" UpgradeCode="9a1f9b7a-d0b3-4b8a-aad9-2d2b06c9a111">
    <Package InstallerVersion="500" Compressed="yes" InstallScope="perMachine" />

    <MediaTemplate EmbedCab="yes" />
    <Icon Id="AppIcon.ico" SourceFile="{ICON_PATH}" />
    <Property Id="ARPPRODUCTICON" Value="AppIcon.ico" />
{license_file_xml}{logo_banner_xml}{logo_dialog_xml}

    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFilesFolder">
{directory_tree_xml}
      </Directory>
      <Directory Id="ProgramMenuFolder">
        <Directory Id="ProgramMenuDir" Name="{APP_DISPLAY_NAME}" />
      </Directory>
      <Directory Id="DesktopFolder" />
    </Directory>

    <DirectoryRef Id="DesktopFolder">
      <Component Id="DesktopShortcutComponent" Guid="*">
        <Shortcut Id="DesktopShortcut" Directory="DesktopFolder"
                  Name="{APP_DISPLAY_NAME}" Target="[#AppEXE]"
                  WorkingDirectory="INSTALLFOLDER"
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
                  Name="{APP_DISPLAY_NAME}" Target="[#AppEXE]"
                  WorkingDirectory="INSTALLFOLDER"
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
{component_refs_xml}
      <ComponentRef Id="DesktopShortcutComponent" />
      <ComponentRef Id="ProgramMenuShortcutComponent" />
      <ComponentRef Id="ProgramMenuCleanupComponent" />
    </Feature>

    <UIRef Id="WixUI_Mondo" />
    <Property Id="WIXUI_INSTALLDIR" Value="INSTALLFOLDER" />
  </Product>
</Wix>
"""
WXS_PATH.write_text(wxs_content, encoding="utf-8")
print(f"[OK] WXS file created at: {WXS_PATH}")
print(f"[DEBUG] WXS file size: {WXS_PATH.stat().st_size:,} bytes")
print(f"[DEBUG] WXS file lines: {len(wxs_content.splitlines()):,}")

# ------------------------------------------------------------------------------
# Run WiX (candle + light)
# ------------------------------------------------------------------------------
# Use short TEMP path to avoid LGHT0103 (WiX hits ~255 char path limit with long temp dirs)
_wix_temp = Path("C:/WiXTemp")
_wix_temp.mkdir(parents=True, exist_ok=True)
_orig_temp = os.environ.get("TEMP")
_orig_tmp = os.environ.get("TMP")
os.environ["TEMP"] = str(_wix_temp)
os.environ["TMP"] = str(_wix_temp)

# Change to buildfiles directory where WXS file is located
os.chdir(BUILDFILES_DIR)
try:
    # Run candle - outputs .wixobj to current directory (buildfiles)
    print(f"[DEBUG] Running candle on {APP_BASENAME}.wxs...")
    subprocess.run(["candle", f"{APP_BASENAME}.wxs"], check=True)
    print(f"[DEBUG] Candle completed successfully")
    
    # MSI goes to version directory (top level)
    msi_path = VERSION_DIR / f"{MSI_BASENAME}.msi"
    
    # CAB file goes to buildfiles directory
    cab_path = BUILDFILES_DIR / "cab1.cab"
    if cab_path.exists():
        try:
            cab_path.unlink()
        except PermissionError:
            os.chmod(cab_path, 0o666)
            cab_path.unlink(missing_ok=True)
    
    # Remove old MSI if it exists
    if msi_path.exists():
        try:
            msi_path.unlink()
        except PermissionError:
            os.chmod(msi_path, 0o666)
            msi_path.unlink(missing_ok=True)
    
    # Run light - outputs MSI to version directory
    wixobj_path = BUILDFILES_DIR / f"{APP_BASENAME}.wixobj"
    print(f"[DEBUG] Running light on {wixobj_path.name}...")
    subprocess.run([
        "light", "-ext", "WixUIExtension",
        str(wixobj_path), "-o", str(msi_path)
    ], check=True)
    print(f"[DEBUG] Light completed successfully")
    print(f"\n[OK] MSI created: {msi_path}")
    if msi_path.exists():
        print(f"[DEBUG] MSI file size: {msi_path.stat().st_size:,} bytes")
    
    # Move wixpdb to buildfiles if it was created in version directory
    wixpdb_name = f"{MSI_BASENAME}.wixpdb"
    wixpdb_src = VERSION_DIR / wixpdb_name
    if wixpdb_src.exists():
        wixpdb_dest = BUILDFILES_DIR / wixpdb_name
        shutil.move(str(wixpdb_src), str(wixpdb_dest))
        print(f"[OK] Moved {wixpdb_name} to buildfiles")
    
    # Ensure cab file is in buildfiles (it should be created there, but check version_dir too)
    cab_src = VERSION_DIR / "cab1.cab"
    if cab_src.exists():
        cab_dest = BUILDFILES_DIR / "cab1.cab"
        shutil.move(str(cab_src), str(cab_dest))
        print(f"[OK] Moved cab1.cab to buildfiles")
    
    # CRITICAL: Copy CAB file to same directory as MSI (installer expects it there)
    # Even with EmbedCab="yes", we copy it as a safeguard
    cab_in_buildfiles = BUILDFILES_DIR / "cab1.cab"
    if cab_in_buildfiles.exists():
        cab_with_msi = msi_path.parent / "cab1.cab"
        shutil.copy2(str(cab_in_buildfiles), str(cab_with_msi))
        print(f"[OK] Copied cab1.cab to MSI directory: {cab_with_msi}")
    
    # Code signing (if configured)
    try:
        from config.code_signing_config import (
            ENABLE_CODE_SIGNING, CERT_PATH, CERT_PASSWORD, CERT_THUMBPRINT,
            TIMESTAMP_URL, FILE_DESCRIPTION, FILE_DESCRIPTION_URL
        )
        from utilities.code_signing import sign_file
        
        if ENABLE_CODE_SIGNING:
            print(f"\n[INFO] Code signing enabled - signing MSI...")
            sign_file(
                msi_path,
                cert_path=CERT_PATH,
                cert_password=CERT_PASSWORD,
                cert_thumbprint=CERT_THUMBPRINT,
                timestamp_url=TIMESTAMP_URL,
                description=FILE_DESCRIPTION,
                description_url=FILE_DESCRIPTION_URL,
            )
    except ImportError:
        # Code signing not configured - this is OK
        pass
    except Exception as e:
        print(f"[WARN] Code signing failed: {e}")
        print("       Continuing without code signing...")
        
except subprocess.CalledProcessError as e:
    print(f"[ERROR] WiX build failed: {e}")
    sys.exit(1)
finally:
    # Restore original TEMP/TMP
    if _orig_temp is not None:
        os.environ["TEMP"] = _orig_temp
    if _orig_tmp is not None:
        os.environ["TMP"] = _orig_tmp

# ------------------------------------------------------------------------------
# Create portable ZIP (from build directory)
# ------------------------------------------------------------------------------
ZIP_PATH = VERSION_DIR / f"{MSI_BASENAME}-portable.zip"
zip_base = ZIP_PATH.with_suffix("")
if LATEST_BUILD_DIR.exists():
    print(f"[OK] Creating portable ZIP from {LATEST_BUILD_DIR.name}: {ZIP_PATH.name}")
    try:
        # Remove existing ZIP if it exists
        if ZIP_PATH.exists():
            ZIP_PATH.unlink()
        
        # Create ZIP archive with maximum compression
        import zipfile
        print(f"[optimize] Creating ZIP with maximum compression...")
        with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for root, dirs, files in os.walk(LATEST_BUILD_DIR):
                # Skip __pycache__ directories
                dirs[:] = [d for d in dirs if d != '__pycache__']
                for file in files:
                    # Skip .pyc files
                    if file.endswith('.pyc'):
                        continue
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(LATEST_BUILD_DIR.parent)
                    zf.write(file_path, arcname)
        
        # Verify ZIP was created and has content
        if ZIP_PATH.exists():
            zip_size = ZIP_PATH.stat().st_size
            print(f"[OK] Portable ZIP created at: {ZIP_PATH}")
            print(f"[DEBUG] ZIP file size: {zip_size:,} bytes ({zip_size / (1024*1024):.2f} MB)")
            
            # Verify ZIP contains files
            try:
                with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
                    file_count = len(zf.namelist())
                    print(f"[DEBUG] ZIP contains {file_count} files")
                    if file_count == 0:
                        print("[WARN] ZIP file is empty!")
                    # Check for EXE
                    exe_in_zip = any(name.endswith('.exe') for name in zf.namelist())
                    if not exe_in_zip:
                        print("[WARN] ZIP does not contain .exe file!")
                    else:
                        print("[OK] ZIP contains executable file")
            except zipfile.BadZipFile:
                print("[ERROR] Created ZIP file is corrupted!")
        else:
            print("[ERROR] ZIP file was not created!")
    except Exception as e:
        print(f"[ERROR] Failed to create portable ZIP: {e}")
        import traceback
        traceback.print_exc()
else:
    print("[WARN] No archived build folder found to zip.")

# ------------------------------------------------------------------------------
# Note: Old build purging is no longer needed with versioned directory structure.
# Each version has its own directory, and old versions can be manually cleaned up if needed.
# ------------------------------------------------------------------------------
print("\n[SUCCESS] All done - MSI + ZIP ready!")
