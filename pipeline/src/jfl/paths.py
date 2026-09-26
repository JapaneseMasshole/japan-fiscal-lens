"""Repository paths, resolved from this file so commands work from any directory."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SOURCES_FILE = DATA_DIR / "sources.yaml"
WEB_DATA_DIR = REPO_ROOT / "web" / "public" / "data"
