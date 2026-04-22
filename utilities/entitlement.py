"""
Entitlement storage and migration helpers.

Primary store:
- %APPDATA%/MVC_Calculator/entitlement.json (Windows frozen build)
- ~/.local/share/MVC_Calculator/entitlement.json (Linux/macOS frozen build)
- project root / MVC_Calculator/entitlement.json (dev mode)

Backward compatibility:
- Existing license.key is automatically migrated into entitlement.json.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

from utilities.license import (
    WILDCARD_HWID_HFMDD,
    find_license_file,
    get_country,
    get_machine_id,
    get_user_data_dir,
    validate_license_key,
)


def is_preactivated_bundle_entitlement(data: Optional[Dict]) -> bool:
    """True when entitlement was installed from a bundled preactivated artifact."""
    if not isinstance(data, dict):
        return False
    return str(data.get("source", "")).strip().lower() == "preactivated_bundle"

logger = logging.getLogger(__name__)

ENTITLEMENT_FILENAME = "entitlement.json"
PREACTIVATED_DIRNAME = "preactivated"


def get_entitlement_file_path() -> Path:
    return get_user_data_dir() / ENTITLEMENT_FILENAME


def load_entitlement() -> Optional[Dict]:
    path = get_entitlement_file_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception as e:
        logger.warning("Failed to read entitlement file: %s", e)
    return None


def save_entitlement(entitlement_data: Dict) -> Tuple[bool, Optional[str]]:
    path = get_entitlement_file_path()
    payload = {
        **entitlement_data,
        "stored_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    try:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
        return True, None
    except Exception as e:
        return False, str(e)


def build_preactivated_entitlement(
    license_key: str,
    issued_for: str = "hfmdd.de",
    bundle_id: Optional[str] = None,
) -> Dict:
    """
    Build a standard preactivated entitlement artifact payload.
    """
    payload = {
        "format": "license_key_v1",
        "license_key": license_key.strip(),
        "source": "preactivated_bundle",
        "issued_for": issued_for,
        "issued_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    if bundle_id:
        payload["bundle_id"] = bundle_id
    return payload


def _validate_license_data_on_this_machine(
    license_data: Dict[str, str], *, skip_country: bool = False
) -> Tuple[bool, Optional[str]]:
    current_hwid = get_machine_id()
    current_country = get_country()

    if license_data.get("hwid") == WILDCARD_HWID_HFMDD:
        email = license_data.get("email", "")
        email_domain = email.split("@")[-1].lower() if "@" in email else ""
        if email_domain != "hfmdd.de":
            return False, "Wildcard license is only valid for @hfmdd.de email addresses."
    elif license_data.get("hwid") != current_hwid:
        return False, "License key is not valid for this machine. Hardware ID mismatch."

    if not skip_country and current_country and license_data.get("country") != current_country:
        return (
            False,
            f"License key is not valid for this country. Expected: {license_data.get('country')}, Detected: {current_country}",
        )

    return True, None


def migrate_license_key_to_entitlement() -> Tuple[bool, Optional[str]]:
    """
    If entitlement file does not exist but license.key exists, migrate into entitlement.json.
    """
    if load_entitlement() is not None:
        return True, None

    lic_path = find_license_file()
    if not lic_path:
        return False, "No license.key found to migrate."

    try:
        license_key = lic_path.read_text(encoding="utf-8").strip()
    except Exception as e:
        return False, f"Could not read legacy license.key: {e}"

    ok, _, err = validate_license_key(license_key)
    if not ok:
        return False, err or "Legacy license.key is invalid."

    entitlement = {
        **build_preactivated_entitlement(license_key, issued_for="legacy-license-key"),
        "source": "migrated_license_key",
        "source_path": str(lic_path),
    }
    return save_entitlement(entitlement)


def install_bundled_entitlement_if_available() -> Tuple[bool, Optional[str]]:
    """
    Install preactivated entitlement from bundled file, if present.

    Candidate paths (in order):
    - <exe_dir>/preactivated/entitlement.json
    - <exe_dir>/_internal/preactivated/entitlement.json
    - <project_root>/preactivated/entitlement.json (dev)
    """
    target = get_entitlement_file_path()
    if target.exists():
        return True, None

    candidates = []

    # frozen build: check beside EXE and _internal
    import sys
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.append(exe_dir / PREACTIVATED_DIRNAME / ENTITLEMENT_FILENAME)
        candidates.append(exe_dir / "_internal" / PREACTIVATED_DIRNAME / ENTITLEMENT_FILENAME)

    # dev fallback
    project_root = Path(__file__).resolve().parent.parent
    candidates.append(project_root / PREACTIVATED_DIRNAME / ENTITLEMENT_FILENAME)

    for src in candidates:
        if not src.exists():
            continue
        try:
            data = json.loads(src.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return False, f"Bundled entitlement has invalid JSON object at {src}"
            license_key = str(data.get("license_key", "")).strip()
            if not license_key:
                return False, f"Bundled entitlement is missing license_key at {src}"
            ok, _, err = validate_license_key(license_key)
            if not ok:
                return False, f"Bundled entitlement has invalid license key: {err}"
            return save_entitlement(data)
        except Exception as e:
            return False, f"Failed to install bundled entitlement from {src}: {e}"

    return False, "No bundled entitlement found."


def validate_entitlement() -> Tuple[bool, Optional[str]]:
    """
    Validate current entitlement (with migration fallback from legacy license.key).
    """
    entitlement = load_entitlement()
    if entitlement is None:
        install_bundled_entitlement_if_available()
        entitlement = load_entitlement()
    if entitlement is None:
        migrate_license_key_to_entitlement()
        entitlement = load_entitlement()

    if entitlement is None:
        return False, f"Entitlement file not found.\n\nExpected path:\n{get_entitlement_file_path()}"

    license_key = str(entitlement.get("license_key", "")).strip()
    if not license_key:
        return False, "Entitlement file is missing license_key."

    ok, license_data, err = validate_license_key(license_key)
    if not ok or not license_data:
        return False, err or "Invalid license key in entitlement."

    skip_country = is_preactivated_bundle_entitlement(entitlement)
    ok, machine_error = _validate_license_data_on_this_machine(
        license_data, skip_country=skip_country
    )
    if not ok:
        return False, machine_error

    return True, None
