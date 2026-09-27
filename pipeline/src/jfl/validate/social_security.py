"""Reconciliation checks for IPSS 社会保障費用統計 tables, for every published year.

Figures are whole 億円, rounded per cell, so sums may be off by about n/2 億円.
"""

from __future__ import annotations

from collections import defaultdict

from jfl.transform.ipss_social_security import Row
from jfl.validate.balance_sheet import Issue

# table → [(total, [parts])]
SUMS = {
    "benefit_by_category": [("合計", ["医療", "年金", "福祉その他"])],
    "benefit_by_function": [
        (
            "合計",
            [
                "高齢",
                "遺族",
                "障害",
                "労働災害",
                "保健医療",
                "家族",
                "失業",
                "住宅",
                "生活保護その他",
            ],
        )
    ],
    "revenue": [
        ("合計", ["社会保険料", "公費負担", "資産収入", "その他"]),
        ("社会保険料", ["被保険者拠出", "事業主拠出"]),
        ("公費負担", ["国庫負担", "他の公費負担"]),
    ],
}


def check(rows: list[Row]) -> list[Issue]:
    issues: list[Issue] = []
    by: dict[tuple[str, int], dict[str, float]] = defaultdict(dict)
    for r in rows:
        by[(r.table, r.fiscal_year)][r.item_ja] = r.value_oku_yen
    for (table, fy), vals in sorted(by.items()):
        for total, parts in SUMS[table]:
            present = [p for p in parts if p in vals]
            if total not in vals or not present:
                continue
            got = sum(vals[p] for p in present)
            if abs(got - vals[total]) > 0.5 * len(present) + 0.5:
                issues.append(
                    Issue(f"{table}:{total}", f"FY{fy}: parts {got:,.0f} vs {vals[total]:,.0f}")
                )
        # 介護対策 is part of 福祉その他, never more.
        if table == "benefit_by_category" and vals.get("介護対策", 0) > vals.get("福祉その他", 0):
            issues.append(Issue("long-term-care", f"FY{fy}: 介護対策 exceeds 福祉その他"))
    # Both benefit tables describe the same total.
    for (table, fy), vals in by.items():
        if table == "benefit_by_function":
            other = by.get(("benefit_by_category", fy), {}).get("合計")
            if other is not None and other != vals["合計"]:
                issues.append(
                    Issue("benefit-totals", f"FY{fy}: 第8表 {other} vs 第13表 {vals['合計']}")
                )
    return issues
