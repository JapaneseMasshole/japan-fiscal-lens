"""Tests for the budget, social security and population transforms (committed raw files).

Expected values are the figures printed in the official documents.
"""

import dataclasses

import pytest

from jfl.paths import RAW_DIR
from jfl.transform import ipss_social_security, mof_budget, population
from jfl.transform.mof_budget import _figures
from jfl.validate import budget, social_security

BUDGET = RAW_DIR / "mof-budget" / "fy2026"
IPSS = RAW_DIR / "ipss-ss-cost" / "fy2024"
POP = RAW_DIR / "sb-population" / "y2024" / "table03.xlsx"
needs_raw = pytest.mark.skipif(not (BUDGET / "gaisan.pdf").exists(), reason="raw data not fetched")


@pytest.mark.parametrize(
    "line, label, nums",
    [
        (
            "社 会 保 障 関 係 費 382,938 390,559 7,621 2.0",
            "社会保障関係費",
            [382938, 390559, 7621, 2.0],
        ),
        ("⑴公 債 金 67,910 67,160 △ 750 △ 1.1", "⑴公債金", [67910, 67160, -750, -1.1]),
        (
            "う ち 科 学 技 術 振 興 費 （ 14,221）（ 14,378）（ 156 ) ( 1.1 )",
            "うち科学技術振興費",
            [14221, 14378, 156, 1.1],
        ),
        ("防衛特別所得税（仮称） － － 380 380 380", "防衛特別所得税（仮称）", None),
        ("（単位 億円）", None, None),
    ],
)
def test_figures_split_label_and_numbers(line, label, nums):
    parsed = _figures(line)
    if label is None:
        assert parsed is None
        return
    assert parsed[0] == label
    if nums is not None:
        assert parsed[1] == pytest.approx(nums)


@pytest.fixture(scope="module")
def budget_rows():
    return mof_budget.parse(BUDGET)


@needs_raw
def test_budget_known_values(budget_rows):
    fy, rows = budget_rows
    assert fy == 2026
    v = {(r.statement, r.item_ja): r.value_oku_yen for r in rows}
    assert v[("expenditure", "合計")] == 1_223_092
    assert v[("expenditure", "社会保障関係費")] == 390_559
    assert v[("expenditure", "防衛関係費")] == 89_843
    assert v[("expenditure", "公共事業関係費")] == 61_078
    assert v[("revenue", "公債金")] == 295_840
    assert v[("tax", "消費税")] == 266_880
    assert v[("tax", "所得税計")] == 253_250
    assert v[("debt_service", "うち利払費")] == 130_371
    assert v[("social_security", "年金給付費")] == 139_012
    prev = {(r.statement, r.item_ja): r.prev_oku_yen for r in rows}
    assert prev[("expenditure", "合計")] == 1_151_978
    assert prev[("tax", "防衛特別法人税")] is None  # 「－」: new tax


@needs_raw
def test_budget_reconciles(budget_rows):
    assert budget.check(budget_rows[1]) == []


@needs_raw
def test_budget_check_catches_a_misread_line(budget_rows):
    rows = [
        dataclasses.replace(r, value_oku_yen=r.value_oku_yen + 100)
        if r.item_ja == "防衛関係費"
        else r
        for r in budget_rows[1]
    ]
    assert [i.check for i in budget.check(rows)] == ["expenditure-total"]


@needs_raw
def test_social_security_known_values_and_checks():
    rows = ipss_social_security.parse_all(IPSS)
    v = {(r.table, r.fiscal_year, r.item_ja): r.value_oku_yen for r in rows}
    assert v[("benefit_by_category", 2024, "合計")] == 1_383_019
    assert v[("benefit_by_category", 2024, "年金")] == 578_528
    assert v[("revenue", 2024, "被保険者拠出")] == 436_765
    assert v[("revenue", 2024, "事業主拠出")] == 393_661
    assert v[("revenue", 2024, "国庫負担")] == 383_563
    assert v[("benefit_by_function", 1994, "合計")] == 607_314
    assert social_security.check(rows) == []


@needs_raw
def test_population_total():
    assert population.parse(POP)[2024] == 123_802_000
