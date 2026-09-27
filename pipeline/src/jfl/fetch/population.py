"""Fetch 総務省統計局 人口推計 (population estimates as of 1 October) from e-Stat.

e-Stat lists one set of tables per year. Download links are opaque
(file-download?statInfId=…), so the table is identified by its title:
第３表「年齢（5歳階級）、男女別人口及び割合－総人口（各年10月1日現在）」, which
holds the total population for the last five years in thousands.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from jfl.fetch.common import download, get_html, session, write_manifest
from jfl.fetch.mic import Planned, compact
from jfl.paths import RAW_DIR
from jfl.sources import Source

SOURCE_ID = "sb-population"
ESTAT = "https://www.e-stat.go.jp"
ANNUAL = (
    ESTAT + "/stat-search/files?page=1&layout=datalist&cycle=7&toukei=00200524"
    "&tstat=000000090001&tclass1=000001011679&tclass2val=0"
)
YEAR_PARAM = re.compile(r"[?&]year=(\d{4})0(?:&|$)")
TITLE = "総人口（各年10月1日現在）"


def year_pages(html: str) -> dict[int, str]:
    """Year facet links (「2024年」) on the annual listing."""
    soup = BeautifulSoup(html, "html.parser")
    pages: dict[int, str] = {}
    for a in soup.find_all("a", href=True):
        m = YEAR_PARAM.search(a["href"])
        if m and compact(a.get_text()) == f"{m.group(1)}年":
            pages.setdefault(int(m.group(1)), urljoin(ESTAT, a["href"]))
    if not pages:
        raise RuntimeError("No year links on the e-Stat listing; the layout may have changed.")
    return pages


def plan(html: str) -> Planned:
    """The formatted Excel (「EXCEL 閲覧用」) of 第３表 on a year page."""
    soup = BeautifulSoup(html, "html.parser")
    for article in soup.select("article.stat-dataset_list-item"):
        title = compact(article.get_text(" "))
        if TITLE not in title or "年齢（5歳階級）" not in title:
            continue
        link = article.find("a", attrs={"data-file_type": "EXCEL_Report"}, href=True)
        if link:
            label = next(compact(a.get_text()) for a in article.select("a.stat-link_text"))
            return Planned("table03", label, urljoin(ESTAT, link["href"]))
    raise RuntimeError(f"Table 「{TITLE}」 not found; the e-Stat layout may have changed.")


def run(source: Source, year: int | None, dry_run: bool = False, out_root: Path = RAW_DIR):
    """Newest year by default."""
    s = session()
    pages = year_pages(get_html(s, ANNUAL))
    y = max(pages) if year is None else year
    if y not in pages:
        raise SystemExit(f"{y}: not listed on e-Stat (latest: {max(pages)}).")
    f = plan(get_html(s, pages[y]))
    if dry_run:
        print(f"[dry-run] {y} {f.key} {f.label} {f.url}")
        return
    out_dir = out_root / SOURCE_ID / f"y{y}"
    print(f"Downloading {f.key}: {f.label} {f.url}")
    entry = download(s, f.url, out_dir / f"{f.key}.xlsx")
    write_manifest(out_dir, SOURCE_ID, pages[y], [entry])
    (out_dir / "labels.tsv").write_text(f"{f.key}\t{f.label}\n", encoding="utf-8")
