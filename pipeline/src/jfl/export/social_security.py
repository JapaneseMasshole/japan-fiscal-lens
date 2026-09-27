"""Build the social security dataset (IPSS 社会保障費用統計): parse → validate → CSV + JSON.

Outputs
    data/processed/social_security.csv     tidy, one row per table × year × item
    web/public/data/social-security.json   what the site reads
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from jfl.export.national_balance_sheet import _update_index
from jfl.export.national_budget import _population
from jfl.paths import PROCESSED_DIR, RAW_DIR, WEB_DATA_DIR
from jfl.sources import load_sources
from jfl.transform.ipss_social_security import TABLES, parse_all
from jfl.validate.social_security import check

DATASET_ID = "social-security"
SOURCE_ID = "ipss-ss-cost"

# IPSS's own notes (summarised), shown with the charts.
NOTES = {
    "income_from_capital": {
        "ja": "国立社会保障・人口問題研究所の注記（要約）：資産収入は公的年金制度等の運用実績により年度ごとに大きく変動します。「その他」には積立金からの受入等を含みます。",
        "en": "IPSS note (summarised): income from capital swings from year to year with the investment results of public pension funds. 'Others' includes transfers from reserves.",
    },
    "public": {
        "ja": "公費負担は、国庫負担（国）と他の公費負担（主に地方公共団体）の合計です。",
        "en": "Tax-funded contributions are the national government's share plus other public contributions (mainly local governments).",
    },
    "revenue_vs_benefit": {
        "ja": "財源（収入）と給付費（支出のうち給付に充てた分）は別々に集計されたもので、合計は一致しません。",
        "en": "Revenue and benefits are compiled separately; the totals do not match.",
    },
    "insured": {
        "ja": "被保険者拠出には、会社員・公務員が給与から納める保険料のほか、国民年金・国民健康保険・後期高齢者医療・介護保険の保険料も含まれます。事業主拠出は、事業主（雇い主）が被用者の保険料として負担する分です。",
        "en": "Contributions from insured persons include premiums deducted from employees' pay as well as premiums for the national pension, national health insurance, late-stage elderly medical care and long-term care insurance. Employer contributions are paid by employers for their employees.",
    },
    "break_2015": {
        "ja": "2015年度から集計対象の範囲が変わったため、2014年度との間に段差があります。",
        "en": "The scope changed in FY2015, so there is a break between FY2014 and FY2015.",
    },
    "bridge": {
        "ja": "国の一般会計の社会保障関係費は、このうち主に「国庫負担」に当たります。両者を足し合わせると二重計上になります。",
        "en": "The general account's social security spending corresponds mainly to the 'national government' share here. Adding the two together would count the same money twice.",
    },
}


def build(
    raw_root: Path = RAW_DIR, processed_dir: Path = PROCESSED_DIR, web_dir: Path = WEB_DATA_DIR
):
    folders = sorted((raw_root / SOURCE_ID).glob("fy*"))
    if not folders:
        raise SystemExit(f"No {SOURCE_ID} data; run `jfl fetch {SOURCE_ID}`.")
    raw = folders[-1]
    rows = parse_all(raw)
    issues = check(rows)
    if issues:
        raise SystemExit("Validation failed:\n" + "\n".join(f"  {i}" for i in issues))

    processed_dir.mkdir(parents=True, exist_ok=True)
    csv_path = processed_dir / "social_security.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(asdict(rows[0]).keys()))
        w.writeheader()
        w.writerows(asdict(r) for r in rows)

    tables = {}
    for table, (_, items) in TABLES.items():
        t_rows = [r for r in rows if r.table == table]
        years = sorted({r.fiscal_year for r in t_rows})
        val = {(r.fiscal_year, r.item_ja): r.value_oku_yen for r in t_rows}
        tables[table] = {
            "years": years,
            "items": [
                {"ja": ja, "en": en, "values": [val.get((y, ja)) for y in years]}
                for ja, en in items
            ],
        }

    manifest = json.loads((raw / "manifest.json").read_text(encoding="utf-8"))
    labels = dict(
        ln.split("\t", 1) for ln in (raw / "labels.tsv").read_text(encoding="utf-8").splitlines()
    )
    src = load_sources()[SOURCE_ID]
    latest = max(r.fiscal_year for r in rows)
    first = min(r.fiscal_year for r in rows)
    out = {
        "id": DATASET_ID,
        "title_ja": "社会保障費用（給付と財源）",
        "title_en": "Social security benefits and revenue",
        "source": {
            "id": SOURCE_ID,
            "publisher": "国立社会保障・人口問題研究所",
            "publisher_en": "National Institute of Population and Social Security Research",
            "title": src.title_ja,
            "url": manifest["listing_page"],
            "files": [
                {
                    "key": Path(f["file"]).stem,
                    "label": labels.get(Path(f["file"]).stem, ""),
                    "url": f["source_url"],
                }
                for f in manifest["files"]
            ],
        },
        "unit": "億円",
        "basis": "settlement",
        "latest_year": latest,
        "years": [first, latest],
        "tables": tables,
        "population": _population(raw_root),
        "notes": NOTES,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    web_dir.mkdir(parents=True, exist_ok=True)
    json_path = web_dir / f"{DATASET_ID}.json"
    json_path.write_text(
        json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    _update_index(web_dir, out)
    return csv_path, json_path, []
