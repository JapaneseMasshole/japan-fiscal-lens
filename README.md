# Japan Fiscal Lens

**Japan's public finances, national and local, as charts: balance sheets, income and cash flow from official data.**

[日本語版 README はこちら](README.ja.md)

News coverage of Japan's finances tends to pick one number — "debt is over 1,000 trillion yen", "tax revenue hit a record" — and build a story around it. Japan Fiscal Lens puts the whole picture on the table instead, built only from figures the government itself publishes, so anyone can look at it and draw their own conclusions.

## What the site shows

| Level | Statements | Official source |
|---|---|---|
| National (国) | Balance sheet, operating cost statement, cash flow by category | Ministry of Finance — 国の財務書類 |
| National (国) | Budget vs. settlement, revenue and spending by category | Ministry of Finance — 決算 |
| National (国) | Who holds government bonds | Bank of Japan — 資金循環統計 |
| Prefectures & municipalities (地方) | Balance sheet, administrative cost statement, cash flow | MIC (総務省) — 統一的な基準による財務書類 |
| Prefectures & municipalities (地方) | Revenue and spending breakdown, fiscal health indicators | MIC (総務省) — 決算カード |

Every source is listed in [`data/sources.yaml`](data/sources.yaml).

## Principles

1. **Official data only.** No estimates or projections of our own. If a figure is derived (e.g. % of GDP), the method is documented in [`docs/methodology.md`](docs/methodology.md).
2. **Every chart cites its source**, with a link to the original file.
3. **Raw files are kept unedited** in `data/raw/`, so anyone can rerun the pipeline and reproduce every number.
4. **Several views, reader's choice.** Nominal vs. inflation-adjusted, yen vs. % of GDP, gross vs. net. The same data can look alarming or calm depending on the view, so the reader picks.
5. **Data changes arrive as pull requests**, so every update to the numbers is visible in the git history.

## Repository layout

```
data/            sources.yaml, raw/ (original files), processed/ (tidy CSVs)
pipeline/        Python: fetch → transform → validate → export JSON
web/             Vue 3 + Vite + ECharts static site (reads web/public/data/)
docs/            methodology, data dictionary
notebooks/       exploratory Jupyter notebooks (not part of the build)
.github/         CI, scheduled data updates, GitHub Pages deploy
```

## Running locally

**Pipeline** (Python 3.11+):

```bash
cd pipeline
pip install -e ".[dev]"
jfl sources                          # list configured datasets
jfl fetch mof-fs --year 2024         # download MOF national financial statements
pytest
```

**Website** (Node 20+):

```bash
cd web
npm install
npm run dev
```

## Status

Early scaffold. See the issues for the roadmap.

## License

Code: [MIT](LICENSE). Data: see [DATA_LICENSE.md](DATA_LICENSE.md). The underlying data belongs to its publishers.
