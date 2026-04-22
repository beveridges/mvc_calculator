# License Key System for MVC Calculator

## Overview

The MVC Calculator uses a hardware-locked license system that prevents:
- Copying licenses to other machines
- Running in unauthorized countries
- Using VPNs to bypass country restrictions

## How It Works

### 1. Hardware Fingerprint (HWID)
- Generated from: CPU/Motherboard UUID, Disk Serial, Windows Machine GUID
- Unique per machine
- Cannot be easily changed by users

### 2. Country Detection
- **Offline method**: Uses Windows locale/region settings (primary)
- **Online fallback**: IP geolocation API (if offline method fails)
- Prevents VPN bypass by comparing Windows country with IP country

### 3. License Key Format
```
base64(email|country|hwid|expiration|signature)
```

The license key contains:
- **Email**: User's email address
- **Country**: 2-letter ISO code (e.g., "CO", "US", "GB")
- **HWID**: Hardware fingerprint (SHA256 hash)
- **Expiration**: Days until expiration (0 = no expiration)
- **Signature**: HMAC-SHA256 signature for tamper protection

## Generating License Keys

`generate_license.py` now writes timestamped files to keep payload pure while adding an identifier in the filename:

- `license-YYYYMMDDTHHMMSSZ-CLT0002.key`
- Payload remains unchanged: `base64(email|country|hwid|expiration|signature)`

### For Current Machine
```bash
python generate_license.py user@example.com CO 365 --current-machine
```

### For Specific Machine (requires HWID)
```bash
python generate_license.py user@example.com CO 365 <hwid>
```

### Parameters
- `email`: User's email address
- `country`: 2-letter ISO country code (e.g., "CO", "US")
- `expiration_days`: Days until expiration (0 = no expiration)
- `--current-machine`: Use current machine's HWID
- `--wildcard-hfmdd`: Create wildcard key for `@hfmdd.de` (any machine, still country-checked)
- `<hwid>`: Specific hardware ID (optional, 5th argument)

### Examples
```bash
# License for Colombia, expires in 1 year
python generate_license.py user@example.com CO 365 --current-machine

# License for USA, no expiration
python generate_license.py user@example.com US 0 --current-machine

# License for specific machine (requires HWID)
python generate_license.py user@example.com GB 180 abc123def456...

# Wildcard license for @hfmdd.de (any machine in matching country)
python generate_license.py institutional@hfmdd.de DE 0 --wildcard-hfmdd
```

## Installing License Keys

