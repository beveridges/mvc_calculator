#!/usr/bin/env python3
"""
FTP Deployment Script for MVC Calculator Releases

Usage:
    # Generate index.html only (no upload)
    python deploy_release_ftp.py
    
    # Upload files to FTP server
    python deploy_release_ftp.py -u
    python deploy_release_ftp.py --upload
"""

import re
import argparse
import ftplib
import zipfile
from pathlib import Path
from datetime import datetime

# Optional import for progress bar
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


BUILD_BASE = Path.home() / "Documents/.builds/mvc_calculator"
NOTES_DIR = BUILD_BASE

TEMPLATE  = Path(__file__).parent / "TEMPLATE_RELEASE.html"
OUTPUT    = BUILD_BASE / "index.html"

# FTP Configuration (hardcoded)
TARGET_DIR = "/public_html/downloads/MVC_Calculator/releases"
DEFAULT_HOST = "ftp.moviolabs.com"
DEFAULT_USER = "moviolab"
DEFAULT_PASS = "xTQSz1g,n2we"

# MaxMSP Patch Configuration
# Path to the MaxPatches directory containing MuscleMonitor.maxpat
MAXPATCHES_SOURCE = Path.home() / "Dropbox/__PROJECTS__/.AUGMENTED_FEEDBACK_DRUMMERS/AUGMENTED_FEEDBACK_DRUMMERS/MaxPatches"

def find_logo_path():
    """Use icon.png from project resources/icons for the release HTML. Copy to BUILD_BASE if needed."""
    import shutil

    resources_dir = Path(__file__).parent / "resources" / "icons"
    source_logo = resources_dir / "icon.png"
    dest_logo = BUILD_BASE / "icon.png"

    if source_logo.exists():
        shutil.copy2(source_logo, dest_logo)
    return "icon.png"

PATTERNS = [
    "MVC_Calculator-*-alpha.*.msi",
    "MVC_Calculator-*-alpha.*-portable.zip",
    "mvc-calculator_*_amd64.deb",
    "MVC_Calculator-*-alpha.*-x86_64.AppImage",
    "MuscleMonitor-maxmsp-patch-*-alpha.*.zip",
]
OA_PATTERNS = [
    "MVC_Calculator-oa-*-alpha.*.msi",
    "MVC_Calculator-oa-*-alpha.*-portable.zip",
    "mvc-calculator-oa_*_amd64.deb",
    "MVC_Calculator-oa-*-alpha.*-x86_64.AppImage",
]

VERSION_RE = re.compile(r"(\d{2}\.\d{2}-alpha\.\d{2}\.\d{2})")


def parse_version(name: str):
    m = VERSION_RE.search(name)
    return m.group(1) if m else None


def load_notes(version: str, oa: bool = False):
    notes = {
        "date": "",
        "description": "",
        "whats_new": [],
        "bug_fixes": [],
        "tags": [],
    }

    # Look for release notes (same format: Date:, Description:, What's New, Bug Fixes, Tags:)
    # 1) versioned dir buildfiles: MVC_Calculator-{version}/buildfiles/RELEASE_NOTES-{version}.txt
    # 2) build base (OA only): RELEASE_NOTES-oa-{version}.txt — check before generic so OA-specific wins
    # 3) build base: RELEASE_NOTES-{version}.txt
    # 4) build base: text file named like the directory, e.g. MVC_Calculator-26.02-alpha.01.03.txt
    dir_prefix = f"MVC_Calculator-oa-{version}" if oa else f"MVC_Calculator-{version}"
    version_dir = BUILD_BASE / dir_prefix
    notes_file = version_dir / "buildfiles" / f"RELEASE_NOTES-{version}.txt"

    if not notes_file.exists() and oa:
        notes_file = BUILD_BASE / f"RELEASE_NOTES-oa-{version}.txt"
    if not notes_file.exists():
        notes_file = BUILD_BASE / f"RELEASE_NOTES-{version}.txt"
    if not notes_file.exists():
        notes_file = BUILD_BASE / f"{dir_prefix}.txt"

    if not notes_file.exists():
        return notes

    content = notes_file.read_text(encoding="utf-8")
    
    # Find section markers first
    # Prefer matching header with colon so ":" is not left as a line in the section content
    whats_new_match = re.search(r'(?i)(?:^|\n)\s*(?:what\'?s\s+new:|\[?what\'?s\s+new\]?)\s*\n?', content)
    bug_fixes_match = re.search(r'(?i)(?:^|\n)\s*(?:bug\s+fixes:|\[?bug\s+fixes\]?)\s*\n?', content)
    
    # Find where description section ends (before WHAT'S NEW or BUG FIXES)
    desc_end_idx = len(content)
    if whats_new_match:
        desc_end_idx = min(desc_end_idx, whats_new_match.start())
    if bug_fixes_match:
        desc_end_idx = min(desc_end_idx, bug_fixes_match.start())
    
    # Extract metadata from top of file
    lines = content.splitlines()
    in_description = False
    description_lines = []
    skip_next_line = False  # Flag to skip line after TAGS: if tags are on next line
    
    for i, line in enumerate(lines):
        if skip_next_line:
            skip_next_line = False
            continue
            
        s = line.strip()
        
        if s.lower().startswith("date:"):
            notes["date"] = s.split(":", 1)[1].strip()
        elif s.lower().startswith("tags:"):
            # Tags might be on the same line or the next line(s)
            tags_str = s.split(":", 1)[1].strip()
            if not tags_str:
                # Tags are on the next line(s) - skip blank lines
                for j in range(i + 1, len(lines)):
                    next_line = lines[j].strip()
                    if next_line:  # Found first non-empty line
                        tags_str = next_line
                        skip_next_line = True  # Skip this line in next iteration
                        break
            if tags_str:
                # Strip quotes and whitespace from tags
                notes["tags"] = [t.strip().strip('"\'').strip() for t in tags_str.split(",") if t.strip()]
        elif s.lower().startswith("description:"):
            # Get description text after the colon on this line
            desc_text = s.split(":", 1)[1].strip() if ":" in s else ""
            if desc_text:
                description_lines.append(desc_text)
            in_description = True
        elif in_description:
            # Check if we've hit a section marker
            if any(marker in s.upper() for marker in ["WHAT'S NEW", "BUG FIXES", "[WHAT'S", "[BUG"]):
                in_description = False
            elif s:  # Only add non-empty lines
                description_lines.append(s)
    
    # Join description lines with spaces
    notes["description"] = " ".join(description_lines).strip()
    
    # Extract WHAT'S NEW and BUG FIXES sections
    if whats_new_match:
        start_idx = whats_new_match.end()
        if bug_fixes_match and bug_fixes_match.start() > start_idx:
            # Extract what's new section
            whats_new_text = content[start_idx:bug_fixes_match.start()].strip()
            bug_fixes_text = content[bug_fixes_match.end():].strip()
        else:
            whats_new_text = content[start_idx:].strip()
            bug_fixes_text = ""
        
        # Extract items from what's new (bullets "- item" or plain lines); skip empty or colon-only
        for line in whats_new_text.splitlines():
            s = line.strip()
            if not s or s == ":":
                continue
            item = s[1:].strip() if s.startswith("-") else s
            if item:
                notes["whats_new"].append(item)
        
        # Extract items from bug fixes (bullets "- item" or plain lines); skip empty or colon-only
        for line in bug_fixes_text.splitlines():
            s = line.strip()
            if not s or s == ":":
                continue
            item = s[1:].strip() if s.startswith("-") else s
            if item:
                notes["bug_fixes"].append(item)
    else:
        # Fallback: line-by-line parsing for WHAT'S NEW and BUG FIXES
        section = None
        for line in lines:
            s = line.strip()
            
            if s.lower() in ["[what's new]", "what's new:", "what's new"]:
                section = "new"
            elif s.lower() in ["[bug fixes]", "bug fixes:", "bug fixes"]:
                section = "bug"
            elif section == "new" and s and s != ":":
                item = s[1:].strip() if s.startswith("-") else s
                if item:
                    notes["whats_new"].append(item)
            elif section == "bug" and s and s != ":":
                item = s[1:].strip() if s.startswith("-") else s
                if item:
                    notes["bug_fixes"].append(item)

    notes["description"] = notes["description"].strip()
    return notes


