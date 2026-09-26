"""Offline tests for MOF link discovery, using a trimmed copy of the real FY2024 page."""

from pathlib import Path

import pytest

from jfl.fetch.mof_financial_statements import plan

FIXTURE = Path(__file__).parent / "fixtures" / "mof_fs_fy2024.html"
PAGE_URL = (
    "https://www.mof.go.jp/policy/budget/report/public_finance_fact_sheet/"
    "fy2024/national/kuninozaimurenketu2024.html"
)


def test_plan_finds_three_workbooks(tmp_path: Path):
    files = plan(FIXTURE.read_text(encoding="utf-8"), PAGE_URL, 2024, out_root=tmp_path)
    by_variant = {f.variant: f for f in files}

    assert set(by_variant) == {"gassan", "ippan", "renketsu"}
    base = "https://www.mof.go.jp/policy/budget/report/public_finance_fact_sheet/fy2024/national/"
    assert by_variant["gassan"].url == base + "fy2024gassan.xlsx"
    assert by_variant["renketsu"].url == base + "fy2024renketsu.xlsx"
    assert by_variant["ippan"].dest == tmp_path / "mof-fs" / "fy2024" / "ippan.xlsx"


def test_plan_ignores_unrelated_excel(tmp_path: Path):
    # The full-cost database xlsx is on the same page but is not a financial statement.
    files = plan(FIXTURE.read_text(encoding="utf-8"), PAGE_URL, 2024, out_root=tmp_path)
    assert not any("fullcost" in f.url or "datebase" in f.url for f in files)


def test_plan_fails_loudly_when_layout_changes(tmp_path: Path):
    with pytest.raises(RuntimeError, match="layout may have changed"):
        plan("<html><a href='other.xlsx'>x</a></html>", PAGE_URL, 2024, out_root=tmp_path)


def test_plan_corrects_link_to_wrong_year(tmp_path: Path):
    # The real FY2021 page links fy2019/national/fy2019gassan.xlsx.
    base = "https://www.mof.go.jp/policy/budget/report/public_finance_fact_sheet/"
    html = f'<a href="{base}fy2019/national/fy2019gassan.xlsx">Excel</a>'
    (f,) = plan(html, base + "fy2021/kuninozaimugassan2021.html", 2021, out_root=tmp_path)
    assert f.url == base + "fy2021/national/fy2021gassan.xlsx"
    assert f.fallback_url == base + "fy2019/national/fy2019gassan.xlsx"
