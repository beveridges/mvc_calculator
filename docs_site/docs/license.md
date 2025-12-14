# License System

## Overview

   MVC Calculator uses a hardware-locked license system to ensure proper software usage and prevent unauthorized distribution.
---

## Requesting a License

### For @hfmdd.de Users

If you have an `@hfmdd.de` email address:

1. Send an email to **support@moviolabs.com** from your `@hfmdd.de` account
2. Your license will be sent **automatically** via email
3. Follow the [licence installation instructions](#installing-your-licence) below

### For Other Users

1. Go to **Help** → **Request License...** in the application menu
2. Or contact **support@moviolabs.com** with:
   - Your email address
   - Your country code (2-letter ISO, e.g., "US", "CO", "GB")
   - Any special requirements

---

## Installing Your License

### Step 1: Receive License File

You will receive a `license.key` file via email

### Step 2: Place License File

**Recommended Location (Windows)**:
```
%APPDATA%\MVC_Calculator\license.key
```

To find this folder:

   1. Press <kbd>Win</kbd> + <kbd>R</kbd>
   2. Type: `%APPDATA%`
   3. Press <kbd>Enter</kbd>
   4. Navigate to (or create) the `MVC_Calculator` folder
   5. Place `license.key` in this folder

**Alternative Locations** (the application will check these automatically):

   - Same folder as the executable
   - Your home directory
   - Current working directory

### Step 3: Restart Application

Close and restart MVC Calculator. The license will be validated automatically.

---

## License Validation

### Validation Messages

**Success**: The application starts normally - no message needed.

**License Not Found**:
```
License file not found.

Please place license.key in:
C:\Users\YourName\AppData\Roaming\MVC_Calculator\license.key
```

**Hardware Mismatch**:
```
License key is not valid for this machine. 
Hardware ID mismatch.
```

**Country Mismatch**:
```
License key is not valid for this country. 
Expected: CO, Detected: US
```

**Expired License**:
```
License key has expired.
```

---

## Troubleshooting License Issues

### License Not Found

**Problem**: Application says license file not found.

**Solution**:

   1. Verify the file is named exactly `license.key` (not `license.key.txt`)
   2. Check the file is in the correct location (see installation above)
   3. Ensure you have write permissions in the target folder
   4. Try placing the file in the same folder as the executable

### Hardware ID Mismatch

**Problem**: License works on one computer but not another.

**Explanation**: This is expected behavior. Licenses are tied to specific hardware.

**Solution**:

- Request a new license for the new computer
- Provide the Hardware ID (HWID) from the error message if available
- Contact support@moviolabs.com for assistance

### Country Mismatch

**Problem**: License is valid but shows country mismatch error.

**Possible Causes**:

   - Using a VPN that changes your detected country
   - Windows region settings don't match license country
   - License was issued for a different country

**Solution**:

   - Disable VPN if using one
   - Check Windows region settings match your actual location
   - Request a license for your actual country

### License Expired

**Problem**: License was working but now shows as expired.

**Solution**:

   - Contact support@moviolabs.com to renew your license
   - Provide your email address and previous license details

---

## License Transfer

### Can I Move My License?

**Generally No**: Licenses are hardware-locked and cannot be easily transferred.

**Exceptions**:

   - If you get a new computer, request a new license
   - If your hardware changes significantly, contact support
   - For institutional licenses, contact support for transfer options

### What If I Upgrade My Computer?

If you upgrade hardware components:

- **Minor upgrades** (RAM, storage): License should still work
- **Major upgrades** (motherboard, CPU): May require a new license
- **New computer**: Requires a new license

Contact support@moviolabs.com if you're unsure.

---

## Development and Testing

### Development Mode

When running MVC Calculator from source code (not as a compiled executable):

   - **License checking is disabled** by default
   - This allows developers to test without a license
   - Production builds always require a valid license

---

## Support

For license-related issues:

   - **Email**: support@moviolabs.com
   - **Include**: Your email address, error messages, and any relevant details
   - **Response Time**: Typically within 1-2 business days

---

## Technical Details

### Hardware Fingerprint (HWID)

The license system generates a unique hardware ID from:

   - CPU/Motherboard UUID
   - Disk serial number
   - Windows Machine GUID

This ensures the license is tied to your specific computer.

### Country Detection

The system detects your country using:

   - **Primary**: Windows locale/region settings (offline)
   - **Fallback**: IP geolocation API (if offline method fails)

This prevents VPN-based license bypassing.

### License Format

Licenses are base64-encoded and contain:

   - Email address
   - Country code (2-letter ISO)
   - Hardware ID (SHA256 hash)
   - Expiration date (if applicable)
   - Cryptographic signature (HMAC-SHA256)

---

## Frequently Asked Questions

**Q: Can I use my license on multiple computers?**  
A: No, each license is tied to one computer. Contact support for multi-computer licenses.

**Q: What happens if I reinstall Windows?**  
A: Your license should still work as long as the hardware hasn't changed significantly.

**Q: Can I get a refund if the license doesn't work?**  
A: Contact support@moviolabs.com - we'll work with you to resolve any issues.

**Q: How long does a license last?**  
A: Depends on your license type. Some licenses never expire, others have expiration dates.

**Q: Can I share my license with colleagues?**  
A: No, licenses are non-transferable and tied to specific hardware.




