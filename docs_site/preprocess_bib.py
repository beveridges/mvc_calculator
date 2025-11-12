#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Preprocess Markdown with citations for MkDocs
---------------------------------------------
• Converts docs/_index_raw.md → docs/index.md
• Applies APA 6th CSL style and renders citations inline
• Ensures a clean “## References” heading before reference list
• Prevents accidental folder creation (site/_index_raw/)
• Compatible with MkDocs + ReadTheDocs themes
"""

import re
from pathlib import Path
import pypandoc

# =============================================================================
# 1. Paths
# =============================================================================
RAW_MD = Path("docs/_index_raw.md")
OUT_MD = Path("docs/index.md")
BIB_PATH = "docs/bibs/IMM_DRUMMER.bib"
CSL_PATH = "docs/bibs/apa-6th-edition.csl"

print(f"🔄 Converting {RAW_MD} → {OUT_MD}")

# Safety check: prevent "_index_raw" directory problem
bad_folder = Path("site/_index_raw")
if bad_folder.exists() and bad_folder.is_dir():
    import shutil
    print(f"⚠️ Found stray folder {bad_folder} — removing...")
    shutil.rmtree(bad_folder)

# ... existing imports/paths ...

markdown_source = RAW_MD.read_text(encoding="utf-8")

cleaned_md = pypandoc.convert_text(
    markdown_source,
    to="gfm",           # keep Markdown for MkDocs
    format="md",
    extra_args=[
        "--citeproc",
        "--strip-comments",
        "--wrap=none",  # <— prevent Pandoc from inserting soft wraps
        f"--bibliography={BIB_PATH}",
        f"--csl={CSL_PATH}",
    ],
)

# Collapse single newlines (soft breaks) into spaces, but keep paragraph breaks.
# i.e., turn "...The MVC\nCalculator provides..." -> "...The MVC Calculator provides..."
import re
cleaned_md = re.sub(r"(?<!\n)\n(?!\n)", " ", cleaned_md)

# (keep your existing References cleanup)



# =============================================================================
# 2. Read + Convert Markdown to Markdown (NOT HTML)
# =============================================================================
markdown_source = RAW_MD.read_text(encoding="utf-8")

cleaned_md = pypandoc.convert_text(
    markdown_source,
    to="gfm",  # GitHub-flavored Markdown (MkDocs-friendly)
    format="md",
    extra_args=[
        "--citeproc",
        "--strip-comments",
        f"--bibliography={BIB_PATH}",
        f"--csl={CSL_PATH}",
    ],
)

# =============================================================================
# 3. Normalize “References” heading and remove stray HTML comments
# =============================================================================
cleaned_md = re.sub(r"<!--.*?-->", "", cleaned_md, flags=re.DOTALL)
cleaned_md = re.sub(
    r"(?:^|\n)(?:#+\s*)?references\s*(?:#+)?",
    "\n## References",
    cleaned_md,
    flags=re.IGNORECASE,
)

if not cleaned_md.strip().endswith("\n"):
    cleaned_md += "\n"

# =============================================================================
# 4. Write final file
# =============================================================================
OUT_MD.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.write_text(cleaned_md, encoding="utf-8")
print(f"✅ Done — Clean Markdown written to {OUT_MD}")

















# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# """
# Preprocess Markdown with citations for MkDocs
# ---------------------------------------------
# • Converts docs/_index_raw.md → docs/index.md
# • Applies APA 6th CSL style and renders citations inline
# • Ensures a clean “## References” heading before reference list
# • Compatible with MkDocs and ReadTheDocs-style pipelines
# """

# import re
# from pathlib import Path
# import pypandoc

# # =============================================================================
# # 1. Paths
# # =============================================================================
# RAW_MD = Path("docs/_index_raw.md")
# OUT_MD = Path("docs/index.md")
# BIB_PATH = "docs/bibs/IMM_DRUMMER.bib"
# CSL_PATH = "docs/bibs/apa-6th-edition.csl"

# print(f"🔄 Converting {RAW_MD} → {OUT_MD}")

# # =============================================================================
# # 2. Read + Convert Markdown to HTML (string)
# # =============================================================================
# markdown_source = RAW_MD.read_text(encoding="utf-8")

