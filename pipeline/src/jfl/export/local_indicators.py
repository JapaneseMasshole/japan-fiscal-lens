"""Build the local fiscal indicators dataset (総務省 主要財政指標一覧) for the site.

Output: web/public/data/local-indicators.json, compact arrays keyed by code:
    municipalities[code] = [prefecture_index, name, designated(0/1), {indicator: [v per year]}]
Values: number, null (not published) or "nc" (将来負担比率 not calculated).
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path

from jfl.export.national_balance_sheet import _update_index
from jfl.fetch.mic import PREFECTURES
from jfl.paths import PROCESSED_DIR, RAW_DIR, WEB_DATA_DIR
from jfl.sources import load_sources
from jfl.transform.mic_indicators import INDICATORS, designated_cities, parse_all
from jfl.validate.local_indicators import check

SOURCE_ID = "mic-fiscal-indicators"
KEYS = list(INDICATORS.values())

# Official descriptions (summarised) and the legal thresholds of the
# 地方公共団体財政健全化法 (総務省「早期健全化基準と財政再生基準」).
META = {
    "fiscal_strength": {
        "ja": "財政力指数",
        "en": "Fiscal strength index",
        "unit": "",
        "digits": 2,
        "desc_ja": "標準的な行政に必要な経費を、自前の税収等でどれだけ賄えるかを示す指数（過去3年平均）。1を超えると普通交付税が交付されません。",
        "desc_en": "How far a government's own standard revenue covers the cost of standard services (3-year average). Above 1.0, no ordinary local allocation tax grant is paid.",
        "thresholds": [],
    },
    "current_balance_ratio": {
        "ja": "経常収支比率",
        "en": "Current balance ratio",
        "unit": "%",
        "digits": 1,
        "desc_ja": "毎年必ず出ていく経費（人件費・扶助費・公債費など）に、毎年入ってくる一般財源がどれだけ使われているかの割合。",
        "desc_en": "Share of recurring general revenue used by recurring costs (personnel, welfare, debt service, …).",
        "thresholds": [],
    },
    "real_debt_service_ratio": {
        "ja": "実質公債費比率",
        "en": "Real debt service ratio",
        "unit": "%",
        "digits": 1,
        "desc_ja": "借金の返済額（実質的なものを含む）が、標準的な財政規模に占める割合（過去3年平均）。",
        "desc_en": "Debt service (including de facto debt service) relative to standard fiscal size (3-year average).",
        "thresholds": [
            {"value": 25, "ja": "早期健全化基準", "en": "Early-warning line", "applies": "all"},
            {"value": 35, "ja": "財政再生基準", "en": "Reconstruction line", "applies": "all"},
        ],
    },
    "future_burden_ratio": {
        "ja": "将来負担比率",
        "en": "Future burden ratio",
        "unit": "%",
        "digits": 1,
        "desc_ja": "将来支払う可能性のある負担（地方債残高など）から、充当できる基金等を差し引いた額が、標準的な財政規模に占める割合。「算定なし」は、負担額を充当可能な財源等が上回っていることを示します。",
        "desc_en": "Future obligations (such as local bonds) minus funds available to cover them, relative to standard fiscal size. 'Not calculated' means available funds exceed the obligations.",
        "thresholds": [
            {
                "value": 350,
                "ja": "早期健全化基準（市町村）",
                "en": "Early-warning line (municipalities)",
                "applies": "municipality",
            },
            {
                "value": 400,
                "ja": "早期健全化基準（都道府県・政令市）",
                "en": "Early-warning line (prefectures, designated cities)",
                "applies": "prefecture_or_designated",
            },
        ],
    },
    "laspeyres": {
        "ja": "ラスパイレス指数",
        "en": "Laspeyres index (salary level)",
        "unit": "",
        "digits": 1,
        "desc_ja": "一般行政職員の給与水準を、国家公務員を100として比べた指数。",
        "desc_en": "Salary level of general administrative staff, with national public servants = 100.",
        "thresholds": [],
    },
}


def _v(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    return x if x == "nc" else round(float(x), 5)


def build(
    raw_root: Path = RAW_DIR, processed_dir: Path = PROCESSED_DIR, web_dir: Path = WEB_DATA_DIR
):
    raw = raw_root / SOURCE_ID
    df, averages = parse_all(raw)
    issues = check(df, averages)
    if issues:
        raise SystemExit("Validation failed:\n" + "\n".join(f"  {i}" for i in issues))

    processed_dir.mkdir(parents=True, exist_ok=True)
    csv_path = processed_dir / "local_indicators.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")

    years = sorted(int(y) for y in df["fiscal_year"].unique())
    latest = raw / f"fy{years[-1]}"
    designated = designated_cities(latest)

    def series(g, key):
        s = g.set_index("fiscal_year")[key]
        return [_v(s.get(y)) for y in years]

    municipalities = {}
    muni = df[df["kind"] == "municipality"]
    for code, g in muni.groupby("code"):
        last = g.sort_values("fiscal_year").iloc[-1]  # current name after mergers/renames
        pref_i = int(code[:2]) - 1
        municipalities[code] = [
            pref_i,
            last["name"],
            int((last["prefecture"], last["name"]) in designated),
            {k: series(g, k) for k in KEYS},
        ]

    prefectures = []
    pref = df[df["kind"] == "prefecture"]
    for name in PREFECTURES:
        g = pref[pref["name"] == name]
        if g.empty:
            raise SystemExit(f"prefecture {name} missing")
        prefectures.append([name, {k: series(g, k) for k in KEYS}])

    avg = {
        which: {k: [_v(averages[y].get(which, {}).get(k)) for y in years] for k in KEYS}
        for which in ("municipal_average", "prefectural_average")
    }

    src = load_sources()[SOURCE_ID]
    pages = {}
    for y in years:
        m = json.loads((raw / f"fy{y}" / "manifest.json").read_text(encoding="utf-8"))
        pages[y] = m["listing_page"]
    out = {
        "id": "local-indicators",
        "title_ja": "地方公共団体の主要財政指標",
        "title_en": "Key fiscal indicators of local governments",
        "source": {
            "id": SOURCE_ID,
            "publisher": "総務省",
            "publisher_en": "Ministry of Internal Affairs and Communications",
            "title": src.title_ja,
            "url": src.listing_url,
            "year_pages": {str(y): u for y, u in pages.items()},
        },
        "years": years,
        "prefecture_names": PREFECTURES,
        "indicators": [{"key": k, **META[k]} for k in KEYS],
        "municipalities": municipalities,
        "prefectures": prefectures,
        "averages": avg,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    web_dir.mkdir(parents=True, exist_ok=True)
    path = web_dir / "local-indicators.json"
    path.write_text(
        json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    _update_index(web_dir, out)
    return csv_path, path, []
