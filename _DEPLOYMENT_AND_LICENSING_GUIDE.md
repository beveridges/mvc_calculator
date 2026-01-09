# Deployment and Licensing Guide

## Overview

This guide consolidates the procedures for deploying releases to the server and creating/issuing licenses for users. It serves as a quick reference reminder for these processes.

## Part 1: Deploying Releases to Server

### Prerequisites

- Build files must exist in: `C:\Users\Scott\Documents\.builds\mvc_calculator\MVC_Calculator-{version}\`
- FTP credentials configured in `deploy_release_ftp.py`

### Step-by-Step Deployment Process
--------------------------------------------------------------------------------------------------------------
#### STEP 1: Modify application and help files if modified.

Navigate to the `docs_site` directory and run:

```bash
cd docs_site
mkdocs build
```
### Previewing the Documentation

To preview the documentation locally (with live reload):

```bash
mkdocs serve -f docs_site/mkdocs.yml
```

Or from the `docs_site` directory:

```bash
cd docs_site
mkdocs serve
```
Then open your browser to: `http://127.0.0.1:8000`
--------------------------------------------------------------------------------------------------------------

#### Step 2: Build Your Release

First, create the build files (if not already done):

```bash
# Build Windows versions
python BUILD_ALL_WINDOWS.py

# Optionally build Linux versions (in WSL)
python BUILD_ALL_LINUX.py
```

#### Step 3: Review Before Upload (Optional)

Generate the HTML page locally to review:

```bash
python deploy_release_ftp.py
```

This creates `index.html` in the build directory without uploading anything.

#### Step 3: Deploy to Server

Upload everything to the FTP server:

```bash
python deploy_release_ftp.py -u
```

**What gets uploaded:**

- MSI installer (Windows)
- Portable ZIP (Windows)
- DEB package (Linux, if built)
- AppImage (Linux, if built)
- MaxMSP patch zip
- Release notes (if present)
- `index.html` (auto-generated)
- Logo files
- Tracking scripts (`track_download.php`)

**Smart Upload Behavior:**

- Files are only uploaded if they don't exist or have different sizes
- Use `--force` flag to overwrite existing files: `python deploy_release_ftp.py -u --force`

#### Common Deployment Options

**Upload only MaxMSP patch:**

```bash
python deploy_release_ftp.py -u --upload-maxmsp-only
```

**Upload auxiliary files without builds:**

```bash
python deploy_release_ftp.py -u --upload-auxiliary
```

**Force upload everything:**

```bash
python deploy_release_ftp.py -u --force
```

### Server Location

Files are uploaded to:

```
ftp.moviolabs.com:/public_html/downloads/MVC_Calculator/releases/
```

## Part 2: Creating and Issuing Licenses

### Understanding the License System

**License Characteristics:**

- Each license is **hardware-locked** to a specific machine (HWID)
- Each license is tied to a specific **email address** and **country**
- Licenses can have an **expiration date** or be **perpetual** (0 days)
- Licenses work for **any release version** - they're not tied to a specific build

**Important:** You can generate as many licenses as needed for a release. Licenses are independent of release versions, so:

✅ **YES, you can have 2 (or more) licenses for one release** - Each license would typically be for a different user/machine. You can generate multiple licenses as needed.

### License Generation Methods

#### Method 1: Generate for Current Machine

If the user's machine is available, generate a license directly:

```bash
python generate_license.py <email> <country> [expiration_days] --current-machine
```

**Examples:**

```bash
# License for Colombia, expires in 1 year
python generate_license.py user@example.com CO 365 --current-machine

# License for USA, no expiration (perpetual)
python generate_license.py user@example.com US 0 --current-machine

# License for Germany, expires in 180 days
python generate_license.py user@example.com DE 180 --current-machine
```

#### Method 2: Generate for Specific Machine (with HWID)

If you have the user's Hardware ID (HWID), generate a license for that machine:

```bash
python generate_license.py <email> <country> [expiration_days] <hwid>
```

**Example:**

```bash
python generate_license.py user@example.com GB 365 abc123def456...
```

**Getting the HWID:**

- Ask the user to run the application (it will show an error with their HWID if license is missing)
- Or use a separate tool/script to collect HWID from the user

#### Method 3: Auto-License for @hfmdd.de Users

For special `@hfmdd.de` email addresses, there's an automated system:

1. **Start the auto-license service:**
   ```bash
   python scripts/run_auto_license_service.py
   ```

2. The service monitors `support@moviolabs.com` inbox

3. When an email arrives from an `@hfmdd.de` address:
   - License is automatically generated with wildcard HWID (works on any machine)
   - License is sent via email to the user
   - Email is processed and moved to processed folder

