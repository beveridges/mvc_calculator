#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate inline version string for MkDocs sidebar/header.
Example output:  MVC Calculator – version 25.11-alpha.01.13
"""

import re
from pathlib import Path

root = Path(__file__).resolve().parents[2]  # project root
vi = root / "utilities" / "version_info.py"

if not vi.exists():
    raise SystemExit("version_info.py not found. Run build.py first.")

# Import dynamically
namespace = {}
exec(vi.read_text(encoding="utf-8"), namespace)

app_name = namespace.get("FRIENDLYVERSIONNAME", "Unknown App")
build = namespace.get("BUILDNUMBER", "?.??")
version = namespace.get("VERSIONNUMBER", "?.??")

inline_html = f"""
<div class="inline-version">
  <span class="inline-version__name">{app_name}</span>
  <span class="inline-version__badge">{build}</span>
</div>
"""

out = root / "docs_site" / "overrides" / "partials" / "version_inline.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(inline_html, encoding="utf-8")
print(f"[ok] wrote version_inline.html: {app_name} / {build}")


def update_build_badge(target: Path, new_label: str) -> None:
    """Update the Build badge in markdown/HTML files."""
    if not target.exists():
        return

    text = target.read_text(encoding="utf-8")
    badge_url = f"https://img.shields.io/badge/build-{new_label}-blueviolet?style=flat-square"

    if target.suffix.lower() == ".md":
        badge_pattern = re.compile(r"(!\[Build\]\()[^)]+(\))")

        def repl(match: re.Match) -> str:
            return f"{match.group(1)}{badge_url}{match.group(2)}"
    else:
        badge_pattern = re.compile(r'(alt="Build"\s+src=")[^"]+(")')

        def repl(match: re.Match) -> str:
            return f'{match.group(1)}{badge_url}{match.group(2)}'

    new_text, count = badge_pattern.subn(repl, text)

    if count:
        target.write_text(new_text, encoding="utf-8")
        try:
            rel = target.relative_to(root)
        except ValueError:
            rel = target
        print(f"[ok] updated build badge in {rel}")


def update_version_badge(target: Path, new_label: str) -> None:
    """Update the Version badge in markdown/HTML files."""
    if not target.exists():
        return

    text = target.read_text(encoding="utf-8")
    badge_url = f"https://img.shields.io/badge/version-{new_label}-orange?style=flat-square"

    if target.suffix.lower() == ".md":
        badge_pattern = re.compile(r"(!\[Version\]\()[^)]+(\))")

        def repl(match: re.Match) -> str:
            return f"{match.group(1)}{badge_url}{match.group(2)}"
    else:
        badge_pattern = re.compile(r'(alt="Version"\s+src=")[^"]+(")')

        def repl(match: re.Match) -> str:
            return f'{match.group(1)}{badge_url}{match.group(2)}'

    new_text, count = badge_pattern.subn(repl, text)

    if count:
        target.write_text(new_text, encoding="utf-8")
        try:
            rel = target.relative_to(root)
        except ValueError:
            rel = target
        print(f"[ok] updated version badge in {rel}")


# Prepare badge labels - both use consistent format; hyphens escaped for shields.io
build_badge_label = version.replace("-", "--")   # Build: 26.01-alpha.01 (VERSIONNUMBER)
version_badge_label = build.replace("-", "--")   # Version: 26.01-alpha.01.02 (BUILDNUMBER)

targets = [
    root / "docs_site" / "docs" / "_index_raw.md",
    root / "docs_site" / "docs" / "index.md",
    root / "docs_site" / "docs" / "user-guide.md",
    root / "docs_site" / "site" / "index.html",
    root / "docs_site" / "site" / "_index_raw" / "index.html",
]

for path in targets:
    update_build_badge(path, build_badge_label)
    update_version_badge(path, version_badge_label)
