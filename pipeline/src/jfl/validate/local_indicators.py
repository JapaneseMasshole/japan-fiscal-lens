"""Sanity checks for the local fiscal indicators (主要財政指標一覧)."""

from __future__ import annotations

import pandas as pd

from jfl.transform.mic_indicators import NOT_CALCULATED
from jfl.validate.balance_sheet import Issue

# Wide but finite bounds: a value outside them almost certainly means a parsing error
# (shifted column, unit change), not a real municipality.
RANGES = {
    "fiscal_strength": (0.0, 3.5),
    "current_balance_ratio": (20.0, 200.0),
    "real_debt_service_ratio": (-30.0, 120.0),  # 夕張市 (under fiscal reconstruction) is ~70
    "future_burden_ratio": (0.0, 1500.0),
    "laspeyres": (70.0, 120.0),
}


def check(df: pd.DataFrame, averages: dict[int, dict]) -> list[Issue]:
    issues: list[Issue] = []
    for fy, g in df.groupby("fiscal_year"):
        muni = g[g["kind"] == "municipality"]
        pref = g[g["kind"] == "prefecture"]
        if not 1700 <= len(muni) <= 1800:
            issues.append(Issue("count", f"FY{fy}: {len(muni)} municipalities"))
        if len(pref) != 47:
            issues.append(Issue("count", f"FY{fy}: {len(pref)} prefectures"))
        if muni["code"].duplicated().any():
            issues.append(Issue("unique", f"FY{fy}: duplicate municipality codes"))
        for key, (lo, hi) in RANGES.items():
            vals = pd.to_numeric(g[key].where(g[key] != NOT_CALCULATED), errors="coerce").dropna()
            bad = g.loc[vals[(vals < lo) | (vals > hi)].index, "name"].tolist()
            if bad:
                issues.append(Issue("range", f"FY{fy} {key}: out of [{lo}, {hi}] for {bad[:5]}"))
        for which in ("municipal_average", "prefectural_average"):
            if which not in averages.get(fy, {}):
                issues.append(Issue("average", f"FY{fy}: {which} row not found"))
    return issues
