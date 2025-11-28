#!/usr/bin/env python3

import re
import ftplib
from pathlib import Path
from datetime import datetime
from tqdm import tqdm


BUILD_BASE = Path.home() / "Documents/.builds/mvc_calculator"
NOTES_DIR = BUILD_BASE

TEMPLATE  = Path(__file__).parent / "TEMPLATE_RELEASE.html"
OUTPUT    = BUILD_BASE / "index.html"

# FTP Configuration (hardcoded)
TARGET_DIR = "/public_html/downloads/MVC_Calculator/releases"
DEFAULT_HOST = "ftp.moviolabs.com"
DEFAULT_USER = "moviolab"
DEFAULT_PASS = "xTQSz1g,n2we"

def find_logo_path():
    """Find logo file in output directory or copy from resources."""
    import shutil
    
    # Check for common logo file names in the output directory first
    # icon.png is the primary logo name
    logo_names = ["icon.png", "logo.svg", "logo.png", "coming.soon.light.on.darkL.svg", "manandsnareRASTERIZED.png"]
    for name in logo_names:
        logo_path = BUILD_BASE / name
        if logo_path.exists():
            return name
    
    # If not found, check resources/icons directory and copy it
    resources_dir = Path(__file__).parent / "resources" / "icons"
    for name in logo_names:
        source_logo = resources_dir / name
        if source_logo.exists():
            # Copy to output directory
            dest_logo = BUILD_BASE / name
            shutil.copy2(source_logo, dest_logo)
            print(f"Copied logo from {source_logo} to {dest_logo}")
            return name
    
    # Default fallback
    return "icon.png"

PATTERNS = [
    "MVC_Calculator-*-alpha.*.msi",
    "MVC_Calculator-*-alpha.*-portable.zip",
    "mvc-calculator_*_amd64.deb",
    "MVC_Calculator-*-alpha.*-x86_64.AppImage",
]

VERSION_RE = re.compile(r"(\d{2}\.\d{2}-alpha\.\d{2}\.\d{2})")


def parse_version(name: str):
    m = VERSION_RE.search(name)
    return m.group(1) if m else None


def load_notes(version: str):
    notes = {
        "date": "",
        "description": "",
        "whats_new": [],
        "bug_fixes": [],
        "tags": [],
    }

    # Look for release notes in versioned directory's buildfiles subdirectory
    version_dir = BUILD_BASE / f"MVC_Calculator-{version}"
    notes_file = version_dir / "buildfiles" / f"RELEASE_NOTES-{version}.txt"
    
    # Fallback to base directory for backwards compatibility
    if not notes_file.exists():
        notes_file = BUILD_BASE / f"RELEASE_NOTES-{version}.txt"
    
    if not notes_file.exists():
        return notes

    content = notes_file.read_text(encoding="utf-8")
    
    # Find section markers first
    whats_new_match = re.search(r'(?i)(?:^|\n)\s*(?:\[?what\'?s\s+new\]?|what\'?s\s+new:)\s*\n?', content)
    bug_fixes_match = re.search(r'(?i)(?:^|\n)\s*(?:\[?bug\s+fixes\]?|bug\s+fixes:)\s*\n?', content)
    
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
            # Tags might be on the same line or the next line
            tags_str = s.split(":", 1)[1].strip()
            if not tags_str and i + 1 < len(lines):
                # Tags are on the next line
                tags_str = lines[i + 1].strip()
                skip_next_line = True  # Skip the tags line in next iteration
            if tags_str:
                notes["tags"] = [t.strip() for t in tags_str.split(",") if t.strip()]
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
        
        # Extract bullet points from what's new
        for line in whats_new_text.splitlines():
            s = line.strip()
            if s.startswith("-"):
                notes["whats_new"].append(s[1:].strip())
        
        # Extract bullet points from bug fixes
        for line in bug_fixes_text.splitlines():
            s = line.strip()
            if s.startswith("-"):
                notes["bug_fixes"].append(s[1:].strip())
    else:
        # Fallback: line-by-line parsing for WHAT'S NEW and BUG FIXES
        section = None
        for line in lines:
            s = line.strip()
            
            if s.lower() in ["[what's new]", "what's new:", "what's new"]:
                section = "new"
            elif s.lower() in ["[bug fixes]", "bug fixes:", "bug fixes"]:
                section = "bug"
            elif section == "new" and s.startswith("-"):
                notes["whats_new"].append(s[1:].strip())
            elif section == "bug" and s.startswith("-"):
                notes["bug_fixes"].append(s[1:].strip())

    notes["description"] = notes["description"].strip()
    return notes


def make_li_list(items):
    if not items:
        return ""
    return "\n            ".join(f"<li>{i}</li>" for i in items)


