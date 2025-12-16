#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Signing Utility for Windows Executables and MSI Installers
================================================================
Prevents "Windows protected your PC" SmartScreen warnings.

Requirements:
- Code signing certificate (.pfx file or installed in Windows Certificate Store)
- signtool.exe (comes with Windows SDK)
- Optional: Timestamp server URL

Usage:
    from utilities.code_signing import sign_file
    
    # Sign with PFX file
    sign_file("app.exe", 
              cert_path="certificate.pfx",
              cert_password="password",
              timestamp_url="http://timestamp.digicert.com")
    
    # Sign with certificate from store (by thumbprint)
    sign_file("app.exe",
              cert_thumbprint="ABC123...",
              timestamp_url="http://timestamp.digicert.com")
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


def find_signtool() -> Optional[Path]:
    """Find signtool.exe on the system."""
    # Common locations for signtool.exe
    possible_paths = [
        # Windows SDK (most common)
        Path("C:/Program Files (x86)/Windows Kits/10/bin/x64/signtool.exe"),
        Path("C:/Program Files (x86)/Windows Kits/10/bin/10.0.22621.0/x64/signtool.exe"),
        Path("C:/Program Files (x86)/Windows Kits/10/bin/10.0.19041.0/x64/signtool.exe"),
        # Alternative locations
        Path("C:/Program Files/Windows Kits/10/bin/x64/signtool.exe"),
        # Check PATH
        None,  # Will check via shutil.which
    ]
    
    # Check if signtool is in PATH
    signtool_in_path = shutil.which("signtool")
    if signtool_in_path:
        return Path(signtool_in_path)
    
    # Check common installation paths
    for path in possible_paths:
        if path and path.exists():
            return path
    
    return None


def sign_file(
    file_path: Path | str,
    cert_path: Optional[str] = None,
    cert_password: Optional[str] = None,
    cert_thumbprint: Optional[str] = None,
    timestamp_url: str = "http://timestamp.digicert.com",
    description: Optional[str] = None,
    description_url: Optional[str] = None,
) -> bool:
    """
    Sign a file (EXE, MSI, DLL, etc.) using signtool.exe.
    
    Args:
        file_path: Path to file to sign
        cert_path: Path to .pfx certificate file (if using file-based cert)
        cert_password: Password for .pfx file (if using file-based cert)
        cert_thumbprint: Certificate thumbprint from Windows Certificate Store
        timestamp_url: Timestamp server URL (prevents signature expiration)
        description: Description of the signed file
        description_url: URL for more information about the file
    
    Returns:
        True if signing succeeded, False otherwise
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"[ERROR] File not found: {file_path}")
        return False
    
    # Find signtool
    signtool = find_signtool()
    if not signtool:
        print("[ERROR] signtool.exe not found. Install Windows SDK.")
        print("  Download: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/")
        return False
    
    print(f"[INFO] Signing {file_path.name}...")
    
    # Build signtool command
    cmd = [str(signtool), "sign"]
    
    # Certificate selection
    if cert_path:
        # Use PFX file
        cmd.extend(["/f", cert_path])
        if cert_password:
            cmd.extend(["/p", cert_password])
    elif cert_thumbprint:
        # Use certificate from store
        cmd.extend(["/sha1", cert_thumbprint])
    else:
        print("[ERROR] Must provide either cert_path or cert_thumbprint")
        return False
    
    # Timestamp (prevents signature from expiring when cert expires)
    if timestamp_url:
        cmd.extend(["/tr", timestamp_url])
        cmd.extend(["/td", "sha256"])  # Use SHA-256 for timestamp
    
    # Description (optional)
    if description:
        cmd.extend(["/d", description])
    
    # Description URL (optional)
    if description_url:
        cmd.extend(["/du", description_url])
    
    # Verbose output
    cmd.append("/v")
    
    # File to sign
    cmd.append(str(file_path))
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print(f"✅ Successfully signed: {file_path.name}")
            return True
        else:
            print(f"❌ Signing failed for {file_path.name}")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running signtool: {e}")
        return False


# Import shutil for which()
import shutil

