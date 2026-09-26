"""Load and validate the dataset catalog in data/sources.yaml."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from jfl.paths import SOURCES_FILE

REQUIRED_FIELDS = ("id", "level", "publisher", "title_ja", "title_en", "listing_url", "verified")
LEVELS = {"national", "local"}


@dataclass(frozen=True)
class Source:
    id: str
    level: str
    publisher: str
    title_ja: str
    title_en: str
    listing_url: str
    verified: str
    statements: list[str] = field(default_factory=list)
    year_pages: dict[int, str] = field(default_factory=dict)
    variants: dict[str, str] = field(default_factory=dict)
    notes: str = ""


def load_sources(path: Path = SOURCES_FILE) -> dict[str, Source]:
    """Return sources keyed by id. Raises ValueError on a malformed catalog."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    entries = raw.get("sources") if isinstance(raw, dict) else None
    if not isinstance(entries, list):
        raise ValueError(f"{path}: expected a top-level 'sources' list")

    sources: dict[str, Source] = {}
    for i, entry in enumerate(entries):
        missing = [f for f in REQUIRED_FIELDS if not entry.get(f)]
        if missing:
            raise ValueError(f"{path}: source #{i} is missing {missing}")
        if entry["level"] not in LEVELS:
            raise ValueError(f"{path}: {entry['id']}: level must be one of {sorted(LEVELS)}")
        if entry["id"] in sources:
            raise ValueError(f"{path}: duplicate source id {entry['id']!r}")
        if not str(entry["listing_url"]).startswith("https://"):
            raise ValueError(f"{path}: {entry['id']}: listing_url must be https")

        sources[entry["id"]] = Source(
            id=entry["id"],
            level=entry["level"],
            publisher=entry["publisher"],
            title_ja=entry["title_ja"],
            title_en=entry["title_en"],
            listing_url=entry["listing_url"],
            verified=str(entry["verified"]),
            statements=list(entry.get("statements") or []),
            year_pages={int(k): v for k, v in (entry.get("year_pages") or {}).items()},
            variants=dict(entry.get("variants") or {}),
            notes=(entry.get("notes") or "").strip(),
        )
    return sources
