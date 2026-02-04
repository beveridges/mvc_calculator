# utilities/license.py
"""
License key validation system for MVC Calculator.

Features:
- Hardware fingerprint (HWID) generation
- Country detection (offline via Windows locale)
- License key validation with embedded HWID and country
- Prevents license copying to other machines
"""

import hashlib
import hmac
import base64
import subprocess
import platform
import ctypes
from ctypes import wintypes
from pathlib import Path
from typing import Optional, Dict, Tuple
import logging
import sys

logger = logging.getLogger(__name__)

# Only enforce license in frozen (PyInstaller) builds
# Allow override via environment variable: LICENSE_CHECK=1 or LICENSE_CHECK=0
# Also check for DEV_BUILD flag in version_info (set by --dev build flag)
import os
ENFORCE_LICENSE = getattr(sys, "frozen", False)

# Check for DEV_BUILD flag (license-free dev builds)
try:
    from utilities.version_info import DEV_BUILD
    if DEV_BUILD:
        ENFORCE_LICENSE = False
except (ImportError, AttributeError):
    # version_info.py might not have DEV_BUILD (old builds or dev mode)
    pass

# Allow override via environment variable: LICENSE_CHECK=1 or LICENSE_CHECK=0
if "LICENSE_CHECK" in os.environ:
    ENFORCE_LICENSE = os.environ.get("LICENSE_CHECK", "").lower() not in ("0", "false")

# Secret key for HMAC signing (in production, store this securely)
# This should be the same key used to generate licenses
LICENSE_SECRET = b"moviolabs_license_secret_key_2024_change_in_production"

# License file location (in same directory as executable or in user data)
LICENSE_FILENAME = "license.key"

# Wildcard HWID for @hfmdd.de users (allows license to work on any machine)
WILDCARD_HWID_HFMDD = "WILDCARD_HFMDD_DE"

# Telemetry: only send one license failure/success report per application session
_license_failure_reported = False
_license_success_reported = False


def _report_license_failure(error_message: str) -> None:
    """Send email to telemetry@moviolabs.com on license failure (once per session)."""
    global _license_failure_reported
    if not ENFORCE_LICENSE or _license_failure_reported:
        return
    try:
        from telemetry.notifier import send_license_failure_report
        send_license_failure_report(error_message)
        _license_failure_reported = True
    except Exception as e:
        logger.debug(f"Could not send license failure report: {e}")


def _report_license_success(license_email: str) -> None:
    """Send email to telemetry@moviolabs.com on license success (once per session)."""
    global _license_success_reported
    if not ENFORCE_LICENSE or _license_success_reported:
        return
    try:
        from telemetry.notifier import send_license_success_report
        send_license_success_report(
            license_email=license_email,
            hwid=get_machine_id(),
            country=get_country() or "Unknown",
        )
        _license_success_reported = True
    except Exception as e:
        logger.debug(f"Could not send license success report: {e}")


def get_machine_id() -> str:
    """
    Generate a stable hardware fingerprint (HWID) from:
    - CPU/Motherboard UUID
    - Disk serial number
    - Windows machine GUID (if available)
    """
    components = []
    
    try:
        # Windows UUID (Motherboard/System UUID)
        if platform.system() == "Windows":
            try:
                cmd = "wmic csproduct get uuid"
                result = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode()
                uuid_out = result.split('\n')[1].strip() if len(result.split('\n')) > 1 else ""
                if uuid_out:
                    components.append(uuid_out)
            except Exception:
                pass
            
            # Disk serial number
            try:
                cmd = "wmic diskdrive get serialnumber"
                result = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode()
                disk_out = result.split('\n')[1].strip() if len(result.split('\n')) > 1 else ""
                if disk_out:
                    components.append(disk_out)
            except Exception:
                pass
            
            # Windows machine GUID (additional component)
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Cryptography"
                )
                machine_guid = winreg.QueryValueEx(key, "MachineGuid")[0]
                winreg.CloseKey(key)
                if machine_guid:
                    components.append(machine_guid)
            except Exception:
                pass
        
        # Fallback: use platform node (hostname) if Windows methods fail
        if not components:
            components.append(platform.node())
            components.append(platform.processor() or "unknown")
    
    except Exception as e:
        logger.warning(f"Error generating machine ID: {e}")
        # Fallback to basic platform info
        components = [platform.node(), platform.processor() or "unknown"]
    
    # Combine all components and hash
    raw = "-".join(components)
    return hashlib.sha256(raw.encode()).hexdigest()


