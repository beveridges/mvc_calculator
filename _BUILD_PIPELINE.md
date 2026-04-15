# MVC Calculator — Build pipeline and release plan

**Last updated:** April 2026

This document is the canonical guide for building and releasing MVC Calculator on Windows and Linux, including optional **@hfmdd.de institutional (preactivated)** packages.

**Layout:** Implementation scripts live under **`___BUILD___/`** (see `___BUILD___/README.md`). You still run **`python BUILD_ALL_WINDOWS.py`** and **`python deploy_release_ftp.py`** from the **repository root** — thin launchers forward into `___BUILD___/` with the correct working directory.

### Paths (repository layout)

| What | Where |
|------|--------|
| **Working directory for all build/deploy commands** | **Repository root** (where `main.py` lives). Launchers set this automatically. |
| **Entry launchers** (short names) | `BUILD_ALL_WINDOWS.py`, `BUILD_ALL_LINUX.py`, `deploy_release_ftp.py`, `deploy_release_ftp_configurable.py` at **repo root** — they invoke scripts under `___BUILD___/`. |
| **Build implementation** | `___BUILD___/BUILD_ALL_WINDOWS.py`, `___BUILD___/BUILD_ALL_LINUX.py`, `___BUILD___/build_windows_portable.py`, `___BUILD___/build_windows_msi.py`, `___BUILD___/build_linux_*.py`, `___BUILD___/deploy_release_ftp.py`, `___BUILD___/deploy_release_ftp_configurable.py` |
| **Release HTML template** | `___BUILD___/TEMPLATE_RELEASE.html` |
| **Preactivation helper** (unchanged) | `scripts/build_preactivated_entitlement.py` |
| **Version file (read/written by portable build)** | `utilities/version_info.py` |
| **Windows build output tree** | `%USERPROFILE%\Documents\.builds\mvc_calculator\` |
| **Linux staging + logs** | `~/.linux_builds/MVC_CALCULATOR/linux_builds/` (artifacts then copied next to Windows output; **`WIN_BUILD_BASE`** is set in `___BUILD___/BUILD_ALL_LINUX.py`) |
| **Local junk / old backups** | `___BUILD___/trash/` (gitignored) |

**Direct invocation (optional):** `python ___BUILD___/BUILD_ALL_WINDOWS.py` from repo root — same effect as the launcher if the current working directory is the repo root.

---

## Build modes (choose one path per release)

| Mode | When to use | Windows | Linux (WSL) |
|------|-------------|---------|-------------|
| **Standard licensed** | Normal customers; activation via Licence manager or entitlement | `python BUILD_ALL_WINDOWS.py` | After Windows: `python BUILD_ALL_LINUX.py` |
| **Licensed + Open Access** | Same version: licensed build plus license-free OA variant | `python BUILD_ALL_WINDOWS.py -oa` | `python BUILD_ALL_LINUX.py -oa` |
| **Institutional @hfmdd.de (preactivated)** | Bundled entitlement; app unlocks from packaged `preactivated/entitlement.json` | `python BUILD_ALL_WINDOWS.py --preactivated-hfmdd` | `python BUILD_ALL_LINUX.py --preactivated-hfmdd --hfmdd-license-file MVC_Calculator/license.key` |

**Rules:**

- **Linux builds** assume you already ran **`BUILD_ALL_WINDOWS.py`** so `utilities/version_info.py` has the correct incremented `BUILDNUMBER`.
- **`--preactivated-hfmdd`** requires a valid **`license.key`**. Recommended location is `MVC_Calculator/license.key` (gitignored local folder), then pass `--hfmdd-license-file MVC_Calculator/license.key`. Generate it first (see [Phase AA — HFMDD key creation](#phase-aa--hfmdd-key-creation-preactivated-only) below).
- Do **not** combine `--preactivated-entitlement` and `--preactivated-hfmdd` on the same command (use one or the other).

---

## New build plan (end-to-end)

### Phase A — Prepare (Windows, developer machine)

1. Activate Conda: `conda activate mvccalculator`
2. **Help / MkDocs (optional manual step):** `cd docs_site` then `mkdocs build` — use this for **doc-only edits** (Markdown, theme, nav) when you are **not** running a full `BUILD_ALL_WINDOWS.py` yet, or to **preview** (`mkdocs serve`). A normal **`BUILD_ALL_WINDOWS.py`** already runs **`mkdocs build`** via **`___BUILD___/build_windows_portable.py`** after updating `version_info.py`; run mkdocs yourself if the portable step **skipped or failed** docs (e.g. mkdocs missing on PATH, `SKIP_DOCS`, or build error).
3. **Choose build mode** (see table above).
4. **If institutional HFMDD:** complete **Phase AA** below, then continue to Phase B.

### Phase AA — HFMDD key creation (preactivated only)

Run once per institutional build cycle (or whenever you rotate keys).

1. Create/enter local key folder (gitignored):

```bash
mkdir MVC_Calculator
cd MVC_Calculator
```

2. Generate wildcard institutional license (example: Germany, no expiration):

```bash
python ..\generate_license.py institutional@hfmdd.de DE 0 --wildcard-hfmdd
```

This writes **`license.key`** in `MVC_Calculator/` (recommended local secret path).

3. Return to repo root, then run build with explicit key path:

```bash
cd ..
python BUILD_ALL_WINDOWS.py --preactivated-hfmdd --hfmdd-license-file MVC_Calculator\license.key
```

### Phase B — Windows build (increments build number)

Run from **project root** on **Windows** (not WSL):

```bash
# Standard licensed
python BUILD_ALL_WINDOWS.py