def normalize_tag_name(tag: str) -> str:
    """
    Normalize tag names to match predefined CSS classes.
    Predefined tags: api, security, performance, bugfix, feature, 
                     ui, documentation, breaking, enhancement, testing
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
    }
    
    # Check direct match first
    if tag_lower in tag_map:
        return tag_map[tag_lower]
    
    # Check if tag contains any of the keywords
    for key, normalized in tag_map.items():
        if key in tag_lower:
            return normalized
    
    # Default: return lowercase version (will use default styling if CSS class doesn't exist)
    return tag_lower.replace(" ", "-").replace("/", "-")


def scan_builds():
    """Scan versioned directories for build files."""
    all_files = []
    
    # Scan all versioned directories (MVC_Calculator-XX.XX-alpha.XX.XX)
    if BUILD_BASE.exists():
        for version_dir in BUILD_BASE.iterdir():
            if version_dir.is_dir() and version_dir.name.startswith("MVC_Calculator-"):
                # Look for build files in the version directory (not in buildfiles subdirectory)
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


def detect_description(filename: str):
    fn = filename.lower()
    if fn.endswith(".msi"): return "Windows installer"
    if fn.endswith(".zip"): return "Portable ZIP build"
    if fn.endswith(".deb"): return "Linux .deb package"
    if fn.endswith(".appimage"): return "Linux AppImage"
    return "Build File"


def build_table(files):
    rows = []
    for f in sorted(files, key=lambda x: x.name.lower()):
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
    """Upload file to FTP with progress bar."""
    total = path.stat().st_size
    bar = tqdm(total=total, unit="B", unit_scale=True, desc=f"Uploading {path.name}")

    def callback(chunk):
        bar.update(len(chunk))

    with path.open("rb") as f:
        ftp.storbinary(f"STOR {path.name}", f, 8192, callback)

    bar.close()


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


def should_upload_file(ftp: ftplib.FTP, path: Path, existing_files: dict[str, int]) -> bool:
    """Check if file should be uploaded (skip if exists with same size)."""
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


def upload_file_if_needed(ftp: ftplib.FTP, path: Path, existing_files: dict[str, int]):
    """Upload file only if it doesn't exist or has different size."""
    if should_upload_file(ftp, path, existing_files):
        upload_file(ftp, path)


def upload_to_ftp(latest_version: str, prev_version: str | None, versions: dict, logo_path: str):
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
            upload_file_if_needed(ftp, logo_file, existing_files)
        else:
            print(f"⚠️  Warning: Logo file not found: {logo_path}")
        
        # Upload latest release files
        print(f"\n📤 Latest release ({latest_version}) files:")
        for f in versions[latest_version]:
            upload_file_if_needed(ftp, f, existing_files)
        
        # Upload latest release notes
        version_dir = BUILD_BASE / f"MVC_Calculator-{latest_version}"
        notes_file = version_dir / "buildfiles" / f"RELEASE_NOTES-{latest_version}.txt"
        if not notes_file.exists():
            notes_file = BUILD_BASE / f"RELEASE_NOTES-{latest_version}.txt"
        
        if notes_file.exists():
            print(f"\n📤 Release notes: {notes_file.name}")
            upload_file_if_needed(ftp, notes_file, existing_files)
        
        # Upload previous release files (if exists)
        if prev_version:
            print(f"\n📤 Previous release ({prev_version}) files:")
            for f in versions[prev_version]:
                upload_file_if_needed(ftp, f, existing_files)
            
            # Upload previous release notes
            prev_version_dir = BUILD_BASE / f"MVC_Calculator-{prev_version}"
            prev_notes_file = prev_version_dir / "buildfiles" / f"RELEASE_NOTES-{prev_version}.txt"
            if not prev_notes_file.exists():
                prev_notes_file = BUILD_BASE / f"RELEASE_NOTES-{prev_version}.txt"
            
            if prev_notes_file.exists():
                print(f"\n📤 Release notes: {prev_notes_file.name}")
                upload_file_if_needed(ftp, prev_notes_file, existing_files)
        
        # Upload index.html (always upload as it changes)
        print(f"\n📤 Uploading index.html (always updated)")
        upload_file(ftp, OUTPUT)
        
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
    try:
        print(f"Scanning for builds in versioned directories:")
        print(f"  BUILD_BASE: {BUILD_BASE}")
        
        versions = scan_builds()
        if not versions:
            print("No builds found.")
            print(f"Checked patterns: {PATTERNS}")
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

        notes = load_notes(latest)
        print(f"Loaded notes for {latest}: date={notes['date']}, tags={notes['tags']}")

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
            f"<span class='tag tag-{normalize_tag_name(t)}'>{t}</span>"
            for t in notes["tags"]
            if t and t.strip()
        )
        if latest_tags_html:
            latest_tags_html = f"<div style='margin-top: 10px;'>{latest_tags_html}</div>"

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
                f"<span class='tag tag-{normalize_tag_name(t)}'>{t}</span>"
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
        
        print(f"\n📁 Build files in version directory:")
        version_dir = BUILD_BASE / f"MVC_Calculator-{latest}"
        if version_dir.exists():
            for f in sorted(version_dir.iterdir()):
                if f.is_file() and f.suffix in [".msi", ".zip", ".deb", ".AppImage"]:
                    print(f"  - {f.name} ({f.stat().st_size / (1024*1024):.1f} MB)")
        
        # Upload to FTP
        print(f"\n🚀 Starting FTP upload...")
        upload_to_ftp(latest, prev, versions, logo_path)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
