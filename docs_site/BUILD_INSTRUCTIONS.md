# Building the Documentation

## Prerequisites

You need to have **MkDocs** installed. If you don't have it yet:

```bash
pip install mkdocs
pip install mkdocs-material  # Optional: if using material theme
```

Or if you're using conda:

```bash
conda install -c conda-forge mkdocs in the 
```

## Building the Documentation

### Option 1: From Project Root

Navigate to the project root directory and run:

```bash
mkdocs build -f docs_site/mkdocs.yml
```

This will build the documentation site into `docs_site/site/`

### Option 2: From docs_site Directory

Navigate to the `docs_site` directory and run:

```bash
cd docs_site
mkdocs build
```

## Previewing the Documentation

To preview the documentation locally (with live reload):

```bash
mkdocs serve -f docs_site/mkdocs.yml
```

Or from the `docs_site` directory:

```bash
cd docs_site
mkdocs serve
```

Then open your browser to: `http://127.0.0.1:8000`

## Output Location

The built documentation will be in:
- `docs_site/site/` - Contains all HTML, CSS, JS, and assets

## Troubleshooting

### MkDocs Not Found

If you get "mkdocs: command not found":
1. Make sure MkDocs is installed: `pip install mkdocs`
2. Check your PATH includes Python scripts directory
3. Try using: `python -m mkdocs build -f docs_site/mkdocs.yml`

### Theme Issues

If you get theme-related errors:
1. Install the readthedocs theme: `pip install mkdocs-readthedocs-theme`
2. Or install material theme: `pip install mkdocs-material`

### Build Errors

If the build fails:
1. Check `mkdocs.yml` for syntax errors
2. Verify all markdown files exist in `docs_site/docs/`
3. Check for broken links or missing images

## Automated Build

The documentation is also built automatically when you run the main build script (if configured).

