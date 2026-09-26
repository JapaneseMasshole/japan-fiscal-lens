"""Fetch 総務省 (MIC) local-government datasets.

MIC file names are opaque serial numbers (main_content/001031221.xlsx), so files
are identified by their link text on the official page (「兵庫県」,
「全市町村の主要財政指標」 …). Year pages are discovered from the listing page by
their link text (「令和6年度主要財政指標一覧」), because their URLs are irregular.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import requests

from jfl.fetch.common import download, find_links, get_html, session, write_manifest
from jfl.paths import RAW_DIR
from jfl.sources import Source

PREFECTURES = [
    "北海道",
    "青森県",
    "岩手県",
    "宮城県",
    "秋田県",
    "山形県",
    "福島県",
    "茨城県",
    "栃木県",
    "群馬県",
    "埼玉県",
    "千葉県",
    "東京都",
    "神奈川県",
    "新潟県",
    "富山県",
    "石川県",
    "福井県",
    "山梨県",
    "長野県",
    "岐阜県",
    "静岡県",
    "愛知県",
    "三重県",
    "滋賀県",
    "京都府",
    "大阪府",
    "兵庫県",
    "奈良県",
    "和歌山県",
    "鳥取県",
    "島根県",
    "岡山県",
    "広島県",
    "山口県",
    "徳島県",
    "香川県",
    "愛媛県",
    "高知県",
    "福岡県",
    "佐賀県",
    "長崎県",
    "熊本県",
    "大分県",
    "宮崎県",
    "鹿児島県",
    "沖縄県",
]  # fmt: skip  (JIS X 0401 order: index + 1 = prefecture code)

ERA = re.compile(r"(令和|平成)(元|\d+)年度")


def era_to_fy(text: str) -> int | None:
    m = ERA.search(text.translate(str.maketrans("０１２３４５６７８９", "0123456789")))
    if not m:
        return None
    n = 1 if m.group(2) == "元" else int(m.group(2))
    return (2018 if m.group(1) == "令和" else 1988) + n


def compact(text: str) -> str:
    return "".join(text.split())


@dataclass
class Planned:
    key: str  # file stem in data/raw/<source>/fy<year>/
    label: str  # link text as published
    url: str


# ---------------------------------------------------------------- 主要財政指標一覧

INDICATOR_FILES = {
    # key: substring that must appear in the link text
    "prefectures": "全都道府県",
    "municipalities": "全市町村",
    "municipal_averages_by_prefecture": "都道府県別平均",
    "designated_cities": "政令指定都市",
    "prefectural_capitals": "道府県庁所在市",
}


def indicator_year_pages(listing_html: str, listing_url: str) -> dict[int, str]:
    pages: dict[int, str] = {}
    for link in find_links(listing_html, listing_url, (".html", ".htm")):
        if "主要財政指標一覧" in link.text:
            fy = era_to_fy(link.text)
            if fy and fy not in pages:
                pages[fy] = link.url
    return pages


def plan_indicators(html: str, page_url: str) -> list[Planned]:
    links = find_links(html, page_url, (".xlsx", ".xls"))
    planned = []
    for key, needle in INDICATOR_FILES.items():
        match = next((lk for lk in links if needle in compact(lk.text)), None)
        if match:
            planned.append(Planned(key, match.text, match.url))
    if not any(p.key in ("prefectures", "municipalities") for p in planned):
        raise RuntimeError(
            f"No indicator workbooks found on {page_url}; the layout may have changed."
        )
    return planned


# ------------------------------------------------- 統一的な基準による財務書類 (詳細版)


def plan_unified(html: str, page_url: str) -> list[Planned]:
    """Excel links: the all-prefecture file, one per prefecture, and the indicator lists."""
    planned: list[Planned] = []
    for link in find_links(html, page_url, (".xlsx", ".xls")):
        text = compact(link.text)
        text = re.sub(r"[（(].*?[)）]", "", text)  # drop "(EXCEL:123KB)"
        if text == "都道府県":
            planned.append(Planned("prefectures", link.text, link.url))
        elif text in PREFECTURES:
            code = PREFECTURES.index(text) + 1
            planned.append(Planned(f"pref-{code:02d}", link.text, link.url))
        elif "都道府県指標一覧" in text:
            planned.append(Planned("indicators_prefectures", link.text, link.url))
        elif "市区町村指標一覧" in text or "市町村指標一覧" in text:
            planned.append(Planned("indicators_municipalities", link.text, link.url))
    # Keep the first link per key (a page lists each file once in the detailed section).
    seen: set[str] = set()
    planned = [p for p in planned if not (p.key in seen or seen.add(p.key))]
    n_pref = sum(p.key.startswith("pref-") for p in planned)
    if n_pref == 0:
        raise RuntimeError(
            f"No per-prefecture workbooks found on {page_url}; the layout may have changed."
        )
    if n_pref != 47:
        print(f"warning: found {n_pref} of 47 prefecture workbooks on {page_url}")
    return planned


def unified_year_page(source: Source, year: int) -> str:
    if year in source.year_pages:
        return source.year_pages[year]
    reiwa = year - 2018
    if reiwa < 1:
        raise SystemExit(
            f"FY{year}: add its page to data/sources.yaml (pre-Reiwa pages are irregular)."
        )
    return f"https://www.soumu.go.jp/iken/kokaikei/R{reiwa:02d}_chihou_zaimusyorui.html"


# ------------------------------------------------------------------------ runner


def _download_all(
    s, source_id: str, year: int, page_url: str, files: list[Planned], out_root: Path
):
    out_dir = out_root / source_id / f"fy{year}"
    entries = []
    for f in files:
        ext = Path(f.url.split("?", 1)[0]).suffix.lower()
        print(f"Downloading {f.key}: {f.label} {f.url}")
        entries.append(download(s, f.url, out_dir / f"{f.key}{ext}"))
    write_manifest(out_dir, source_id, page_url, entries)
    # Which link text each file came from (e.g. pref-28 ← 「兵庫県」).
    (out_dir / "labels.tsv").write_text(
        "".join(f"{f.key}\t{f.label}\n" for f in files), encoding="utf-8"
    )


def run_indicators(source: Source, year: int | None, dry_run=False, out_root: Path = RAW_DIR):
    s = session()
    pages = indicator_year_pages(get_html(s, source.listing_url), source.listing_url)
    years = sorted(y for y in pages if y >= FIRST_INDICATOR_YEAR) if year is None else [year]
    for y in years:
        if y not in pages:
            print(f"FY{y}: no 主要財政指標一覧 page listed; skipping")
            continue
        files = plan_indicators(get_html(s, pages[y]), pages[y])
        if dry_run:
            for f in files:
                print(f"[dry-run] FY{y} {f.key:34s} {f.url}")
            continue
        _download_all(s, source.id, y, pages[y], files, out_root)


def run_unified(source: Source, year: int | None, dry_run=False, out_root: Path = RAW_DIR):
    s = session()
    years = [max(source.year_pages)] if year is None else [year]  # latest only by default (large)
    for y in years:
        page = unified_year_page(source, y)
        try:
            html = get_html(s, page)
        except requests.HTTPError as e:
            print(f"FY{y}: {page} not available ({e}); skipping")
            continue
        files = plan_unified(html, page)
        if dry_run:
            for f in files:
                print(f"[dry-run] FY{y} {f.key:28s} {f.label} {f.url}")
            continue
        _download_all(s, source.id, y, page, files, out_root)


FIRST_INDICATOR_YEAR = 2015  # 10 years of history by default; older years on request
