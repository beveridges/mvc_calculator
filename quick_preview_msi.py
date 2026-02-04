#!/usr/bin/env python3
"""
Quick MSI Dialog Preview - Builds a minimal MSI to test dialog images
This is MUCH faster than building the full installer
"""
import subprocess
import sys
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent.resolve()
BANNER_IMAGE = PROJECT_ROOT / "resources" / "icons" / "MSI_INSTALLER_BANNER.png"
DIALOG_IMAGE = PROJECT_ROOT / "resources" / "icons" / "MSI_INSTALLER_DIALOG_IMAGE_LARGE_B_W.png"

# Convert paths to forward slashes for WiX
def wix_path(p):
    return str(p).replace("\\", "/")

wxs_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*" Name="MVC Calculator Preview" Language="1033" Version="1.0.0"
           Manufacturer="Moviolabs" UpgradeCode="9a1f9b7a-d0b3-4b8a-aad9-2d2b06c9a111">
    <Package InstallerVersion="500" Compressed="yes" InstallScope="perMachine" />
    <MediaTemplate EmbedCab="yes" />
    
    <WixVariable Id="WixUIBannerBmp" Value="{wix_path(BANNER_IMAGE)}" />
    <WixVariable Id="WixUIDialogBmp" Value="{wix_path(DIALOG_IMAGE)}" />
    
    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFilesFolder">
        <Directory Id="INSTALLFOLDER" Name="MVC Calculator" />
      </Directory>
    </Directory>
    
    <Feature Id="DefaultFeature" Level="1">
      <Component Id="TestComponent" Directory="INSTALLFOLDER" Guid="*">
        <File Id="TestFile" Source="C:\\\\Windows\\\\System32\\\\notepad.exe" KeyPath="yes" />
      </Component>
    </Feature>
    
    <UIRef Id="WixUI_Mondo" />
    <Property Id="WIXUI_INSTALLDIR" Value="INSTALLFOLDER" />
  </Product>
</Wix>'''

# Write WXS file
wxs_file = PROJECT_ROOT / "preview_test.wxs"
wxs_file.write_text(wxs_content, encoding="utf-8")
print(f"[OK] Created preview WXS: {wxs_file}")

# Build MSI
print("\n[INFO] Building preview MSI...")
try:
    # Compile
    print("  Running candle...")
    subprocess.run(["candle", str(wxs_file)], check=True, cwd=PROJECT_ROOT)
    
    # Link
    print("  Running light...")
    msi_path = PROJECT_ROOT / "preview_test.msi"
    subprocess.run([
        "light", "-ext", "WixUIExtension",
        str(PROJECT_ROOT / "preview_test.wixobj"),
        "-o", str(msi_path)
    ], check=True, cwd=PROJECT_ROOT)
    
    print(f"\n[SUCCESS] Preview MSI created: {msi_path}")
    print("  Run this MSI to preview your dialog images!")
    print("  This is much faster than building the full installer.")
    
except subprocess.CalledProcessError as e:
    print(f"\n[ERROR] Build failed: {e}")
    sys.exit(1)
except FileNotFoundError:
    print("\n[ERROR] WiX Toolset not found in PATH")
    print("  Make sure candle.exe and light.exe are available")
    sys.exit(1)

