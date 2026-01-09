# MVC Calculator Build Pipeline

## Confirmed Build Process

### 0. In Windows: Make Changes to Spyder Version on Local Machine
- Edit source code in your local repository
- Test changes locally


### 1 In Windows: Build help files
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

### 2. In Windows:  Activate the Conda environment
```bash
conda activate mvccalculator
```

### 3. In Windows: Commit and Push to GitHub
```bash
git add .
git commit -m "Your commit message"
git push
```

### 4. In WSL: Git Pull
```bash
git pull
```
- Updates WSL repository with latest changes from GitHub

### 5. In WSL: activate conda environment 
```bash
conda activate mvccalculator
```

### 6. In Windows: BUILD_ALL_WINDOWS.py 
```bash
python BUILD_ALL_WINDOWS.py
```
**DETAILS**
**Location:** Project root directory  
**What it does:**
- Runs `build_windows_portable.py` (PyInstaller onedir build - increments build number)
- Runs `build_windows_msi.py` (creates MSI installer and portable ZIP)
- **Output location:** `C:\Users\Scott\Documents\.builds\mvc_calculator\MVC_Calculator-{BUILDNUMBER}\`
  - MSI file: `MVC_Calculator-{version}.msi`
  - ZIP file: `MVC_Calculator-{version}-portable.zip`
  - Build artifacts/logs: `MVC_Calculator-{BUILDNUMBER}\buildfiles\`

**Note:** This must be run on Windows (not WSL) because it uses Windows-specific build tools.

### 5. In WSL: BUILD_ALL_LINUX.py 


**Location:** Project root directory (in WSL)  
**What it does:**
- Runs `build_linux_portable.py` (Linux portable build)
- Runs `build_linux_appimage.py` (creates AppImage)
- Runs `build_linux_deb.py` (creates .deb package)
- **Initial output:** `~/.linux_builds/MVC_CALCULATOR/linux_builds/`
- **Final output:** Copies files to Windows directory:
  - `C:\Users\Scott\Documents\.builds\mvc_calculator\MVC_Calculator-{BUILDNUMBER}\`
  - DEB file: `mvc-calculator_{version}_amd64.deb`
  - AppImage: `MVC_Calculator-{version}-x86_64.AppImage`
  - Build artifacts: `MVC_Calculator-{BUILDNUMBER}\buildfiles\`

**Note:** This reads the build number that was incremented by the Windows build, ensuring version consistency.


### 6: Review Before Upload (Optional)

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

































### 6. deploy_release_ftp.py (Run from Windows or WSL)





**Location:** Project root directory  
**What it does:**
- Scans for build files in versioned directories:
  - `C:\Users\Scott\Documents\.builds\mvc_calculator\MVC_Calculator-{version}\`
- Finds all build files (MSI, ZIP, DEB, AppImage) for latest and previous releases
- Reads `RELEASE_NOTES-{version}.txt` from:
  - `MVC_Calculator-{version}\buildfiles\RELEASE_NOTES-{version}.txt` (preferred)
  - Or `C:\Users\Scott\Documents\.builds\mvc_calculator\RELEASE_NOTES-{version}.txt` (fallback)
- Generates `index.html` with:
  - Latest release (n) with all build files
  - Previous release (n-1) with all build files (if exists)
- Uploads to FTP server:
  - **Target:** `ftp.moviolabs.com:/public_html/downloads/MVC_Calculator/releases`
  - Uploads logo, build files, release notes, and index.html
  - **Smart upload:** Skips files that already exist with same size (prevents duplicates)

## File Structure After Build

```
C:\Users\Scott\Documents\.builds\mvc_calculator\
├── MVC_Calculator-25.11-alpha.01.78\          (Latest version)
│   ├── MVC_Calculator-25.11-alpha.01.78.msi
│   ├── MVC_Calculator-25.11-alpha.01.78-portable.zip
│   ├── mvc-calculator_25.11-alpha.01.78_amd64.deb
│   ├── MVC_Calculator-25.11-alpha.01.78-x86_64.AppImage
│   └── buildfiles\
│       ├── RELEASE_NOTES-25.11-alpha.01.78.txt
│       └── (build logs and artifacts)
├── MVC_Calculator-25.11-alpha.01.77\          (Previous version)
│   └── (same structure)
└── index.html                                 (generated by deploy script)
```

## Important Notes

1. **Version Consistency:** The Linux build reads the build number that was incremented by the Windows build, ensuring both platforms use the same version number.

2. **File Locations:** All build files end up in the same versioned directory structure on Windows, making it easy for the deploy script to find them.

3. **Duplicate Prevention:** The deploy script checks existing files on the FTP server and skips uploads if files already exist with the same size.

4. **Release Notes:** The deploy script looks for release notes in the `buildfiles` subdirectory first, then falls back to the base directory.

5. **HTML Generation:** The deploy script only includes the latest (n) and previous (n-1) releases in the generated HTML page.

## Quick Reference Commands

```bash
# Windows (PowerShell/CMD)
python BUILD_ALL_WINDOWS.py

# WSL
python BUILD_ALL_LINUX.py
python deploy_release_ftp.py
```

