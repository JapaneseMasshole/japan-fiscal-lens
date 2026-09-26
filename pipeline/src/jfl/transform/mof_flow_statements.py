"""Parse MOF's three "flow" statements (one fiscal year each) from 国の財務書類 workbooks.

    業務費用計算書             operating cost statement
    資産・負債差額増減計算書    statement of changes in net assets (includes 財源 = funding)
    区分別収支計算書           cash flow by category

Layout shared by all three (FY2020–FY2023): label in column A, previous year
in B, current year in C; the period headers read 「(至 令和6年3月31日)」.
Section headings without numbers (e.g. 「Ⅰ 業務収支」) are kept as context
for the lines below them but produce no rows.
"""

from __future__ import annotations

import re
import warnings
from pathlib import Path

import openpyxl
import pandas as pd

from jfl.transform.excel import UnreadableWorkbook, check_readable_xlsx, norm
from jfl.transform.mof_balance_sheet import UNIT_DIVISORS_TO_OKU, _era_year

SHEETS = {
    "operating_cost": "業務費用計算書",
    "net_assets_change": "資産・負債差額増減計算書",
    "cash_flow": "区分別収支計算書",
}
HEADING = re.compile(r"^([ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]|[0-9０-９]+[\s　]|\([0-9]+\)|（[0-9]+）)")

ITEM_EN = {
    # 業務費用計算書
    "人件費": "Personnel",
    "賞与引当金繰入額": "Bonus reserve provision",
    "退職給付引当金繰入額": "Retirement benefit provision",
    "基礎年金給付費": "Basic pension benefits",
    "国民年金給付費": "National pension benefits",
    "厚生年金給付費": "Employees' pension benefits",
    "国家公務員共済組合連合会等交付金": "Public-servant mutual aid grants",
    "保険料等交付金": "Health insurance grants",
    "失業等給付費": "Unemployment benefits",
    "育児休業給付費": "Childcare leave benefits",
    "雇用安定等給付費": "Employment stabilisation benefits",
    "その他の社会保障費": "Other social security",
    "（再）保険費等": "(Re)insurance claims",
    "公共用施設整備費等": "Public facility maintenance",
    "持続化給付金等": "Business continuity payments (COVID-19)",
    "補助金等": "Subsidies",
    "委託費等": "Outsourcing",
    "地方交付税交付金等": "Transfers to local governments (地方交付税)",
    "資金援助交付費": "Deposit-insurance assistance",
    "運営費交付金": "Grants to independent agencies",
    "庁費等": "Office expenses",
    "公債事務取扱費": "Bond administration",
    "その他の経費": "Other expenses",
    "減価償却費": "Depreciation",
    "責任準備金繰入額": "Policy reserve provision",
    "貸倒引当金繰入額": "Bad-debt provision",
    "支払利息": "Interest paid",
    "為替換算差損益": "Foreign-exchange translation loss/gain",
    "公債償還損益": "Bond redemption loss/gain",
    "資産処分損益": "Asset disposal loss/gain",
    "出資金等評価損": "Write-down of capital investments",
    "本年度業務費用合計": "Total operating cost",
    # 資産・負債差額増減計算書
    "前年度末資産・負債差額": "Net assets at start of year",
    "本年度業務費用合計(増減)": "Operating cost for the year",
    "財源": "Funding",
    "租税等財源": "Taxes and similar",
    "その他の財源": "Other funding (incl. social insurance premiums)",
    "資産評価差額": "Asset revaluation",
    "為替換算差額": "Foreign-exchange translation",
    "公的年金預り金の変動に伴う増減": "Change in public pension reserves",
    "その他資産･負債差額の増減": "Other changes",
    "本年度末資産・負債差額": "Net assets at end of year",
    # 区分別収支計算書 (main lines)
    "租税等収入": "Tax and similar receipts",
    "その他の収入": "Other receipts",
    "前年度剰余金受入": "Surplus carried from previous year",
    "財源合計": "Total funding",
    "業務支出合計": "Total operating payments",
    "業務収支": "Operating cash flow",
    "公債の発行による収入": "Bond issuance",
    "公債の償還による支出": "Bond redemption",
    "利息の支払額（預託金利息を除く）": "Interest paid",
    "財務収支": "Financing cash flow",
    "本年度収支": "Net cash flow for the year",
    "本年度末現金･預金残高": "Cash and deposits at year end",
    "その他収入": "Other receipts",
    "資金からの受入（予算上措置されたもの）": "Transfers from funds (budgeted)",
    "資金への繰入（予算上措置されたもの）": "Transfers to funds (budgeted)",
    "資金からの受入（決算処理によるもの）": "Transfers from funds (settlement)",
    "資金への繰入（決算処理によるもの）": "Transfers to funds (settlement)",
    "資金からの受入": "Transfers from funds",
    "資金への繰入": "Transfers to funds",
    "恩給給付費": "Old-age pensions for former public servants (恩給)",
    "貸付けによる支出": "Lending",
    "出資による支出": "Capital investment",
    "庁費等の支出": "Office expenses",
    "その他の支出": "Other payments",
    "業務支出（施設整備支出を除く）合計": "Operating payments excl. facilities",
    "公共用財産用地に係る支出": "Public-use land",
    "公共用財産施設に係る支出": "Public-use facilities",
    "その他の施設整備支出": "Other facility payments",
    "施設整備支出合計": "Total facility payments",
    "政府短期証券の発行による収入": "Financing bill issuance",
    "政府短期証券の償還による支出": "Financing bill redemption",
    "借入による収入": "Borrowing",
    "借入金の返済による支出": "Loan repayment",
    "リース・ＰＦＩ債務の返済による支出": "Lease/PFI repayments",
    "預託金利息": "Interest on FILP deposits",
    "公債事務取扱に係る支出": "Bond administration",
    "翌年度歳入繰入": "Carried to next year's revenue",
    "特別会計に関する法律第47条第1項の規定による借換国債収入額": "Advance refunding bond receipts (Special Accounts Act art. 47)",
    "翌年度歳入繰入の預託金への運用": "Carry-over placed in FILP deposits",
    "翌年度歳入繰入の預託金以外への運用": "Carry-over placed elsewhere",
    "収支に関する換算差額": "Translation difference",
    "資金本年度末残高": "Fund balances at year end",
    "その他歳計外現金･預金本年度末残高": "Other off-budget cash at year end",
    "国庫余裕金の繰替使用": "Temporary use of treasury surplus",
    "旧臨時軍事費特別会計に係る控除額": "Deduction for former wartime special account",
    "国立研究開発法人森林総合研究所に承継する額": "Transferred to Forest Research institute",
    "「高度専門医療に関する研究等を行う独立行政法人に関する法律」第2条各号に規定する独立行政法人に承継する支出": "Transferred to national advanced-medicine research agencies",
}


