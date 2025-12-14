# Deploy Release FTP - Command Reference

## Overview

The `deploy_release_ftp.py` script manages uploading MVC Calculator releases and related files to the FTP server. It includes smart upload detection (skips files that already exist with the same size) and supports various upload modes.

## Basic Usage

### Generate HTML Only (No Upload)
```bash
python deploy_release_ftp.py
```
- Scans for build files
- Generates `index.html` locally
- Does NOT upload anything to the server

### Full Upload
```bash
python deploy_release_ftp.py -u
```
- Scans for build files
- Generates `index.html`
- Uploads all files to FTP server:
  - Build files (MSI, ZIP, DEB, AppImage)
  - MaxMSP patch zip
  - Release notes
  - Logo
  - index.html
  - Auxiliary files (track_download.php, etc.)

## Command-Line Flags

### `-u, --upload`
Enable FTP upload. Without this flag, the script only generates HTML locally.

**Example:**
```bash
python deploy_release_ftp.py -u
```

### `--upload-maxmsp-only`
Upload only the MaxMSP patch zip file. Skips all other files (builds, HTML, etc.).

**Requirements:**
- Must be used with `-u/--upload` flag
- Finds the latest MaxMSP zip in versioned directories
- Uses smart upload (skips if file exists with same size) unless `--force` is used

**Example:**
```bash
python deploy_release_ftp.py -u --upload-maxmsp-only
```

**Use Case:**
When you've updated the MaxMSP patch and want to upload just that file without uploading everything else.

### `--force`
Force upload even if file already exists with the same size. This overwrites existing files on the server.

**Example:**
```bash
python deploy_release_ftp.py -u --force
python deploy_release_ftp.py -u --upload-maxmsp-only --force
```

**Use Case:**
- When you need to overwrite a file that exists with the same size
- When you want to ensure the latest version is uploaded regardless of existing files

### `--upload-auxiliary`
Upload auxiliary files (track_download.php, MaxMSP zip, etc.) even when no builds are found.

**Example:**
```bash
python deploy_release_ftp.py -u --upload-auxiliary
```

**Use Case:**
- When you want to update tracking scripts without having build files
- When you want to upload MaxMSP patch without builds

### `--upload-html`
Upload index.html even when no builds are found (if it exists locally).

**Example:**
```bash
python deploy_release_ftp.py -u --upload-html
```

**Use Case:**
- When you've manually edited index.html and want to upload it
- When you want to update the HTML without regenerating it

### `--include-test`
Include test_track_download.php for debugging.

**Example:**
```bash
python deploy_release_ftp.py -u --upload-auxiliary --include-test
```

**Use Case:**
- When debugging download tracking issues
- When you need the test script on the server

## Common Usage Patterns

### Upload Everything (Full Release)
```bash
python deploy_release_ftp.py -u
```
Uploads all build files, MaxMSP patch, release notes, HTML, and auxiliary files.

### Upload Only MaxMSP Patch (Frequently Updated)
```bash
python deploy_release_ftp.py -u --upload-maxmsp-only
```
Quick upload of just the MaxMSP patch zip file. Perfect for frequent updates.

### Force Upload MaxMSP Patch
```bash
python deploy_release_ftp.py -u --upload-maxmsp-only --force
```
Forces upload of MaxMSP patch even if it exists with the same size.

### Update Tracking Scripts Only
```bash
python deploy_release_ftp.py -u --upload-auxiliary
```
Uploads track_download.php and MaxMSP patch without requiring build files.

### Generate HTML and Review Before Upload
```bash
# Step 1: Generate HTML locally
python deploy_release_ftp.py

# Step 2: Review the generated index.html
# (Open in browser, check content, etc.)

# Step 3: Upload when ready
python deploy_release_ftp.py -u
```

## Smart Upload Behavior

By default, the script uses **smart upload**:
- Checks if file exists on server
- Compares file sizes
- **Skips upload** if file exists with same size
- **Uploads** if file doesn't exist or has different size

**Example Output:**
```
⏭️  Skipping MVC_Calculator-25.12-alpha.01.00.msi (already exists, same size: 52428800 bytes)
🔄 Re-uploading index.html (size differs: local=15234, remote=15000)
```

### Override Smart Upload

Use `--force` flag to always upload, even if file exists with same size:
```bash
python deploy_release_ftp.py -u --force
```

## File Locations

### Local Build Directory
```
C:\Users\Scott\Documents\.builds\mvc_calculator\
├── MVC_Calculator-{version}\
│   ├── MVC_Calculator-{version}.msi
│   ├── MVC_Calculator-{version}-portable.zip
│   ├── MuscleMonitor-maxmsp-patch-{version}.zip
│   └── buildfiles\
│       └── RELEASE_NOTES-{version}.txt
└── index.html
```

### FTP Server Location
```
/public_html/downloads/MVC_Calculator/releases/
```

## MaxMSP Patch Upload

The MaxMSP patch zip is automatically:
- Created during normal build process (if dependencies found)
- Uploaded as part of full release upload
- Can be uploaded independently with `--upload-maxmsp-only`

**File Naming:**
- Versioned: `MuscleMonitor-maxmsp-patch-{version}.zip`
- Example: `MuscleMonitor-maxmsp-patch-25.12-alpha.01.00.zip`

**Search Order:**
1. Latest version directory: `MVC_Calculator-{version}/MuscleMonitor-maxmsp-patch-{version}.zip`
2. Any version directory with matching pattern
3. Fallback to old naming convention

## Troubleshooting

### "No builds found"
- Check that build files exist in versioned directories
- Verify file naming matches expected patterns
- Use `--upload-auxiliary` to upload auxiliary files without builds

### "MaxMSP patch zip not found"
- Verify MaxMSP dependencies exist in source directory
- Check that zip was created during build process
- Ensure version directory exists

### File Not Uploading
- Check if file already exists with same size (smart upload skipped it)
- Use `--force` to force upload
- Verify FTP credentials and connection

### Upload Fails
- Check FTP server connectivity
- Verify FTP credentials in script
- Check file permissions
- Review error messages in console output

## Examples

### Example 1: Quick MaxMSP Update
```bash
# You've updated the MaxMSP patch, just upload that
python deploy_release_ftp.py -u --upload-maxmsp-only
```

### Example 2: Full Release with Force
```bash
# Force upload everything (overwrites existing files)
python deploy_release_ftp.py -u --force
```

### Example 3: Update Tracking Script
```bash
# Update PHP tracking script without builds
python deploy_release_ftp.py -u --upload-auxiliary
```

### Example 4: Review Before Upload
```bash
# Generate HTML
python deploy_release_ftp.py

# Review index.html, then upload
python deploy_release_ftp.py -u
```

## Flag Combinations

| Flags | Behavior |
|-------|----------|
| `-u` | Full upload (all files) |
| `-u --upload-maxmsp-only` | Upload only MaxMSP patch |
| `-u --force` | Full upload, overwrite existing |
| `-u --upload-maxmsp-only --force` | Upload MaxMSP patch, overwrite existing |
| `-u --upload-auxiliary` | Upload auxiliary files (no builds required) |
| `-u --upload-html` | Upload HTML even without builds |
| `-u --upload-auxiliary --include-test` | Upload auxiliary files + test script |

## Notes

- The script automatically finds the latest version directory
- MaxMSP patch is included in both release uploads and auxiliary uploads
- Smart upload prevents duplicate uploads (saves time and bandwidth)
- Use `--force` sparingly - only when you need to overwrite existing files
- The `--upload-maxmsp-only` flag is perfect for frequent MaxMSP patch updates

