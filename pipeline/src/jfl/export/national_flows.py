"""Build the national operating-cost/funding and cash-flow datasets.

Outputs
    data/processed/national_flow_statements.csv
    web/public/data/national-operating-cost.json   業務費用計算書 + 財源 (資産・負債差額増減計算書)
    web/public/data/national-cash-flow.json        区分別収支計算書
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from jfl.export.national_balance_sheet import SCOPE, SOURCE_ID, _folder_urls, _update_index
from jfl.paths import PROCESSED_DIR, RAW_DIR, WEB_DATA_DIR
from jfl.sources import load_sources
from jfl.transform import mof_balance_sheet as bs_mod
from jfl.transform import mof_flow_statements as flow_mod
from jfl.validate.flow_statements import check_flow

NOTES = {
    "operating_cost": {
        "ja": (
            "業務費用は発生主義による1年間のコストで、公債の元本償還は含みません。"
            "財源は資産・負債差額増減計算書の「財源」（租税等とその他。その他には社会保険料などを含みます）です。"
            "国の財務書類では税収を企業の売上のようには扱わないため、「利益」の行はありません。"
        ),
        "en": (
            "Operating cost is the accrual-basis cost of the year and excludes repayment of bond "
            "principal. Funding is the 財源 line of the statement of changes in net assets "
            "(taxes and other sources, including social insurance premiums). Government "
            "statements do not treat taxes as sales, so there is no 'profit' line."
        ),
    },
    "cash_flow": {
        "ja": (
            "区分別収支計算書は現金ベースです。業務収支には前年度剰余金の受入なども含まれます。"
            "財務収支には公債の発行・償還、借入・返済、利払いなどが含まれます。"
        ),
        "en": (
            "The cash flow statement is on a cash basis. Operating cash flow also includes items "
            "such as the surplus carried over from the previous year. Financing cash flow covers "
            "bond issuance and redemption, borrowing and repayment, and interest."
        ),
    },
}


def _num(v: float) -> float | None:
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else round(float(v), 2)


def _series(df: pd.DataFrame, statement: str, item: str, years: list[int]) -> list[float | None]:
    s = df[(df["statement"] == statement) & (df["item_ja"] == item)].set_index("fiscal_year")
    return [_num(s["value_oku_yen"].get(y)) for y in years]


def _lines(df: pd.DataFrame, statement: str, years: list[int]) -> list[dict]:
    """All lines of a statement across years, in the order of the newest year's layout."""
    d = df[df["statement"] == statement]
    order = d.sort_values(["fiscal_year", "order"], ascending=[False, True]).drop_duplicates(
        "item_ja"
    )[["item_ja", "item_en", "heading", "level"]]
    out = []
    for row in order.itertuples():
        out.append(
            {
                "item_ja": row.item_ja,
                "item_en": row.item_en,
                "heading": row.heading,
                "level": int(row.level),
                "values": _series(df, statement, row.item_ja, years),
            }
        )
    return out


def _provenance(df: pd.DataFrame, statement: str, urls: dict[str, str]) -> list[dict]:
    d = df[df["statement"] == statement].drop_duplicates("fiscal_year")
    return [
        {
            "fiscal_year": int(r.fiscal_year),
            "file_url": urls.get(r.source_folder, ""),
            "column": "本会計年度" if r.column == "current" else "前会計年度",
        }
        for r in d.itertuples()
    ]


def _missing(skipped: list[str], raw: Path, years: list[int]) -> list[dict]:
    folders = {int(p.name[2:]) for p in raw.glob("fy*") if p.is_dir()}
    return [
        {
            "fiscal_year": y,
            "reason_ja": "財務省が公開したExcelファイルが暗号化（権限管理）されており開けません。",
            "reason_en": "The Excel file published by the Ministry of Finance is rights-protected "
            "(encrypted) and cannot be opened.",
        }
        for y in sorted(folders - set(years))
        if any(f"fy{y}/" in s for s in skipped)
    ]


def build(
    raw_root: Path = RAW_DIR, processed_dir: Path = PROCESSED_DIR, web_dir: Path = WEB_DATA_DIR
):
    raw = raw_root / SOURCE_ID
    flow_all, skipped = flow_mod.parse_all(raw, SCOPE)
    flow = flow_mod.canonical(flow_all)
    bs = bs_mod.canonical(bs_mod.parse_all(raw, SCOPE)[0])

    issues = check_flow(flow, bs)
    if issues:
        raise SystemExit("Validation failed:\n" + "\n".join(f"  {i}" for i in issues))

    processed_dir.mkdir(parents=True, exist_ok=True)
    csv_path = processed_dir / "national_flow_statements.csv"
    flow.to_csv(csv_path, index=False, encoding="utf-8")

    years = sorted(int(y) for y in flow["fiscal_year"].unique())
    urls = _folder_urls(raw)
    src = load_sources()[SOURCE_ID]
    now = datetime.now(UTC).isoformat(timespec="seconds")
    base_source = {
        "id": SOURCE_ID,
        "publisher": "財務省",
        "publisher_en": "Ministry of Finance",
        "title": src.title_ja,
        "url": src.listing_url,
    }
    missing = _missing(skipped, raw, years)

    cost = {
        "id": "national-operating-cost",
        "title_ja": "国の業務費用と財源（一般会計・特別会計 合算）",
        "title_en": "National government operating cost and funding (general + special accounts)",
        "source": {**base_source, "provenance": _provenance(flow, "operating_cost", urls)},
        "unit": "億円",
        "basis": "accrual",
        "scope": SCOPE,
        "years": years,
        "missing_years": missing,
        "totals": {
            "cost": _series(flow, "operating_cost", "本年度業務費用合計", years),
            "funding": _series(flow, "net_assets_change", "財源", years),
            "funding_tax": _series(flow, "net_assets_change", "租税等財源", years),
            "funding_other": _series(flow, "net_assets_change", "その他の財源", years),
        },
        "lines": [
            line
            for line in _lines(flow, "operating_cost", years)
            if line["item_ja"] != "本年度業務費用合計"
        ],
        "notes": [NOTES["operating_cost"]],
        "generated_at": now,
    }
    cash = {
        "id": "national-cash-flow",
        "title_ja": "国の区分別収支（一般会計・特別会計 合算）",
        "title_en": "National government cash flow by category (general + special accounts)",
        "source": {**base_source, "provenance": _provenance(flow, "cash_flow", urls)},
        "unit": "億円",
        "basis": "cash",
        "scope": SCOPE,
        "years": years,
        "missing_years": missing,
        "totals": {
            "operating": _series(flow, "cash_flow", "業務収支", years),
            "financing": _series(flow, "cash_flow", "財務収支", years),
            "net": _series(flow, "cash_flow", "本年度収支", years),
            "bond_issuance": _series(flow, "cash_flow", "公債の発行による収入", years),
            "bond_redemption": _series(flow, "cash_flow", "公債の償還による支出", years),
        },
        "lines": _lines(flow, "cash_flow", years),
        "notes": [NOTES["cash_flow"]],
        "generated_at": now,
    }

    web_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for dataset in (cost, cash):
        p = web_dir / f"{dataset['id']}.json"
        p.write_text(json.dumps(dataset, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        _update_index(web_dir, dataset)
        paths.append(p)
    return csv_path, paths, skipped
