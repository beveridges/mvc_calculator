# MVC CALCULATOR BUILD PIPELINE - 04 Feb 2026

## Confirmed Build Process

# ----------------------------------
### 0. In Windows: Make Changes to Spyder Version on Local Machine
- Edit source code in your local repository
- Test changes locally


# ----------------------------------
### 1. In Windows:  Activate the Conda environment
```bash
conda activate mvccalculator
```

# ----------------------------------
### 2 In Windows: Build help files
Navigate to the `docs_site` directory and run:

```bash
cd docs_site
mkdocs build
```
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

# ----------------------------------
### 3. In Windows: BUILD_ALL_WINDOWS.py 
```bash
  python BUILD_ALL_WINDOWS.py           # Licensed only
  python BUILD_ALL_WINDOWS.py -oa       # Licensed + Open Access
```
**DETAILS**
**Location:** Project root directory  
**What it does:**
- Runs `build_windows_portable.py` (PyInstaller onedir build - increments build number)
- Runs `build_windows_msi.py` (creates MSI installer and portable ZIP)
- **With -oa:** Also builds Open Access (license-free) version: portable + MSI + ZIP
**Output location:** `C:\Users\Scott\Documents\.builds\mvc_calculator\`
  - Licensed: `MVC_Calculator-{version}\` — MSI, portable ZIP, buildfiles
  - Open Access (when -oa): `MVC_Calculator-oa-{version}\` — `MVC_Calculator-oa-{version}.msi`, `MVC_Calculator-oa-{version}-portable.zip`
**Note:** This must be run on Windows (not WSL) because it uses Windows-specific build 
tools.

# ----------------------------------
### 4. In Windows: Commit and Push to GitHub -> this is for WSL to pull
```bash
git add .
git commit -m "Your commit message"
git push
```

# ----------------------------------
### 5. In WSL: activate conda environment 
```bash
conda activate mvccalculator
```

# ----------------------------------
### 6. In WSL: Git Pull
- Updates WSL repository with latest changes from GitHub.  Especially THE VERSION INFORMATION
```bash
git pull
```

# ----------------------------------
### 7. In WSL: BUILD_ALL_LINUX.py 

```bash
python BUILD_ALL_LINUX.py           # Licensed only
python BUILD_ALL_LINUX.py -oa       # Licensed + Open Access
```

**Location:** Project root directory (in WSL)  
**What it does:**
- Runs `build_linux_portable.py` (Linux portable build)
- Runs `build_linux_appimage.py` (creates AppImage)
- Runs `build_linux_deb.py` (creates .deb package)
- **With -oa:** Also builds OA portable, AppImage, and DEB
**Initial output:** `~/.linux_builds/MVC_CALCULATOR/linux_builds/`
**Final output:** Copies files to Windows directory:
  - Licensed: `MVC_Calculator-{BUILDNUMBER}\` — DEB, AppImage, buildfiles
  - Open Access (when -oa): `MVC_Calculator-oa-{BUILDNUMBER}\` — `mvc-calculator-oa_{version}_amd64.deb`, `MVC_Calculator-oa-{version}-x86_64.AppImage`
**Note:** This reads the build number that was incremented by the Windows build, ensuring version consistency.

# ----------------------------------
### 8: Review Before Upload (Optional)

Generate the HTML page locally to review:

```bash
python deploy_release_ftp.py
```

This creates `index.html` in the build directory without uploading anything.

# ----------------------------------
#### Step 9: Deploy to Server

Upload everything to the FTP server:

```bash
python deploy_release_ftp.py -u
```

**Location:** Project root directory  
**What it does:**
- Scans for build files in versioned directories:
  - `C:\Users\Scott\Documents\.builds\mvc_calculator\MVC_Calculator-{version}\`
- Finds all build files (MSI, ZIP, DEB, AppImage) for latest, previous, and Open Access releases
- Reads `RELEASE_NOTES-{version}.txt` from:
  - `MVC_Calculator-{version}\buildfiles\RELEASE_NOTES-{version}.txt` (preferred)
  - Or `C:\Users\Scott\Documents\.builds\mvc_calculator\RELEASE_NOTES-{version}.txt` (fallback)
- Generates `index.html` with:
  - Latest release (n) with all build files
  - Previous release (n-1) with all build files (if exists)
  - Open Access section (if OA builds exist)
- Uploads to FTP server:
  - **Target:** `ftp.moviolabs.com:/public_html/downloads/MVC_Calculator/releases`
  - Uploads logo, build files, release notes, and index.html
  - **Smart upload:** Skips files that already exist with same size (prevents duplicates)

  **What gets uploaded:**
- MSI installer (Windows)
- Portable ZIP (Windows)
- DEB package (Linux, if built)
- AppImage (Linux, if built)
- Open Access builds (MSI, ZIP, DEB, AppImage with -oa suffix, if built)
- MaxMSP patch zip
- Release notes (if present)
- `index.html` (auto-generated)
- Logo files
- Tracking scripts (`track_download.php`)
**Smart Upload Behavior:**
- Files are only uploaded if they don't exist or have different sizes
- Use `--force` flag to overwrite existing files: `python deploy_release_ftp.py -u --force`

## File Structure After Build

```
C:\Users\Scott\Documents\.builds\mvc_calculator\
├── MVC_Calculator-26.02-alpha.01.03\          (Licensed - latest)
│   ├── MVC_Calculator-26.02-alpha.01.03.msi
│   ├── MVC_Calculator-26.02-alpha.01.03-portable.zip
│   ├── mvc-calculator_26.02-alpha.01.03_amd64.deb
│   ├── MVC_Calculator-26.02-alpha.01.03-x86_64.AppImage
│   └── buildfiles\
│       ├── RELEASE_NOTES-26.02-alpha.01.03.txt
│       └── (build logs and artifacts)
├── MVC_Calculator-oa-26.02-alpha.01.03\       (Open Access - same version)
│   ├── MVC_Calculator-oa-26.02-alpha.01.03.msi
│   ├── MVC_Calculator-oa-26.02-alpha.01.03-portable.zip
│   ├── mvc-calculator-oa_26.02-alpha.01.03_amd64.deb
│   ├── MVC_Calculator-oa-26.02-alpha.01.03-x86_64.AppImage
│   └── buildfiles\
├── MVC_Calculator-26.02-alpha.01.02\          (Previous version)
│   └── (same structure)
└── index.html                                 (generated by deploy script)
```

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

## Important Notes

1. **Version Consistency:** The Linux build reads the build number that was incremented by the Windows build, ensuring both platforms use the same version number.

2. **File Locations:** All build files end up in the same versioned directory structure on Windows, making it easy for the deploy script to find them.

3. **Duplicate Prevention:** The deploy script checks existing files on the FTP server and skips uploads if files already exist with the same size.

4. **Release Notes:** The deploy script looks for release notes in the `buildfiles` subdirectory first, then falls back to the base directory.

5. **HTML Generation:** The deploy script includes the latest (n), previous (n-1), and Open Access releases in the generated HTML page.

6. **Open Access (OA) builds:** Use `-oa` with `BUILD_ALL_WINDOWS.py` and `BUILD_ALL_LINUX.py` to also produce license-free builds. OA uses the same version as the licensed build but different filenames (e.g. `MVC_Calculator-oa-26.02-alpha.01.03.msi`).

## Quick Reference Commands

```bash
# Windows (PowerShell/CMD)
python BUILD_ALL_WINDOWS.py           # Licensed only
python BUILD_ALL_WINDOWS.py -oa       # Licensed + Open Access

# WSL
python BUILD_ALL_LINUX.py             # Licensed only
python BUILD_ALL_LINUX.py -oa         # Licensed + Open Access
python deploy_release_ftp.py -u
```

