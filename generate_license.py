#!/usr/bin/env python3
"""
License Key Generator for MVC Calculator

Usage:
    python generate_license.py <email> <country> [expiration_days] [--wildcard-hfmdd | --current-machine | <hwid>]

Examples:
    python generate_license.py user@example.com CO
    python generate_license.py user@example.com US 365
    python generate_license.py user@example.com GB 0  # No expiration
    python generate_license.py institutional@hfmdd.de DE 0 --wildcard-hfmdd  # Any machine for @hfmdd.de
"""

import sys
from pathlib import Path

# Add utilities to path
sys.path.insert(0, str(Path(__file__).parent))

from utilities.license import generate_license_key, get_machine_id, get_country


def main():
    args = [a for a in sys.argv[1:] if a != "--wildcard-hfmdd"]
    use_wildcard_hfmdd = "--wildcard-hfmdd" in sys.argv[1:]

    if len(args) < 3:
        print(__doc__)
        print("\nUsage: python generate_license.py <email> <country> [expiration_days] [--wildcard-hfmdd | --current-machine | <hwid>]")
        print("\nExample: python generate_license.py support@moviolabs.com CO 365")
        print("Wildcard (any machine for @hfmdd.de): python generate_license.py institutional@hfmdd.de DE 0 --wildcard-hfmdd")
        sys.exit(1)

    email = args[0]
    country = args[1].upper()

    # Optional expiration (0 = no expiration)
    expiration_days = 0
    if len(args) > 2:
        try:
            expiration_days = int(args[2])
        except ValueError:
            print(f"Error: Invalid expiration days: {args[2]}")
            sys.exit(1)
    rest = args[3:] if len(args) > 3 else []  # args[3] = --current-machine or hwid if present

    print("Generating license key...")
    print(f"Email: {email}")
    print(f"Country: {country}")
    print(f"Expiration: {expiration_days} days (0 = no expiration)")

    if use_wildcard_hfmdd:
        hwid = "WILDCARD_HFMDD_DE"
        print("HWID: wildcard (valid on any machine for @hfmdd.de)")
    elif rest and rest[0] == "--current-machine":
        hwid = get_machine_id()
        print(f"HWID (current machine): {hwid[:16]}...")
    elif rest:
        hwid = rest[0]
        print(f"HWID (provided): {hwid[:16]}...")
    else:
        hwid = get_machine_id()
        print(f"HWID (current machine, default): {hwid[:16]}...")
        print("\nNote: To generate for a different machine, provide HWID as 5th argument; or use --wildcard-hfmdd for @hfmdd.de")

    license_key = generate_license_key(email, country, hwid, expiration_days, use_wildcard_hwid=use_wildcard_hfmdd)

    license_file = Path("license.key")
    license_file.write_text(license_key, encoding="utf-8")

    print("\n" + "="*70)
    print("LICENSE KEY GENERATED")
    print("="*70)
    print(license_key)
    print("="*70)
    print(f"\nLicense saved to: {license_file.absolute()}")
    print("\nLicense file location options:")
    print("  - The same directory as the executable (for PyInstaller builds)")
    print("  - Or the current working directory")
    print("  - Or the user's home directory")
    print(f"\n  Current location: {license_file.absolute()}")
    print("\nLicense details:")
    print(f"  Email: {email}")
    print(f"  Country: {country}")
    print(f"  HWID: {hwid[:20]}..." if not use_wildcard_hfmdd else "  HWID: wildcard (@hfmdd.de any machine)")
    print(f"  Expiration: {expiration_days} days" if expiration_days > 0 else "  Expiration: Never")
    print()


if __name__ == "__main__":
    main()