**Recommended Location (Persistent across updates):**
- **Windows**: `%APPDATA%\MVC_Calculator\` (for either `license.key` or `license-YYYYMMDDTHHMMSSZ-<client>.key`)
- **Linux/Mac**: `~/.local/share/MVC_Calculator/` (for either naming format)

The application automatically migrates licenses from old locations to this persistent directory.

When multiple files exist in one directory, selection priority is:
1. exact `license.key`
2. newest timestamped `license-YYYYMMDDTHHMMSSZ-<client>.key` (newest by timestamp in filename)

**Legacy Locations (for backward compatibility):**
The application also checks these locations and will automatically migrate licenses found here:
1. Same directory as the executable (for PyInstaller builds)
2. Current working directory
3. User's home directory

**Note**: The persistent location is recommended because it survives application updates. When you update to a new version, your license will automatically be found in the persistent location.

## Activation (New Schema)

The app now supports activation-code redemption in **Help -> Licence manager**.

High-level flow:
1. User enters activation code
2. App sends code + HWID + country to activation API (`ACTIVATION_API_URL`)
3. API returns a signed `license_key`
4. App stores local entitlement in:
   - **Windows**: `%APPDATA%\MVC_Calculator\entitlement.json`
   - **Linux/Mac**: `~/.local/share/MVC_Calculator/entitlement.json`
5. App validates entitlement locally and enables features

Backward compatibility:
- Existing `license.key` is migrated into `entitlement.json` when possible.

Activation API contract (v1):
- Request JSON:
  - `activation_code`, `hwid`, `country`, `app_version`, `build_number`, `platform`, `timestamp_utc`
- Response JSON:
  - `license_key` (same base64 format described above), optional `email`, optional `message`

Environment variables:
- `ACTIVATION_API_URL`: activation endpoint URL
- `ACTIVATION_HTTP_TIMEOUT_SECONDS`: request timeout (default 8)
- `ACTIVATION_HTTP_RETRIES`: retry count (default 2)

## Preactivated Institutional Distribution (@hfmdd.de)

For institutional deployment, you can bundle a pre-generated entitlement artifact:

1. Generate wildcard key:
   - `python generate_license.py institutional@hfmdd.de DE 0 --wildcard-hfmdd`
2. Build entitlement artifact:
   - `python scripts/build_preactivated_entitlement.py --license-file <generated-license-file> --output preactivated/entitlement.json --issued-for hfmdd.de --bundle-id HFMDD-YYYYMM`
3. Build package with bundled entitlement:
   - Windows: `python BUILD_ALL_WINDOWS.py --preactivated-entitlement preactivated/entitlement.json`
   - Linux: `python BUILD_ALL_LINUX.py --preactivated-entitlement preactivated/entitlement.json`

At runtime, the app auto-installs bundled `preactivated/entitlement.json` into the user-data entitlement path if no local entitlement exists.

Recovery steps:
- If activation is missing after install, reinstall from the institutional package.
- Or manually place a valid `entitlement.json` in:
  - Windows: `%APPDATA%\\MVC_Calculator\\entitlement.json`
  - Linux/Mac: `~/.local/share/MVC_Calculator/entitlement.json`

See `PREACTIVATED_HFMDD_RUNBOOK.md` for operator details.

## License Validation

The application validates the license at startup:
1. **File check**: Ensures a supported license file exists (`license.key` or `license-YYYYMMDDTHHMMSSZ-<client>.key`)
2. **Format check**: Validates base64 encoding and structure
3. **Signature check**: Verifies HMAC signature (prevents tampering)
4. **HWID check**: Compares current machine HWID with license HWID
5. **Country check**: Compares detected country with license country
6. **Expiration check**: Verifies license hasn't expired

### Error Messages

- **"License file not found"**: Place `license.key` or `license-YYYYMMDDTHHMMSSZ-<client>.key` in the correct location
- **"Invalid license key format"**: License file is corrupted or invalid
- **"Invalid license key signature"**: License has been tampered with
- **"Hardware ID mismatch"**: License is for a different machine
- **"Country mismatch"**: License is for a different country
- **"License key has expired"**: License expiration date has passed

## Security Features

### What Users CANNOT Do
- ❌ Copy license to another machine (HWID mismatch)
- ❌ Run in different country (country mismatch)
- ❌ Use VPN to bypass (Windows country vs IP country check)
- ❌ Modify HWID (requires hardware changes)
- ❌ Tamper with license (HMAC signature prevents this)
- ❌ Run on multiple PCs simultaneously (one license = one machine)

### What Users CAN Do
- ✅ Use the application normally on the licensed machine
- ✅ Reinstall the application (HWID doesn't change)
- ✅ Update the application (license persists)

## Development Mode

License checking is **disabled** when running from source code (not frozen).

To test license validation:
1. Set environment variable: `LICENSE_CHECK=1`
2. Or build with PyInstaller (license check is automatic)

## Production Setup

### Important: Change the Secret Key!

Before deploying, **change the `LICENSE_SECRET` in `utilities/license.py`**:

```python
LICENSE_SECRET = b"your_secure_secret_key_here_change_this"
```

Use a strong, random secret key (at least 32 bytes).

### License Generation Server

For production, you should:
1. Create a secure license generation service
2. Store the secret key securely (not in source code)
3. Generate licenses server-side
4. Provide a web interface for customers to request licenses

## Support

For license issues, contact: **support@moviolabs.com**