# Licensed + OA
python BUILD_ALL_WINDOWS.py -oa

# Institutional preactivated (needs license.key first)
python BUILD_ALL_WINDOWS.py --preactivated-hfmdd --hfmdd-license-file MVC_Calculator\license.key
python BUILD_ALL_WINDOWS.py --preactivated-hfmdd --hfmdd-license-file MVC_Calculator\license.key --hfmdd-bundle-id HFMDD-2026-04
python BUILD_ALL_WINDOWS.py --preactivated-hfmdd --hfmdd-license-file path\to\license.key
```

**What runs:** `___BUILD___/build_windows_portable.py` (PyInstaller onedir) → `___BUILD___/build_windows_msi.py` (MSI + portable ZIP). With `-oa`, a second portable + MSI + ZIP for Open Access.

**Output:** `%USERPROFILE%\Documents\.builds\mvc_calculator\`  
- `MVC_Calculator-{BUILDNUMBER}\` — MSI, portable ZIP, `buildfiles\`  
- If `-oa`: `MVC_Calculator-oa-{BUILDNUMBER}\` — OA MSI and ZIP  

### Phase C — Sync source (for Linux)

5. Commit and push so WSL (or Linux builder) has the same `version_info.py`:

```bash
git add .
git commit -m "Your release message"
git push
```

### Phase D — Linux build (WSL)

6. `conda activate mvccalculator`
7. `git pull`
8. From **project root in WSL**:

```bash
python BUILD_ALL_LINUX.py
python BUILD_ALL_LINUX.py -oa
python BUILD_ALL_LINUX.py --preactivated-hfmdd --hfmdd-license-file MVC_Calculator/license.key
python BUILD_ALL_LINUX.py --preactivated-hfmdd --hfmdd-license-file MVC_Calculator/license.key --hfmdd-bundle-id HFMDD-2026-04
```

**What runs:** `___BUILD___/build_linux_portable.py` → `___BUILD___/build_linux_appimage.py` → `___BUILD___/build_linux_deb.py` (and OA variants if `-oa`).

**Artifacts:** Built under `~/.linux_builds/MVC_CALCULATOR/linux_builds/`, then copied next to the matching Windows output folder. The Windows destination is **`WIN_BUILD_BASE`** in **`___BUILD___/BUILD_ALL_LINUX.py`** (default: `%USERPROFILE%\Documents\.builds\mvc_calculator\`, accessed from WSL as `/mnt/c/Users/<you>/...`). Adjust that constant if your drive letter or username differs.

### Phase E — Deploy (optional)

9. Preview the download page locally: `python deploy_release_ftp.py`  
10. Upload builds + generated `index.html`: `python deploy_release_ftp.py -u`  
    Target: `ftp.moviolabs.com:/public_html/downloads/MVC_Calculator/releases/`  
    Public URL (typical): `https://moviolabs.com/downloads/MVC_Calculator/releases/` (or `https://downloads.moviolabs.com/MVC_Calculator/releases/` depending on hosting)

