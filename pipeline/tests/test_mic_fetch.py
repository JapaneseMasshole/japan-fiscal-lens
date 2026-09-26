"""Offline tests for MIC link discovery, using trimmed copies of the real pages."""

from pathlib import Path

import pytest

from jfl.fetch.mic import era_to_fy, indicator_year_pages, plan_indicators, plan_unified

FX = Path(__file__).parent / "fixtures"
BASE = "https://www.soumu.go.jp"


def read(name: str) -> str:
    return (FX / name).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "text, fy",
    [
        ("令和6年度主要財政指標一覧", 2024),
        ("令和元年度", 2019),
        ("平成29年度", 2017),
        ("決算カード", None),
    ],
)
def test_era_to_fy(text, fy):
    assert era_to_fy(text) == fy


def test_indicator_year_pages_follow_link_text_not_urls():
    pages = indicator_year_pages(
        read("mic_shihyo_listing.html"), BASE + "/iken/shihyo_ichiran.html"
    )
    assert pages[2024] == BASE + "/menu_seisaku/toukei/02zaisei07_04000135.html"
    assert pages[2019] == BASE + "/iken/zaisei/R01_chiho.html"
    # FY2017's page is named H28_chiho_00001.html; the link text decides.
    assert pages[2017] == BASE + "/iken/zaisei/H28_chiho_00001.html"
    assert pages[2016] == BASE + "/iken/zaisei/H28_chiho.html"


def test_plan_indicators_names_files_by_link_text():
    files = {
        f.key: f.url
        for f in plan_indicators(read("mic_shihyo_r04.html"), BASE + "/iken/zaisei/R04_chiho.html")
    }
    assert files["prefectures"].endswith("000917807.xlsx")
    assert files["municipalities"].endswith("000917808.xlsx")
    assert files["designated_cities"].endswith("000917812.xlsx")
    assert len(files) == 5


def test_plan_unified_maps_prefectures_to_jis_codes():
    page = BASE + "/iken/kokaikei/R05_chihou_zaimusyorui.html"
    files = {f.key: f for f in plan_unified(read("mic_unified_r05.html"), page)}
    assert sum(k.startswith("pref-") for k in files) == 47
    assert files["prefectures"].url.endswith("001031193.xlsx")  # the xlsx, not the PDF
    assert files["pref-28"].label.startswith("兵庫県")
    assert files["pref-01"].label.startswith("北海道")
    assert files["indicators_municipalities"].url.endswith("001033346.xlsx")
    assert not any(f.url.endswith(".pdf") for f in files.values())


def test_plan_unified_fails_loudly_on_layout_change():
    with pytest.raises(RuntimeError, match="layout may have changed"):
        plan_unified("<a href='x.xlsx'>something else</a>", BASE)