# html_text = pypandoc.convert_text(
    # markdown_source,
    # to="html",
    # format="md",
    # extra_args=[
        # "--citeproc",
        # "--strip-comments",
        # f"--bibliography={BIB_PATH}",
        # f"--csl={CSL_PATH}",
    # ],
# )

# # =============================================================================
# # 3. Normalize “References” heading and remove stray HTML comments
# # =============================================================================
# html_text = re.sub(r"<!--.*?-->", "", html_text, flags=re.DOTALL)
# html_text = re.sub(r"(?:<h2.*?>)?\s*References\s*(?:</h2>)?", "## References", html_text, flags=re.IGNORECASE)

# # Optional: make sure final References section is separated by a newline
# if not html_text.strip().endswith("</div>"):
    # html_text += "\n"

# # =============================================================================
# # 4. Write final file
# # =============================================================================
# OUT_MD.write_text(html_text, encoding="utf-8")
# print(f"✅ Done — Cleaned output written to {OUT_MD}")


















# # # # python preprocess_bib.py && mkdocs serve
# # # #python preprocess_bib.py && mkdocs build --clean


# # #!/usr/bin/env python3
# # # -*- coding: utf-8 -*-
# # """
# # Preprocess Markdown with citations for MkDocs
# # ---------------------------------------------
# # • Converts docs/_index_raw.md → docs/index.md
# # • Fixes 'date' → 'year' fields in .bib so (Author, 2005) renders properly
# # • Applies APA 6th CSL style via Pandoc
# # • Ensures a single clean “## References” heading before the ref list
# # • Removes numeric citation artifacts (*1*, 1, etc.)
# # • Optimized for MkDocs (ReadTheDocs theme)
# # """

# # import re
# # import pypandoc
# # from pathlib import Path

# # # --- Paths ---
# # raw = Path("docs/_index_raw.md")
# # out = Path("docs/index.md")
# # bib = Path("docs/bibs/IMM_DRUMMER.bib")
# # csl = Path("docs/bibs/apa-6th-edition.csl")

# # # --- Step 1: Fix 'date' → 'year' fields in the .bib ---
# # if bib.exists():
    # # bib_text = bib.read_text(encoding="utf-8")
    # # fixed_bib = re.sub(
        # # r"(?m)^\s*date\s*=\s*\{(\d{4})\}", r"  year = {\1}", bib_text
    # # )
    # # if bib_text != fixed_bib:
        # # bib.write_text(fixed_bib, encoding="utf-8")
        # # print(f"🩹 Converted 'date' → 'year' in {bib.name}")
# # else:
    # # print(f"⚠️ Missing bibliography file: {bib}")

# # # --- Step 2: Convert Markdown with Pandoc ---
# # print(f"🔄 Converting {raw} → {out}")
# # pypandoc.convert_file(
    # # str(raw),
    # # to="markdown_strict",  # strict Markdown → proper citation syntax
    # # outputfile=str(out),
    # # extra_args=[
        # # "--citeproc",                                 # enable CSL
        # # "--strip-comments",                           # remove <!-- -->
        # # f"--bibliography={bib}",
        # # f"--csl={csl}",
        # # "--metadata", "lang=en-US",
        # # "--metadata", "link-citations=true",
        # # "--metadata", "reference-section-title=References",
    # # ],
# # )

# # # --- Step 3: Post-process output ---
# # text = out.read_text(encoding="utf-8")

# # # Remove duplicate or malformed "References" headers
# # text =  (r"(?im)^#+\s*references\s*\n+", "", text)

# # # Insert a clean References heading above ref list (if missing)
# # if "## References" not in text:
    # # text = re.sub(
        # # r"(\n)(\s*Konrad|[A-Z].+,\s*\d{4}\..+)",
        # # r"\1## References\n\n\2",
        # # text,
        # # count=1,
    # # )
    # # if "## References" not in text:
        # # text += "\n\n---\n\n## References\n"

# # # Remove stray numeric markers (*1*, 1, etc.)
# # # text = re.sub(r"\s*\*?\d+\*?\s*", " ", text)
# # text = re.sub(r"(?m)^\s*\*\d+\*\s*$", "", text)