def make_li_list(items):
    if not items:
        return ""
    return "\n            ".join(f"<li>{i}</li>" for i in items)


def format_tag_display(tag: str) -> str:
    """Format tag for display. 'new-release' displays as 'NEW RELEASE' in all caps."""
    normalized = normalize_tag_name(tag)
    if normalized == "new-release":
        return "NEW RELEASE"
    return tag  # Display original tag text


def normalize_tag_name(tag: str) -> str:
    """
    Normalize tag names to match predefined CSS classes.
    Predefined tags: api, security, performance, bugfix, feature, 
                     ui, documentation, breaking, enhancement, testing, new-release
    """
    tag_lower = tag.lower().strip()
    
    # Mapping of common variations to normalized tag names
    tag_map = {
        # API variations
        "api": "api",
        
        # Security variations
        "security": "security",
        "sec": "security",
        
        # Performance variations
        "performance": "performance",
        "perf": "performance",
        
        # Bug fix variations
        "bugfix": "bugfix",
        "bug fix": "bugfix",
        "bug-fix": "bugfix",
        "bugs": "bugfix",
        "bug": "bugfix",
        
        # Feature variations
        "feature": "feature",
        "features": "feature",
        "new feature": "feature",
        
        # UI variations
        "ui": "ui",
        "ui/ux": "ui",
        "ux": "ui",
        "user interface": "ui",
        "interface": "ui",
        
        # Documentation variations
        "documentation": "documentation",
        "docs": "documentation",
        "doc": "documentation",
        
        # Breaking change variations
        "breaking": "breaking",
        "breaking change": "breaking",
        "breaking-change": "breaking",
        "breaking changes": "breaking",
        
        # Enhancement variations
        "enhancement": "enhancement",
        "enhancements": "enhancement",
        "improvement": "enhancement",
        "improvements": "enhancement",
        
        # Testing variations
        "testing": "testing",
        "system testing": "testing",
        "system-testing": "testing",
        "test": "testing",
        
        # New Release variations
        "new release": "new-release",
        "new-release": "new-release",
        "new_release": "new-release",
        "newrelease": "new-release",
        "release": "new-release",
    }
    
    # Check direct match first
    if tag_lower in tag_map:
        return tag_map[tag_lower]
    
    # Check if tag contains any of the keywords
    for key, normalized in tag_map.items():
        if key in tag_lower:
            return normalized
    
    # Default: return lowercase version (will use default styling if CSS class doesn't exist)
    # Replace underscores, spaces, and slashes with hyphens
    return tag_lower.replace("_", "-").replace(" ", "-").replace("/", "-")


def scan_builds():
    """Scan versioned directories for build files."""
    all_files = []
    
    # Scan all versioned directories (MVC_Calculator-XX.XX-alpha.XX.XX), exclude OA dirs
    if BUILD_BASE.exists():
        for version_dir in BUILD_BASE.iterdir():
            if version_dir.is_dir() and version_dir.name.startswith("MVC_Calculator-"):
                if version_dir.name.startswith("MVC_Calculator-oa-"):
                    continue  # OA dirs handled by scan_oa_builds()
                for pat in PATTERNS:
                    all_files.extend(version_dir.glob(pat))
        
        # Fallback: also check old locations for backwards compatibility
        # Check old MSI builds location
        old_msi_dir = BUILD_BASE / "msi" / "builds"
        if old_msi_dir.exists():
            for pat in PATTERNS:
                all_files.extend(old_msi_dir.glob(pat))
        
        # Check base directory for Linux builds (old location)
        for pat in PATTERNS:
            all_files.extend(BUILD_BASE.glob(pat))

    versions = {}
    for f in all_files:
        v = parse_version(f.name)
        if v:
            versions.setdefault(v, []).append(f)

    return versions


