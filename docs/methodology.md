# Methodology / 方法

This page explains how every number on the site is produced. If a chart and this page disagree, the chart is wrong. Please open an issue.

## 1. Two kinds of government accounts

Japanese governments publish two different sets of figures, and news coverage often mixes them up.

| | Cash basis (現金主義) | Accrual basis (発生主義) |
|---|---|---|
| National | 一般会計 決算: tax revenue, bond issuance, spending | 国の財務書類: balance sheet, operating cost, cash flow by category |
| Local | 決算カード, 地方財政状況調査 | 統一的な基準による財務書類 |
| Answers | "How much came in and went out this year?" | "What does the government own and owe, and what did this year really cost?" |

The accrual statements are the ones closest to a company's balance sheet, income statement and cash flow statement. The site labels which basis each chart uses.

## 2. Corporate statements vs. government statements

| Company | National government (国) | Local government (地方) |
|---|---|---|
| Balance sheet | 貸借対照表 | 貸借対照表 |
| Income statement | 業務費用計算書 (costs only; taxes are not treated as "sales") | 行政コスト計算書 |
| Statement of changes in equity | 資産・負債差額増減計算書 | 純資産変動計算書 |
| Cash flow statement | 区分別収支計算書 | 資金収支計算書 |

Governments do not "earn" taxes the way a company earns sales, so there is no profit line. Tax revenue appears in the change-in-net-assets statement instead. The site says this plainly rather than forcing a corporate "profit" figure.

## 3. Scope choices that change the numbers

- **合算 vs. 連結 (national):** 合算 covers the general and special accounts. 連結 also includes related public entities (independent administrative agencies and others). The site shows 合算 by default and lets readers switch.
- **Gross vs. net debt:** gross debt ignores assets; net debt subtracts financial assets. Both are shown, side by side.
- **Central government vs. general government:** the 国の財務書類 do not include local governments or social security funds. International comparisons (IMF, OECD) usually use general government, so they are not directly comparable with these statements.

## 4. Processing rules

1. Original files are stored unedited in `data/raw/<source-id>/fy<year>/`, with a `manifest.json` recording the URL, SHA-256 hash and fetch time.
2. Units are unified to **億円 (100 million yen)**. Display may convert to 兆円.
3. Fiscal years are April–March, labelled by starting year (FY2024 = 令和6年度 = April 2024 – March 2025).
4. Derived figures (per-capita, % of GDP, inflation-adjusted) state their denominator's source and year.
5. Validation checks run on every change, e.g. assets = liabilities + net assets, and components sum to reported totals.

## 5. Chart rules

- **Shared scales.** When two charts sit side by side for comparison (e.g. assets vs. liabilities), they use the same axis range.
- **"Other" grouping.** In breakdown charts, lines under 2% of their side's total are combined into "Other (n items)". The rule is mechanical, the grouped items are listed in the tooltip, and every line appears in the table view.
- **Publisher caveats travel with the chart.** When the source document carries a note that changes how a figure should be read (e.g. MOF's note that net assets are not the future burden on the public), it is shown under the chart.

## 6. Local government indicators (主要財政指標一覧)

- **Source:** 総務省「地方公共団体の主要財政指標一覧」, one workbook for all prefectures and one for all municipalities per year (FY2015 onward). Values are shown exactly as published.
- **"Not calculated" is not zero.** In 将来負担比率, 総務省 prints "-" when the ratio is not calculated because funds available to cover future obligations exceed them. The site labels these 「算定なし」, lists them separately in rankings, and never plots them as 0. In other columns a dash means "not published" and is shown as a gap.
- **Benchmarks are official averages only:** 全国市町村平均 for municipalities and 都道府県平均 for prefectures, as printed in the same workbooks.
- **Legal thresholds** come from the 地方公共団体財政健全化法 (総務省「早期健全化基準と財政再生基準」): 実質公債費比率 25% (early warning) and 35% (reconstruction); 将来負担比率 350% for municipalities and 400% for prefectures and designated cities (early warning only). A threshold is drawn on a chart only when the data reaches at least half its value; otherwise it is stated in text, so a distant line does not flatten the trend.
- **No verdicts.** Indicators are not colored good/bad. Population, industry and geography differ, so the page says plainly that a high or low value alone does not show whether finances are sound.

## 7. Known problems in the source files

Each problem is detected by the pipeline and never silently patched.

| Found | File | Problem | How it is handled |
|---|---|---|---|
| 2026-09-26 | MOF 国の財務書類 FY2024, 合算 and 一般会計 Excel | Published with Microsoft rights-management (DRM) encryption; cannot be opened outside MOF. The 連結 Excel file is normal. | FY2024 is shown as missing, with the reason, until MOF republishes. |
| 2026-09-26 | MOF 国の財務書類 FY2021 page | The 合算 Excel link points to the FY2019 file (`fy2019/national/fy2019gassan.xlsx`). | The parser reads the fiscal year from each sheet's own date headers, so a misfiled workbook cannot mislabel data. The fetcher tries the correctly-named FY2021 file first, and now downloads it. National charts therefore start at FY2019 (from the FY2020 file's 前会計年度 column). |

## 8. What this site does not do

- No forecasts, projections or scenarios.
- No judgement words ("crisis", "safe") in chart titles or labels.
- No selective time ranges: charts default to the full available history.
