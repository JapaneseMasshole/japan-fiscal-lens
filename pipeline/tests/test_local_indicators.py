"""Tests for 総務省 主要財政指標一覧 parsing (committed raw files)."""

import pytest

from jfl.paths import RAW_DIR
from jfl.transform.mic_indicators import NOT_CALCULATED, _cell, designated_cities, parse_all
from jfl.validate.local_indicators import check

RAW = RAW_DIR / "mic-fiscal-indicators"
needs_raw = pytest.mark.skipif(not (RAW / "fy2024").exists(), reason="raw data not fetched")


def test_dash_means_not_calculated_only_for_future_burden():
    assert _cell("-", "将来負担比率") == NOT_CALCULATED
    assert _cell("－", "ラスパイレス指数") is None
    assert _cell("0.76", "財政力指数") == 0.76


@pytest.fixture(scope="module")
def parsed():
    return parse_all(RAW)


@needs_raw
def test_all_years_parse_and_validate(parsed):
    df, averages = parsed
    assert sorted(df["fiscal_year"].unique())[:2] == [2015, 2016]  # FY2015 is a legacy .xls
    assert check(df, averages) == []


@needs_raw
def test_known_values_fy2024(parsed):
    df, averages = parsed
    kobe = df[(df["fiscal_year"] == 2024) & (df["code"] == "281000")].iloc[0]
    assert (kobe["name"], kobe["fiscal_strength"], kobe["future_burden_ratio"]) == (
        "神戸市",
        0.76,
        64.5,
    )
    chiyoda = df[(df["fiscal_year"] == 2024) & (df["code"] == "131016")].iloc[0]
    assert chiyoda["future_burden_ratio"] == NOT_CALCULATED
    assert averages[2024]["municipal_average"]["current_balance_ratio"] == 93.8


@needs_raw
def test_designated_cities_fy2024():
    cities = designated_cities(RAW / "fy2024")
    assert len(cities) == 20
    assert ("兵庫県", "神戸市") in cities