def scan_oa_builds():
    """Scan for Development Release builds. Returns (version, files) for latest OA or (None, [])."""
    if not BUILD_BASE.exists():
        return None, []
    oa_dirs = [d for d in BUILD_BASE.iterdir() if d.is_dir() and d.name.startswith("MVC_Calculator-oa-")]
    if not oa_dirs:
        return None, []
    # Extract version from dir name: MVC_Calculator-oa-26.02-alpha.01.03
    def get_oa_version(d):
        rest = d.name.replace("MVC_Calculator-oa-", "")
        m = VERSION_RE.search(rest)
        return m.group(1) if m else ""
    valid = [(d, get_oa_version(d)) for d in oa_dirs if get_oa_version(d)]
    if not valid:
        return None, []
    # Sort by version descending, take latest
    valid.sort(key=lambda x: x[1], reverse=True)
    latest_dir, latest_version = valid[0]
    all_files = []
    for pat in OA_PATTERNS:
        all_files.extend(latest_dir.glob(pat))
    return latest_version, all_files


def detect_description(filename: str):
    fn = filename.lower()
    if fn.endswith(".msi"): return "Windows installer"
    if "maxmsp" in fn and fn.endswith(".zip"): return "MaxMSP patch and dependencies"
    if fn.endswith(".zip"): return "Portable ZIP build"
    if fn.endswith(".deb"): return "Linux .deb package"
    if fn.endswith(".appimage"): return "Linux AppImage"
    return "Build File"


def get_file_sort_priority(filename: str) -> tuple[int, str]:
    """Get sort priority for files to group by platform.
    Returns (priority, filename) where lower priority = appears first.
    Priority order:
    1. Windows MSI
    2. Windows ZIP (portable)
    3. Linux DEB
    4. Linux AppImage
    5. MaxMSP zip
    6. Other files
    """
    fn = filename.lower()
    if fn.endswith(".msi"):
        return (1, filename)  # Windows MSI first
    elif fn.endswith(".zip") and "portable" in fn:
        return (2, filename)  # Windows ZIP second
    elif fn.endswith(".deb"):
        return (3, filename)  # Linux DEB third
    elif fn.endswith(".appimage"):
        return (4, filename)  # Linux AppImage fourth
    elif "maxmsp" in fn and fn.endswith(".zip"):
        return (5, filename)  # MaxMSP zip fifth
    else:
        return (6, filename)  # Other files last


def build_table(files):
    rows = []
    # Sort files: Windows files together, Linux files together
    sorted_files = sorted(files, key=lambda x: get_file_sort_priority(x.name))
    
    for f in sorted_files:
        size_bytes = f.stat().st_size
        if size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.0f}K"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.0f}M"
        mod = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        desc = detect_description(f.name)

        # Use just filename for href (files uploaded to root of releases directory)
        href = f.name

        rows.append(
            "<tr>"
            f"<td><a class='file-link' href='{href}' download>{f.name}</a></td>"
            f"<td class='date-col'>{mod}</td>"
            f"<td class='size-col'>{size_str}</td>"
            f"<td class='desc-col'>{desc}</td>"
            "</tr>"
        )

    return (
        "<table>"
        "<thead><tr>"
        "<th>Name</th><th>Last Modified</th><th>Size</th><th>Description</th>"
        "</tr></thead>"
        "<tbody>"
        + "\n".join(rows) +
        "</tbody></table>"
    )


def upload_file(ftp: ftplib.FTP, path: Path):
    """Upload file to FTP with progress bar (if tqdm is available)."""
    total = path.stat().st_size
    
    if HAS_TQDM:
        bar = tqdm(total=total, unit="B", unit_scale=True, desc=f"Uploading {path.name}")
        
        def callback(chunk):
            bar.update(len(chunk))
        
        with path.open("rb") as f:
            ftp.storbinary(f"STOR {path.name}", f, 8192, callback)
        
        bar.close()
    else:
        # Fallback: upload without progress bar
        print(f"  Uploading {path.name} ({total / (1024*1024):.1f} MB)...")
        with path.open("rb") as f:
            ftp.storbinary(f"STOR {path.name}", f, 8192)
        print(f"  ✓ Uploaded: {path.name}")


def ensure_dir(ftp: ftplib.FTP, remote: str):
    """Ensure remote directory exists, creating it if necessary."""
    parts = remote.strip("/").split("/")
    for i in range(1, len(parts) + 1):
        sub = "/" + "/".join(parts[:i])
        try:
            ftp.cwd(sub)
        except ftplib.error_perm:
            ftp.mkd(sub)
            ftp.cwd(sub)


def get_existing_files(ftp: ftplib.FTP) -> dict[str, int]:
    """Get list of existing files on FTP server with their sizes.
    Returns dict mapping filename -> file_size_in_bytes."""
    existing = {}
    try:
        files = ftp.nlst()
        for filename in files:
            try:
                size = ftp.size(filename)
                if size is not None:
                    existing[filename] = size
            except ftplib.error_perm:
                # File might not exist or might be a directory, skip
                pass
    except Exception as e:
        print(f"⚠️  Warning: Could not list existing files: {e}")
    return existing


def should_upload_file(ftp: ftplib.FTP, path: Path, existing_files: dict[str, int], force: bool = False) -> bool:
    """Check if file should be uploaded (skip if exists with same size, unless force=True)."""
    if force:
        return True
    
    filename = path.name
    local_size = path.stat().st_size
    
    if filename in existing_files:
        remote_size = existing_files[filename]
        if local_size == remote_size:
            print(f"  ⏭️  Skipping {filename} (already exists, same size: {local_size} bytes)")
            return False
        else:
            print(f"  🔄 Re-uploading {filename} (size differs: local={local_size}, remote={remote_size})")
            return True
    
    return True


def check_maxmsp_dependencies() -> tuple[bool, list[str], dict[str, Path]]:
    """
    Check for all required MaxMSP patch dependencies.
    Returns: (all_found, missing_files, found_files_dict)
    """
    required_files = {
        # Main patch
        "MuscleMonitor.maxpat": MAXPATCHES_SOURCE / "MuscleMonitor.maxpat",
        
        # JavaScript files
        "xml_reader.js": MAXPATCHES_SOURCE / "xml_reader.js",
        "filternans": MAXPATCHES_SOURCE / "filternans",
    }
    
    missing = []
    found = {}
    
    for rel_path, full_path in required_files.items():
        if full_path.exists():
            found[rel_path] = full_path
        else:
            missing.append(rel_path)
    
    all_found = len(missing) == 0
    return all_found, missing, found


