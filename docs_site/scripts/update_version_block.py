#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate inline version string for MkDocs sidebar/header.
Example output:  MVC Calculator – version 25.11-alpha.01.13
"""

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

# Format: MVC_Calculator-25.11-alpha.01.57
version_text = f"{app_name.replace(' ', '_')}-{build}"

html = f"""
<div class="inline-version" style="text-align:center; font-size:1.1em; margin:2px 0 8px 0; color:#000; font-weight:500;">
  {version_text}
</div>
"""

out = root / "docs_site" / "overrides" / "partials" / "version_inline.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html, encoding="utf-8")
print(f"[ok] wrote version_inline.html: {version_text}")