def get_country_offline() -> Optional[str]:
    """
    Get country code from Windows locale/region settings.
    Returns 2-letter ISO country code (e.g., "CO", "US", "GB", "DE").
    """
    try:
        if platform.system() == "Windows":
            # Method 1: GetLocaleInfoEx - returns proper ISO 3166-1 alpha-2 country code (e.g. "DE", "US")
            # Avoids locale strings like "German_Germany" which would yield "GERMANY" instead of "DE"
            try:
                kernel32 = ctypes.windll.kernel32
                LOCALE_SISO3166CTRYNAME = 0x5A  # Returns ISO 3166-1 alpha-2 country code
                buf = ctypes.create_unicode_buffer(16)
                result = kernel32.GetLocaleInfoEx(
                    None,  # LOCALE_NAME_USER_DEFAULT - user's default locale
                    LOCALE_SISO3166CTRYNAME,
                    buf,
                    ctypes.sizeof(buf) // ctypes.sizeof(ctypes.c_wchar),
                )
                if result > 0:
                    code = buf.value.strip().upper()
                    if len(code) == 2:
                        return code
            except Exception:
                pass

            # Method 2: Fallback to locale (may return full names like "GERMANY" on some Windows configs)
            try:
                import locale
                locale_str = locale.getdefaultlocale()[0] or ""
                if "_" in locale_str:
                    parts = locale_str.split("_")
                    if len(parts) > 1:
                        raw = parts[1].upper()
                        # If already 2 chars, use as ISO code (e.g. en_DE -> DE)
                        if len(raw) == 2:
                            return raw
                        # Map full country names to ISO codes (e.g. German_Germany -> GERMANY)
                        country_map = {
                            "GERMANY": "DE",
                            "UNITED STATES": "US",
                            "UNITED KINGDOM": "GB",
                            "FRANCE": "FR",
                            "SPAIN": "ES",
                            "ITALY": "IT",
                            "BRAZIL": "BR",
                            "COLOMBIA": "CO",
                            "MEXICO": "MX",
                            "ARGENTINA": "AR",
                            "CHILE": "CL",
                            "AUSTRALIA": "AU",
                            "CANADA": "CA",
                            "NETHERLANDS": "NL",
                            "BELGIUM": "BE",
                            "SWITZERLAND": "CH",
                            "AUSTRIA": "AT",
                            "PORTUGAL": "PT",
                            "JAPAN": "JP",
                            "CHINA": "CN",
                            "INDIA": "IN",
                            "SOUTH AFRICA": "ZA",
                            "RUSSIA": "RU",
                        }
                        return country_map.get(raw)
            except Exception:
                pass

    except Exception as e:
        logger.warning(f"Error getting country: {e}")

    return None


def get_country_online() -> Optional[str]:
    """
    Get country code from IP geolocation API (requires internet).
    Returns 2-letter ISO country code or None if unavailable.
    """
    try:
        import requests
        response = requests.get("https://ipapi.co/country/", timeout=3)
        if response.status_code == 200:
            country = response.text.strip()
            if len(country) == 2:
                return country.upper()
    except Exception:
        pass
    
    return None


def get_country() -> Optional[str]:
    """
    Get country code, trying offline method first, then online if needed.
    """
    country = get_country_offline()
    if country:
        return country
    
    # Fallback to online if offline method fails
    return get_country_online()