def create_maxmsp_zip(output_path: Path, found_files: dict[str, Path]) -> bool:
    """
    Create a zip file containing the MaxMSP patch and all dependencies.
    Returns True if successful, False otherwise.
    """
    try:
        print(f"\n📦 Creating MaxMSP patch zip file: {output_path.name}")
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for rel_path, full_path in found_files.items():
                # Add file to zip preserving directory structure
                zipf.write(full_path, rel_path)
                print(f"  ✓ Added: {rel_path}")
        
        zip_size = output_path.stat().st_size
        print(f"✓ Created zip file: {output_path.name} ({zip_size / (1024*1024):.2f} MB)")
        return True
        
    except Exception as e:
        print(f"❌ Error creating MaxMSP zip file: {e}")
        import traceback
        traceback.print_exc()
        return False


def upload_file_if_needed(ftp: ftplib.FTP, path: Path, existing_files: dict[str, int], force: bool = False):
    """Upload file only if it doesn't exist or has different size (unless force=True)."""
    if should_upload_file(ftp, path, existing_files, force=force):
        upload_file(ftp, path)


def find_maxmsp_zip(latest_version: str | None = None) -> Path | None:
    """Find the MaxMSP patch zip file in versioned directories.
    Only returns versioned filenames (MuscleMonitor-maxmsp-patch-{version}.zip).
    Does NOT return old unversioned files (MuscleMonitor-maxmsp-patch.zip).
    """
    maxmsp_zip = None
    if latest_version:
        version_dir = BUILD_BASE / f"MVC_Calculator-{latest_version}"
        maxmsp_zip = version_dir / f"MuscleMonitor-maxmsp-patch-{latest_version}.zip"
    
    # If not found in specific version, scan for latest version directory
    if not maxmsp_zip or not maxmsp_zip.exists():
        # Find all version directories and get the latest one
        version_dirs = sorted(BUILD_BASE.glob("MVC_Calculator-*"), reverse=True)
        for version_dir in version_dirs:
            if version_dir.is_dir():
                # Extract version from directory name
                dir_version = version_dir.name.replace("MVC_Calculator-", "")
                potential_zip = version_dir / f"MuscleMonitor-maxmsp-patch-{dir_version}.zip"
                if potential_zip.exists():
                    maxmsp_zip = potential_zip
                    break
    
    # DO NOT fallback to old naming convention - only return versioned files
    return maxmsp_zip if (maxmsp_zip and maxmsp_zip.exists()) else None


def upload_maxmsp_only(force: bool = False):
    """Upload only the MaxMSP patch zip file."""
    try:
        print("\n🔌 Connecting to FTP...")
        ftp = ftplib.FTP(DEFAULT_HOST)
        ftp.login(user=DEFAULT_USER, passwd=DEFAULT_PASS)
        
        ensure_dir(ftp, TARGET_DIR)
        ftp.cwd(TARGET_DIR)
        print(f"✓ Connected and changed to {TARGET_DIR}")
        
        # Get list of existing files on server
        print("\n📋 Checking existing files on server...")
        existing_files = get_existing_files(ftp)
        if existing_files:
            print(f"  Found {len(existing_files)} existing file(s)")
        else:
            print("  No existing files found (first upload)")
        
        # Find and upload MaxMSP zip
        maxmsp_zip = find_maxmsp_zip()
        if maxmsp_zip:
            print(f"\n📤 Uploading MaxMSP patch zip: {maxmsp_zip.name}")
            upload_file_if_needed(ftp, maxmsp_zip, existing_files, force=force)
            print("\n✅ MaxMSP patch upload complete!")
        else:
            print("\n❌ MaxMSP patch zip not found!")
            print(f"  Searched in: {BUILD_BASE}")
            print("  Expected filename pattern: MuscleMonitor-maxmsp-patch-{version}.zip")
            return False
        
        ftp.quit()
        return True
        
    except Exception as e:
        print(f"❌ Error uploading MaxMSP patch: {e}")
        import traceback
        traceback.print_exc()
        return False


def upload_auxiliary_files(ftp: ftplib.FTP, existing_files: dict[str, int], include_test: bool = False, latest_version: str | None = None, force: bool = False):
    """Upload auxiliary/non-release files (PHP scripts, etc.)."""
    # Upload PHP tracking script
    php_tracker = Path(__file__).parent / "track_download.php"
    if php_tracker.exists():
        print(f"\n📤 Uploading download tracker: track_download.php")
        upload_file_if_needed(ftp, php_tracker, existing_files, force=force)
    else:
        print(f"⚠️  Warning: track_download.php not found")
    
    # Upload test script if requested
    if include_test:
        test_tracker = Path(__file__).parent / "test_track_download.php"
        if test_tracker.exists():
            print(f"\n📤 Uploading test script: test_track_download.php")
            upload_file_if_needed(ftp, test_tracker, existing_files, force=force)
    
    # Upload MaxMSP patch zip if it exists
    maxmsp_zip = find_maxmsp_zip(latest_version)
    if maxmsp_zip:
        print(f"\n📤 Uploading MaxMSP patch zip: {maxmsp_zip.name}")
        upload_file_if_needed(ftp, maxmsp_zip, existing_files, force=force)


