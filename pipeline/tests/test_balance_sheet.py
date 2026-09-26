"""Tests for the national balance sheet parser and checks, run against the committed raw files."""

from pathlib import Path

import pytest

from jfl.paths import RAW_DIR
from jfl.transform.excel import UnreadableWorkbook, check_readable_xlsx
from jfl.transform.mof_balance_sheet import _era_year, canonical, parse_all
from jfl.validate.balance_sheet import check_all, compare_restatements

RAW = RAW_DIR / "mof-fs"
needs_raw = pytest.mark.skipif(
    not (RAW / "fy2023" / "gassan.xlsx").exists(), reason="raw data not fetched"
)


@pytest.mark.parametrize(
    "text, year",
    [
        ("(令和５年", 2023),
        ("(令和６年", 2024),
        ("(平成31年", 2019),
        ("(令和元年", 2019),
        ("3月31日)", None),
    ],
)
def test_era_year(text, year):
    assert _era_year(text) == year


def test_drm_file_is_reported_not_parsed(tmp_path: Path):
    # Minimal OLE container with an EncryptedPackage stream is hard to build by hand,
    # so check the plain "not an Excel file" path here and the DRM path on real data below.
    bogus = tmp_path / "x.xlsx"
    bogus.write_bytes(b"not a workbook")
    with pytest.raises(UnreadableWorkbook):
        check_readable_xlsx(bogus)


@pytest.fixture(scope="module")
def parsed():
    return parse_all(RAW)


@needs_raw
def test_misfiled_workbook_is_detected_by_its_own_dates(tmp_path):
    # Reproduce MOF's FY2021 link mistake: a FY2020 workbook stored under fy2021/.
    import shutil

    (tmp_path / "fy2021").mkdir()
    shutil.copy(RAW / "fy2020" / "gassan.xlsx", tmp_path / "fy2021" / "gassan.xlsx")
    with pytest.warns(UserWarning, match="sheet is dated FY2020"):
        df, _ = parse_all(tmp_path)
    assert set(df["fiscal_year"]) == {2019, 2020}


@needs_raw
def test_fy2024_drm_file_is_skipped(parsed):
    _, skipped = parsed
    assert any("fy2024" in s and "rights-management" in s for s in skipped)


@needs_raw
def test_years_come_from_sheet_dates_not_folders(parsed):
    df, _ = parsed
    c = canonical(df)
    assert sorted(c["fiscal_year"].unique()) == [2019, 2020, 2021, 2022, 2023]
    # Each year comes from its own workbook where one exists.
    fy21 = c[c["fiscal_year"] == 2021].iloc[0]
    assert (fy21["column"], fy21["source_file_year"]) == ("current", 2021)
    fy19 = c[c["fiscal_year"] == 2019].iloc[0]
    assert (fy19["column"], fy19["source_file_year"]) == ("previous", 2020)


@needs_raw
def test_known_published_totals(parsed):
    # FY2023 (令和5年度) balance sheet, 合算, as printed by MOF (百万円).
    c = canonical(parsed[0])
    fy23 = c[c["fiscal_year"] == 2023].set_index("item_ja")["value_oku_yen"]
    assert fy23["資産合計"] == pytest.approx(778_088_061 / 100)
    assert fy23["負債合計"] == pytest.approx(1_473_827_288 / 100)
    assert fy23["公債"] == pytest.approx(1_164_288_080 / 100)


@needs_raw
def test_all_sheets_reconcile(parsed):
    assert check_all(parsed[0]) == []


@needs_raw
def test_overlapping_years_agree(parsed):
    assert compare_restatements(parsed[0]).empty