# # # Normalize spacing and blank lines
# # text = re.sub(r"\n{3,}", "\n\n", text).strip()

# # # --- Write final clean Markdown ---
# # out.write_text(text + "\n", encoding="utf-8")
# # print(f"✅ Clean Markdown with references written to {out}")




# # # #!/usr/bin/env python3
# # # # -*- coding: utf-8 -*-
# # # """
# # # Preprocess Markdown with citations for MkDocs
# # # ---------------------------------------------
# # # • Converts docs/_index_raw.md → docs/index.md
# # # • Forces Pandoc to apply APA 6th CSL correctly
# # # • Converts 'date' → 'year' in .bib entries so (Author, 2005) works
# # # • Guarantees a clean “## References” heading before the reference list
# # # • Compatible with MkDocs ReadTheDocs theme
# # # """

# # # import re
# # # import pypandoc
# # # from pathlib import Path

# # # # --- Paths ---
# # # raw = Path("docs/_index_raw.md")
# # # out = Path("docs/index.md")
# # # bib = Path("docs/bibs/IMM_DRUMMER.bib")
# # # csl = Path("docs/bibs/apa-6th-edition.csl")

# # # # --- Step 1: Fix 'date' → 'year' fields in the .bib ---
# # # if bib.exists():
    # # # bib_text = bib.read_text(encoding="utf-8")
    # # # fixed_bib = re.sub(
        # # # r"(?m)^\s*date\s*=\s*\{(\d{4})\}", r"  year = {\1}", bib_text
    # # # )
    # # # if bib_text != fixed_bib:
        # # # bib.write_text(fixed_bib, encoding="utf-8")
        # # # print(f"🩹 Converted 'date' → 'year' in {bib.name}")
# # # else:
    # # # print(f"⚠️ Missing bibliography file: {bib}")

# # # # --- Step 2: Run Pandoc conversion ---
# # # print(f"🔄 Converting {raw} → {out}")
# # # pypandoc.convert_file(
    # # # str(raw),
    # # # to="markdown_strict",  # ✅ NOT gfm – ensures full CSL citation support
    # # # outputfile=str(out),
    # # # extra_args=[
        # # # "--citeproc",                                 # enable CSL
        # # # "--strip-comments",
        # # # f"--bibliography={bib}",
        # # # f"--csl={csl}",
        # # # "--metadata", "lang=en-US",
        # # # "--metadata", "link-citations=true",
        # # # "--metadata", "reference-section-title=References",
    # # # ],
# # # )

# # # # --- Step 3: Post-process Markdown output ---
# # # text = out.read_text(encoding="utf-8")

# # # # Remove duplicate/malformed "References" headers
# # # text = re.sub(r"(?im)^#+\s*references\s*\n+", "", text)

# # # # Insert clean heading above final ref list (if missing)
# # # if "## References" not in text:
    # # # text = re.sub(
        # # # r"(\n)(\s*Konrad|[A-Z].+,\s*\d{4}\..+)", r"\1## References\n\n\2", text, count=1
    # # # )
    # # # if "## References" not in text:
        # # # text += "\n\n---\n\n## References\n"

# # # # Remove leftover citation markers (*1*, 1, etc.)
# # # text =                                                                                                                                            (r"\s*\*?\d+\*?\s*", " ", text)

# # # # Clean excess blank lines
# # # text = re.sub(r"\n{3,}", "\n\n", text).strip()

# # # # Write clean Markdown
# # # out.write_text(text + "\n", encoding="utf-8")
# # # print(f"✅ Clean Markdown with references written to {out}")





# # # # #!/usr/bin/env python3
# # # # # -*- coding: utf-8 -*-
# # # # """
# # # # Preprocess Markdown with citations for MkDocs
# # # # ---------------------------------------------
# # # # • Converts docs/_index_raw.md → docs/index.md
# # # # • Applies APA 6th CSL style via Pandoc
# # # # • Ensures a single “## References” heading above citations
# # # # • Keeps publication years visible
# # # # """

# # # # import re
# # # # import pypandoc
# # # # from pathlib import Path

