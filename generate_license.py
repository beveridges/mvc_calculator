#!/usr/bin/env python3
"""
License Key Generator for MVC Calculator

Usage:
    python generate_license.py <email> <country> [expiration_days]

Examples:
    python generate_license.py user@example.com CO
    python generate_license.py user@example.com US 365
    python generate_license.py user@example.com GB 0  # No expiration
"""

import sys
from pathlib import Path

# Add utilities to path
sys.path.insert(0, str(Path(__file__).parent))

from utilities.license import generate_license_key, get_machine_id, get_country


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        print("\nUsage: python generate_license.py <email> <country> [expiration_days]")
        print("\nExample: python generate_license.py support@moviolabs.com CO 365")
        sys.exit(1)
    
    email = sys.argv[1]
    country = sys.argv[2].upper()
    
    # Optional expiration (0 = no expiration)
    expiration_days = 0
    if len(sys.argv) > 3:
        try:
            expiration_days = int(sys.argv[3])
        except ValueError:
            print(f"Error: Invalid expiration days: {sys.argv[3]}")
            sys.exit(1)
    
    # Get HWID (for current machine, or user can specify)
    print("Generating license key...")
    print(f"Email: {email}")
    print(f"Country: {country}")
    print(f"Expiration: {expiration_days} days (0 = no expiration)")
    
    # Determine HWID source
    if len(sys.argv) > 4:
        if sys.argv[4] == "--current-machine":
            # Generate for current machine
            hwid = get_machine_id()
            print(f"HWID (current machine): {hwid[:16]}...")
        else:
            # Use provided HWID
            hwid = sys.argv[4]
            print(f"HWID (provided): {hwid[:16]}...")
    else:
        # Default: use current machine (most common case)
        hwid = get_machine_id()
        print(f"HWID (current machine, default): {hwid[:16]}...")
        print("\nNote: To generate for a different machine, provide HWID as 5th argument")
    
    # Generate license key
    license_key = generate_license_key(email, country, hwid, expiration_days)
    
    print("\n" + "="*70)
    print("LICENSE KEY GENERATED")
    print("="*70)
    print(license_key)
    print("="*70)
    print("\nSave this key to a file named 'license.key' and place it in:")
    print("  - The same directory as the executable (for PyInstaller builds)")
    print("  - Or the current working directory")
    print("  - Or the user's home directory")
    print("\nLicense details:")
    print(f"  Email: {email}")
    print(f"  Country: {country}")
    print(f"  HWID: {hwid[:16]}...")
    print(f"  Expiration: {expiration_days} days" if expiration_days > 0 else "  Expiration: Never")
    print()


if __name__ == "__main__":
    main()

