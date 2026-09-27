# CLAUDE.md — Japan Fiscal Lens

Public website that shows Japan's national and local public finances as charts, built **only** from official government data, so readers can judge for themselves without media spin. Live at https://japanesemasshole.github.io/japan-fiscal-lens/.

The owner (Jimmy) is bilingual Japanese/English and fluent in Python. The site is Japanese-first with an English toggle.

## Non-negotiable principles

These come before looks, speed or convenience. If a request conflicts with one, say so and ask.

1. **Official data only.** No estimates, forecasts, scenarios or made-up numbers, not even as placeholders. An empty card says 「データ準備中」 or shows a "coming next" list; it never shows dummy charts.
2. **Every chart cites its source**, with a link to the publisher's page and 「（加工して作成）」 / "processed by Japan Fiscal Lens" (Government Standard Terms of Use). Web JSON without a `source` object must not be drawn (`web/src/data.js` enforces this).
3. **Raw files are never edited.** `data/raw/<source-id>/fy<year>/` keeps originals plus `manifest.json` (URL, SHA-256, size, fetch time).
4. **No verdicts.** No good/bad colors, no judgement words (危機, 健全, "crisis", "safe") in titles or labels. Status colors are not used for data.
5. **Honest scales.** Charts shown side by side for comparison share one axis range. Stat-tile sparklines are zero-anchored. Charts default to the full available history.
6. **Publisher caveats travel with the chart.** Example: MOF's note that 資産・負債差額 is not the future burden on the public is shown under the balance sheet chart.
7. **"Not calculated" is not zero.** In 将来負担比率, 総務省 prints "-" when available funds exceed the burden. It is stored as `"nc"` and shown as 「算定なし」, listed in text and never plotted as 0. In other columns a dash means "not published" (`null`).
8. **Problems in source files are detected and documented, never silently patched.** Record them in `docs/methodology.md` §8.

## Repository layout

```
data/sources.yaml        catalog of every dataset (id, publisher, listing_url, year_pages, notes)
data/raw/                original downloads (committed), one folder per source id and fiscal year
data/processed/          tidy CSVs written by the pipeline
pipeline/src/jfl/
  fetch/                 download originals: mof_financial_statements.py, mof_budget.py, ipss.py,
                         population.py, mic.py, common.py
  transform/             parse Excel/PDF: mof_balance_sheet.py, mof_flow_statements.py, mof_budget.py (PDF),
                         ipss_social_security.py, population.py, mic_indicators.py, excel.py
  validate/              reconciliation checks; a failed check stops the build
  export/                write web/public/data/*.json and index.json
  cli.py                 `jfl` command
pipeline/tests/          pytest; runs against the committed raw files + HTML fixtures of official pages
web/                     Vue 3 + Vite + ECharts static site (GitHub Pages)
  src/pages/             Overview, National, Local, Methodology
  src/components/        ChartCard, DataTable, StatTile, BalanceSheet, OperatingCost, CashFlow,
                         IndicatorTrend, RankBars, ComingNext
  src/charts.js          shared ECharts option builders (mark specs live here)
  src/echarts.js         tree-shaken ECharts: register every chart type/component you use
  src/i18n.js            all UI text, ja + en (t() for strings, tm() for lists)
docs/methodology.md      how numbers are produced, chart rules, known source problems
docs/data-dictionary.md  processed CSV / web JSON schemas
.github/workflows/       test.yml, deploy.yml, update-data.yml
```

## Commands

```bash
# pipeline (Python 3.11+)
cd pipeline && pip install -e ".[dev]"
jfl sources                      # list datasets and which have fetchers
jfl fetch all                    # every source, default years
jfl fetch mof-fs --year 2024     # one source/year; add --dry-run to preview
jfl build all                    # parse → validate → export JSON (fails on any reconciliation issue)
pytest -q && ruff check . && ruff format --check .

# web (Node 20+)
cd web && npm install
npm run dev                      # local preview
npm run build                    # must pass before pushing
```

## Data conventions