# # # # # --- Paths ---
# # # # raw = Path("docs/_index_raw.md")
# # # # out = Path("docs/index.md")
# # # # bib = Path("docs/bibs/IMM_DRUMMER.bib")
# # # # csl = Path("docs/bibs/apa-6th-edition.csl")

# # # # # --- Convert raw → processed Markdown ---
# # # # print(f"🔄 Converting {raw} → {out}")
# # # # pypandoc.convert_file(
    # # # # str(raw),
    # # # # to="gfm",  # GitHub-flavored Markdown for MkDocs
    # # # # outputfile=str(out),
    # # # # extra_args=[
        # # # # "--citeproc",                   # enable citations
        # # # # "--strip-comments",             # clean HTML artifacts
        # # # # f"--bibliography={bib}",
        # # # # f"--csl={csl}",
        # # # # "--metadata", "link-citations=true",  # keep clickable links and years
    # # # # ],
# # # # )

# # # # # --- Post-process output ---
# # # # text = out.read_text(encoding="utf-8")

# # # # # Remove stray duplicated reference headers
# # # # text = re.sub(r"#+\s*References\s*\n+", "", text)

# # # # # Insert clean References heading before the refs block
# # # # if re.search(r"^---", text, flags=re.MULTILINE):
    # # # # # Insert after final horizontal rule
    # # # # text = re.sub(r"(---\s*\n+)(?=\Z)", r"\1\n## References\n", text)
# # # # elif "## References" not in text:
    # # # # text += "\n\n---\n\n## References\n"

# # # # # Remove stray italicized or standalone numeric artifacts (*1*, 1, etc.)
# # # # text = re.sub(r"\s*\*?\d+\*?\s*", " ", text)

# # # # # Write clean output
# # # # out.write_text(text.strip() + "\n", encoding="utf-8")
# # # # print(f"✅ Clean Markdown with formatted references written to {out}")











# # # # #!/usr/bin/env python3
# # # # # -*- coding: utf-8 -*-
# # # # """
# # # # Preprocess Markdown with citations for MkDocs
# # # # ---------------------------------------------
# # # # • Converts docs/_index_raw.md → docs/index.md
# # # # • Applies APA 6th CSL style via Pandoc
# # # # • Cleans stray numeric artifacts (*1*, *2*, etc.)
# # # # • Ensures "## References" heading is present
# # # # """

# # # # import re
# # # # import pypandoc
# # # # from pathlib import Path

# # # # # --- Paths ---
# # # # raw = Path("docs/_index_raw.md")
# # # # out = Path("docs/index.md")
# # # # bib = Path("docs/bibs/IMM_DRUMMER.bib")
# # # # csl = Path("docs/bibs/apa-6th-edition.csl")

# # # # # --- Convert raw → processed Markdown ---
# # # # print(f"🔄 Converting {raw} → {out}")
# # # # pypandoc.convert_file(
    # # # # str(raw),
    # # # # to="gfm",  # GitHub-flavored Markdown for MkDocs
    # # # # outputfile=str(out),
    # # # # extra_args=[
        # # # # "--citeproc",
        # # # # "--strip-comments",
        # # # # f"--bibliography={bib}",
        # # # # f"--csl={csl}",
    # # # # ],
# # # # )

# # # # # --- Post-process output ---
# # # # text = out.read_text(encoding="utf-8")

# # # # # Ensure a References heading exists
# # # # if "## References" not in text:
    # # # # text += "\n\n---\n\n## References\n"

# # # # # Remove stray italicized numbers like *1*, *2*, etc.
# # # # text = re.sub(r"\*?\s*\d+\*?", "", text)

# # # # out.write_text(text, encoding="utf-8")
# # # # print(f"✅ Clean Markdown with formatted references written to {out}")







# # # # # import pypandoc
# # # # # from pathlib import Path

# # # # # raw = Path("docs/_index_raw.md")
# # # # # out = Path("docs/index.md")

# # # # # pypandoc.convert_file(
    # # # # # str(raw),
    # # # # # to="gfm",  # ✅ ensures MkDocs-compatible Markdown
    # # # # # outputfile=str(out),
    # # # # # extra_args=[
        # # # # # "--citeproc",
        # # # # # "--strip-comments",
        # # # # # "--bibliography=docs/bibs/IMM_DRUMMER.bib",
        # # # # # "--csl=docs/bibs/apa-6th-edition.csl",
    # # # # # ],