def upload_to_ftp(latest_version: str | None, prev_version: str | None, versions: dict, logo_path: str, upload_auxiliary: bool = True, include_test: bool = False, force: bool = False):
    """Upload all files to FTP server."""
    ftp = None
    try:
        print("\n🔌 Connecting to FTP...")
        ftp = ftplib.FTP(DEFAULT_HOST)
        ftp.login(user=DEFAULT_USER, passwd=DEFAULT_PASS)
        
        ensure_dir(ftp, TARGET_DIR)
        ftp.cwd(TARGET_DIR)
        print(f"✓ Connected and changed to {TARGET_DIR}")
        
        # Get list of existing files on server
        print("\n📋 Checking existing files on server...")
        existing_files = get_existing_files(ftp)
        if existing_files:
            print(f"  Found {len(existing_files)} existing file(s)")
        else:
            print("  No existing files found (first upload)")
        
        # Upload logo
        logo_file = BUILD_BASE / logo_path
        if logo_file.exists():
            print(f"\n📤 Logo: {logo_path}")
            upload_file_if_needed(ftp, logo_file, existing_files, force=force)
        else:
            print(f"⚠️  Warning: Logo file not found: {logo_path}")
        
        # Upload release files only if versions exist
        if latest_version and versions:
            # Upload latest release files
            print(f"\n📤 Latest release ({latest_version}) files:")
            maxmsp_in_versions = False
            for f in versions[latest_version]:
                # Check if this is the MaxMSP zip (to avoid duplicate upload)
                if "maxmsp" in f.name.lower() and f.name.endswith(".zip"):
                    maxmsp_in_versions = True
                    print(f"  ✓ Found MaxMSP zip in scan: {f.name}")
                upload_file_if_needed(ftp, f, existing_files, force=force)
            
            # Also upload MaxMSP zip if it exists and wasn't already uploaded
            if not maxmsp_in_versions:
                print(f"\n🔍 MaxMSP zip not found in scan_builds(), searching separately...")
                maxmsp_zip = find_maxmsp_zip(latest_version)
                if maxmsp_zip:
                    print(f"📤 MaxMSP patch zip: {maxmsp_zip.name}")
                    upload_file_if_needed(ftp, maxmsp_zip, existing_files, force=force)
                else:
                    print(f"\n⚠️  MaxMSP patch zip not found for version {latest_version}")
                    version_dir = BUILD_BASE / f"MVC_Calculator-{latest_version}"
                    expected_path = version_dir / f"MuscleMonitor-maxmsp-patch-{latest_version}.zip"
                    print(f"   Expected location: {expected_path}")
                    if version_dir.exists():
                        print(f"   Version directory exists. Files in directory:")
                        for f in sorted(version_dir.glob("*.zip")):
                            print(f"     - {f.name}")
                    else:
                        print(f"   Version directory does not exist: {version_dir}")
            
            # Upload latest release notes
            version_dir = BUILD_BASE / f"MVC_Calculator-{latest_version}"
            notes_file = version_dir / "buildfiles" / f"RELEASE_NOTES-{latest_version}.txt"
            if not notes_file.exists():
                notes_file = BUILD_BASE / f"RELEASE_NOTES-{latest_version}.txt"
            
            if notes_file.exists():
                print(f"\n📤 Release notes: {notes_file.name}")
                upload_file_if_needed(ftp, notes_file, existing_files, force=force)
            
            # Upload previous release files (if exists)
            if prev_version:
                print(f"\n📤 Previous release ({prev_version}) files:")
                for f in versions[prev_version]:
                    upload_file_if_needed(ftp, f, existing_files, force=force)
                
                # Upload previous release notes
                prev_version_dir = BUILD_BASE / f"MVC_Calculator-{prev_version}"
                prev_notes_file = prev_version_dir / "buildfiles" / f"RELEASE_NOTES-{prev_version}.txt"
                if not prev_notes_file.exists():
                    prev_notes_file = BUILD_BASE / f"RELEASE_NOTES-{prev_version}.txt"
                
                if prev_notes_file.exists():
                    print(f"\n📤 Release notes: {prev_notes_file.name}")
                    upload_file_if_needed(ftp, prev_notes_file, existing_files, force=force)
        
        # Upload Development Release files (if exists)
        oa_version, oa_files = scan_oa_builds()
        if oa_version and oa_files:
            print(f"\n📤 Development Release ({oa_version}) files:")
            for f in oa_files:
                upload_file_if_needed(ftp, f, existing_files, force=force)
        
        # Upload index.html if it exists (may not exist if no builds found)
        if OUTPUT.exists():
            print(f"\n📤 Uploading index.html")
            if force:
                upload_file(ftp, OUTPUT)
            else:
                upload_file_if_needed(ftp, OUTPUT, existing_files, force=force)
        else:
            print(f"⚠️  Info: index.html not found - skipping (normal if no builds exist)")
        
        # Upload auxiliary files if requested
        if upload_auxiliary:
            upload_auxiliary_files(ftp, existing_files, include_test=include_test, latest_version=latest_version, force=force)
        
        print("\n✅ FTP upload complete!")
    except Exception as e:
        print(f"❌ Error during FTP upload: {e}")
        raise
    finally:
        if ftp:
            try:
                ftp.quit()
            except:
                pass


