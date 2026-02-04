#!/usr/bin/env python3
"""
Configurable version of deploy_release_ftp.py
All paths can be configured via command-line arguments.
Use this for different contexts/projects.
"""

import re
import argparse
import ftplib
import sys
from pathlib import Path
from datetime import datetime

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    # Simple progress bar fallback
    class SimpleProgress:
        def __init__(self, total, desc=""):
            self.total = total
            self.desc = desc
            self.uploaded = 0
            self.last_pct = -1
        
        def update(self, n):
            self.uploaded += n
            pct = int((self.uploaded / self.total) * 100)
            if pct != self.last_pct:
                bar_length = 40
                filled = int(bar_length * self.uploaded / self.total)
                bar = '=' * filled + '-' * (bar_length - filled)
                sys.stdout.write(f'\r{self.desc} [{bar}] {pct}% ({self.uploaded/1024/1024:.1f}MB/{self.total/1024/1024:.1f}MB)')
                sys.stdout.flush()
                self.last_pct = pct
        
        def close(self):
            print()  # New line after progress


# Default paths (can be overridden via command-line arguments)
DEFAULT_BUILD_BASE = Path.home() / "Documents/.builds/mvc_calculator"
DEFAULT_TEMPLATE = Path(__file__).parent / "TEMPLATE_RELEASE.html"
DEFAULT_OUTPUT = None  # Will be set to BUILD_BASE / "index.html" if not specified
DEFAULT_TARGET_DIR = "/public_html/downloads/MVC_Calculator/releases"
DEFAULT_HOST = "ftp.moviolabs.com"
DEFAULT_USER = "moviolab"
DEFAULT_PASS = "xTQSz1g,n2we"

def find_logo_path(build_base: Path, script_dir: Path):
    """Find logo file in output directory or copy from resources."""
    import shutil
    
    # Check for common logo file names in the output directory first
    logo_names = ["icon.png", "logo.svg", "logo.png", "coming.soon.light.on.darkL.svg", "manandsnareRASTERIZED.png"]
    for name in logo_names:
        logo_path = build_base / name
        if logo_path.exists():
            return name
    
    # If not found, check resources/icons directory and copy it
    resources_dir = script_dir / "resources" / "icons"
    for name in logo_names:
        source_logo = resources_dir / name
        if source_logo.exists():
            # Copy to output directory
            dest_logo = build_base / name
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


def load_notes(version: str, build_base: Path):
    notes = {
        "date": "",
        "description": "",
        "whats_new": [],
        "bug_fixes": [],
        "tags": [],
    }

    # Look for release notes in versioned directory's buildfiles subdirectory
    version_dir = build_base / f"MVC_Calculator-{version}"
    notes_file = version_dir / "buildfiles" / f"RELEASE_NOTES-{version}.txt"
    
    # Fallback to base directory for backwards compatibility
    if not notes_file.exists():
        notes_file = build_base / f"RELEASE_NOTES-{version}.txt"
    
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
    skip_next_line = False
    
    for i, line in enumerate(lines):
        if skip_next_line:
            skip_next_line = False
            continue
            
        s = line.strip()
        
        if s.lower().startswith("date:"):
            notes["date"] = s.split(":", 1)[1].strip()
        elif s.lower().startswith("tags:"):
            tags_str = s.split(":", 1)[1].strip()
            if not tags_str and i + 1 < len(lines):
                tags_str = lines[i + 1].strip()
                skip_next_line = True
            if tags_str:
                notes["tags"] = [t.strip() for t in tags_str.split(",") if t.strip()]
        elif s.lower().startswith("description:"):
            desc_text = s.split(":", 1)[1].strip() if ":" in s else ""
            if desc_text:
                description_lines.append(desc_text)
            in_description = True
        elif in_description:
            if any(marker in s.upper() for marker in ["WHAT'S NEW", "BUG FIXES", "[WHAT'S", "[BUG"]):
                in_description = False
            elif s:
                description_lines.append(s)
    
    notes["description"] = " ".join(description_lines).strip()
    
    # Extract WHAT'S NEW and BUG FIXES sections
    if whats_new_match:
        start_idx = whats_new_match.end()
        if bug_fixes_match and bug_fixes_match.start() > start_idx:
            whats_new_text = content[start_idx:bug_fixes_match.start()].strip()
            bug_fixes_text = content[bug_fixes_match.end():].strip()
        else:
            whats_new_text = content[start_idx:].strip()
            bug_fixes_text = ""
        
        for line in whats_new_text.splitlines():
            s = line.strip()
            if s.startswith("-"):
                notes["whats_new"].append(s[1:].strip())
        
        for line in bug_fixes_text.splitlines():
            s = line.strip()
            if s.startswith("-"):
                notes["bug_fixes"].append(s[1:].strip())
    else:
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
    """Normalize tag names to match predefined CSS classes."""
    tag_lower = tag.lower().strip()
    
    tag_map = {
        "api": "api",
        "security": "security", "sec": "security",
        "performance": "performance", "perf": "performance",
        "bugfix": "bugfix", "bug fix": "bugfix", "bug-fix": "bugfix", "bugs": "bugfix", "bug": "bugfix",
        "feature": "feature", "features": "feature", "new feature": "feature",
        "ui": "ui", "ui/ux": "ui", "ux": "ui", "user interface": "ui", "interface": "ui",
        "documentation": "documentation", "docs": "documentation", "doc": "documentation",
        "breaking": "breaking", "breaking change": "breaking", "breaking-change": "breaking", "breaking changes": "breaking",
        "enhancement": "enhancement", "enhancements": "enhancement", "improvement": "enhancement", "improvements": "enhancement",
        "testing": "testing", "system testing": "testing", "system-testing": "testing", "test": "testing",
    }
    
    if tag_lower in tag_map:
        return tag_map[tag_lower]
    
    for key, normalized in tag_map.items():
        if key in tag_lower:
            return normalized
    
    return tag_lower.replace(" ", "-").replace("/", "-")


