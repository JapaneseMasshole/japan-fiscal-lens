"""Offline tests for budget, IPSS and population link discovery (trimmed copies of real pages)."""

from pathlib import Path

import pytest

from jfl.fetch import ipss, mof_budget, population

FX = Path(__file__).parent / "fixtures"
MOF = "https://www.mof.go.jp/policy/budget/budger_workflow/budget/"


def read(name: str) -> str:
    return (FX / name).read_text(encoding="utf-8")


def test_budget_year_pages_follow_link_text():
    pages = mof_budget.year_pages(read("mof_budget_index.html"), MOF + "index.html")
    assert pages[2026] == MOF + "fy2026/index.html"
    assert pages[2025] == MOF + "fy2025/fy2025.html"  # irregular name
    # FY2023 and older point at the National Diet Library archive; not used.
    assert 2023 not in pages


def test_enactment_distinguishes_main_interim_and_supplementary_budgets():
    # FY2026: interim (暫定), main and supplementary budgets all 「政府案どおり成立」.
    assert mof_budget.enactment(read("mof_budget_fy2026.html")) == "as_proposed"
    # FY2025: the Diet amended the budget; only its 補正 passed unchanged.
    assert mof_budget.enactment(read("mof_budget_fy2025.html")) == "amended"
    # Only the interim budget enacted so far.
    interim = "<p>令和８年度暫定予算は 政府案 どおり成立しました</p>"
    assert mof_budget.enactment(interim) is None


def test_seifuan_page_found_by_link_text():
    url = mof_budget.seifuan_page(read("mof_budget_fy2026.html"), MOF + "fy2026/index.html", 2026)
    assert url == MOF + "fy2026/seifuan2026/index.html"


def test_budget_plan_picks_four_pdfs():
    page = MOF + "fy2026/seifuan2026/index.html"
    files = {f.key: f for f in mof_budget.plan(read("mof_budget_seifuan2026.html"), page)}
    assert files["gaisan"].url.endswith("/03.pdf")
    assert files["tax"].url.endswith("/24.pdf")
    assert files["frame"].url.endswith("/02.pdf")
    # 「社会保障関係予算」, not the one-page 「概要」 that follows it.
    assert files["social_security"].url.endswith("/13.pdf")


def test_budget_plan_fails_loudly_on_layout_change():
    with pytest.raises(RuntimeError, match="layout may have changed"):
        mof_budget.plan("<a href='x.pdf'>別の資料</a>", MOF)


def test_ipss_year_pages_and_tables():
    listing = "https://www.ipss.go.jp/site-ad/index_Japanese/security.html"
    pages = ipss.year_pages(read("ipss_listing.html"), listing)
    assert max(pages) == 2024
    assert pages[2024] == "https://www.ipss.go.jp/ss-cost/j/fsss-R06/fsss_R06.html"
    files = {f.key: f.url for f in ipss.plan(read("ipss_r06.html"), pages[2024])}
    assert files == {
        "table08": "https://www.ipss.go.jp/ss-cost/j/fsss-R06/3/R06-8.xlsx",
        "table13": "https://www.ipss.go.jp/ss-cost/j/fsss-R06/3/R06-13.xlsx",
        "table14": "https://www.ipss.go.jp/ss-cost/j/fsss-R06/3/R06-14.xlsx",
    }


def test_population_year_links_and_table():
    pages = population.year_pages(read("estat_population_annual.html"))
    assert max(pages) == 2024
    f = population.plan(read("estat_population_2024.html"))
    # The formatted 「EXCEL 閲覧用」 file of 第３表, not 第１表 or the raw EXCEL.
    assert f.url.endswith("statInfId=000040268912&fileKind=4")
    assert "総人口（各年10月1日現在）" in f.label
