"""Build the general account budget dataset (mof-budget): parse → validate → CSV + JSON.

Outputs
    data/processed/national_budget.csv       tidy, one row per table × line
    web/public/data/national-budget.json     what the site reads
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from jfl.export.national_balance_sheet import _update_index
from jfl.fetch.mic import compact
from jfl.fetch.mof_budget import enactment
from jfl.paths import PROCESSED_DIR, RAW_DIR, WEB_DATA_DIR
from jfl.sources import load_sources
from jfl.transform import population
from jfl.transform.mof_budget import parse
from jfl.validate.budget import check

DATASET_ID = "national-budget"
SOURCE_ID = "mof-budget"

# item as printed → (display ja, en). Every printed line needs an entry, so a new
# MOF category stops the build instead of reaching the site without a translation.
LABELS = {
    "合計": ("合計", "Total"),
    # 歳入
    "租税及印紙収入": ("租税及印紙収入", "Taxes and stamp revenue"),
    "その他収入": ("その他収入", "Other revenue"),
    "公債金": ("公債金（国債の発行）", "Government bond issuance"),
    "⑴公債金": ("建設公債", "Construction bonds"),
    "⑵特例公債金": ("特例公債", "Special deficit-financing bonds"),
    # 歳出（主要経費別）
    "社会保障関係費": ("社会保障関係費", "Social security"),
    "文教及び科学振興費": ("文教及び科学振興費", "Education and science"),
    "うち科学技術振興費": ("うち科学技術振興費", "of which science and technology"),
    "国債費": ("国債費", "Debt service"),
    "恩給関係費": ("恩給関係費", "Pensions for former public servants (恩給)"),
    "地方交付税交付金等": ("地方交付税交付金等", "Transfers to local governments"),
    "防衛関係費": ("防衛関係費", "Defense"),
    "公共事業関係費": ("公共事業関係費", "Public works"),
    "経済協力費": ("経済協力費", "Economic cooperation (ODA)"),
    "中小企業対策費": ("中小企業対策費", "Small and medium enterprises"),
    "エネルギー対策費": ("エネルギー対策費", "Energy"),
    "食料安定供給関係費": ("食料安定供給関係費", "Food supply"),
    "その他の事項経費": ("その他の事項経費", "Other expenses"),
    "予備費": ("予備費", "Reserve fund"),
    # 社会保障関係費の内訳
    "年金給付費": ("年金給付費", "Pensions"),
    "医療給付費": ("医療給付費", "Medical care"),
    "介護給付費": ("介護給付費", "Long-term care"),
    "少子化対策費": ("少子化対策費", "Children and families"),
    "生活扶助等社会福祉費": ("生活扶助等社会福祉費", "Public assistance and welfare"),
    "保健衛生対策費": ("保健衛生対策費", "Public health"),
    "雇用労災対策費": ("雇用労災対策費", "Employment and work injury"),
    # 国債費の内訳
    "うち債務償還費（交付国債分を除く）": ("債務償還費", "Redemption of principal"),
    "うち利払費": ("利払費", "Interest"),
    # 税目
    "源泉所得税": ("源泉所得税", "Income tax withheld at source"),
    "申告所得税": ("申告所得税", "Income tax by self-assessment"),
    "所得税計": ("所得税", "Income tax"),
    "防衛特別所得税（仮称）": (
        "防衛特別所得税（仮称）",
        "Special income tax for defense (provisional name)",
    ),
    "法人税": ("法人税", "Corporate tax"),
    "防衛特別法人税": ("防衛特別法人税", "Special corporate tax for defense"),
    "相続税": ("相続税", "Inheritance tax"),
    "消費税": ("消費税", "Consumption tax"),
    "酒税": ("酒税", "Liquor tax"),
    "たばこ税": ("たばこ税", "Tobacco tax"),
    "揮発油税": ("揮発油税", "Gasoline tax"),
    "石油ガス税": ("石油ガス税", "Liquefied petroleum gas tax"),
    "航空機燃料税": ("航空機燃料税", "Aviation fuel tax"),
    "石油石炭税": ("石油石炭税", "Petroleum and coal tax"),
    "電源開発促進税": ("電源開発促進税", "Power development promotion tax"),
    "自動車重量税": ("自動車重量税", "Motor vehicle tonnage tax"),
    "国際観光旅客税": ("国際観光旅客税", "International tourist tax"),
    "関税": ("関税", "Customs duties"),
    "とん税": ("とん税", "Tonnage due"),
    "印紙収入": ("印紙収入", "Stamp revenue"),
    "一般会計分計": ("租税及印紙収入", "Taxes and stamp revenue"),
}

# Publisher notes that travel with the charts.
NOTES = {
    "rounding": {
        "ja": "財務省の注記：計数はそれぞれ四捨五入によっているので、端数において合計とは合致しないものがある。",
        "en": "MOF note: figures are rounded, so items may not add up exactly to totals.",
    },
    "social_security": {
        "ja": "財務省の注記：社会保障関係費は、一般歳出の内訳として主要経費別に分類したものです。年金・医療・介護などの給付の多くは社会保険料で賄われ、一般会計にはその国庫負担分だけが計上されます。",
        "en": "MOF note: social security spending here is the general account's share only. Most pension, medical and long-term care benefits are paid from social insurance contributions outside the general account.",
    },
    "debt_service": {
        "ja": "予算フレームによる内訳。債務償還費は交付国債分を除いた額で、両者の合計は国債費と一致しません。",
        "en": "Breakdown from MOF's budget frame. Redemption excludes grant bonds (交付国債), so the two parts do not add up to total debt service.",
    },
    "public_works": {
        "ja": "道路・河川・港湾などの整備は、地方公共団体の予算でも多く行われています（地方交付税交付金等はその財源の一部）。ここに示すのは国の一般会計の公共事業関係費です。",
        "en": "Much road, river and port construction is carried out in local government budgets, funded partly by the transfers to local governments. This figure is the national general account only.",
    },
    "consumption_tax": {
        "ja": "消費税の収入（地方交付税分を除く）は、法律により年金・医療・介護・少子化対策（社会保障4経費）に充てることとされています（消費税法第1条第2項）。",
        "en": "By law, consumption tax revenue (excluding the local allocation share) is to be spent on pensions, medical care, long-term care and measures for children (Consumption Tax Act, Art. 1(2)).",
    },
}


def _labels(item: str) -> tuple[str, str]:
    if item not in LABELS:
        raise SystemExit(f"{SOURCE_ID}: no display label for 「{item}」; add it to LABELS.")
    return LABELS[item]


def _supplementary(status_html: str) -> bool:
    """Whether a 補正予算 for the same year has been enacted (not included in these figures)."""
    text = compact(re.sub(r"<[^>]+>", "", status_html))
    return bool(re.search(r"年度補正予算.{0,20}は政府案どおり成立", text))


def _population(raw_root: Path) -> dict:
    folders = sorted((raw_root / "sb-population").glob("y*/table03.xlsx"))
    if not folders:
        raise SystemExit("No sb-population data; run `jfl fetch sb-population`.")
    path = folders[-1]
    series = population.parse(path)
    year = max(series)
    manifest = json.loads((path.parent / "manifest.json").read_text(encoding="utf-8"))
    src = load_sources()["sb-population"]
    return {
        "persons": series[year],
        "as_of": f"{year}-10-01",
        "source": {
            "id": src.id,
            "publisher": "総務省統計局",
            "publisher_en": "Statistics Bureau of Japan",
            "title": src.title_ja,
            "url": manifest["listing_page"],
            "file_url": manifest["files"][0]["source_url"],
        },
        "series": {str(y): v for y, v in sorted(series.items())},
    }


def build(
    raw_root: Path = RAW_DIR, processed_dir: Path = PROCESSED_DIR, web_dir: Path = WEB_DATA_DIR
):
    folders = sorted((raw_root / SOURCE_ID).glob("fy*"))
    if not folders:
        raise SystemExit(f"No {SOURCE_ID} data; run `jfl fetch {SOURCE_ID}`.")
    raw = folders[-1]
    status = (raw / "status.html").read_text(encoding="utf-8", errors="replace")
    state = enactment(status)
    if state != "as_proposed":
        raise SystemExit(f"{raw}: budget enactment is {state!r}; the 政府案 PDFs don't apply.")

    fy, rows = parse(raw)
    issues = check(rows)
    if issues:
        raise SystemExit("Validation failed:\n" + "\n".join(f"  {i}" for i in issues))

    processed_dir.mkdir(parents=True, exist_ok=True)
    csv_path = processed_dir / "national_budget.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["fiscal_year", *asdict(rows[0]).keys()])
        w.writeheader()
        for r in rows:
            w.writerow({"fiscal_year": fy, **asdict(r)})

    def lines(statement, skip=()):
        out = []
        for r in rows:
            if r.statement != statement or r.item_ja in skip:
                continue
            ja, en = _labels(r.item_ja)
            out.append(
                {
                    "item": r.item_ja,
                    "ja": ja,
                    "en": en,
                    "value": r.value_oku_yen,
                    "prev": r.prev_oku_yen,
                }
            )
        return out

    def one(statement, item):
        return next(x for x in lines(statement) if x["item"] == item)

    manifest = json.loads((raw / "manifest.json").read_text(encoding="utf-8"))
    files = {Path(f["file"]).stem: f["source_url"] for f in manifest["files"]}
    labels = dict(
        ln.split("\t", 1) for ln in (raw / "labels.tsv").read_text(encoding="utf-8").splitlines()
    )
    src = load_sources()[SOURCE_ID]

    expenditure = lines("expenditure", skip=("合計", "うち科学技術振興費"))
    revenue_total = one("revenue", "合計")["value"]
    notes_supp = _supplementary(status)
    out = {
        "id": DATASET_ID,
        "title_ja": "国の一般会計予算",
        "title_en": "National general account budget",
        "source": {
            "id": SOURCE_ID,
            "publisher": "財務省",
            "publisher_en": "Ministry of Finance",
            "title": src.title_ja,
            "url": manifest["listing_page"],
            "year_page": files["status"],
            "files": [
                {"key": k, "label": labels.get(k, k), "url": u}
                for k, u in files.items()
                if k != "status"
            ],
        },
        "unit": "億円",
        "basis": "budget",
        "stage": "initial",
        "enactment": state,
        "supplementary_enacted": notes_supp,
        "fiscal_year": fy,
        "years": [fy, fy],
        "total": revenue_total,
        "expenditure": expenditure,
        "science": one("expenditure", "うち科学技術振興費"),
        "revenue": {
            "taxes": one("revenue", "租税及印紙収入"),
            "other": one("revenue", "その他収入"),
            "bonds": one("revenue", "公債金"),
            "construction_bonds": one("revenue", "⑴公債金"),
            "deficit_bonds": one("revenue", "⑵特例公債金"),
        },
        "tax": lines("tax", skip=("一般会計分計", "源泉所得税", "申告所得税")),
        "income_tax_parts": [one("tax", "源泉所得税"), one("tax", "申告所得税")],
        "social_security": lines("social_security", skip=("社会保障関係費（Ｃ）",)),
        "debt_service": {
            "redemption": one("debt_service", "うち債務償還費（交付国債分を除く）"),
            "interest": one("debt_service", "うち利払費"),
        },
        "population": _population(raw_root),
        "notes": NOTES,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    web_dir.mkdir(parents=True, exist_ok=True)
    json_path = web_dir / f"{DATASET_ID}.json"
    json_path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    _update_index(web_dir, out)
    return csv_path, json_path, []
