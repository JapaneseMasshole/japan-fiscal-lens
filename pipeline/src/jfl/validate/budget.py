"""Reconciliation checks for the general account budget (mof-budget).

MOF rounds every line to the nearest 億円 (「端数において合計とは合致しないものがある」),
so a sum of n lines may differ from its printed total by up to about n/2 億円.
"""

from __future__ import annotations

from jfl.transform.mof_budget import Row
from jfl.validate.balance_sheet import Issue


def _tol(n_lines: int) -> float:
    return 0.5 * n_lines + 0.5


def check(rows: list[Row]) -> list[Issue]:
    issues: list[Issue] = []
    v: dict[tuple[str, str], float] = {(r.statement, r.item_ja): r.value_oku_yen for r in rows}

    def get(statement, item):
        return v[(statement, item)]

    def eq(name, got, want, n):
        if abs(got - want) > _tol(n):
            issues.append(Issue(name, f"{got:,.0f} vs {want:,.0f} 億円 (diff {got - want:,.0f})"))

    # 歳入: taxes + other revenue + bonds = total; bonds = construction + deficit-financing.
    eq(
        "revenue-total",
        get("revenue", "租税及印紙収入") + get("revenue", "その他収入") + get("revenue", "公債金"),
        get("revenue", "合計"),
        3,
    )
    eq(
        "bonds",
        get("revenue", "⑴公債金") + get("revenue", "⑵特例公債金"),
        get("revenue", "公債金"),
        2,
    )

    # 歳出 主要経費別: items (not the うち line) = total = 歳入 total.
    items = [
        r
        for r in rows
        if r.statement == "expenditure"
        and r.item_ja not in ("合計",)
        and not r.item_ja.startswith("うち")
    ]
    eq(
        "expenditure-total",
        sum(r.value_oku_yen for r in items),
        get("expenditure", "合計"),
        len(items),
    )
    eq("balanced", get("expenditure", "合計"), get("revenue", "合計"), 0)

    # 税目: every tax except the 所得税計 subtotal = 一般会計分計 = 租税及印紙収入.
    taxes = [
        r for r in rows if r.statement == "tax" and r.item_ja not in ("所得税計", "一般会計分計")
    ]
    eq("tax-total", sum(r.value_oku_yen for r in taxes), get("tax", "一般会計分計"), len(taxes))
    eq("income-tax", get("tax", "源泉所得税") + get("tax", "申告所得税"), get("tax", "所得税計"), 2)
    eq("tax-ties", get("tax", "一般会計分計"), get("revenue", "租税及印紙収入"), 0)

    # 社会保障関係費: the seven items = the total, which ties to 主要経費別.
    ss = [r for r in rows if r.statement == "social_security" and r.order > 0]
    eq(
        "social-security-total",
        sum(r.value_oku_yen for r in ss),
        get("social_security", "社会保障関係費（Ｃ）"),
        len(ss),
    )
    eq(
        "social-security-ties",
        get("social_security", "社会保障関係費（Ｃ）"),
        get("expenditure", "社会保障関係費"),
        0,
    )

    # 国債費 in the budget frame ties to 主要経費別; its parts can't exceed it.
    eq("debt-service-ties", get("debt_service", "国債費"), get("expenditure", "国債費"), 0)
    parts = get("debt_service", "うち債務償還費（交付国債分を除く）") + get(
        "debt_service", "うち利払費"
    )
    if parts > get("debt_service", "国債費") + _tol(2):
        issues.append(Issue("debt-service-parts", f"parts {parts:,.0f} exceed 国債費"))
    return issues