def scan_builds(build_base: Path, patterns):
    """Scan versioned directories for build files."""
    all_files = []
    
    if build_base.exists():
        for version_dir in build_base.iterdir():
            if version_dir.is_dir() and version_dir.name.startswith("MVC_Calculator-"):
                for pat in patterns:
                    all_files.extend(version_dir.glob(pat))
        
        old_msi_dir = build_base / "msi" / "builds"
        if old_msi_dir.exists():
            for pat in patterns:
                all_files.extend(old_msi_dir.glob(pat))
        
        for pat in patterns:
            all_files.extend(build_base.glob(pat))

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


def ensure_dir(ftp, remote: str):
    """Ensure remote directory exists, creating it if necessary."""
    parts = remote.strip("/").split("/")
    for part in parts:
        if not part:
            continue
        try:
            ftp.cwd(part)
        except ftplib.error_perm:
            ftp.mkd(part)
            ftp.cwd(part)


def upload(ftp, path: Path):
    """Upload a file to FTP with progress bar."""
    total = path.stat().st_size
    
    if HAS_TQDM:
        bar = tqdm(total=total, unit="B", unit_scale=True, desc=f"Uploading {path.name}")
    else:
        bar = SimpleProgress(total, f"Uploading {path.name}")
    
    def cb(chunk):
        bar.update(len(chunk))

    try:
        with path.open("rb") as f:
            ftp.storbinary(f"STOR {path.name}", f, 8192, cb)
    finally:
        bar.close()


def build_table(files, build_base: Path):
    rows = []
    for f in sorted(files, key=lambda x: x.name.lower()):
        size_bytes = f.stat().st_size
        if size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.0f}K"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.0f}M"
        mod = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        desc = detect_description(f.name)

        try:
            relative_path = f.relative_to(build_base)
            href = str(relative_path).replace("\\", "/")
        except ValueError:
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


