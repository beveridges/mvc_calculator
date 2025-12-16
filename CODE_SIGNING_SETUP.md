# Code Signing Setup Guide

## Overview

Code signing prevents the "Windows protected your PC" SmartScreen warning when users download your application. This guide explains how to set it up.

## Why Code Sign?

- **Eliminates SmartScreen warnings** - Users won't see scary warnings
- **Builds trust** - Shows your software is legitimate
- **Professional appearance** - Signed software looks more credible
- **Better user experience** - Users can install without warnings

## Step 1: Get a Code Signing Certificate

### Option A: Purchase from Certificate Authority (Recommended)

**Popular Providers:**
- **DigiCert** - https://www.digicert.com/code-signing/ (~$200-400/year)
- **Sectigo** - https://sectigo.com/ssl-certificates-tls/code-signing (~$200-300/year)
- **GlobalSign** - https://www.globalsign.com/en/code-signing-certificate (~$200-400/year)

**What you'll get:**
- `.pfx` file (certificate + private key)
- Password for the PFX file
- Instructions for installation

### Option B: Free Certificate (Limited)

- **Let's Encrypt** - Free but limited Windows support
- **Self-signed** - Not recommended (users will still see warnings)

## Step 2: Install Windows SDK (for signtool.exe)

The code signing utility requires `signtool.exe` from Windows SDK.

1. Download Windows SDK: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/
2. Install (you only need the "Signing Tools" component)
3. Verify installation:
   ```cmd
   signtool.exe
   ```
   If it's not found, add to PATH or update the path in `utilities/code_signing.py`

## Step 3: Configure Code Signing

Edit `config/code_signing_config.py`:

### Option A: Using PFX File (Recommended)

```python
ENABLE_CODE_SIGNING = True

# PFX file path (use raw string for Windows paths)
CERT_PATH = r"C:\path\to\your\certificate.pfx"
CERT_PASSWORD = "your-pfx-password"

# Leave these as None when using PFX
CERT_THUMBPRINT = None
```

### Option B: Using Windows Certificate Store

1. Install certificate in Windows Certificate Store:
   - Double-click your `.pfx` file
   - Follow the import wizard
   - Store location: **Personal**

2. Find certificate thumbprint:
   - Open `certlm.msc` (Certificate Manager)
   - Navigate to: **Personal** → **Certificates**
   - Double-click your certificate
   - Go to **Details** tab
   - Find **Thumbprint** field
   - Copy the value (remove spaces)

3. Configure:
   ```python
   ENABLE_CODE_SIGNING = True
   
   # Certificate thumbprint from Windows Certificate Store
   CERT_THUMBPRINT = "ABC123DEF456..."  # Your thumbprint here
   
   # Leave these as None when using certificate store
   CERT_PATH = None
   CERT_PASSWORD = None
   ```

### Timestamp Server (Recommended)

The timestamp server prevents signatures from expiring when your certificate expires:

```python
TIMESTAMP_URL = "http://timestamp.digicert.com"  # Default - works well
```

Other options:
- `http://timestamp.sectigo.com` (Sectigo)
- `http://timestamp.globalsign.com/tsa/r6advanced1` (GlobalSign)

## Step 4: Test Code Signing

1. Build your application:
   ```bash
   python BUILD_ALL_WINDOWS.py
   ```

2. Check if files are signed:
   - Right-click the `.exe` or `.msi` file
   - Go to **Properties** → **Digital Signatures** tab
   - You should see your certificate listed

3. Test on a clean Windows machine:
   - Download the signed file
   - You should NOT see SmartScreen warnings

## Troubleshooting

### "signtool.exe not found"
- Install Windows SDK
- Or update the path in `utilities/code_signing.py`

### "Signing failed"
- Check certificate path is correct
- Verify certificate password
- Ensure certificate hasn't expired
- Check certificate has code signing capability

### "Certificate not trusted"
- Make sure you purchased from a trusted CA (DigiCert, Sectigo, etc.)
- Self-signed certificates won't work for SmartScreen

### SmartScreen still shows warning
- **First-time downloads** may still show warnings (this is normal)
- After many downloads, SmartScreen builds reputation
- Users can click "More info" → "Run anyway" the first time
- Subsequent downloads from the same publisher won't show warnings

## Security Notes

⚠️ **Keep your certificate secure!**
- Never commit `.pfx` files or passwords to git
- Store certificates in a secure location
- Use environment variables for passwords in CI/CD
- Consider using Windows Certificate Store (more secure than PFX files)

## What Gets Signed?

- **EXE file** - The main executable (signed after PyInstaller build)
- **MSI installer** - The Windows installer (signed after WiX build)

Both are automatically signed when `ENABLE_CODE_SIGNING = True` in the config file.

## Cost Estimate

- **Certificate**: $200-400/year
- **Windows SDK**: Free
- **Time to set up**: ~30 minutes

## Need Help?

- Check Windows SDK documentation: https://docs.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools
- Certificate provider support (DigiCert, Sectigo, etc.)
- Microsoft SmartScreen: https://docs.microsoft.com/en-us/windows/security/threat-protection/windows-defender-smartscreen/