def generate_license_key(email: str, country: str, hwid: str, expiration_days: Optional[int] = None, use_wildcard_hwid: bool = False) -> str:
    """
    Generate a license key with embedded email, country, HWID, and optional expiration.
    
    Format: base64(email|country|hwid|expiration|signature)
    
    Args:
        email: User's email address
        country: 2-letter ISO country code
        hwid: Hardware ID (ignored if use_wildcard_hwid=True)
        expiration_days: Days until expiration (0 = no expiration)
        use_wildcard_hwid: If True, use wildcard HWID (allows license on any machine)
    """
    expiration = expiration_days or 0  # 0 = no expiration
    
    # Use wildcard HWID if requested (for @hfmdd.de users)
    if use_wildcard_hwid:
        hwid = WILDCARD_HWID_HFMDD
    
    # Create payload
    payload = f"{email}|{country}|{hwid}|{expiration}"
    
    # Sign with HMAC
    signature = hmac.new(LICENSE_SECRET, payload.encode(), hashlib.sha256).hexdigest()
    
    # Combine payload and signature
    full_data = f"{payload}|{signature}"
    
    # Encode to base64
    license_key = base64.b64encode(full_data.encode()).decode()
    
    return license_key


def validate_license_key(license_key: str) -> Tuple[bool, Optional[Dict[str, str]], Optional[str]]:
    """
    Validate a license key.
    
    Returns:
        (is_valid, license_data, error_message)
        license_data contains: email, country, hwid, expiration
    """
    try:
        # Decode from base64
        decoded = base64.b64decode(license_key.encode()).decode()
        parts = decoded.split("|")
        
        if len(parts) != 5:
            return False, None, "Invalid license key format"
        
        email, country, hwid, expiration_str, signature = parts
        
        # Reconstruct payload
        payload = f"{email}|{country}|{hwid}|{expiration_str}"
        
        # Verify signature
        expected_sig = hmac.new(LICENSE_SECRET, payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return False, None, "Invalid license key signature"
        
        # Check expiration
        try:
            expiration_days = int(expiration_str)
            if expiration_days > 0:
                from datetime import datetime, timedelta
                # Calculate expiration date (assuming license was issued today)
                # In production, you'd store the issue date in the license
                expiration_date = datetime.now() + timedelta(days=expiration_days)
                if datetime.now() > expiration_date:
                    return False, None, "License key has expired"
        except ValueError:
            pass
        
        license_data = {
            "email": email,
            "country": country,
            "hwid": hwid,
            "expiration": expiration_str
        }
        
        return True, license_data, None
    
    except Exception as e:
        logger.error(f"License validation error: {e}")
        return False, None, f"License validation failed: {str(e)}"


def get_user_data_dir() -> Path:
    """
    Get the persistent user data directory for storing license files.
    This location persists across application updates.
    """
    import sys
    import os
    
    if getattr(sys, "frozen", False):
        # Running as frozen EXE (PyInstaller) → use a writable user dir
        if platform.system() == "Windows":
            data_dir = Path(os.environ.get("APPDATA", Path.home()))
        else:
            # Linux/Mac: use ~/.local/share or ~/.config
            data_dir = Path.home() / ".local" / "share"
    else:
        # Running from source (dev mode)
        data_dir = Path(__file__).parent.parent
    
    # Create MVC_Calculator subdirectory
    app_data_dir = data_dir / "MVC_Calculator"
    app_data_dir.mkdir(parents=True, exist_ok=True)
    
    return app_data_dir


def migrate_license_from_old_locations() -> Optional[Path]:
    """
    Migrate license file from old locations to the persistent user data directory.
    This ensures licenses persist across application updates.
    
    Returns the path to the migrated license file, or None if no license was found.
    """
    import sys
    import shutil
    
    user_data_dir = get_user_data_dir()
    persistent_license_path = user_data_dir / LICENSE_FILENAME
    
    # If license already exists in persistent location, no migration needed
    if persistent_license_path.exists():
        return persistent_license_path
    
    # Check old locations and migrate if found
    old_locations = []
    
    # 1. Same directory as executable (for PyInstaller builds)
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
        old_locations.append(exe_dir / LICENSE_FILENAME)
    
    # 2. Current working directory
    old_locations.append(Path.cwd() / LICENSE_FILENAME)
    
    # 3. User's home directory
    old_locations.append(Path.home() / LICENSE_FILENAME)
    
    # Try to migrate from old locations
    for old_path in old_locations:
        if old_path.exists() and old_path != persistent_license_path:
            try:
                # Copy to persistent location
                shutil.copy2(old_path, persistent_license_path)
                logger.info(f"Migrated license from {old_path} to {persistent_license_path}")
                return persistent_license_path
            except Exception as e:
                logger.warning(f"Failed to migrate license from {old_path}: {e}")
                # If migration fails, still try to use the old location
                return old_path
    
    return None


def find_license_file() -> Optional[Path]:
    """
    Find the license.key file.
    Checks in this order:
    1. Persistent user data directory (survives updates) - PRIORITY
    2. Old locations (for backward compatibility and migration)
    
    Also automatically migrates licenses from old locations to persistent location.
    """
    # First, try to migrate from old locations
    migrated = migrate_license_from_old_locations()
    if migrated:
        return migrated
    
    # Check persistent location (even if migration didn't find anything)
    user_data_dir = get_user_data_dir()
    persistent_license_path = user_data_dir / LICENSE_FILENAME
    if persistent_license_path.exists():
        return persistent_license_path
    
    # Fallback: check old locations (for backward compatibility)
    import sys
    
    # Same directory as executable (for PyInstaller builds)
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
        license_path = exe_dir / LICENSE_FILENAME
        if license_path.exists():
            return license_path
    
    # Current working directory
    license_path = Path.cwd() / LICENSE_FILENAME
    if license_path.exists():
        return license_path
    
    # User's home directory
    license_path = Path.home() / LICENSE_FILENAME
    if license_path.exists():
        return license_path
    
    return None


def get_license_file_path() -> Optional[Path]:
    """
    Get the recommended path where the license file should be stored.
    This is the persistent user data directory that survives updates.
    """
    user_data_dir = get_user_data_dir()
    return user_data_dir / LICENSE_FILENAME


def load_and_validate_license() -> Tuple[bool, Optional[str]]:
    """
    Load license file and validate it against current machine.
    
    Returns:
        (is_valid, error_message)
    """
    license_path = find_license_file()
    
    if not license_path:
        recommended_path = get_license_file_path()
        err = (
            f"License file not found.\n\n"
            f"Please place license.key in:\n{recommended_path}\n\n"
            f"This location persists across application updates."
        )
        _report_license_failure(err)
        return False, err
    
    try:
        license_key = license_path.read_text(encoding="utf-8").strip()
    except Exception as e:
        err = f"Error reading license file: {str(e)}"
        _report_license_failure(err)
        return False, err
    
    # Validate license key format and signature
    is_valid, license_data, error = validate_license_key(license_key)
    if not is_valid:
        err = error or "Invalid license key"
        _report_license_failure(err)
        return False, err
    
    # Get current machine info
    current_hwid = get_machine_id()
    current_country = get_country()
    
    # Check HWID match (skip for wildcard HWID if email is from @hfmdd.de)
    if license_data["hwid"] == WILDCARD_HWID_HFMDD:
        # Wildcard HWID: check if email domain is @hfmdd.de
        email_domain = license_data["email"].split("@")[-1].lower() if "@" in license_data["email"] else ""
        if email_domain == "hfmdd.de":
            # Skip HWID check for @hfmdd.de users with wildcard license
            logger.info(f"Wildcard license detected for {license_data['email']} - skipping HWID validation")
        else:
            # Wildcard HWID but not @hfmdd.de - invalid
            err = "Wildcard license is only valid for @hfmdd.de email addresses."
            _report_license_failure(err)
            return False, err
    elif license_data["hwid"] != current_hwid:
        err = "License key is not valid for this machine. Hardware ID mismatch."
        _report_license_failure(err)
        return False, err

    # Check country match
    if current_country and license_data["country"] != current_country:
        err = f"License key is not valid for this country. Expected: {license_data['country']}, Detected: {current_country}"
        _report_license_failure(err)
        return False, err
    
    logger.info(f"License validated successfully for {license_data['email']}")
    _report_license_success(license_data["email"])
    return True, None


def check_license() -> bool:
    """
    Main license check function.
    Returns True if license is valid, False otherwise.
    Only enforces license in frozen builds unless overridden.
    """
    # Skip license check if not enforcing (development mode)
    if not ENFORCE_LICENSE:
        logger.debug("License check skipped (not in frozen build)")
        return True
    
    is_valid, error = load_and_validate_license()
    
    if not is_valid:
        logger.error(f"License validation failed: {error}")
        return False
    
    return True