**What the deploy script produces:** `index.html` in your build base (e.g. `%USERPROFILE%\Documents\.builds\mvc_calculator\index.html`) from **`___BUILD___/TEMPLATE_RELEASE.html`**, using scanned installers under `MVC_Calculator-{version}\`. See [Releases page sections (Latest, Previous, LTS, Development)](#releases-page-sections-latest-previous-lts-development) below.

---

## Institutional @hfmdd.de prerequisite (preactivated builds)

Before **`--preactivated-hfmdd`**, the signing key file must exist:

1. Create/enter local key folder (gitignored):

```bash
mkdir MVC_Calculator
cd MVC_Calculator
```

2. Generate wildcard institutional license (example: Germany, no expiration):

```bash
python ..\generate_license.py institutional@hfmdd.de DE 0 --wildcard-hfmdd
```

This writes **`license.key`** in `MVC_Calculator/` (recommended local secret path).

3. Run build from repo root with explicit key path:

```bash
cd ..
python BUILD_ALL_WINDOWS.py --preactivated-hfmdd --hfmdd-license-file MVC_Calculator\license.key
```

4. Or build entitlement manually and use the explicit entitlement path:

```bash
python scripts/build_preactivated_entitlement.py --license-file MVC_Calculator/license.key --output preactivated/entitlement.json --issued-for hfmdd.de --bundle-id HFMDD-2026-04
python BUILD_ALL_WINDOWS.py --preactivated-entitlement preactivated/entitlement.json
```

Full operator notes: **`PREACTIVATED_HFMDD_RUNBOOK.md`**.

---

## Build flags reference (`BUILD_ALL_WINDOWS.py` / `BUILD_ALL_LINUX.py`)

| Flag | Meaning |
|------|---------|
| `-oa` / `--oa` | Also build Open Access (license-free) artifacts for the same `BUILDNUMBER`. |
| `--preactivated-hfmdd` | Run `scripts/build_preactivated_entitlement.py`, write `preactivated/entitlement.json` from the specified key file, bundle into portable output. |
| `--hfmdd-license-file PATH` | Source license file for `--preactivated-hfmdd` (default: `license.key`; recommended: `MVC_Calculator/license.key`). |
| `--hfmdd-bundle-id ID` | Optional metadata stored in generated entitlement JSON. |
| `--preactivated-entitlement PATH` | Use a pre-built `entitlement.json` file (do not combine with `--preactivated-hfmdd`). |

Lower-level scripts (run from **repo root** so imports resolve):

- `___BUILD___/build_windows_portable.py --preactivated-entitlement <path>` — bundle entitlement into PyInstaller output.
- `___BUILD___/build_linux_portable.py --preactivated-entitlement <path>` — same for Linux portable tree.

---

## Releases page sections (Latest, Previous, LTS, Development)

The deploy script (**launcher** `deploy_release_ftp.py` → **`___BUILD___/deploy_release_ftp.py`**) generates the public downloads listing. Section **headings** (em dash before the version string):

| Section | Source |
|--------|--------|
| **Latest Release —** `{version}` | Newest licensed build found by the scan. |
| **Development Release —** `{version}` | Newest **Open Access** build (`MVC_Calculator-oa-*`), if present. |
| **Previous Release —** `{version}` | Second-newest **licensed** build. |
| **Long Term Support (LTS) Release —** `{version}` | Third-newest **licensed** build — **only if at least three** distinct licensed versions exist with artifacts. |

**LTS pipeline implication:** The LTS block appears automatically when your build directory still contains **three or more** licensed version folders (e.g. `MVC_Calculator-26.02-alpha.01.05`, `.01.04`, `.01.03`) each with the usual MSI / portable ZIP / DEB / AppImage files. If you delete older directories and only two licensed versions remain, the LTS section is omitted from `index.html`.

**Copy under each section title** comes from `RELEASE_NOTES-{version}.txt` (`Description:` line). If omitted:

- **Development (OA):** default text describes an internal / unstable build.
- **LTS:** default text describes a stable, long-term / production-oriented build.

Override either by editing `Description:` in the notes file for that version (preferred: `MVC_Calculator-{version}\buildfiles\RELEASE_NOTES-{version}.txt`).

**FTP upload:** With `-u`, the script uploads artifacts and release notes for **Latest**, **Previous**, and **LTS** (when that slot exists), plus Development OA files, `index.html`, logo, and auxiliary files (e.g. tracker) per existing flags.

---

## Step-by-step (legacy numbered sections)

### 0. In Windows: local development

- Edit and test in your repository.

### 1. In Windows: activate Conda

```bash
conda activate mvccalculator
```

### 2. In Windows: build help (optional)

```bash
cd docs_site
mkdocs build
```

Preview:

```bash
mkdocs serve -f docs_site/mkdocs.yml
```

Browser: `http://127.0.0.1:8000`

### 3. In Windows: `BUILD_ALL_WINDOWS.py`

