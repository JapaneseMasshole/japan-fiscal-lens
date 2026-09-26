"""Build the national balance sheet dataset: parse → validate → CSV + JSON.

Outputs
    data/processed/national_balance_sheet.csv     tidy, one row per year × line
    web/public/data/national-balance-sheet.json   what the site reads
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from jfl.paths import PROCESSED_DIR, RAW_DIR, WEB_DATA_DIR
from jfl.sources import load_sources
from jfl.transform.mof_balance_sheet import canonical, parse_all
from jfl.validate.balance_sheet import check_all, compare_restatements

DATASET_ID = "national-balance-sheet"
SOURCE_ID = "mof-fs"
SCOPE = "gassan"

# MOF's own caveat (注2 under every balance sheet), summarised. Shown next to the chart.
MOF_NOTE = {
    "ja": (
        "財務省の注記（要約）：国の資産には、道路・河川など売却して現金化することを"
        "基本的に予定していない公共用財産が相当程度含まれています。このため、"
        "資産・負債差額が必ずしも将来の国民負担となる額を示すものではありません。"
    ),
    "en": (
        "Ministry of Finance note (summarised): a large share of the government's assets is "
        "public-use property such as roads and rivers, which is not intended to be sold. "
        "The gap between assets and liabilities therefore does not necessarily equal the "
        "future burden on the public."
    ),
}


def _folder_urls(raw: Path) -> dict[str, str]:
    """Map raw folder (e.g. 'fy2023') → the URL its 合算 workbook was downloaded from."""
    urls = {}
    for manifest in sorted(raw.glob("fy*/manifest.json")):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        for f in data["files"]:
            if f["file"].startswith(SCOPE):
                urls[manifest.parent.name] = f["source_url"]
    return urls


def _provenance(df: pd.DataFrame, raw: Path) -> list[dict]:
    """For each fiscal year: the exact workbook and column its figures came from."""
    urls = _folder_urls(raw)
    out = []
    for fy, g in df.groupby("fiscal_year"):
        first = g.iloc[0]
        out.append(
            {
                "fiscal_year": int(fy),
                "file_url": urls.get(first["source_folder"], ""),
                "column": "本会計年度" if first["column"] == "current" else "前会計年度",
            }
        )
    return out


def build(
    raw_root: Path = RAW_DIR, processed_dir: Path = PROCESSED_DIR, web_dir: Path = WEB_DATA_DIR
):
    raw = raw_root / SOURCE_ID
    all_rows, skipped = parse_all(raw, SCOPE)
    if all_rows.empty:
        raise SystemExit(f"No readable {SCOPE} workbooks in {raw}")

    issues = check_all(all_rows)
    if issues:
        raise SystemExit("Validation failed:\n" + "\n".join(f"  {i}" for i in issues))
    restated = compare_restatements(all_rows)

    df = canonical(all_rows)
    processed_dir.mkdir(parents=True, exist_ok=True)
    csv_path = processed_dir / "national_balance_sheet.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")

    years = sorted(int(y) for y in df["fiscal_year"].unique())
    available_folders = {int(p.name[2:]) for p in raw.glob("fy*") if p.is_dir()}
    missing = [
        {
            "fiscal_year": y,
            "reason_ja": "財務省が公開したExcelファイルが暗号化（権限管理）されており開けません。",
            "reason_en": "The Excel file published by the Ministry of Finance is rights-protected "
            "(encrypted) and cannot be opened.",
        }
        for y in sorted(available_folders - set(years))
        if any(f"fy{y}/" in s or f"fy{y}\\" in s for s in skipped)
    ]

    def series(item: str) -> list[float]:
        s = df[df["item_ja"] == item].set_index("fiscal_year")["value_oku_yen"]
        return [round(float(s[y]), 2) for y in years]

    lines = []
    for (section, order, item_ja), g in df[~df["is_total"]].groupby(
        ["section", "order", "item_ja"]
    ):
        g = g.set_index("fiscal_year")
        first = g.iloc[0]
        lines.append(
            {
                "section": section,
                "order": int(order),
                "item_ja": item_ja,
                "item_en": first["item_en"],
                "level": int(first["level"]),
                "parent_ja": first["parent_ja"],
                "values": [round(float(g["value_oku_yen"].get(y, float("nan"))), 2) for y in years],
            }
        )
    section_rank = {"assets": 0, "liabilities": 1, "net_assets": 2}
    lines.sort(key=lambda x: (section_rank[x["section"]], x["order"]))

    src = load_sources()[SOURCE_ID]
    out = {
        "id": DATASET_ID,
        "title_ja": "国の貸借対照表（一般会計・特別会計 合算）",
        "title_en": "National government balance sheet (general + special accounts)",
        "source": {
            "id": SOURCE_ID,
            "publisher": "財務省",
            "publisher_en": "Ministry of Finance",
            "title": src.title_ja,
            "url": src.listing_url,
            "provenance": _provenance(df, raw),
        },
        "unit": "億円",
        "basis": "accrual",
        "scope": SCOPE,
        "as_of": "each fiscal year end (March 31)",
        "years": years,
        "missing_years": missing,
        "totals": {
            "assets": series("資産合計"),
            "liabilities": series("負債合計"),
            "net_assets": series("資産・負債差額"),
        },
        "lines": lines,
        "notes": [MOF_NOTE],
        "restatements": len(restated),
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    web_dir.mkdir(parents=True, exist_ok=True)
    json_path = web_dir / f"{DATASET_ID}.json"
    json_path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    _update_index(web_dir, out)
    return csv_path, json_path, skipped


def _update_index(web_dir: Path, dataset: dict) -> None:
    path = web_dir / "index.json"
    index = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"datasets": []}
    entries = [d for d in index.get("datasets", []) if d["id"] != dataset["id"]]
    entries.append(
        {
            "id": dataset["id"],
            "title_ja": dataset["title_ja"],
            "title_en": dataset["title_en"],
            "years": [dataset["years"][0], dataset["years"][-1]],
            "source_id": dataset["source"]["id"],
        }
    )
    index = {
        "generated_at": dataset["generated_at"],
        "datasets": sorted(entries, key=lambda d: d["id"]),
    }
    path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
