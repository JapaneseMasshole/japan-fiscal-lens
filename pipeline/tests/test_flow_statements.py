"""Tests for the cost, net-asset change and cash flow statements (committed raw files)."""

import pytest

from jfl.paths import RAW_DIR
from jfl.transform import mof_balance_sheet as B
from jfl.transform import mof_flow_statements as F
from jfl.transform.mof_balance_sheet import _era_year
from jfl.validate.flow_statements import check_flow

RAW = RAW_DIR / "mof-fs"
needs_raw = pytest.mark.skipif(
    not (RAW / "fy2023" / "gassan.xlsx").exists(), reason="raw data not fetched"
)


def test_era_year_ignores_month_and_day():
    assert _era_year("(至　令和６年３月31日)") == 2024
    assert _era_year("(自　令和５年４月 1日)") == 2023


@pytest.fixture(scope="module")
def tables():
    with pytest.warns(UserWarning):
        flow = F.canonical(F.parse_all(RAW)[0])
        bs = B.canonical(B.parse_all(RAW)[0])
    return flow, bs


@needs_raw
def test_one_workbook_per_statement_year(tables):
    flow, _ = tables
    per = flow.groupby(["statement", "fiscal_year"])["source_file_year"].nunique()
    assert (per == 1).all()
    assert sorted(flow["fiscal_year"].unique()) == [2018, 2019, 2020, 2021, 2022, 2023]


@needs_raw
def test_statements_reconcile_and_tie_to_balance_sheet(tables):
    flow, bs = tables
    assert check_flow(flow, bs) == []


@needs_raw
def test_known_published_values(tables):
    # FY2023 (令和5年度), 百万円 as printed by MOF.
    flow, _ = tables
    fy23 = flow[flow["fiscal_year"] == 2023].set_index(["statement", "item_ja"])["value_oku_yen"]
    assert fy23[("operating_cost", "本年度業務費用合計")] == pytest.approx(170_383_457 / 100)
    assert fy23[("net_assets_change", "租税等財源")] == pytest.approx(77_387_202 / 100)
    assert fy23[("cash_flow", "公債の発行による収入")] == pytest.approx(193_455_155 / 100)
