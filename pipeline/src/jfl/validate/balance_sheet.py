"""Reconciliation checks for the parsed national balance sheet.

Figures are published in 百万円 with amounts below 1 百万円 dropped per line, so a
sum of n lines may differ from its printed subtotal by up to about n 百万円.
Tolerances are expressed in 億円 (1 百万円 = 0.01 億円).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

TOLERANCE_OKU = 0.1  # = 10 百万円, for single-figure comparisons
PER_LINE_OKU = 0.01  # = 1 百万円 per summed line


def _tol(n_lines: int) -> float:
    return PER_LINE_OKU * (n_lines + 1)


@dataclass
class Issue:
    check: str
    detail: str

    def __str__(self) -> str:
        return f"[{self.check}] {self.detail}"


def _value(g: pd.DataFrame, item: str) -> float:
    return float(g.loc[g["item_ja"] == item, "value_oku_yen"].iloc[0])


def check_sheet(g: pd.DataFrame) -> list[Issue]:
    """Checks within one balance sheet (one workbook column)."""
    fy = int(g["fiscal_year"].iloc[0])
    where = f"FY{fy} ({g['column'].iloc[0]} column of FY{int(g['source_file_year'].iloc[0])} file)"
    issues: list[Issue] = []

    # 1. Every subtotal equals the sum of its direct children.
    for section in ("assets", "liabilities"):
        s = g[g["section"] == section]
        for parent, kids in s[s["parent_ja"] != ""].groupby("parent_ja"):
            diff = _value(s, parent) - kids["value_oku_yen"].sum()
            if abs(diff) > _tol(len(kids)):
                issues.append(
                    Issue(
                        "subtotal", f"{where}: {parent} differs from its items by {diff:,.2f} 億円"
                    )
                )

    # 2. Top-level lines add up to the printed totals.
    for section, total in (("assets", "資産合計"), ("liabilities", "負債合計")):
        lines = g[(g["section"] == section) & (g["parent_ja"] == "")]
        diff = _value(g, total) - lines["value_oku_yen"].sum()
        if abs(diff) > _tol(len(lines)):
            issues.append(
                Issue("total", f"{where}: {total} differs from its lines by {diff:,.2f} 億円")
            )

    # 3. Assets = liabilities + net assets.
    assets = _value(g, "資産合計")
    liab = _value(g, "負債合計")
    net = _value(g, "資産・負債差額")
    grand = _value(g, "負債及び資産・負債差額合計")
    if abs(assets - (liab + net)) > TOLERANCE_OKU or abs(assets - grand) > TOLERANCE_OKU:
        issues.append(
            Issue(
                "identity",
                f"{where}: assets {assets:,.0f} ≠ liabilities {liab:,.0f} + net {net:,.0f}",
            )
        )
    return issues


def check_all(all_rows: pd.DataFrame) -> list[Issue]:
    issues: list[Issue] = []
    for _, g in all_rows.groupby(["source_file_year", "column"]):
        issues += check_sheet(g)
    return issues


def compare_restatements(all_rows: pd.DataFrame) -> pd.DataFrame:
    """Lines where a later workbook's "previous" figure differs from the year's own workbook.

    Differences are not errors: ministries restate prior-year figures. They are
    reported so the site can say which figure it shows and why.
    """
    key = ["fiscal_year", "section", "parent_ja", "item_ja"]
    cur = all_rows[all_rows["column"] == "current"][key + ["value_oku_yen"]]
    prev = all_rows[all_rows["column"] == "previous"][key + ["value_oku_yen", "source_file_year"]]
    m = cur.merge(prev, on=key, suffixes=("_own", "_later"))
    m["diff"] = m["value_oku_yen_later"] - m["value_oku_yen_own"]
    return m[m["diff"].abs() > TOLERANCE_OKU].reset_index(drop=True)
