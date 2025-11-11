#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
release_to_github.py — Publishes latest MSI + ZIP as a GitHub release
--------------------------------------------------------------------------------
✓ Uploads MSI + ZIP only (no source archives)
✓ Creates a detached tag (not linked to any commit)
✓ Works for the Application Template and derived apps
Requires:
  • GitHub CLI (gh)
  • Git installed and authenticated with 'gh auth login'
================================================================================
PASSWORD FOR 
imm.qtm.machine
Nc)D6J(Fs1q+t=&x
"""

import subprocess, sys
from pathlib import Path

APP_NAME = "MVC_Calculator"
BUILD_DIR = Path.home() / "Documents" / ".builds" / APP_NAME.lower() / "msi" / "builds"

# ----------------------------------------------------------------------
# Locate latest MSI and ZIP
# ----------------------------------------------------------------------
msi_files = sorted(BUILD_DIR.glob(f"{APP_NAME}-*.msi"), key=lambda p: p.stat().st_mtime, reverse=True)
zip_files = sorted(BUILD_DIR.glob(f"{APP_NAME}-*-portable.zip"), key=lambda p: p.stat().st_mtime, reverse=True)

if not msi_files or not zip_files:
    print("❌ No build files found. Run build_template_msi.py first.")
    sys.exit(1)

latest_msi = msi_files[0]
latest_zip = zip_files[0]
tag_name = latest_msi.stem.replace(f"{APP_NAME}-", "")
release_title = f"{APP_NAME} {tag_name}"

print(f"📦 Preparing release for {release_title}")
print(f"   MSI: {latest_msi.name}")
print(f"   ZIP: {latest_zip.name}")

# ----------------------------------------------------------------------
# Step 1 — Create a truly detached tag (not tied to any commit)
# ----------------------------------------------------------------------
try:
    # Create lightweight tag
    subprocess.run(["git", "tag", "-f", tag_name], check=True)

    # Overwrite it with a null reference to detach from all commits
    subprocess.run(["git", "update-ref", f"refs/tags/{tag_name}", "0000000000000000000000000000000000000000"], check=False)

    # Push the tag reference explicitly to remote
    subprocess.run(["git", "push", "-f", "origin", f"refs/tags/{tag_name}"], check=True)

    print(f"[OK] Created detached tag '{tag_name}' (no commit linkage).")
except subprocess.CalledProcessError as e:
    print(f"[WARN] Tag push failed: {e} — continuing...")

# ----------------------------------------------------------------------
# Step 2 — Create GitHub release (no source code zips)
# ----------------------------------------------------------------------
cmd = [
    "gh", "release", "create", tag_name,
    str(latest_msi),
    str(latest_zip),
    "--title", release_title,
    "--notes", f"Automated release for {APP_NAME} build {tag_name}",
    "--latest"
]

try:
    subprocess.run(cmd, check=True)
    print(f"\n✅ GitHub release {tag_name} created successfully!")
    print("   (No 'Source code' assets should appear on the release.)")
except subprocess.CalledProcessError as e:
    print(f"❌ Failed to create release: {e}")
    sys.exit(1)

# ----------------------------------------------------------------------
# Done
# ----------------------------------------------------------------------
print("\n🎉 Release workflow complete.")
print("Visit your repository → Releases to confirm only MSI + ZIP are attached.")




















# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# """
# release_to_github.py — Publishes latest MSI + ZIP as a GitHub release
# ✓ Uploads MSI + ZIP only
# ✓ Skips "Source code" assets by creating a detached release tag
# Requires: GitHub CLI (gh)
# """

# import subprocess, sys
# from pathlib import Path

# APP_NAME = "MyAppTemplate"
# BUILD_DIR = Path.home() / "Documents" / ".builds" / APP_NAME.lower() / "msi" / "builds"

# # ------------------------------------------------------------------------------
# # Find latest MSI + ZIP
# # ------------------------------------------------------------------------------
# msi_files = sorted(BUILD_DIR.glob(f"{APP_NAME}-*.msi"), key=lambda p: p.stat().st_mtime, reverse=True)
# zip_files = sorted(BUILD_DIR.glob(f"{APP_NAME}-*-portable.zip"), key=lambda p: p.stat().st_mtime, reverse=True)

# if not msi_files or not zip_files:
    # print("❌ No build files found. Run build_template_msi.py first.")
    # sys.exit(1)

# latest_msi = msi_files[0]
# latest_zip = zip_files[0]

# # Extract version tag
# tag_name = latest_msi.stem.replace(f"{APP_NAME}-", "")
# release_title = f"{APP_NAME} {tag_name}"

# print(f"📦 Preparing release for {release_title}")
# print(f"   MSI: {latest_msi.name}")
# print(f"   ZIP: {latest_zip.name}")

# # ------------------------------------------------------------------------------
# # Step 1: Create a detached tag (prevents GitHub from generating source zips)
# # ------------------------------------------------------------------------------
# try:
    # subprocess.run(["git", "tag", "-f", tag_name, "--no-sign"], check=True)
    # subprocess.run(["git", "push", "-f", "origin", f"refs/tags/{tag_name}"], check=True)
    # print(f"[OK] Created detached tag '{tag_name}'")
# except subprocess.CalledProcessError:
    # print("[WARN] Could not push tag (non-fatal).")

# # ------------------------------------------------------------------------------
# # Step 2: Create release with only binary assets
# # ------------------------------------------------------------------------------
# cmd = [
    # "gh", "release", "create", tag_name,
    # str(latest_msi),
    # str(latest_zip),
    # "--title", release_title,
    # "--notes", f"Automated release for {APP_NAME} build {tag_name}",
    # "--latest"
# ]

# try:
    # subprocess.run(cmd, check=True)
    # print(f"\n✅ GitHub release {tag_name} created successfully!")
    # print("   (No 'Source code' assets were included.)")
# except subprocess.CalledProcessError as e:
    # print(f"❌ Failed to create release: {e}")
    # sys.exit(1)