def _clean(label: str) -> str:
    """Drop the roman-numeral / number prefix: 'Ⅲ　財源' -> '財源'."""
    return HEADING.sub("", norm(label)) if HEADING.match(norm(label)) else norm(label)


def _years(ws) -> tuple[int, int]:
    """(previous FY, current FY) from the 「至 …3月31日」 row."""
    for r in range(1, 10):
        b, c = ws.cell(r, 2).value, ws.cell(r, 3).value
        if isinstance(c, str) and "至" in c and isinstance(b, str):
            prev_end, cur_end = _era_year(b), _era_year(c)
            if prev_end and cur_end and cur_end == prev_end + 1:
                return prev_end - 1, cur_end - 1
    raise ValueError(f"{ws.title}: period headers (至 …) not found")


def _divisor(ws) -> int:
    for row in ws.iter_rows(min_row=1, max_row=6):
        for cell in row:
            text = norm(cell.value)
            for unit, d in UNIT_DIVISORS_TO_OKU.items():
                if "単位" in text and unit in text:
                    return d
    raise ValueError(f"{ws.title}: unit row not found")


def parse_sheet(ws, statement: str, folder: str) -> list[dict]:
    divisor = _divisor(ws)
    prev_fy, cur_fy = _years(ws)
    rows: list[dict] = []
    heading = ""
    order = 0
    seen: dict[str, int] = {}
    for r in range(6, ws.max_row + 1):
        raw = ws.cell(r, 1).value
        if raw is None:
            continue
        label = norm(raw)
        if label.startswith("(注") or label.startswith("（注"):
            break
        prev_v, cur_v = ws.cell(r, 2).value, ws.cell(r, 3).value
        if not isinstance(cur_v, int | float):
            heading = _clean(label)  # a section heading with no numbers
            continue
        item = _clean(label)
        # The net-asset statement repeats the cost total; keep it distinguishable.
        if statement == "net_assets_change" and item == "本年度業務費用合計":
            item = "本年度業務費用合計(増減)"
        # A few older layouts print the same line name twice; number the repeats.
        seen[item] = seen.get(item, 0) + 1
        if seen[item] > 1:
            item = f"{item} ({seen[item]})"
        order += 1
        for column, fy, value in (("current", cur_fy, cur_v), ("previous", prev_fy, prev_v)):
            if not isinstance(value, int | float):
                continue
            rows.append(
                {
                    "statement": statement,
                    "fiscal_year": fy,
                    "column": column,
                    "source_file_year": cur_fy,
                    "source_folder": folder,
                    "order": order,
                    "heading": heading,
                    "item_ja": item,
                    "item_en": ITEM_EN.get(item.split(" (")[0], ""),
                    "level": int(ws.cell(r, 1).alignment.indent or 0),
                    "value_oku_yen": value / divisor,
                }
            )
    return rows


def parse_all(raw_dir: Path, scope: str = "gassan") -> tuple[pd.DataFrame, list[str]]:
    rows: list[dict] = []
    skipped: list[str] = []
    for year_dir in sorted(raw_dir.glob("fy*")):
        path = year_dir / f"{scope}.xlsx"
        if not path.exists():
            continue
        try:
            check_readable_xlsx(path)
        except UnreadableWorkbook as e:
            skipped.append(str(e))
            continue
        wb = openpyxl.load_workbook(path, data_only=True)
        for statement, sheet in SHEETS.items():
            name = next((n for n in wb.sheetnames if norm(n) == sheet), None)
            if name is None:
                raise ValueError(f"{path}: sheet {sheet!r} not found")
            rows += parse_sheet(wb[name], statement, year_dir.name)
    df = pd.DataFrame(rows)
    missing = sorted({i for i in df["item_ja"] if not ITEM_EN.get(i.split(" (")[0])})
    if missing:
        warnings.warn(f"no English label for {missing}", stacklevel=2)
    return df, skipped


def canonical(df: pd.DataFrame) -> pd.DataFrame:
    """Each (statement, year) taken whole from one workbook column.

    Prefer the year's own workbook ("current"); otherwise the newest workbook's
    "previous" column. Line lists change between years, so lines are never
    mixed across workbooks.
    """
    picks = (
        df.assign(_rank=(df["column"] != "current").astype(int))
        .sort_values(["_rank", "source_file_year"], ascending=[True, False])
        .drop_duplicates(["statement", "fiscal_year"])[
            ["statement", "fiscal_year", "column", "source_file_year"]
        ]
    )
    out = df.merge(picks, on=list(picks.columns))
    return out.sort_values(["statement", "fiscal_year", "order"]).reset_index(drop=True)
