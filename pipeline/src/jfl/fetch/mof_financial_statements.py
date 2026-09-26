"""Fetch MOF 国の財務書類 (national government financial statements) Excel files.

For each fiscal year, the MOF page links three workbooks:
    fy{YEAR}gassan.xlsx    一般会計・特別会計 合算
    fy{YEAR}ippan.xlsx     一般会計
    fy{YEAR}renketsu.xlsx  連結
Each workbook contains the four statements (BS, 業務費用計算書,
資産・負債差額増減計算書, 区分別収支計算書).

We discover links from the year page rather than hard-coding file names,
because naming has changed between years.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import requests

from jfl.fetch.common import Link, download, find_links, get_html, session, write_manifest
from jfl.paths import RAW_DIR
from jfl.sources import Source

SOURCE_ID = "mof-fs"

# Map a file name to its variant. Older years use "renketu" (no s) and "gassan".
VARIANT_PATTERNS: dict[str, re.Pattern[str]] = {
    "gassan": re.compile(r"gassan", re.I),
    "ippan": re.compile(r"ippan", re.I),
    "renketsu": re.compile(r"renke(ts|t)u", re.I),
}


@dataclass
class PlannedFile:
    variant: str
    url: str
    dest: Path
    # If the page links a file for a different year (a publishing mistake seen on
    # the FY2021 page), `url` is the corrected guess and `fallback_url` the link
    # as published. The transform step verifies the year from the sheet itself.
    fallback_url: str | None = None


YEAR_IN_URL = re.compile(r"fy(\d{4})", re.I)


def correct_year(url: str, year: int) -> str | None:
    """Return `url` with every fyYYYY replaced by fy{year}, or None if it already matches."""
    found = {int(y) for y in YEAR_IN_URL.findall(url)}
    if not found or found == {year}:
        return None
    return YEAR_IN_URL.sub(f"fy{year}", url)


def classify(link: Link) -> str | None:
    name = link.url.rsplit("/", 1)[-1]
    for variant, pattern in VARIANT_PATTERNS.items():
        if pattern.search(name):
            return variant
    return None


def plan(html: str, page_url: str, year: int, out_root: Path = RAW_DIR) -> list[PlannedFile]:
    """Decide which files to download from a year page's HTML. Pure; no network."""
    links = find_links(html, page_url, (".xlsx", ".xls"))
    planned: list[PlannedFile] = []
    taken: set[str] = set()
    for link in links:
        variant = classify(link)
        if variant is None or variant in taken:
            continue
        taken.add(variant)
        ext = Path(link.url.split("?", 1)[0]).suffix.lower()
        dest = out_root / SOURCE_ID / f"fy{year}" / f"{variant}{ext}"
        fixed = correct_year(link.url, year)
        if fixed:
            print(f"warning: FY{year} page links {link.url}; trying {fixed} first")
            planned.append(PlannedFile(variant, fixed, dest, fallback_url=link.url))
        else:
            planned.append(PlannedFile(variant=variant, url=link.url, dest=dest))
    if not planned:
        raise RuntimeError(
            f"No financial-statement workbooks found on {page_url}. "
            "The page layout may have changed; check it and update VARIANT_PATTERNS."
        )
    return sorted(planned, key=lambda p: p.variant)


def run(source: Source, year: int, dry_run: bool = False, out_root: Path = RAW_DIR) -> list[Path]:
    page_url = source.year_pages.get(year)
    if not page_url:
        known = ", ".join(str(y) for y in sorted(source.year_pages)) or "none"
        raise SystemExit(
            f"No year page configured for FY{year} in data/sources.yaml (known: {known})."
        )

    s = session()
    html = get_html(s, page_url)
    files = plan(html, page_url, year, out_root)

    if dry_run:
        for f in files:
            print(f"[dry-run] {f.variant:9s} {f.url} -> {f.dest}")
        return [f.dest for f in files]

    entries = []
    for f in files:
        print(f"Downloading {f.variant}: {f.url}")
        try:
            entries.append(download(s, f.url, f.dest))
        except requests.HTTPError as e:
            if not f.fallback_url:
                raise
            print(f"  {e}; falling back to the published link {f.fallback_url}")
            entries.append(download(s, f.fallback_url, f.dest))
    manifest = write_manifest(files[0].dest.parent, SOURCE_ID, page_url, entries)
    print(f"Wrote {manifest}")
    return [f.dest for f in files]