- **Units:** store 億円 (`value_oku_yen`); display 兆円 via `web/src/format.js`. MOF source unit is 百万円 (÷100).
- **Fiscal years** are labelled by starting year: FY2024 = 令和6年度 = Apr 2024–Mar 2025. Balance sheets are dated 3月31日 of the following year.
- **Read the fiscal year from the sheet's own headers,** never trust file or folder names (see MOF FY2021 incident). `_era_year()` handles 令和/平成/元年 and 「至 令和6年3月31日」.
- **Each statement-year comes whole from one workbook column.** Prefer the year's own workbook ("current"); otherwise use the newest workbook's 前会計年度 column. Never mix lines across workbooks.
- **Provenance:** every exported year records the exact file URL and column it came from.
- **MIC file names are serial numbers** (`main_content/001031221.xlsx`). Identify files by link text; `labels.tsv` records which text each file came from. Prefectures use JIS codes (`pref-28` = 兵庫県).
- **Validation tolerance:** MOF drops amounts below 1百万円 per line, so a sum of n lines may differ from its subtotal by up to about n百万円 (`_tol(n)`).
- **Current checks:** balance-sheet subtotals, totals and assets = liabilities + net assets; cost/cash-flow sums; net-asset roll-forward ties to the balance sheet at both ends; year-end cash ties to 現金・預金; local indicators entity counts, unique codes and parsing-error bounds (夕張市's ~70% 実質公債費比率 is real).

## Chart rules

- Colors are CSS tokens in `web/src/style.css` (light and dark): `--viz-series-1/2/3` (validated categorical slots: blue, orange, aqua), `--viz-context` (gray for "the rest" behind a highlight), `--viz-reference` (averages, thresholds). Read them through `tokens()` in `theme.js`. Never hard-code hex in components, and never add a 4th categorical color without validating it.
- Marks: 2px lines; ≥8px markers with a 2px surface ring; bars ≤18px with 4px rounded data-ends; hairline solid gridlines (no dashes); text in text colors, never the series color.
- ≥2 series → legend plus selective direct labels. Every chart has a hover tooltip and a table view (`DataTable`); tooltips never hold the only copy of a value. Build tooltip DOM with `textContent`, never `innerHTML`.
- Breakdowns fold lines under 2% of the total into 「その他（n項目）」, listing members in the tooltip.
- One filter row above the charts (sticky); the year selector drives every breakdown on the page.
- Legal thresholds (財政健全化法: 実質公債費比率 25% / 35%; 将来負担比率 350% municipalities, 400% prefectures and 政令市) are drawn only when data reaches half the threshold; otherwise they are stated in text.
- Check every visual change at 390px width and in dark mode; no horizontal page scroll.

## Sources and their quirks

| id | What | Notes |
|---|---|---|
| `mof-fs` | 国の財務書類 (合算/一般会計/連結), FY2019– | FY2024 合算 and 一般会計 Excel files are **DRM-encrypted by MOF**: detected and skipped, and FY2024 is shown as missing with the reason. FY2021 page linked the FY2019 file; the fetcher now tries the correctly named file first. |
| `mic-fiscal-indicators` | 主要財政指標一覧, FY2015– | Year-page URLs are irregular, so they're discovered by link text. FY2015 is a legacy `.xls` (needs `xlrd`). |
| `mof-budget` | 一般会計 当初予算: 歳入, 主要経費別 歳出, 税目別, 社会保障関係費・国債費の内訳 | **PDF only**, parsed with pdfplumber; every line matched against a fixed list. Used only when the year page says 「政府案どおり成立」 (FY2025 was amended by the Diet, so it can't be used). Newest enacted year only. |
| `ipss-ss-cost` | 社会保障費用統計 第8/13/14表, FY1950– | All social security incl. premiums (被保険者拠出 / 事業主拠出). Settled figures, ~2 years behind the budget; never added to budget figures. |
| `sb-population` | 人口推計 (10月1日) via e-Stat | Per-person denominator. Raw folder is `y<year>` (calendar date). |
| `mic-unified-fs` | 統一的な基準による財務書類 (詳細版) | Fetched FY2023 only (files are large). **Downloaded but not yet parsed.** Next task. |
| others in `sources.yaml` | 財政統計, BOJ 資金循環, 決算カード, … | Catalogued, no fetcher yet. |

## Workflow

- **Branch and pull request; don't push to `main`.** Merging to `main` redeploys the site (`deploy.yml`).
- **Data updates arrive as PRs** from `update-data.yml` (monthly, or run it manually). It fetches all sources, runs `jfl build all`, and opens a PR. The bot's PR shows "action required" for checks; that's expected.
- Adding a data source: add it to `sources.yaml` → write the fetcher plus an HTML fixture test → run it and inspect the real files → transform, validate and export with tests using known published values → UI → update `methodology.md` and `data-dictionary.md`.
- Commit messages: imperative summary line, then what changed and why.