def main():
    # Record start time
    start_time = datetime.now()
    start_timestamp = start_time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="FTP Deployment Script for MVC Calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-u", "--upload", action="store_true", 
                      help="Upload files to FTP server (default: only generate index.html locally)")
    parser.add_argument("--upload-auxiliary", action="store_true",
                      help="Upload auxiliary files (track_download.php, etc.) even when no builds are found")
    parser.add_argument("--upload-maxmsp-only", action="store_true",
                      help="Upload only the MaxMSP patch zip file (skips all other files)")
    parser.add_argument("--force", action="store_true",
                      help="Force upload even if file already exists with same size (overwrites existing files)")
    parser.add_argument("--include-test", action="store_true",
                      help="Include test_track_download.php for debugging")
    parser.add_argument("--upload-html", action="store_true",
                      help="Upload index.html even when no builds are found (if it exists locally)")
    args = parser.parse_args()
    
    # Print header with start timestamp
    print("="*60)
    print("MVC CALCULATOR - FTP Deployment Script")
    print("="*60)
    print(f"Started at: {start_timestamp}")
    print(f"Project Root: {Path(__file__).resolve().parent}")
    print("="*60)
    print()
    
    # Handle --upload-maxmsp-only flag early (before build scanning)
    if args.upload_maxmsp_only:
        if not args.upload:
            print("⚠️  Warning: --upload-maxmsp-only requires -u/--upload flag")
            print("  Use: python deploy_release_ftp.py -u --upload-maxmsp-only")
            # Calculate duration even on early return
            end_time = datetime.now()
            end_timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")
            duration = end_time - start_time
            duration_seconds = duration.total_seconds()
            print("\n" + "="*60)
            print(f"Exited at: {end_timestamp}")
            print(f"Duration: {duration_seconds:.2f} seconds")
            print("="*60)
            return
        print("\n📦 MaxMSP Patch Only Upload Mode")
        success = upload_maxmsp_only(force=args.force)
        # Calculate duration for maxmsp-only mode
        end_time = datetime.now()
        end_timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")
        duration = end_time - start_time
        duration_seconds = duration.total_seconds()
        print("\n" + "="*60)
        print("✅ MAXMSP UPLOAD COMPLETED" if success else "❌ MAXMSP UPLOAD FAILED")
        print("="*60)
        print(f"Completed at: {end_timestamp}")
        print(f"Duration: {duration_seconds:.2f} seconds ({duration_seconds/60:.2f} minutes)")
        print("="*60)
        return
    
    try:
        print(f"Scanning for builds in versioned directories:")
        print(f"  BUILD_BASE: {BUILD_BASE}")
        
        versions = scan_builds()
        if not versions:
            print("No builds found.")
            print(f"Checked patterns: {PATTERNS}")
            
            # If --upload-auxiliary is set, allow uploading auxiliary files only
            if args.upload_auxiliary and args.upload:
                print("\n📤 Uploading auxiliary files only (no builds found)...")
                logo_path = find_logo_path()
                # Create a minimal FTP connection just for auxiliary files
                try:
                    ftp = ftplib.FTP(DEFAULT_HOST)
                    ftp.login(user=DEFAULT_USER, passwd=DEFAULT_PASS)
                    ensure_dir(ftp, TARGET_DIR)
                    ftp.cwd(TARGET_DIR)
                    existing_files = get_existing_files(ftp)
                    
                    # Upload index.html if it exists (always upload if available)
                    if OUTPUT.exists():
                        print(f"\n📤 Uploading index.html")
                        if args.force:
                            upload_file(ftp, OUTPUT)
                        else:
                            upload_file_if_needed(ftp, OUTPUT, existing_files, force=args.force)
                    elif args.upload_html:
                        print(f"⚠️  index.html not found at {OUTPUT}")
                    
                    # Try to find latest version for MaxMSP zip lookup
                    version_dirs = sorted(BUILD_BASE.glob("MVC_Calculator-*"), reverse=True)
                    latest_ver = version_dirs[0].name.replace("MVC_Calculator-", "") if version_dirs else None
                    upload_auxiliary_files(ftp, existing_files, include_test=args.include_test, latest_version=latest_ver, force=args.force)
                    ftp.quit()
                    print("✓ Auxiliary files uploaded successfully")
                    
                    # Calculate duration for auxiliary-only upload
                    end_time = datetime.now()
                    end_timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")
                    duration = end_time - start_time
                    duration_seconds = duration.total_seconds()
                    print("\n" + "="*60)
                    print("✅ AUXILIARY FILES UPLOAD COMPLETED")
                    print("="*60)
                    print(f"Completed at: {end_timestamp}")
                    print(f"Duration: {duration_seconds:.2f} seconds ({duration_seconds/60:.2f} minutes)")
                    print("="*60)
                except Exception as e:
                    # Calculate duration even on error
                    end_time = datetime.now()
                    end_timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")
                    duration = end_time - start_time
                    duration_seconds = duration.total_seconds()
                    print("\n" + "="*60)
                    print("❌ AUXILIARY FILES UPLOAD FAILED")
                    print("="*60)
                    print(f"Failed at: {end_timestamp}")
                    print(f"Duration: {duration_seconds:.2f} seconds ({duration_seconds/60:.2f} minutes)")
                    print("="*60)
                    print(f"ERROR: {e}")
                    import traceback
                    traceback.print_exc()
                return
            elif args.upload_auxiliary:
                print("  Use -u/--upload along with --upload-auxiliary to upload files")
            else:
                print("  Use --upload-auxiliary with -u/--upload to upload auxiliary files (track_download.php, etc.) even when no builds are found")
            
            # Check if index.html exists locally and offer to upload it
            if OUTPUT.exists() and args.upload_html and args.upload:
                print(f"\n📤 Found existing index.html, uploading...")
                try:
                    ftp = ftplib.FTP(DEFAULT_HOST)
                    ftp.login(user=DEFAULT_USER, passwd=DEFAULT_PASS)
                    ensure_dir(ftp, TARGET_DIR)
                    ftp.cwd(TARGET_DIR)
                    existing_files = get_existing_files(ftp)
                    if args.force:
                        upload_file(ftp, OUTPUT)
                    else:
                        upload_file_if_needed(ftp, OUTPUT, existing_files, force=args.force)
                    ftp.quit()
                    print("✓ index.html uploaded successfully")
                    
                    # Calculate duration for html-only upload
                    end_time = datetime.now()
                    end_timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")
                    duration = end_time - start_time
                    duration_seconds = duration.total_seconds()
                    print("\n" + "="*60)
                    print("✅ INDEX.HTML UPLOAD COMPLETED")
                    print("="*60)
                    print(f"Completed at: {end_timestamp}")
                    print(f"Duration: {duration_seconds:.2f} seconds ({duration_seconds/60:.2f} minutes)")
                    print("="*60)
                except Exception as e:
                    # Calculate duration even on error
                    end_time = datetime.now()
                    end_timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")
                    duration = end_time - start_time
                    duration_seconds = duration.total_seconds()
                    print("\n" + "="*60)
                    print("❌ INDEX.HTML UPLOAD FAILED")
                    print("="*60)
                    print(f"Failed at: {end_timestamp}")
                    print(f"Duration: {duration_seconds:.2f} seconds ({duration_seconds/60:.2f} minutes)")
                    print("="*60)
                    print(f"ERROR: {e}")
                    import traceback
                    traceback.print_exc()
            elif OUTPUT.exists() and not args.upload_html:
                print(f"\n💡 Tip: Found existing index.html at {OUTPUT}")
                print(f"  Use --upload-html with -u/--upload to upload it to the server")
            
            # Calculate duration when no builds found and no upload requested
            end_time = datetime.now()
            end_timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")
            duration = end_time - start_time
            duration_seconds = duration.total_seconds()
            print("\n" + "="*60)
            print("✅ SCAN COMPLETED (NO BUILDS FOUND)")
            print("="*60)
            print(f"Completed at: {end_timestamp}")
            print(f"Duration: {duration_seconds:.2f} seconds ({duration_seconds/60:.2f} minutes)")
            print("="*60)
            return

        print(f"Found {len(versions)} version(s): {sorted(versions.keys(), reverse=True)}")
        
        sorted_versions = sorted(versions.keys(), reverse=True)
        latest = sorted_versions[0]
        prev = sorted_versions[1] if len(sorted_versions) > 1 else None

        print(f"Latest version: {latest}")
        if prev:
            print(f"Previous version: {prev}")

        # Verify we have all 4 build files for latest version
        latest_files = versions[latest]
        file_types = {".msi": False, ".zip": False, ".deb": False, ".AppImage": False}
        for f in latest_files:
            if f.suffix == ".msi":
                file_types[".msi"] = True
            elif f.suffix == ".zip" and "portable" in f.name:
                file_types[".zip"] = True
            elif f.suffix == ".deb":
                file_types[".deb"] = True
            elif f.suffix == ".AppImage":
                file_types[".AppImage"] = True
        
        missing = [ext for ext, found in file_types.items() if not found]
        if missing:
            print(f"⚠️  Warning: Missing build files: {', '.join(missing)}")
        else:
            print(f"✓ Found all 4 build files (MSI, ZIP, DEB, AppImage)")

        # Check and create MaxMSP patch zip BEFORE generating HTML (so it's included in the table)
        print(f"\n🔍 Checking MaxMSP patch dependencies...")
        print(f"  Source directory: {MAXPATCHES_SOURCE}")
        
        if MAXPATCHES_SOURCE.exists():
            all_found, missing, found_files = check_maxmsp_dependencies()
            
            if not all_found:
                print(f"  ⚠️  Warning: Missing {len(missing)} required file(s):")
                for m in missing:
                    print(f"    - {m}")
                print(f"  Attempting to create zip with available files...")
            else:
                print(f"  ✓ All required dependencies found!")
            
            if found_files:
                # Create zip in the versioned directory with versioned filename
                version_dir = BUILD_BASE / f"MVC_Calculator-{latest}"
                version_dir.mkdir(parents=True, exist_ok=True)
                maxmsp_zip = version_dir / f"MuscleMonitor-maxmsp-patch-{latest}.zip"
                if create_maxmsp_zip(maxmsp_zip, found_files):
                    print(f"  ✓ MaxMSP patch zip created: {maxmsp_zip.name}")
                    # Re-scan builds to include the newly created MaxMSP zip in the HTML
                    versions = scan_builds()
                    if latest in versions and maxmsp_zip not in versions[latest]:
                        versions[latest].append(maxmsp_zip)
                        print(f"  ✓ Added MaxMSP zip to versions for HTML generation")
                else:
                    print(f"  ❌ Failed to create MaxMSP patch zip")
            else:
                print(f"  ❌ No MaxMSP files found, skipping zip creation")
        else:
            print(f"  ⚠️  Warning: MaxPatches source directory not found: {MAXPATCHES_SOURCE}")
            print(f"  Skipping MaxMSP patch zip creation.")

        notes = load_notes(latest)
        print(f"Loaded notes for {latest}: date={notes['date']}, tags={notes['tags']}")
        if notes['tags']:
            print(f"  Tag details:")
            for t in notes['tags']:
                normalized = normalize_tag_name(t)
                display = format_tag_display(t)
                print(f"    '{t}' -> normalized: '{normalized}' -> display: '{display}'")

        if not TEMPLATE.exists():
            print(f"ERROR: Template not found at {TEMPLATE}")
            return
        
        html = TEMPLATE.read_text(encoding="utf-8")
        if not html:
            print(f"ERROR: Template file is empty at {TEMPLATE}")
            return

        # Build replacement values
        latest_date = notes["date"] or datetime.now().strftime("%d %b %Y")
        latest_desc = notes["description"] or f"Version {latest} release."
        whats_new_html = make_li_list(notes["whats_new"]) if notes["whats_new"] else "<li>No new features in this release.</li>"
        bug_fixes_html = make_li_list(notes["bug_fixes"]) if notes["bug_fixes"] else "<li>No bug fixes in this release.</li>"
        
        latest_tags_html = " ".join(
            f"<span class='tag tag-{normalize_tag_name(t)}'>{format_tag_display(t)}</span>"
            for t in notes["tags"]
            if t and t.strip()
        )
        if latest_tags_html:
            latest_tags_html = f"<div style='margin-top: 10px;'>{latest_tags_html}</div>"
            print(f"  Generated tags HTML: {latest_tags_html[:150]}...")
        else:
            latest_tags_html = ""  # Ensure empty string if no tags
            print(f"  ⚠️  Warning: No tags HTML generated (notes['tags'] = {notes['tags']})")

        # Perform replacements
        logo_path = find_logo_path()
        logo_file = BUILD_BASE / logo_path
        if logo_file.exists():
            print(f"✓ Found logo: {logo_path}")
        else:
            print(f"⚠️  Warning: Logo file not found: {logo_path}")
        html = html.replace("{{LOGO_PATH}}", logo_path)
        html = html.replace("{{LATEST_VERSION}}", latest)
        html = html.replace("{{LATEST_DATE}}", latest_date)
        html = html.replace("{{LATEST_DESCRIPTION}}", latest_desc)
        html = html.replace("{{LATEST_WHATS_NEW}}", whats_new_html)
        html = html.replace("{{LATEST_BUG_FIXES}}", bug_fixes_html)
        html = html.replace("{{LATEST_TAGS}}", latest_tags_html)
        html = html.replace("{{LATEST_TABLE}}", build_table(versions[latest]))

        if prev:
            # Load previous release notes
            prev_notes = load_notes(prev)
            prev_date = prev_notes["date"] or datetime.now().strftime("%d %b %Y")
            prev_desc = prev_notes["description"] or f"Version {prev} release."
            prev_whats_new_html = make_li_list(prev_notes["whats_new"]) if prev_notes["whats_new"] else "<li>No new features in this release.</li>"
            prev_bug_fixes_html = make_li_list(prev_notes["bug_fixes"]) if prev_notes["bug_fixes"] else "<li>No bug fixes in this release.</li>"
            
            prev_tags_html = " ".join(
                f"<span class='tag tag-{normalize_tag_name(t)}'>{format_tag_display(t)}</span>"
                for t in prev_notes["tags"]
                if t and t.strip()
            )
            if prev_tags_html:
                prev_tags_html = f"<div style='margin-top: 10px;'>{prev_tags_html}</div>"
            
            # Previous release section - EXACT same structure as latest release
            prev_section = f'''<div class="release-section">
    <div class="release-left">
        <div>{prev_date}</div>
        {prev_tags_html}
    </div>

    <!-- RIGHT CONTENT -->
    <div>
        <div class="section-title">Previous Release — {prev}</div>

    <div class="release-description">
        {prev_desc}
    </div>

    <div class="release-notes-text">

        <h3>What's New</h3>
        <ul>
            {prev_whats_new_html}
        </ul>

        <h3>Bug Fixes</h3>
        <ul>
            {prev_bug_fixes_html}
        </ul>

    </div>

        <!-- FILE TABLE -->
        {build_table(versions[prev])}

    </div>
</div>'''
            html = html.replace("{{PREV_VERSION}}", prev_section)
        else:
            html = html.replace("{{PREV_VERSION}}", "")

        # Development Release section
        oa_version, oa_files = scan_oa_builds()
        if oa_version and oa_files:
            oa_notes = load_notes(oa_version, oa=True)
            oa_date = oa_notes["date"] or datetime.now().strftime("%d %b %Y")
            oa_desc = oa_notes["description"] or f"Development Release version {oa_version}."
            oa_whats_new = make_li_list(oa_notes["whats_new"]) if oa_notes["whats_new"] else "<li>No new features in this release.</li>"
            oa_bug_fixes = make_li_list(oa_notes["bug_fixes"]) if oa_notes["bug_fixes"] else "<li>No bug fixes in this release.</li>"
            oa_tags_html = " ".join(
                f"<span class='tag tag-{normalize_tag_name(t)}'>{format_tag_display(t)}</span>"
                for t in (oa_notes["tags"] or [])
                if t and t.strip()
            )
            if oa_tags_html:
                oa_tags_html = f"<div style='margin-top: 10px;'>{oa_tags_html}</div>"
            oa_section = f'''<div class="release-section">
    <div class="release-left">
        <div>{oa_date}</div>
        {oa_tags_html}
    </div>

    <div>
        <div class="section-title">Development Release — {oa_version}</div>

    <div class="release-description">
        {oa_desc}
    </div>

    <div class="release-notes-text">

        <h3>What's New</h3>
        <ul>
            {oa_whats_new}
        </ul>

        <h3>Bug Fixes</h3>
        <ul>
            {oa_bug_fixes}
        </ul>

    </div>

        {build_table(oa_files)}

    </div>
</div>'''
            html = html.replace("{{OA_SECTION}}", oa_section)
        else:
            html = html.replace("{{OA_SECTION}}", "")

        # Verify all placeholders were replaced
        if "{{" in html:
            print("WARNING: Some placeholders were not replaced!")
            import re
            remaining = re.findall(r'\{\{[^}]+\}\}', html)
            print(f"  Remaining placeholders: {remaining}")

        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(html, encoding="utf-8")
        print(f"✓ index.html generated at: {OUTPUT}")
        print(f"  File size: {OUTPUT.stat().st_size} bytes")
        
        # Summary of files ready for FTP upload
        print(f"\n📦 Files ready for FTP upload:")
        print(f"  1. {OUTPUT.name} ({OUTPUT.stat().st_size} bytes)")
        if logo_file.exists():
            print(f"  2. {logo_path} ({logo_file.stat().st_size} bytes)")
        else:
            print(f"  2. {logo_path} (⚠️  not found)")
        
        # Check for MaxMSP zip in versioned directory (versioned filename only)
        maxmsp_zip = find_maxmsp_zip(latest)
        if maxmsp_zip:
            print(f"  3. {maxmsp_zip.name} ({maxmsp_zip.stat().st_size / (1024*1024):.2f} MB)")
        
        print(f"\n📁 Build files in version directory:")
        version_dir = BUILD_BASE / f"MVC_Calculator-{latest}"
        if version_dir.exists():
            for f in sorted(version_dir.iterdir()):
                if f.is_file() and f.suffix in [".msi", ".zip", ".deb", ".AppImage"]:
                    print(f"  - {f.name} ({f.stat().st_size / (1024*1024):.1f} MB)")
        
        # Upload to FTP only if -u/--upload flag is provided
        if not args.upload:
            print(f"\n[INFO] Skipping FTP upload (use -u/--upload to upload files)")
            print(f"       Generated index.html at: {OUTPUT}")
            # Calculate duration when skipping upload
            end_time = datetime.now()
            end_timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")
            duration = end_time - start_time
            duration_seconds = duration.total_seconds()
            print("\n" + "="*60)
            print("✅ INDEX GENERATION COMPLETED")
            print("="*60)
            print(f"Completed at: {end_timestamp}")
            print(f"Duration: {duration_seconds:.2f} seconds ({duration_seconds/60:.2f} minutes)")
            print("="*60)
            return
        
        # Upload to FTP
        print(f"\n🚀 Starting FTP upload...")
        upload_to_ftp(latest, prev, versions, logo_path, upload_auxiliary=True, include_test=args.include_test, force=args.force)
        
        # Calculate and display duration on success
        end_time = datetime.now()
        end_timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")
        duration = end_time - start_time
        duration_seconds = duration.total_seconds()
        
        print("\n" + "="*60)
        print("✅ DEPLOYMENT COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"Completed at: {end_timestamp}")
        print(f"Duration: {duration_seconds:.2f} seconds ({duration_seconds/60:.2f} minutes)")
        print("="*60)
        
    except Exception as e:
        # Calculate duration even on error
        end_time = datetime.now()
        end_timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")
        duration = end_time - start_time
        duration_seconds = duration.total_seconds()
        
        print("\n" + "="*60)
        print("❌ DEPLOYMENT FAILED")
        print("="*60)
        print(f"Failed at: {end_timestamp}")
        print(f"Duration: {duration_seconds:.2f} seconds ({duration_seconds/60:.2f} minutes)")
        print("="*60)
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
