"""Reconciliation checks for the operating cost, net-asset change and cash flow statements.

Besides internal sums, the statements must tie to the balance sheet:
    net assets at start/end of year  = balance sheet 資産・負債差額 (previous/current year end)
    cash at end of year              = balance sheet 現金・預金
"""

from __future__ import annotations

import pandas as pd

from jfl.validate.balance_sheet import TOLERANCE_OKU, Issue, _tol


def _get(g: pd.DataFrame, item: str) -> float:
    s = g.loc[g["item_ja"] == item, "value_oku_yen"]
    if s.empty:
        raise KeyError(item)
    return float(s.iloc[0])


def _check(issues, name, where, got, want, tol=TOLERANCE_OKU):
    if abs(got - want) > tol:
        issues.append(
            Issue(name, f"{where}: {got:,.2f} vs {want:,.2f} 億円 (diff {got - want:,.2f})")
        )


def check_flow(flow: pd.DataFrame, bs: pd.DataFrame) -> list[Issue]:
    """`flow` and `bs` are canonical tables (one statement per year)."""
    issues: list[Issue] = []
    bs_net = bs[bs["item_ja"] == "資産・負債差額"].set_index("fiscal_year")["value_oku_yen"]
    bs_cash = bs[bs["item_ja"] == "現金・預金"].set_index("fiscal_year")["value_oku_yen"]

    for (statement, fy), g in flow.groupby(["statement", "fiscal_year"]):
        where = f"FY{fy} {statement}"
        g = g.sort_values("order")
        if statement == "operating_cost":
            lines = g[g["item_ja"] != "本年度業務費用合計"]
            _check(
                issues,
                "cost-total",
                where,
                lines["value_oku_yen"].sum(),
                _get(g, "本年度業務費用合計"),
                _tol(len(lines)),
            )

        elif statement == "net_assets_change":
            _check(
                issues,
                "funding",
                where,
                _get(g, "租税等財源") + _get(g, "その他の財源"),
                _get(g, "財源"),
                _tol(2),
            )
            movements = g[
                ~g["item_ja"].isin(
                    [
                        "前年度末資産・負債差額",
                        "本年度末資産・負債差額",
                        "租税等財源",
                        "その他の財源",
                    ]
                )
            ]
            _check(
                issues,
                "roll-forward",
                where,
                _get(g, "前年度末資産・負債差額") + movements["value_oku_yen"].sum(),
                _get(g, "本年度末資産・負債差額"),
                _tol(len(movements)),
            )
            if fy in bs_net.index:
                _check(
                    issues, "ties-to-BS(end)", where, _get(g, "本年度末資産・負債差額"), bs_net[fy]
                )
            if fy - 1 in bs_net.index:
                _check(
                    issues,
                    "ties-to-BS(start)",
                    where,
                    _get(g, "前年度末資産・負債差額"),
                    bs_net[fy - 1],
                )

        elif statement == "cash_flow":
            _check(
                issues,
                "operating-cf",
                where,
                _get(g, "財源合計") + _get(g, "業務支出合計"),
                _get(g, "業務収支"),
                _tol(2),
            )
            o_op, o_fin = (
                int(g.loc[g["item_ja"] == k, "order"].iloc[0]) for k in ("業務収支", "財務収支")
            )
            fin_lines = g[(g["order"] > o_op) & (g["order"] < o_fin)]
            _check(
                issues,
                "financing-cf",
                where,
                fin_lines["value_oku_yen"].sum(),
                _get(g, "財務収支"),
                _tol(len(fin_lines)),
            )
            _check(
                issues,
                "net-cf",
                where,
                _get(g, "業務収支") + _get(g, "財務収支"),
                _get(g, "本年度収支"),
                _tol(2),
            )
            if fy in bs_cash.index:
                _check(
                    issues, "ties-to-BS(cash)", where, _get(g, "本年度末現金･預金残高"), bs_cash[fy]
                )
    return issues