**Configuration:** Edit `scripts/auto_license_config.py` to configure:
- Email server settings
- Default country code
- Default expiration days
- Processing behavior

### License Generation Parameters

**Required:**

- `email`: User's email address (must match exactly)
- `country`: 2-letter ISO country code (e.g., "US", "CO", "GB", "DE")

**Optional:**

- `expiration_days`: Number of days until expiration (default: 0 = no expiration/perpetual)
- `hwid` or `--current-machine`: Hardware ID or flag to use current machine

### Sending Licenses to Users

**Manual Process:**

1. Generate the license key using `generate_license.py`
2. Copy the license key that's printed
3. Send it to the user via email or secure channel
4. Provide installation instructions (see below)

**Installation Instructions for Users:**

Save the license key to a file named `license.key` and place it in one of these locations:

**Windows:**
- `%APPDATA%\MVC_Calculator\license.key` (recommended - persists across updates)
- Same folder as the executable

**Linux/Mac:**
- `~/.local/share/MVC_Calculator/license.key` (recommended - persists across updates)
- Same folder as the executable

### Special License Types

#### Wildcard Licenses (for @hfmdd.de only)

These licenses work on any machine but only for `@hfmdd.de` email addresses. Generated automatically by the auto-license service.

#### Country-Specific Licenses

Each license is locked to a specific country code. The application checks:
- Windows locale/region settings (primary method)
- IP geolocation API (fallback if offline method fails)

This prevents users from using VPNs to bypass country restrictions.

### License Validation

When the application starts, it validates:

1. ✅ License file exists
2. ✅ License format is valid (base64)
3. ✅ HMAC signature is valid (prevents tampering)
4. ✅ Hardware ID matches current machine
5. ✅ Country matches detected country
6. ✅ License hasn't expired (if expiration set)

### Multiple Licenses Per Release

**Answer: YES, you can have 2 or more licenses for one release.**

**Common scenarios:**

- **Different users:** Generate separate licenses for each user (different email addresses)
- **Same user, different machines:** Generate separate licenses with different HWIDs
- **Trial licenses:** Generate time-limited licenses (e.g., 30 days) for trial users
- **Permanent licenses:** Generate perpetual licenses (0 expiration) for paid users

**Important Notes:**

- Each license is tied to one machine (one HWID)
- Licenses are not tied to specific release versions - they work across all versions
- You can generate licenses before or after a release is deployed
- There's no limit on the number of licenses you can generate

### Workflow Example: Deploy Release + Issue Licenses

```bash
# 1. Build the release
python BUILD_ALL_WINDOWS.py

# 2. Deploy to server
python deploy_release_ftp.py -u

# 3. Generate licenses for users
python generate_license.py user1@example.com CO 365 --current-machine
python generate_license.py user2@example.com US 0 --current-machine

# 4. Send license keys to users via email
```

## Troubleshooting

### Deployment Issues

**"No builds found"**

- Verify build files exist in `C:\Users\Scott\Documents\.builds\mvc_calculator\MVC_Calculator-{version}\`
- Check file naming matches expected patterns

**"FTP connection failed"**

- Verify FTP credentials in `deploy_release_ftp.py`
- Check network connectivity
- Verify server is accessible

### License Issues

**"License file not found"**

- User needs to place `license.key` in the correct location
- Provide clear installation instructions

**"Hardware ID mismatch"**

- License was generated for a different machine
- Generate a new license with the correct HWID
- Or have user send their HWID (shown in error message)

**"Country mismatch"**

- License country doesn't match user's location
- Generate a new license with the correct country code

## Quick Reference

### Deployment Commands

```bash
# Preview (no upload)
python deploy_release_ftp.py

# Full upload
python deploy_release_ftp.py -u

# Force upload (overwrite)
python deploy_release_ftp.py -u --force

# Upload MaxMSP patch only
python deploy_release_ftp.py -u --upload-maxmsp-only
```

### License Generation Commands

```bash
# For current machine
python generate_license.py email@example.com CO 365 --current-machine

# For specific HWID
python generate_license.py email@example.com US 0 <hwid>

# Perpetual license
python generate_license.py email@example.com GB 0 --current-machine
```

## Files Reference

- **Deployment script:** `deploy_release_ftp.py`
- **License generator:** `generate_license.py`
- **License utilities:** `utilities/license.py`
- **Auto-license service:** `scripts/auto_license_email_handler.py`
- **Auto-license config:** `scripts/auto_license_config.py`
- **Documentation:**
  - `DEPLOY_INSTRUCTIONS.md` - Detailed deployment options
  - `LICENSE_SYSTEM_README.md` - License system details
  - `BUILD_STEPS.md` - Build process overview

