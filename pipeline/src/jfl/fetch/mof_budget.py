"""Fetch MOF 一般会計予算 (the Cabinet's budget, as enacted) PDFs.

Each fiscal year has a page (linked from the budget index as 「令和８年度予算」) that
records the budget's path (概算要求 → 政府案 → 成立 → 補正), and a 政府案 page
(「令和８年度予算政府案」) that links the budget documents. MOF publishes no Excel
for these, so we take the PDFs, found by their link text:

    gaisan.pdf           一般会計歳入歳出概算          歳入, 主要経費別 歳出
    tax.pdf              租税及び印紙収入概算          税目別 税収
    frame.pdf            予算フレーム                  国債費 = 債務償還費 + 利払費 …
    social_security.pdf  社会保障関係予算               年金・医療・介護 … 内訳

The year page itself is kept too (status.html): it states whether the Diet
enacted the budget 「政府案どおり」, which the transform step checks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup

from jfl.fetch.common import download, find_links, get_html, session, write_manifest
from jfl.fetch.mic import compact, era_to_fy
from jfl.paths import RAW_DIR
from jfl.sources import Source

SOURCE_ID = "mof-budget"

# key → pattern the (whitespace-free) link text must match.
FILES = {
    "gaisan": re.compile(r"^.*年度一般会計歳入歳出概算"),
    "tax": re.compile(r"^.*年度租税及び印紙収入概算"),
    "frame": re.compile(r"^.*年度予算フレーム"),
    "social_security": re.compile(r"^社会保障関係予算"),
}


@dataclass
class Planned:
    key: str
    label: str
    url: str


def year_pages(listing_html: str, listing_url: str) -> dict[int, str]:
    """「令和８年度予算」 links on the budget index. URLs are irregular (fy2025/fy2025.html,
    fy2026/index.html), and older years point at the National Diet Library archive."""
    pages: dict[int, str] = {}
    for link in find_links(listing_html, listing_url, (".html", ".htm")):
        if re.fullmatch(r"(令和|平成)(元|[0-9０-９]+)年度予算", compact(link.text)):
            fy = era_to_fy(link.text)
            if fy and fy not in pages and link.url.startswith("https://www.mof.go.jp/"):
                pages[fy] = link.url
    if not pages:
        raise RuntimeError(f"No year pages on {listing_url}; the layout may have changed.")
    return pages


def seifuan_page(year_html: str, year_url: str, year: int) -> str:
    """The 「令和８年度予算政府案」 page linked from a year page."""
    for link in find_links(year_html, year_url, (".html", ".htm")):
        text = compact(link.text)
        if text.endswith("年度予算政府案") and era_to_fy(text) == year:
            return link.url
    raise RuntimeError(f"No 政府案 link on {year_url}; the layout may have changed.")


def plan(html: str, page_url: str) -> list[Planned]:
    """Pick the budget PDFs from a 政府案 page. Pure; no network."""
    links = find_links(html, page_url, (".pdf",))
    planned = []
    for key, pattern in FILES.items():
        # 暫定予算 files have similar titles; they are never the budget itself.
        match = next(
            (lk for lk in links if pattern.match(compact(lk.text)) and "暫定" not in lk.text),
            None,
        )
        if match is None:
            raise RuntimeError(
                f"No link matching {pattern.pattern!r} on {page_url}; the layout may have changed."
            )
        planned.append(Planned(key, match.text, match.url))
    return planned


def enactment(status_html: str) -> str | None:
    """How the main budget (not a 暫定予算 or 補正予算) was enacted, per the year page.

    "as_proposed" when enacted 「政府案どおり」, "amended" when the Diet changed it
    (FY2025: 「衆議院における予算修正（国会修正）」), None while it is still pending.
    """
    text = compact(BeautifulSoup(status_html, "html.parser").get_text())
    if "国会修正" in text or "修正成立" in text:
        return "amended"
    # 「令和８年度予算は政府案どおり成立」; 暫定予算 / 補正予算 sentences must not match.
    if re.search(r"(令和|平成)(元|[0-9０-９]+)年度予算は政府案どおり成立", text):
        return "as_proposed"
    return None


def run(source: Source, year: int | None, dry_run: bool = False, out_root: Path = RAW_DIR):
    """Newest enacted budget by default."""
    s = session()
    pages = year_pages(get_html(s, source.listing_url), source.listing_url)
    for y in sorted(pages, reverse=True) if year is None else [year]:
        if y not in pages:
            raise SystemExit(f"FY{y}: no year page on {source.listing_url}.")
        status = get_html(s, pages[y])
        state = enactment(status)
        if state is None:
            print(f"FY{y}: budget not enacted yet; skipping")
            continue
        if state == "amended":
            # The 政府案 PDFs would not match the budget as enacted.
            raise SystemExit(f"FY{y}: the Diet amended the budget; the 政府案 PDFs don't apply.")
        page = seifuan_page(status, pages[y], y)
        files = plan(get_html(s, page), page)
        if dry_run:
            for f in files:
                print(f"[dry-run] FY{y} {f.key:16s} {f.label} {f.url}")
            return
        out_dir = out_root / SOURCE_ID / f"fy{y}"
        entries = [download(s, pages[y], out_dir / "status.html")]
        for f in files:
            print(f"Downloading {f.key}: {f.label} {f.url}")
            entries.append(download(s, f.url, out_dir / f"{f.key}.pdf"))
        write_manifest(out_dir, SOURCE_ID, page, entries)
        (out_dir / "labels.tsv").write_text(
            "".join(f"{f.key}\t{f.label}\n" for f in files), encoding="utf-8"
        )
        return
    raise SystemExit("No enacted budget found.")
