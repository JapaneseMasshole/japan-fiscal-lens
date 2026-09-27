"""Parse 人口推計 第３表 (total population as of 1 October, thousands).

The sheet has a header row of years (「2020年」 … 「2024年」), then a block headed
「人口（単位 千人）」 whose 「総数」 row holds the totals. The percentage block
further down repeats 「総数」, so only the first one after the unit heading counts.
"""

from __future__ import annotations

import re
from pathlib import Path

import openpyxl

from jfl.transform.excel import check_readable_xlsx, norm

YEAR = re.compile(r"^(\d{4})年$")


def parse(path: Path) -> dict[int, int]:
    """{year: total population in persons} (as of 1 October)."""
    check_readable_xlsx(path)
    ws = openpyxl.load_workbook(path, data_only=True, read_only=True).worksheets[0]
    year_cols: dict[int, int] = {}
    in_population = False
    for row in ws.iter_rows(values_only=True):
        texts = [norm(c) for c in row]
        if not year_cols:
            found = {i: int(m.group(1)) for i, t in enumerate(texts) if (m := YEAR.match(t))}
            if len(found) >= 2:
                year_cols = found
            continue
        if any(t.startswith("人口") and "千人" in t for t in texts):
            in_population = True
            continue
        if in_population and "総数" in texts:
            out = {}
            for i, y in year_cols.items():
                v = row[i]
                if not isinstance(v, (int, float)):
                    raise ValueError(f"{path}: {y} total is {v!r}")
                out[y] = int(v) * 1000
            return out
    raise ValueError(f"{path}: 総数 row under 「人口（単位 千人）」 not found")