# # # # # )

# # # # # print(f"✅ Clean Markdown with formatted references written to {out}")










# # # # # import pypandoc
# # # # # from pathlib import Path

# # # # # raw = Path("docs/_index_raw.md")
# # # # # out = Path("docs/index.md")

# # # # # pypandoc.convert_file(
    # # # # # str(raw),
    # # # # # to="gfm",
    # # # # # outputfile=str(out),
    # # # # # extra_args=[
        # # # # # "--citeproc",  # Enable citation processor
        # # # # # "--strip-comments",  # Prevent stray <!-- -->
        # # # # # "--bibliography=docs/bibs/IMM_DRUMMER.bib",
        # # # # # "--csl=docs/bibs/apa-6th-edition.csl",
    # # # # # ],
# # # # # )

# # # # # print(f"✅ Clean inline HTML fragment written to {out}")










# # # # # import pypandoc
# # # # # from pathlib import Path

# # # # # raw = Path("docs/index_raw.md")
# # # # # out = Path("docs/index.md")

# # # # # # ✅ Convert using Pandoc’s HTML writer
# # # # # pypandoc.convert_file(
    # # # # # str(raw),
    # # # # # to="html",
    # # # # # outputfile=str(out),
    # # # # # extra_args=[
        # # # # # "--standalone",          # ensure complete output
        # # # # # "--citeproc",            # enable citation processing
        # # # # # "--bibliography=docs/bibs/IMM_DRUMMER.bib",
        # # # # # "--csl=docs/bibs/apa-6th-edition.csl",
    # # # # # ],
# # # # # )

# # # # # print(f"✅ Clean HTML version generated at {out}")















# # # # # import pypandoc
# # # # # from pathlib import Path

# # # # # raw = Path("docs/index_raw.md")
# # # # # out = Path("docs/index.md")

# # # # # pypandoc.convert_file(
    # # # # # str(raw),
    # # # # # to="markdown",              # or "html" if you prefer
    # # # # # outputfile=str(out),
    # # # # # extra_args=[
        # # # # # "--citeproc",
        # # # # # "--bibliography=docs/bibs/IMM_DRUMMER.bib",
        # # # # # "--csl=docs/bibs/apa-6th-edition.csl",
    # # # # # ],
# # # # # )
# # # # # print(f"✅ Generated {out}")












# # # # # # import re
# # # # # # from pathlib import Path
# # # # # # import pypandoc

# # # # # # # === Paths ===
# # # # # # BIB = Path("docs/bibs/IMM_DRUMMER.bib")
# # # # # # CSL = Path("docs/bibs/apa-6th-edition.csl")
# # # # # # DOCS = Path("docs")

# # # # # # # === Conversion ===
# # # # # # for raw in DOCS.glob("*_raw.md"):
    # # # # # # out = raw.with_name(raw.stem.replace("_raw", "") + ".md")
    # # # # # # print(f"📖 Generating {out.name} from {raw.name}")

    # # # # # # pypandoc.convert_file(
        # # # # # # str(raw),
        # # # # # # to="html",
        # # # # # # outputfile=str(out),
        # # # # # # extra_args=[
            # # # # # # "--citeproc",
            # # # # # # f"--bibliography={BIB}",
            # # # # # # f"--csl={CSL}"
        # # # # # # ]
    # # # # # # )

    # # # # # # # === Cleanup Pandoc artifacts ===
    # # # # # # text = Path(out).read_text(encoding="utf-8")

    # # # # # # # Remove Pandoc header attributes like {#references .unnumbered}
    # # # # # # text = re.sub(r"\s*\{#references[^\}]*\}", "", text)

    # # # # # # # Remove Pandoc ":::: {#refs ...}" and similar blocks
    # # # # # # text = re.sub(r"^:+\s*\{#refs[^\}]*\}.*?$", "", text, flags=re.MULTILINE)
    # # # # # # text = re.sub(r"^:+$", "", text, flags=re.MULTILINE)

    # # # # # # Path(out).write_text(text, encoding="utf-8")

# # # # # # print("✅ All Markdown pages updated and cleaned.")
