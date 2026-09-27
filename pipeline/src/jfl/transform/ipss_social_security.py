"""Parse IPSS 社会保障費用統計 tables (第８表, 第13表, 第14表) into tidy rows.

Every table is a time series: one row per fiscal year (Western year in column B,
Japanese era in C), amounts in 億円 followed by percentage columns we ignore.
Column headers are two-level (「社会保険料」 over 「被保険者拠出」 …); rather than
trust cell positions, we locate each column by its header text and check the
header row still reads as expected.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import openpyxl

from jfl.transform.excel import check_readable_xlsx, norm


@dataclass
class Row:
    table: str  # benefit_by_category | benefit_by_function | revenue
    fiscal_year: int
    item_ja: str
    item_en: str
    value_oku_yen: float
    order: int


# key → (file, [(header_ja, item_en)]). Amount columns appear left to right in this
# order, directly after the year and era columns; the percentage block that follows
# repeats the same headers and is skipped.
TABLES = {
    "benefit_by_category": (
        "table08.xlsx",
        [
            ("合計", "Total"),
            ("医療", "Medical care"),
            ("年金", "Pension"),
            ("福祉その他", "Welfare and others"),
            ("介護対策", "of which long-term care"),
        ],
    ),
    "benefit_by_function": (
        "table13.xlsx",
        [
            ("合計", "Total"),
            ("高齢", "Old age"),
            ("遺族", "Survivors"),
            ("障害", "Invalidity"),
            ("労働災害", "Employment injury"),
            ("保健医療", "Sickness and health"),
            ("家族", "Family"),
            ("失業", "Unemployment"),
            ("住宅", "Housing"),
            ("生活保護その他", "Public assistance and others"),
        ],
    ),
    "revenue": (
        "table14.xlsx",
        [
            ("合計", "Total"),
            ("社会保険料", "Social insurance contributions"),
            ("被保険者拠出", "Contributions from insured persons"),
            ("事業主拠出", "Contributions from employers"),
            ("公費負担", "Tax"),
            ("国庫負担", "National government"),
            ("他の公費負担", "Local governments and other public"),
            ("資産収入", "Income from capital"),
            ("その他", "Others"),
        ],
    ),
}


def _year(v) -> int | None:
    return int(v) if isinstance(v, (int, float)) and 1900 < v < 2100 else None


def _headers(ws) -> dict[int, set[str]]:
    """Column index → header texts in the first 12 rows (both levels of the two-row header)."""
    cols: dict[int, set[str]] = {}
    for row in ws.iter_rows(min_row=1, max_row=12, values_only=True):
        for i, c in enumerate(row):
            if isinstance(c, str):
                cols.setdefault(i, set()).add(norm(c))
    return cols


def parse_table(path: Path, table: str) -> list[Row]:
    file, items = TABLES[table]
    check_readable_xlsx(path)
    ws = openpyxl.load_workbook(path, data_only=True, read_only=True).worksheets[0]
    headers = _headers(ws)
    rows: list[Row] = []
    first = None  # column of the first amount, checked against the headers once
    for r in ws.iter_rows(values_only=True):
        cells = list(r)
        # The year sits in the first numeric-year cell; the era label follows it.
        idx = next((i for i, c in enumerate(cells[:3]) if _year(c)), None)
        if idx is None:
            continue
        fy = _year(cells[idx])
        if first is None:
            first = idx + 2
            for i, (ja, _) in enumerate(items):
                if ja not in headers.get(first + i, set()):
                    raise ValueError(
                        f"{file}: column {first + i} should be 「{ja}」, found "
                        f"{sorted(headers.get(first + i, []))}; the layout changed"
                    )
        amounts = cells[first : first + len(items)]
        for order, ((ja, en), v) in enumerate(zip(items, amounts, strict=True)):
            if isinstance(v, (int, float)):
                rows.append(Row(table, fy, ja, en, float(v), order))
            elif norm(v) not in ("－", "-", "―", ""):
                raise ValueError(f"{file}: FY{fy} {ja}: unexpected value {v!r}")
    if not rows:
        raise ValueError(f"{file}: no year rows found")
    return rows


def parse_all(raw_dir: Path) -> list[Row]:
    """All three tables from one year folder (data/raw/ipss-ss-cost/fy<year>/)."""
    out: list[Row] = []
    for table, (file, _) in TABLES.items():
        out += parse_table(raw_dir / file, table)
    return out
