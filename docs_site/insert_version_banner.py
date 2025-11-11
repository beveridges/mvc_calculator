#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Insert version banner (MVC Calculator — vXX.XX) into MkDocs HTML template.
"""

from pathlib import Path
import re

# === 1. Paths ===
template_file = Path("overrides/partials/header.html")  # your MkDocs custom header
version_info_file = Path("../utilities/version_info.py")  # adjust if needed

# === 2. Get version name ===
try:
    data = version_info_file.read_text(encoding="utf-8")
    friendly = re.search(r'FRIENDLYVERSIONNAME\s*=\s*["\'](.+?)["\']', data).group(1)
    build = re.search(r'BUILDNUMBER\s*=\s*["\'](.+?)["\']', data).group(1)
    version_text = f"{friendly} — v{build}"
except Exception:
    version_text = "MVC Calculator — Version Unknown"

# === 3. Inject into header template ===
html = template_file.read_text(encoding="utf-8")

# Look for the search bar div and insert version text before it
pattern = r'(<div class="md-search".*?>)'
replacement = rf'<span class="app-version">{version_text}</span>\n\1'

if "app-version" not in html:
    html = re.sub(pattern, replacement, html, flags=re.DOTALL)
    template_file.write_text(html, encoding="utf-8")
    print(f"✅ Inserted version banner: {version_text}")
else:
    print("ℹ️ Version banner already present — no change.")
