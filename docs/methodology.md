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
- **Bars or pie.** Each breakdown can be shown as sorted bars (default) or as a pie of the same rows. The choice applies to every breakdown at once, so charts compared side by side always use the same form, and it is remembered in the viewer's browser. The pie uses one hue stepped lighter by rank with "Other" in gray, and labels every slice with its share (or yen out of ¥100). It is offered only when no item is negative.
- **Publisher caveats travel with the chart.** When the source document carries a note that changes how a figure should be read (e.g. MOF's note that net assets are not the future burden on the public), it is shown under the chart.

## 6. National budget and social security (予算・社会保障)

The home page and the National page answer "how much is spent, on what, and who pays for it" from three sources.

**The general account budget (`mof-budget`).**
- Source: 財務省's budget documents for the newest enacted year: 一般会計歳入歳出概算 (revenue and 主要経費別 spending), 租税及び印紙収入概算 (taxes by type), 予算フレーム (国債費 split into 債務償還費 and 利払費) and 社会保障関係予算 (社会保障関係費 by 年金・医療・介護 …).
- These are **PDF only**. The pipeline extracts the text with `pdfplumber`, matches every line name against a fixed list and stops on any unknown or missing line. It then checks that the parts add up to their printed totals (MOF rounds each line to 1億円), that revenue equals spending, that the tax table ties to 租税及印紙収入, and that the 社会保障関係費 breakdown and the budget frame tie to the 主要経費別 table. Tests assert the printed figures (歳出合計 1,223,092億円 for FY2026, and others).
- These figures are the Cabinet's budget (政府案). They are used only when the year page states that the Diet enacted it 「政府案どおり」. When the Diet amends a budget (as with FY2025), the build stops rather than show figures that were changed. Supplementary budgets (補正予算) are not included; the page says so when one has been enacted.
- A budget is a plan, not a result. Actual spending (決算) differs and is published about 1.5 years later. The site labels budget figures 「当初予算」.
- 国債費 is split into 債務償還費 and 利払費 as printed in the budget frame. 債務償還費 excludes 交付国債, so the two parts do not add up to 国債費. The small remainder is not shown as a separate item.

**Social security as a whole (`ipss-ss-cost`).**
- Most pension, medical and long-term care money never passes through the general account. It is paid from social insurance funds (年金特別会計, 協会けんぽ, 健保組合, 国保, …). To show who pays, the site uses 国立社会保障・人口問題研究所「社会保障費用統計」 第８表 (benefits by 医療・年金・福祉その他), 第13表 (by function) and 第14表 (revenue by source, ILO standard). Revenue splits 社会保険料 into 被保険者拠出 (insured persons) and 事業主拠出 (employers).
- These are settled figures for an earlier year than the budget (FY2024 vs FY2026). The two are never added together. The budget's 社会保障関係費 largely corresponds to IPSS's 国庫負担, so a sum would count the same money twice.
- IPSS notes that travel with the charts: 資産収入 swings with pension-fund returns; revenue and benefits are compiled separately and their totals differ; the scope changed in FY2015.
- 被保険者拠出 is not only payroll deductions. It also includes national pension, national health insurance, late-stage elderly and long-term care premiums paid by the self-employed, retirees and others.

**Per-person figures (`sb-population`).**
- Totals are divided by 総務省統計局「人口推計」 total population as of 1 October (第３表). The newest published year is used for the budget, and the matching year for IPSS figures. The page names the date used. This is arithmetic on two official figures, not an estimate. Raw files are stored as `data/raw/sb-population/y<year>/`, because the date is a calendar date, not a fiscal year.

## 7. Local government indicators (主要財政指標一覧)

- **Source:** 総務省「地方公共団体の主要財政指標一覧」, one workbook for all prefectures and one for all municipalities per year (FY2015 onward). Values are shown exactly as published.
- **"Not calculated" is not zero.** In 将来負担比率, 総務省 prints "-" when the ratio is not calculated because funds available to cover future obligations exceed them. The site labels these 「算定なし」, lists them separately in rankings, and never plots them as 0. In other columns a dash means "not published" and is shown as a gap.
- **Benchmarks are official averages only:** 全国市町村平均 for municipalities and 都道府県平均 for prefectures, as printed in the same workbooks.
- **Legal thresholds** come from the 地方公共団体財政健全化法 (総務省「早期健全化基準と財政再生基準」): 実質公債費比率 25% (early warning) and 35% (reconstruction); 将来負担比率 350% for municipalities and 400% for prefectures and designated cities (early warning only). A threshold is drawn on a chart only when the data reaches at least half its value; otherwise it is stated in text, so a distant line does not flatten the trend.
- **No verdicts.** Indicators are not colored good/bad. Population, industry and geography differ, so the page says plainly that a high or low value alone does not show whether finances are sound.

## 8. Known problems in the source files

Each problem is detected by the pipeline and never silently patched.

| Found | File | Problem | How it is handled |
|---|---|---|---|
| 2026-09-26 | MOF 国の財務書類 FY2024, 合算 and 一般会計 Excel | Published with Microsoft rights-management (DRM) encryption; cannot be opened outside MOF. The 連結 Excel file is normal. | FY2024 is shown as missing, with the reason, until MOF republishes. |
| 2026-09-26 | MOF 国の財務書類 FY2021 page | The 合算 Excel link points to the FY2019 file (`fy2019/national/fy2019gassan.xlsx`). | The parser reads the fiscal year from each sheet's own date headers, so a misfiled workbook cannot mislabel data. The fetcher tries the correctly-named FY2021 file first, and now downloads it. National charts therefore start at FY2019 (from the FY2020 file's 前会計年度 column). |

## 9. What this site does not do

- No forecasts, projections or scenarios.
- No judgement words ("crisis", "safe") in chart titles or labels.
- No selective time ranges: charts default to the full available history.
