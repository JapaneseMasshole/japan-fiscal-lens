"""Fetch 社会保障費用統計 (IPSS) Excel tables.

The listing page links one page per fiscal year (fsss-R06/fsss_R06.html …), with
the fiscal year as link text (「令和６年度」). Each year page links dozens of
tables; we take three, found by the table number in the link text:

    table08.xlsx  第８表  社会保障給付費の部門別推移 (医療 / 年金 / 福祉その他)
    table13.xlsx  第13表  機能別社会保障給付費の推移 (高齢, 保健医療, 家族 …)
    table14.xlsx  第14表  社会保障財源（ILO基準）の項目別推移 (保険料, 公費 …)

Each table is a time series, so the newest year page is enough.
"""

from __future__ import annotations

import re
from pathlib import Path

from jfl.fetch.common import download, find_links, get_html, session, write_manifest
from jfl.fetch.mic import Planned, compact, era_to_fy
from jfl.paths import RAW_DIR
from jfl.sources import Source

SOURCE_ID = "ipss-ss-cost"

TABLES = {"table08": 8, "table13": 13, "table14": 14}
TABLE_NO = re.compile(r"^第([0-9０-９]+)表")


def year_pages(listing_html: str, listing_url: str) -> dict[int, str]:
    pages: dict[int, str] = {}
    for link in find_links(listing_html, listing_url, (".html", ".asp")):
        if "/fsss-" in link.url and "fsss_" in link.url:
            fy = era_to_fy(link.text)
            if fy and fy not in pages:
                pages[fy] = link.url
    if not pages:
        raise RuntimeError(f"No year pages found on {listing_url}; the layout may have changed.")
    return pages


def plan(html: str, page_url: str) -> list[Planned]:
    by_no: dict[int, Planned] = {}
    for link in find_links(html, page_url, (".xlsx",)):
        m = TABLE_NO.match(compact(link.text))
        if not m:
            continue
        no = int(m.group(1).translate(str.maketrans("０１２３４５６７８９", "0123456789")))
        by_no.setdefault(no, Planned("", link.text, link.url))
    planned = []
    for key, no in TABLES.items():
        if no not in by_no:
            raise RuntimeError(f"第{no}表 not found on {page_url}; the layout may have changed.")
        planned.append(Planned(key, by_no[no].label, by_no[no].url))
    return planned


def run(source: Source, year: int | None, dry_run: bool = False, out_root: Path = RAW_DIR):
    """Newest published year by default."""
    s = session()
    pages = year_pages(get_html(s, source.listing_url), source.listing_url)
    y = max(pages) if year is None else year
    if y not in pages:
        raise SystemExit(f"FY{y}: not listed on {source.listing_url} (latest: FY{max(pages)}).")
    files = plan(get_html(s, pages[y]), pages[y])
    if dry_run:
        for f in files:
            print(f"[dry-run] FY{y} {f.key:8s} {f.label} {f.url}")
        return
    out_dir = out_root / SOURCE_ID / f"fy{y}"
    entries = []
    for f in files:
        print(f"Downloading {f.key}: {f.label} {f.url}")
        entries.append(download(s, f.url, out_dir / f"{f.key}.xlsx"))
    write_manifest(out_dir, SOURCE_ID, pages[y], entries)
    (out_dir / "labels.tsv").write_text(
        "".join(f"{f.key}\t{f.label}\n" for f in files), encoding="utf-8"
    )
