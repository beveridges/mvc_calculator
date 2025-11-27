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
- `<hwid>`: Specific hardware ID (optional, 5th argument)

### Examples
```bash
# License for Colombia, expires in 1 year
python generate_license.py user@example.com CO 365 --current-machine

# License for USA, no expiration
python generate_license.py user@example.com US 0 --current-machine

# License for specific machine (requires HWID)
python generate_license.py user@example.com GB 180 abc123def456...
```

## Installing License Keys

**Recommended Location (Persistent across updates):**
- **Windows**: `%APPDATA%\MVC_Calculator\license.key`
- **Linux/Mac**: `~/.local/share/MVC_Calculator/license.key`

The application automatically migrates licenses from old locations to this persistent directory.

**Legacy Locations (for backward compatibility):**
The application also checks these locations and will automatically migrate licenses found here:
1. Same directory as the executable (for PyInstaller builds)
2. Current working directory
3. User's home directory

**Note**: The persistent location is recommended because it survives application updates. When you update to a new version, your license will automatically be found in the persistent location.

## License Validation

The application validates the license at startup:
1. **File check**: Ensures `license.key` exists
2. **Format check**: Validates base64 encoding and structure
3. **Signature check**: Verifies HMAC signature (prevents tampering)
4. **HWID check**: Compares current machine HWID with license HWID
5. **Country check**: Compares detected country with license country
6. **Expiration check**: Verifies license hasn't expired

### Error Messages

- **"License file not found"**: Place `license.key` in the correct location
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

