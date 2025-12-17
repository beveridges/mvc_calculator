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


def extract_build_badge_label(version_number: str) -> str:
    """
    Extract build badge label from VERSIONNUMBER.
    Example: "25.12-alpha.01" -> "alpha--25.12--01"
    """
    # Parse version like "25.12-alpha.01"
    parts = version_number.split("-")
    if len(parts) >= 2:
        yy_mm = parts[0]  # "25.12"
        channel_parts = parts[1].split(".")  # ["alpha", "01"]
        if len(channel_parts) >= 2:
            channel_name = channel_parts[0]  # "alpha"
            channel_num = channel_parts[1]  # "01"
            return f"{channel_name}--{yy_mm}--{channel_num}"
    # Fallback: use version with -- instead of -
    return version_number.replace("-", "--")


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


# Prepare badge labels
build_badge_label = extract_build_badge_label(version)
version_badge_label = build.replace("-", "--")

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