def main():
    parser = argparse.ArgumentParser(
        description="Generate release page and upload to FTP (configurable paths)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default paths
  python deploy_release_ftp_configurable.py

  # Custom build directory and template
  python deploy_release_ftp_configurable.py --build-base /path/to/builds --template /path/to/template.html

  # Custom FTP settings
  python deploy_release_ftp_configurable.py --host ftp.example.com --user myuser --password mypass

  # Skip FTP upload (only generate HTML)
  python deploy_release_ftp_configurable.py --no-upload
        """
    )
    
    # Path arguments
    parser.add_argument("--build-base", type=Path, default=DEFAULT_BUILD_BASE,
                       help=f"Base directory for builds (default: {DEFAULT_BUILD_BASE})")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE,
                       help=f"HTML template file (default: {DEFAULT_TEMPLATE})")
    parser.add_argument("--output", type=Path, default=None,
                       help="Output HTML file path (default: <build-base>/index.html)")
    parser.add_argument("--target-dir", type=str, default=DEFAULT_TARGET_DIR,
                       help=f"FTP target directory (default: {DEFAULT_TARGET_DIR})")
    
    # FTP arguments
    parser.add_argument("--host", default=DEFAULT_HOST,
                       help=f"FTP host (default: {DEFAULT_HOST})")
    parser.add_argument("--user", default=DEFAULT_USER,
                       help=f"FTP username (default: {DEFAULT_USER})")
    parser.add_argument("--password", default=DEFAULT_PASS,
                       help="FTP password (default: from script)")
    parser.add_argument("--no-upload", action="store_true",
                       help="Skip FTP upload (only generate HTML)")
    
    args = parser.parse_args()
    
    # Set output path if not specified
    output = args.output if args.output else args.build_base / "index.html"
    script_dir = Path(__file__).parent
    
    try:
        print(f"Configuration:")
        print(f"  Build Base: {args.build_base}")
        print(f"  Template: {args.template}")
        print(f"  Output: {output}")
        print(f"  FTP Target: {args.target_dir}")
        print()
        
        versions = scan_builds(args.build_base, PATTERNS)
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

        notes = load_notes(latest, args.build_base)
        print(f"Loaded notes for {latest}: date={notes['date']}, tags={notes['tags']}")

        if not args.template.exists():
            print(f"ERROR: Template not found at {args.template}")
            return
        
        html = args.template.read_text(encoding="utf-8")
        if not html:
            print(f"ERROR: Template file is empty at {args.template}")
            return

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

        logo_path = find_logo_path(args.build_base, script_dir)
        logo_file = args.build_base / logo_path
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
        html = html.replace("{{LATEST_TABLE}}", build_table(versions[latest], args.build_base))

        if prev:
            prev_notes = load_notes(prev, args.build_base)
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
        {build_table(versions[prev], args.build_base)}

    </div>
</div>'''
            html = html.replace("{{PREV_VERSION}}", prev_section)
        else:
            html = html.replace("{{PREV_VERSION}}", "")

        if "{{" in html:
            print("WARNING: Some placeholders were not replaced!")
            remaining = re.findall(r'\{\{[^}]+\}\}', html)
            print(f"  Remaining placeholders: {remaining}")

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(html, encoding="utf-8")
        print(f"✓ index.html generated at: {output}")
        print(f"  File size: {output.stat().st_size} bytes")
        
        print(f"\n📦 Files ready for FTP upload:")
        print(f"  1. {output.name} ({output.stat().st_size} bytes)")
        if logo_file.exists():
            print(f"  2. {logo_path} ({logo_file.stat().st_size} bytes)")
        else:
            print(f"  2. {logo_path} (⚠️  not found)")
        
        print(f"\n📁 Build files in version directory:")
        version_dir = args.build_base / f"MVC_Calculator-{latest}"
        if version_dir.exists():
            for f in sorted(version_dir.iterdir()):
                if f.is_file() and f.suffix in [".msi", ".zip", ".deb", ".AppImage"]:
                    print(f"  - {f.name} ({f.stat().st_size / (1024*1024):.1f} MB)")
        
        if args.no_upload:
            print(f"\n⏭️  Skipping FTP upload (--no-upload flag set)")
            print(f"✅ HTML generated successfully. Ready for manual upload.")
        else:
            print(f"\n🔌 Connecting to FTP server: {args.host}")
            try:
                ftp = ftplib.FTP(args.host)
                ftp.login(args.user, args.password)
                print(f"✓ Connected and logged in")
                
                ensure_dir(ftp, args.target_dir)
                ftp.cwd(args.target_dir)
                print(f"✓ Changed to directory: {args.target_dir}")
                
                print(f"\n📤 Uploading build files for version {latest}:")
                for build_file in latest_files:
                    upload(ftp, build_file)
                
                notes_file = version_dir / "buildfiles" / f"RELEASE_NOTES-{latest}.txt"
                if not notes_file.exists():
                    notes_file = args.build_base / f"RELEASE_NOTES-{latest}.txt"
                
                if notes_file.exists():
                    print(f"\n📄 Uploading release notes:")
                    upload(ftp, notes_file)
                else:
                    print(f"\n⚠️  Warning: Release notes file not found")
                
                print(f"\n🌐 Uploading index.html:")
                upload(ftp, output)
                
                if logo_file.exists():
                    print(f"\n🖼️  Uploading logo:")
                    upload(ftp, logo_file)
                
                ftp.quit()
                print(f"\n✅ FTP upload complete!")
                print(f"   Files are now available at: https://downloads.moviolabs.com/MVC_Calculator/releases/")
                
            except ftplib.error_perm as e:
                print(f"\n❌ FTP Error: {e}")
                print(f"   Check your FTP credentials and server permissions")
            except Exception as e:
                print(f"\n❌ Upload Error: {e}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

