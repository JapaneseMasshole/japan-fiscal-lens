# jfl-pipeline

Turns official government files into chart-ready JSON for the website.

```
fetch/      download originals into data/raw/<source-id>/fy<year>/ (never edited)
transform/  parse Excel → tidy CSV in data/processed/ (unified units: 億円)
validate/   reconciliation checks (e.g. assets = liabilities + net assets)
export/     write JSON for web/public/data/
```

## Commands

```bash
pip install -e ".[dev]"
jfl sources                       # list datasets in data/sources.yaml
jfl fetch mof-fs --year 2024      # MOF national financial statements (xlsx)
jfl fetch mof-fs --year 2024 --dry-run   # show what would be downloaded
pytest
ruff check .
```

Each fetch writes a `manifest.json` next to the files, recording the source URL, SHA-256 hash, size and fetch time, so anyone can check that their download matches ours.

Government sites can be slow or change their HTML. Fetchers find file links on the official listing page instead of hard-coding file names, and fail loudly when nothing matches.