See [Phase B](#phase-b--windows-build-increments-build-number) and [Build modes](#build-modes-choose-one-path-per-release).

### 4. In Windows: commit and push (for WSL)

```bash
git add .
git commit -m "Your commit message"
git push
```

### 5–6. In WSL: environment and pull

```bash
conda activate mvccalculator
git pull
```

### 7. In WSL: `BUILD_ALL_LINUX.py`

See [Phase D](#phase-d--linux-build-wsl).

### 8. Review before upload (optional)

```bash
python deploy_release_ftp.py
```

Generates `index.html` locally without uploading. Open it in a browser and confirm **Latest**, **Development** (if OA builds exist), **Previous**, and **LTS** (if three+ licensed versions are present) look correct.

### 9. Deploy to server

```bash
python deploy_release_ftp.py -u
```

**Deploy script behavior:**

- Scans versioned directories under the build base (e.g. `C:\Users\Scott\Documents\.builds\mvc_calculator\MVC_Calculator-{version}\`) for licensed artifacts; OA builds under `MVC_Calculator-oa-{version}\`.
- Builds `index.html` from **`___BUILD___/TEMPLATE_RELEASE.html`** (placeholders: latest table, optional OA section, previous section, optional LTS section — see [Releases page sections](#releases-page-sections-latest-previous-lts-development)).
- Prefers `MVC_Calculator-{version}\buildfiles\RELEASE_NOTES-{version}.txt`, then fallbacks documented in **`___BUILD___/deploy_release_ftp.py`**.
- Uploads binaries and matching release notes for latest, previous, and LTS rows when applicable, then OA, `index.html`, logo, and auxiliary files.
- Smart skip if remote file same size; `--force` / `--force-file` available.

---

## File structure after build (example)

Keeping **multiple** licensed version folders (here `.01.05` newest, `.01.04` previous, `.01.03` LTS) allows the deploy script to fill **Latest**, **Previous**, and **LTS** on the downloads page:

```
C:\Users\Scott\Documents\.builds\mvc_calculator\
├── MVC_Calculator-26.02-alpha.01.05\          ← Latest
│   ├── …msi, …zip, …deb, …AppImage
│   └── buildfiles\RELEASE_NOTES-26.02-alpha.01.05.txt
├── MVC_Calculator-26.02-alpha.01.04\          ← Previous
│   └── …
├── MVC_Calculator-26.02-alpha.01.03\          ← LTS (third-newest licensed)
│   └── …
├── MVC_Calculator-oa-26.02-alpha.01.05\       ← Development (OA), same plan as builds
│   └── …
└── index.html                                 (generated by `deploy_release_ftp.py` launcher → `___BUILD___/deploy_release_ftp.py`)
```

---

## Common deploy options

```bash
python deploy_release_ftp.py -u --upload-maxmsp-only
python deploy_release_ftp.py -u --upload-auxiliary
python deploy_release_ftp.py -u --force
```

**Server path:** `ftp.moviolabs.com:/public_html/downloads/MVC_Calculator/releases/`

---

## Important notes

1. **Version consistency:** Linux master build reads `BUILDNUMBER` from `utilities/version_info.py` updated by the Windows portable step — run Windows first.
2. **OA builds:** `-oa` produces separate `MVC_Calculator-oa-*` artifacts; same semantic version, different filenames.
3. **Preactivated builds:** Do not commit production `license.key` / `preactivated/entitlement.json` to public repos; treat as release secrets.
4. **Release notes:** Deploy script looks under `buildfiles\` first for `RELEASE_NOTES-{version}.txt`.
5. **LTS on the website:** Requires **three** licensed version directories with artifacts under the build base. **`___BUILD___/BUILD_ALL_WINDOWS.py`** runs `cleanup_old_version_directories(..., keep=3)` by default, which keeps the three newest licensed folders — matching **Latest**, **Previous**, and **LTS**. If you change `keep` to **2** (or delete old folders by hand), the LTS section will not appear. Linux staging cleanup in **`___BUILD___/BUILD_ALL_LINUX.py`** only trims **old `.deb` / `.AppImage` files** in the Linux build scratch area; it does not remove whole `MVC_Calculator-{version}` trees on Windows.

---

## Quick reference

Commands below use **repo-root launchers**; implementations live under **`___BUILD___/`** — see [Paths (repository layout)](#paths-repository-layout).

```bash
# Windows — standard
python BUILD_ALL_WINDOWS.py

# Windows — licensed + OA
python BUILD_ALL_WINDOWS.py -oa

# Windows — institutional @hfmdd.de (create key first in MVC_Calculator/license.key)
python BUILD_ALL_WINDOWS.py --preactivated-hfmdd --hfmdd-license-file MVC_Calculator\license.key

# WSL — after git pull, matching version_info
python BUILD_ALL_LINUX.py
python BUILD_ALL_LINUX.py -oa
python BUILD_ALL_LINUX.py --preactivated-hfmdd --hfmdd-license-file MVC_Calculator/license.key

# Upload (includes index.html + artifacts for Latest / Previous / LTS when 3+ licensed versions exist)
python deploy_release_ftp.py -u
```
