"""Parse 総務省「地方公共団体の主要財政指標一覧」 (all prefectures / all municipalities).

Layout (stable FY2015–FY2024): row 1 title, row 2 header, then one row per
local government, then an official average row (全国市町村平均 / 都道府県平均).

    municipalities: 団体コード | 都道府県名 | 団体名 | 財政力指数 | 経常収支比率 |
                    実質公債費比率 | 将来負担比率 | ラスパイレス指数
    prefectures:    都道府県名 | 財政力指数 | … (same indicators)

A "-" in 将来負担比率 is not missing data: the ratio is not calculated because
the future burden is fully covered by available resources (将来負担額 ≤
充当可能財源等). It is kept as the marker NOT_CALCULATED, never as 0 or blank.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

INDICATORS = {
    "財政力指数": "fiscal_strength",
    "経常収支比率": "current_balance_ratio",
    "実質公債費比率": "real_debt_service_ratio",
    "将来負担比率": "future_burden_ratio",
    "ラスパイレス指数": "laspeyres",
}
NOT_CALCULATED = "nc"
DASHES = {"-", "－", "―", "‐", "ー"}
AVERAGE_LABELS = {"全国市町村平均": "municipal_average", "都道府県平均": "prefectural_average"}


def _cell(v, column: str):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, str):
        s = v.strip()
        if s in DASHES:
            # Only 将来負担比率 uses "-" for "not calculated"; elsewhere it means "not published".
            return NOT_CALCULATED if column == "将来負担比率" else None
        try:
            return float(s)
        except ValueError:
            return None
    return float(v)


def _read(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=0, header=1, dtype=object)
    df.columns = ["".join(str(c).split()) for c in df.columns]
    missing = [c for c in INDICATORS if c not in df.columns]
    if missing:
        raise ValueError(f"{path}: missing indicator columns {missing}")
    return df


def parse_year(folder: Path) -> tuple[pd.DataFrame, dict]:
    """Rows for one fiscal year, plus the official averages."""
    fy = int(folder.name[2:])
    rows = []
    averages: dict[str, dict] = {}

    muni = _read(next(folder.glob("municipalities.xls*")))
    for rec in muni.to_dict("records"):
        code = str(rec["団体コード"]).strip() if rec["団体コード"] is not None else ""
        values = {INDICATORS[k]: _cell(rec[k], k) for k in INDICATORS}
        if code in AVERAGE_LABELS:
            averages[AVERAGE_LABELS[code]] = values
            continue
        if not code.isdigit():
            continue  # blank / note rows
        rows.append(
            {
                "fiscal_year": fy,
                "kind": "municipality",
                "code": code.zfill(6),
                "prefecture": str(rec["都道府県名"]).strip(),
                "name": str(rec["団体名"]).strip(),
                **values,
            }
        )

    pref = _read(next(folder.glob("prefectures.xls*")))
    for rec in pref.to_dict("records"):
        name = str(rec["都道府県名"]).strip() if rec["都道府県名"] is not None else ""
        values = {INDICATORS[k]: _cell(rec[k], k) for k in INDICATORS}
        if name in AVERAGE_LABELS:
            averages[AVERAGE_LABELS[name]] = values
            continue
        if not name or name == "nan":
            continue
        rows.append(
            {
                "fiscal_year": fy,
                "kind": "prefecture",
                "code": "",
                "prefecture": name,
                "name": name,
                **values,
            }
        )
    return pd.DataFrame(rows), averages


def parse_all(raw_dir: Path) -> tuple[pd.DataFrame, dict[int, dict]]:
    frames, averages = [], {}
    for folder in sorted(p for p in raw_dir.glob("fy*") if p.is_dir()):
        df, avg = parse_year(folder)
        frames.append(df)
        averages[int(folder.name[2:])] = avg
    return pd.concat(frames, ignore_index=True), averages


def designated_cities(folder: Path) -> set[tuple[str, str]]:
    """(prefecture, city) pairs listed in the 政令指定都市 workbook for that year."""
    path = next(folder.glob("designated_cities.xls*"), None)
    if path is None:
        return set()
    df = pd.read_excel(path, sheet_name=0, header=1, dtype=str)
    df.columns = ["".join(str(c).split()) for c in df.columns]
    return {
        (str(p).strip(), str(n).strip())
        for p, n in zip(df["都道府県名"], df["団体名"], strict=True)
        if isinstance(n, str) and n.strip()
    }
